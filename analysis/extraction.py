"""Optional extraction via a separately obtained RepreGuard visualization loader."""

import hashlib
import importlib.util
import importlib.metadata
import json
import platform
import subprocess
from pathlib import Path
import numpy as np
from .data import load_records, select_texts
from .statistics import activation_tables


def load_upstream(path, model_path):
    source = Path(path).resolve() / "vis/repre_vis.py"
    if not source.is_file():
        raise ValueError("--upstream-repo must contain vis/repre_vis.py")
    spec = importlib.util.spec_from_file_location(
        "beyondhuai_upstream_repre_vis", source
    )
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except ImportError as error:
        raise RuntimeError(
            "Install the extraction and upstream requirements first"
        ) from error
    model, extractor = module.load_model_and_tokenizer(model_path)
    model.eval()
    return model, extractor, source


def extract_statistics(texts, extractor, hidden_layers, positions):
    result = {"mean": [], "abs": [], "rms": []}
    for text in texts:
        hidden = extractor.batched_string_to_hiddens(
            train_inputs=[text],
            rep_token=0,
            hidden_layers=hidden_layers,
            batch_size=1,
            which_hidden_states=None,
        )
        values = {key: [] for key in result}
        for layer in hidden_layers:
            x = np.asarray(hidden[layer])[0, :positions, :].astype(
                np.float32, copy=False
            )
            if x.shape[0] != positions:
                raise ValueError("Extractor returned fewer positions than requested")
            values["mean"].append(x.mean(axis=-1, dtype=np.float32))
            values["abs"].append(np.abs(x).mean(axis=-1, dtype=np.float32))
            values["rms"].append(np.sqrt(np.mean(x * x, axis=-1, dtype=np.float32)))
        for key in result:
            result[key].append(np.stack(values[key]))
    arrays = {key: np.stack(value).astype(np.float32) for key, value in result.items()}
    if not all(np.isfinite(value).all() for value in arrays.values()):
        raise ValueError("Nonfinite activation values")
    return arrays


def extract(config, data_path, upstream_repo, output):
    iterations = int(config.get("bootstrap_iter", 1000))
    seed = int(config.get("seed", 42))
    if iterations < 100 or int(config["sample_size"]) < 2:
        raise ValueError("Use >=100 bootstrap iterations and >=2 samples per class")
    records = load_records(data_path)
    if not all(
        isinstance(row.get("human_text"), str)
        and isinstance(row.get("direct_prompt"), str)
        for row in records
    ):
        raise ValueError(
            "Extraction expects paired records with human_text and direct_prompt fields"
        )
    model, extractor, loader = load_upstream(upstream_repo, config["model_path"])
    layers = config["layer_numbers"]
    if any(not 1 <= int(layer) <= model.config.num_hidden_layers for layer in layers):
        raise ValueError("Layer indices do not match the model")
    negative = [int(layer) - model.config.num_hidden_layers - 1 for layer in layers]
    n = int(config["sample_size"])
    positions = int(config["truncate_len"])
    htexts = select_texts(records, "human_text", extractor.tokenizer, n, positions)
    ltexts = select_texts(records, "direct_prompt", extractor.tokenizer, n, positions)
    human = extract_statistics(htexts, extractor, negative, positions)
    llm = extract_statistics(ltexts, extractor, negative, positions)
    layer, cell = activation_tables(human, llm, layers, iterations, seed)
    output = Path(output)
    np.savez_compressed(
        output / "sample_activations.npz",
        **{"human_" + k: v for k, v in human.items()},
        **{"llm_" + k: v for k, v in llm.items()},
        layer_numbers=np.array(layers)
    )
    layer.to_csv(output / "layer_effects.csv", index=False)
    cell.to_csv(output / "token_layer_effects.csv", index=False)
    cell.head(50).to_csv(output / "top50_token_layer_effects.csv", index=False)
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=Path(upstream_repo),
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        commit = "not available"
    packages = {}
    for name in ["numpy", "pandas", "torch", "transformers", "accelerate"]:
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = "not installed"
    record = {
        "run_id": config["run_id"],
        "model_path": config["model_path"],
        "data_path": str(data_path),
        "input_sha256": hashlib.sha256(Path(data_path).read_bytes()).hexdigest(),
        "sample_size_per_group": n,
        "truncate_len": positions,
        "hidden_layers": layers,
        "seed": seed,
        "bootstrap_iter": iterations,
        "upstream_commit_for_this_run": commit,
        "loader_sha256": hashlib.sha256(loader.read_bytes()).hexdigest(),
        "python": platform.python_version(),
        "packages": packages,
        "model_resolved_commit": getattr(model.config, "_commit_hash", None),
        "selection": "Independent stable descending character-length ranking; minimum token length",
        "selected_text_sha256": {
            "human": [hashlib.sha256(t.encode()).hexdigest() for t in htexts],
            "llm": [hashlib.sha256(t.encode()).hexdigest() for t in ltexts],
        },
        "overall_mean_signed_activation": {
            "human": float(human["mean"].mean()),
            "llm": float(llm["mean"].mean()),
            "llm_minus_human": float(llm["mean"].mean() - human["mean"].mean()),
        },
        "note": "New descriptive extraction; not a detector score or proof of historical cohort identity.",
    }
    (output / "analysis_summary.json").write_text(
        json.dumps(record, indent=2), encoding="utf-8"
    )
    return layer, cell

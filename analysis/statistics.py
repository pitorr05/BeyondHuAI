"""Document-level contrasts and reconstruction from immutable archived CSVs."""

import json
from pathlib import Path

import numpy as np
import pandas as pd


def effect_size(human, llm, axis=0):
    human, llm = np.asarray(human), np.asarray(llm)
    if human.shape[axis] < 2 or llm.shape[axis] < 2:
        raise ValueError("Sample variances require at least two documents per group")
    if not np.isfinite(human).all() or not np.isfinite(llm).all():
        raise ValueError("Activation statistics must be finite")
    n_h, n_l = human.shape[axis], llm.shape[axis]
    mh, ml = human.mean(axis=axis), llm.mean(axis=axis)
    difference = ml - mh
    pooled = (
        (n_h - 1) * human.var(axis=axis, ddof=1)
        + (n_l - 1) * llm.var(axis=axis, ddof=1)
    ) / (n_h + n_l - 2)
    epsilon = max(
        float(np.std(np.concatenate([human.reshape(-1), llm.reshape(-1)]))) * 1e-6,
        1e-12,
    )
    return (
        mh,
        ml,
        difference,
        difference / np.maximum(np.sqrt(np.maximum(pooled, 0)), epsilon),
    )


def bootstrap_difference(human_docs, llm_docs, iterations=1000, seed=42):
    if iterations < 100:
        raise ValueError("Use at least 100 bootstrap iterations")
    rng = np.random.default_rng(seed)
    boot = np.empty((iterations, human_docs.shape[1]))
    for b in range(iterations):
        ih = rng.integers(0, len(human_docs), size=len(human_docs))
        il = rng.integers(0, len(llm_docs), size=len(llm_docs))
        boot[b] = llm_docs[il].mean(axis=0) - human_docs[ih].mean(axis=0)
    return np.percentile(boot, [2.5, 97.5], axis=0)


def activation_tables(human, llm, layer_numbers, iterations=1000, seed=42):
    """Inputs contain per-document coordinate means, absolutes and RMS maps."""
    hm, lm = human["mean"], llm["mean"]
    if (
        hm.ndim != 3
        or lm.ndim != 3
        or hm.shape[1:] != lm.shape[1:]
        or hm.shape[1] != len(layer_numbers)
    ):
        raise ValueError("Expected matching [documents, layers, positions] arrays")
    mh, ml, delta, d = effect_size(hm.mean(axis=2), lm.mean(axis=2))
    low, high = bootstrap_difference(hm.mean(axis=2), lm.mean(axis=2), iterations, seed)
    layer = pd.DataFrame(
        {
            "model_layer": layer_numbers,
            "n_human": len(hm),
            "n_llm": len(lm),
            "human_mean_per_document": mh,
            "llm_mean_per_document": ml,
            "difference_llm_minus_human": delta,
            "cohens_d": d,
            "bootstrap_95ci_low_difference": low,
            "bootstrap_95ci_high_difference": high,
        }
    )
    ch, cl, cdiff, cell_d = effect_size(hm, lm)
    ah, al = human["abs"].mean(axis=0), llm["abs"].mean(axis=0)
    rms_diff = llm["rms"].mean(axis=0) - human["rms"].mean(axis=0)
    cell = pd.DataFrame(
        {
            "model_layer": np.repeat(layer_numbers, hm.shape[2]),
            "token_position": np.tile(np.arange(hm.shape[2]), len(layer_numbers)),
            "human_mean_activation": ch.ravel(),
            "llm_mean_activation": cl.ravel(),
            "difference_llm_minus_human": cdiff.ravel(),
            "cohens_d": cell_d.ravel(),
            "human_mean_absolute_activation": ah.ravel(),
            "llm_mean_absolute_activation": al.ravel(),
            "difference_absolute_activation": (al - ah).ravel(),
            "difference_rms_activation": rms_diff.ravel(),
        }
    )
    return layer.sort_values("model_layer"), cell.sort_values(
        "cohens_d", key=abs, ascending=False, kind="stable"
    )


def read_archives(results_root):
    runs = Path(results_root) / "runs"
    layers, cells, metadata = [], [], {}
    for folder in sorted(p for p in runs.iterdir() if p.is_dir()):
        run = folder.name
        dataset, backbone, _ = run.split("-")
        for filename, collection in [
            ("layer_effects.csv", layers),
            ("token_layer_effects.csv", cells),
        ]:
            frame = pd.read_csv(folder / filename)
            if frame.duplicated(
                ["model_layer"] + (["token_position"] if "token" in filename else [])
            ).any():
                raise ValueError(f"Duplicate coordinates in {folder / filename}")
            if not np.isfinite(frame.select_dtypes(include="number").to_numpy()).all():
                raise ValueError(f"Nonfinite values in {folder / filename}")
            frame["experiment"], frame["dataset"], frame["backbone"] = (
                run,
                dataset,
                backbone,
            )
            if filename == "layer_effects.csv":
                if not (frame.n_human == frame.n_llm).all():
                    raise ValueError(f"Archived per-class count is unequal in {folder}")
                frame["n_per_class"] = frame.n_human
            collection.append(frame)
        metadata[run] = json.loads((folder / "analysis_summary.json").read_text())
    if not layers:
        raise ValueError(f"No archived runs under {runs}")
    return (
        pd.concat(layers, ignore_index=True),
        pd.concat(cells, ignore_index=True),
        metadata,
    )


def summarize_archives(layers, cells, metadata):
    overview, concentration = [], []
    for run in sorted(metadata):
        lf = layers[layers.experiment == run]
        cf = cells[cells.experiment == run]
        peak = lf.loc[lf.cohens_d.abs().idxmax()]
        cp = cf.loc[cf.cohens_d.abs().idxmax()]
        excluded = (
            (lf.bootstrap_95ci_low_difference > 0)
            | (lf.bootstrap_95ci_high_difference < 0)
        ).sum()
        info = metadata[run]
        overview.append(
            dict(
                experiment=run,
                dataset=lf.dataset.iloc[0],
                backbone=lf.backbone.iloc[0],
                n_per_class=int(info["sample_size_per_group"]),
                layers=len(lf),
                tokens=int(info["truncate_len"]),
                mean_signed_delta=info["overall_mean_signed_activation"][
                    "llm_minus_human"
                ],
                peak_layer=int(peak.model_layer),
                peak_cohens_d=peak.cohens_d,
                peak_delta=peak.difference_llm_minus_human,
                peak_ci_low=peak.bootstrap_95ci_low_difference,
                peak_ci_high=peak.bootstrap_95ci_high_difference,
                n_layers_ci_exclude_zero=int(excluded),
                fraction_layers_ci_exclude_zero=excluded / len(lf),
                n_layer_token_cells=len(cf),
                max_abs_token_cohens_d=abs(cp.cohens_d),
            )
        )
        concentration.append(
            dict(
                experiment=run,
                top_abs_d_layer=int(cp.model_layer),
                top_abs_d_position=int(cp.token_position),
                top_abs_d=cp.cohens_d,
                top_abs_d_sign=int(np.sign(cp.cohens_d)),
                top_abs_delta=cp.difference_llm_minus_human,
                fraction_token_cells_abs_d_ge_05=float(
                    (cf.cohens_d.abs() >= 0.5).mean()
                ),
                fraction_token_cells_abs_d_ge_08=float(
                    (cf.cohens_d.abs() >= 0.8).mean()
                ),
            )
        )
    pairs = [
        ("0.5B", "DetectRL-0.5B-n274", "HC3-0.5B-n200"),
        ("0.5B", "DetectRL-0.5B-n274", "HC3-0.5B-n500"),
        ("0.5B", "HC3-0.5B-n200", "HC3-0.5B-n500"),
        ("1.5B", "DetectRL-1.5B-n274", "HC3-1.5B-n500"),
        ("7B", "DetectRL-7B-n274", "HC3-7B-n500"),
        ("7B", "DetectRL-7B-n274", "RAID-7B-n500"),
        ("7B", "HC3-7B-n500", "RAID-7B-n500"),
    ]
    transfer = []
    for backbone, a, b in pairs:
        if a not in metadata or b not in metadata:
            continue
        left = layers[layers.experiment == a].set_index("model_layer").cohens_d
        right = layers[layers.experiment == b].set_index("model_layer").cohens_d
        joined = pd.concat([left, right], axis=1, keys=["a", "b"]).dropna()
        ta = set(left.abs().nlargest(5).index)
        tb = set(right.abs().nlargest(5).index)
        transfer.append(
            dict(
                backbone=backbone,
                experiment_a=a,
                experiment_b=b,
                n_shared_layers=len(joined),
                pearson_r=joined.a.corr(joined.b),
                spearman_r=joined.a.rank().corr(joined.b.rank()),
                sign_agreement_fraction=float(
                    (np.sign(joined.a) == np.sign(joined.b)).mean()
                ),
                top5_overlap=len(ta & tb),
                top5_jaccard=len(ta & tb) / len(ta | tb),
            )
        )
    return {
        "Table_1_Experimental_Overview.csv": pd.DataFrame(overview),
        "Table_2_Token_Position_Concentration.csv": pd.DataFrame(concentration),
        "Table_3_Layer_Profile_Transfer.csv": pd.DataFrame(transfer),
        "Table_S1_All_Layer_Effects.csv": layers,
        "Table_S2_All_Token_Layer_Effects.csv": cells,
    }


def verify_summaries(tables, reference):
    """Compare archived numeric tables by stable keys, independent of CSV row order."""
    report = {}
    for name, actual in tables.items():
        expected = pd.read_csv(Path(reference) / name)
        keys = (
            ["experiment", "model_layer", "token_position"]
            if name.startswith("Table_S2")
            else (
                ["experiment", "model_layer"]
                if name.startswith("Table_S1")
                else (
                    ["experiment_a", "experiment_b"]
                    if name.startswith("Table_3")
                    else ["experiment"]
                )
            )
        )
        a = actual.sort_values(keys).reset_index(drop=True)
        b = expected.sort_values(keys).reset_index(drop=True)
        if set(a.columns) != set(b.columns) or len(a) != len(b):
            raise ValueError(f"Schema or record count differs: {name}")
        for col in b:
            if pd.api.types.is_numeric_dtype(b[col]):
                if not np.allclose(
                    a[col], b[col], rtol=1e-8, atol=1e-10, equal_nan=True
                ):
                    raise ValueError(f"Archived values differ: {name}/{col}")
            elif a[col].astype(str).tolist() != b[col].astype(str).tolist():
                raise ValueError(f"Archived labels differ: {name}/{col}")
        report[name] = {"rows": len(a), "matches_archive": True}
    return report

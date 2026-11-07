"""Read released data and select the independently length-ranked cohorts."""

import json
from pathlib import Path


def load_records(path):
    path = Path(path)
    with path.open(encoding="utf-8-sig") as handle:
        first = handle.read(1)
        handle.seek(0)
        if first == "[":
            records = json.load(handle)
        else:
            records = [json.loads(line) for line in handle if line.strip()]
    if (
        not isinstance(records, list)
        or not records
        or not all(isinstance(r, dict) for r in records)
    ):
        raise ValueError(f"{path}: expected a nonempty record list or JSONL stream")
    return records


def select_texts(records, field, tokenizer, sample_size, truncate_len):
    if sample_size < 2 or truncate_len < 1:
        raise ValueError(
            "Use at least two documents per group and a positive token count"
        )
    # Stable sorting preserves source order for equal character lengths.
    texts = [
        r[field] for r in records if isinstance(r.get(field), str) and r[field].strip()
    ]
    texts.sort(key=len, reverse=True)
    selected = []
    for text in texts:
        ids = tokenizer(text, add_special_tokens=True, truncation=False)["input_ids"]
        if len(ids) >= truncate_len:
            selected.append(text)
        if len(selected) == sample_size:
            return selected
    raise ValueError(
        f"{field}: only {len(selected)} texts have at least {truncate_len} tokens; requested {sample_size}"
    )


def output_directory(path, protected_roots=()):
    path = Path(path).resolve()
    if any(
        path == Path(p).resolve() or path.is_relative_to(Path(p).resolve())
        for p in protected_roots
    ):
        raise ValueError("Output must be separate from released inputs and assets")
    if path.exists() and any(path.iterdir()):
        raise ValueError(f"Refusing to overwrite a nonempty directory: {path}")
    path.mkdir(parents=True, exist_ok=True)
    return path

import ast
import csv
import hashlib
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

import numpy as np
import pandas as pd

from analysis.data import load_records, select_texts, output_directory
from analysis.statistics import (
    effect_size,
    bootstrap_difference,
    activation_tables,
    read_archives,
    summarize_archives,
    verify_summaries,
)

ROOT = Path(__file__).resolve().parents[1]


class SelectionTests(unittest.TestCase):
    def test_jsonl_unicode_line_separator_is_not_record_boundary(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "data.json"
            records = [
                {"text": "first\u2028still first", "label": "human"},
                {"text": "second", "label": "machine"},
            ]
            path.write_text(
                "\n".join(json.dumps(r, ensure_ascii=False) for r in records),
                encoding="utf-8",
            )
            self.assertEqual(load_records(path), records)

    def test_pair_array_is_supported(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "data.json"
            path.write_text('[{"human_text":"h","direct_prompt":"m"}]')
            self.assertEqual(len(load_records(path)), 1)

    def test_independent_stable_length_selection_and_minimum_tokens(self):
        records = [
            {"h": "abc", "m": "q"},
            {"h": "xyz", "m": "longer"},
            {"h": "", "m": "longest"},
            {"h": "ab", "m": ""},
        ]
        tokenizer = lambda text, **kwargs: {"input_ids": list(text)}
        self.assertEqual(select_texts(records, "h", tokenizer, 2, 3), ["abc", "xyz"])
        self.assertEqual(
            select_texts(records, "m", tokenizer, 2, 3), ["longest", "longer"]
        )
        with self.assertRaises(ValueError):
            select_texts(records, "h", tokenizer, 3, 3)

    def test_outputs_cannot_replace_released_inputs_or_existing_work(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            data = base / "data"
            data.mkdir()
            with self.assertRaises(ValueError):
                output_directory(data / "new", [data])
            out = output_directory(base / "out")
            (out / "keep.txt").write_text("keep")
            with self.assertRaises(ValueError):
                output_directory(out)
            self.assertEqual((out / "keep.txt").read_text(), "keep")


class StatisticsTests(unittest.TestCase):
    def test_pooled_standard_deviation_and_sign(self):
        mh, ml, difference, d = effect_size(
            np.array([-1.0, 0.0, 1.0]), np.array([1.0, 2.0, 3.0])
        )
        self.assertEqual(mh, 0)
        self.assertEqual(ml, 2)
        self.assertEqual(difference, 2)
        self.assertEqual(d, 2)
        self.assertEqual(
            effect_size(np.array([1.0, 2.0, 3.0]), np.array([-1.0, 0.0, 1.0]))[3], -2
        )

    def test_bad_or_degenerate_inputs(self):
        with self.assertRaises(ValueError):
            effect_size(np.array([1.0]), np.array([2.0]))
        with self.assertRaises(ValueError):
            effect_size(np.array([1.0, np.nan]), np.array([2.0, 3.0]))
        self.assertTrue(np.isfinite(effect_size(np.ones(3), np.ones(3))[3]))

    def test_bootstrap_reproducibility_uses_document_axis(self):
        h = np.arange(12, dtype=float).reshape(4, 3)
        m = h + 2
        a = bootstrap_difference(h, m, 100, 42)
        b = bootstrap_difference(h, m, 100, 42)
        np.testing.assert_array_equal(a, b)
        self.assertEqual(a.shape, (2, 3))
        with self.assertRaises(ValueError):
            bootstrap_difference(h, m, 10, 42)

    def test_activation_pooling_and_position_indices(self):
        h = np.array(
            [
                [[1.0, 3.0], [2.0, 4.0]],
                [[3.0, 5.0], [4.0, 6.0]],
                [[5.0, 7.0], [6.0, 8.0]],
            ],
            dtype=np.float32,
        )
        m = h + 2
        human = {"mean": h, "abs": np.abs(h), "rms": np.abs(h)}
        machine = {"mean": m, "abs": np.abs(m), "rms": np.abs(m)}
        layer, cell = activation_tables(human, machine, [3, 2], 100, 42)
        np.testing.assert_allclose(layer.difference_llm_minus_human, 2)
        np.testing.assert_allclose(layer.cohens_d, 1)
        self.assertEqual(set(cell.token_position), {0, 1})
        self.assertEqual(len(cell), 4)


class ExtractionInterfaceTests(unittest.TestCase):
    def test_mock_extraction_keeps_layer_mapping_full_text_and_provenance(self):
        from analysis.extraction import extract

        class Extractor:
            def __init__(self):
                self.seen = []
                self.tokenizer = lambda text, **kwargs: {"input_ids": list(text)}

            def batched_string_to_hiddens(self, train_inputs, hidden_layers, **kwargs):
                self.seen.append((train_inputs[0], hidden_layers, kwargs))
                return {
                    layer: np.full(
                        (1, len(train_inputs[0]), 3),
                        len(train_inputs[0]) + layer,
                        dtype=np.float32,
                    )
                    for layer in hidden_layers
                }

        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            data = base / "pairs.json"
            loader = base / "loader.py"
            loader.write_text("# fixture")
            records = [
                {"human_text": "human long", "direct_prompt": "machine long"},
                {"human_text": "short", "direct_prompt": "other"},
            ]
            data.write_text(json.dumps(records))
            dest = base / "out"
            dest.mkdir()
            extractor = Extractor()
            model = SimpleNamespace(
                config=SimpleNamespace(num_hidden_layers=3, _commit_hash="test-only")
            )
            config = {
                "model_path": "test-only",
                "run_id": "test-only",
                "sample_size": 2,
                "truncate_len": 2,
                "layer_numbers": [3, 2],
                "bootstrap_iter": 100,
                "seed": 42,
            }
            with patch(
                "analysis.extraction.load_upstream",
                return_value=(model, extractor, loader),
            ):
                layer, cell = extract(config, data, base, dest)
            self.assertEqual(len(layer), 2)
            self.assertEqual(len(cell), 4)
            self.assertTrue(all(item[1] == [-1, -2] for item in extractor.seen))
            self.assertTrue(all(len(item[0]) > 2 for item in extractor.seen))
            self.assertTrue(all(item[2]["rep_token"] == 0 for item in extractor.seen))
            with np.load(dest / "sample_activations.npz") as cache:
                self.assertEqual(cache["human_mean"].shape, (2, 2, 2))
            report = json.loads((dest / "analysis_summary.json").read_text())
            self.assertEqual(len(report["selected_text_sha256"]["human"]), 2)
            self.assertEqual(
                report["input_sha256"], hashlib.sha256(data.read_bytes()).hexdigest()
            )

    def test_wrong_schema_fails_before_upstream_model_loading(self):
        from analysis.extraction import extract

        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "texts.json"
            path.write_text('[{"text":"h","label":"human"}]')
            config = {
                "sample_size": 2,
                "bootstrap_iter": 100,
                "model_path": "must-not-load",
            }
            with patch("analysis.extraction.load_upstream") as load:
                with self.assertRaises(ValueError):
                    extract(config, path, folder, folder)
                load.assert_not_called()


class ReleasedArtifactTests(unittest.TestCase):
    def test_archived_reconstruction_matches_all_five_tables(self):
        result = ROOT / "results/representation"
        layers, cells, metadata = read_archives(result)
        self.assertEqual((len(metadata), len(layers), len(cells)), (8, 204, 42840))
        tables = summarize_archives(layers, cells, metadata)
        self.assertTrue(
            all(
                row["matches_archive"]
                for row in verify_summaries(tables, result / "summaries").values()
            )
        )

    def test_released_images_are_byte_identical_to_manifest(self):
        manifest = json.loads((ROOT / "assets/manifest.json").read_text())
        self.assertEqual(len(manifest["figures"]), 9)
        for item in manifest["figures"]:
            self.assertEqual(
                hashlib.sha256(
                    (ROOT / item["repository_asset"]).read_bytes()
                ).hexdigest(),
                item["sha256"],
            )
            self.assertTrue((ROOT / item["preview"]).is_file())

    def test_archive_checksums_include_existing_activation_caches(self):
        manifest = json.loads(
            (ROOT / "results/representation/archive-manifest.json").read_text()
        )
        self.assertEqual(sum(item["path"].endswith(".npz") for item in manifest), 6)
        for item in manifest:
            self.assertEqual(
                hashlib.sha256((ROOT / item["path"]).read_bytes()).hexdigest(),
                item["sha256"],
            )

    def test_data_units_counts_and_hashes(self):
        with (ROOT / "data/catalog.csv").open(encoding="utf-8", newline="") as f:
            catalog = list(csv.DictReader(f))
        self.assertEqual(len(catalog), 14)
        for item in catalog:
            path = ROOT / item["path"]
            records = load_records(path)
            self.assertEqual(len(records), int(item["records"]))
            self.assertEqual(
                hashlib.sha256(path.read_bytes()).hexdigest(), item["sha256"]
            )
            if item["unit"] == "human/AI storage pair":
                self.assertEqual(int(item["text_slots"]), 2 * len(records))

    def test_current_detector_correction_and_protocol_separation(self):
        frame = pd.read_csv(ROOT / "results/detectors/five-detector-comparison.csv")
        row = frame[
            (frame.model.str.startswith("RepreGuard")) & (frame.dataset == "DetectRL")
        ].iloc[0]
        self.assertEqual(row.f1_percent, 89.82)
        self.assertAlmostEqual(
            round(
                2
                * row.precision_percent
                * row.recall_percent
                / (row.precision_percent + row.recall_percent),
                2,
            ),
            row.f1_percent,
        )
        cross = pd.read_csv(ROOT / "results/detectors/cross-benchmark-comparison.csv")
        self.assertEqual(len(cross), 5)
        self.assertEqual(len(frame), 10)

    def test_catalog_is_cited_snapshot_not_full_bibliography_count(self):
        with (ROOT / "survey/catalog.csv").open(encoding="utf-8") as f:
            catalog = list(csv.DictReader(f))
        bib = (ROOT / "survey/references.bib").read_text(encoding="utf-8")
        self.assertEqual(len(catalog), 82)
        self.assertEqual(len(re.findall(r"@\w+\s*\{", bib)), 103)
        keys = set(re.findall(r"@\w+\s*\{\s*([^,]+),", bib))
        self.assertTrue(all(row["citation_key"] in keys for row in catalog))

    def test_all_document_relative_links_and_images_resolve(self):
        for path in ROOT.rglob("*.md"):
            if any(part in path.parts for part in [".git", "outputs", "external"]):
                continue
            text = path.read_text(encoding="utf-8")
            urls = re.findall(r"!?\[[^\]]*\]\(([^\s)]+)\)", text) + re.findall(
                r'<img[^>]+src="([^"]+)"', text
            )
            for url in urls:
                if re.match(r"^[a-zA-Z]+:", url) or url.startswith("#"):
                    continue
                self.assertTrue(
                    (path.parent / url.split("#")[0]).resolve().exists(),
                    f"{path.relative_to(ROOT)} -> {url}",
                )

    def test_python_files_are_python_and_do_not_discover_manuscripts(self):
        files = [ROOT / "insight.py", *list((ROOT / "analysis").glob("*.py"))]
        for path in files:
            text = path.read_text()
            ast.parse(text)
            self.assertNotIn("/data/SWIFT/", text)
            self.assertNotIn("render_paar", text)
            self.assertNotIn("Beyond Human vs AI latex", text)


if __name__ == "__main__":
    unittest.main()

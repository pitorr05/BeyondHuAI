"""CLI for archived reconstruction and optional representation extraction."""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="BeyondHuAI representation diagnostics; no detector evaluation"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    rebuild = commands.add_parser(
        "rebuild", help="Reconstruct tables/plots from archived CSVs on CPU"
    )
    rebuild.add_argument(
        "--results-root", type=Path, default=ROOT / "results/representation"
    )
    rebuild.add_argument("--output-dir", type=Path, default=ROOT / "outputs/rebuilt")
    rebuild.add_argument("--tables-only", action="store_true")
    extraction = commands.add_parser(
        "extract", help="Collect hidden states using a separate RepreGuard loader"
    )
    extraction.add_argument("--config", type=Path, required=True)
    extraction.add_argument("--upstream-repo", type=Path, required=True)
    extraction.add_argument("--data-path", type=Path)
    extraction.add_argument("--output-dir", type=Path)
    args = parser.parse_args(argv)
    from .data import output_directory

    try:
        if args.command == "rebuild":
            from .statistics import read_archives, summarize_archives, verify_summaries

            layers, cells, metadata = read_archives(args.results_root)
            tables = summarize_archives(layers, cells, metadata)
            comparison = verify_summaries(tables, args.results_root / "summaries")
            out = output_directory(
                args.output_dir,
                [ROOT / "assets", ROOT / "data", ROOT / "results", args.results_root],
            )
            for name, frame in tables.items():
                frame.to_csv(out / name, index=False)
            if not args.tables_only:
                from .plots import render_archived

                render_archived(layers, cells, tables, out)
            report = {
                "source": "Archived CSVs; no inference or new bootstrap resampling",
                "tables": comparison,
                "limitations": "Descriptive contrasts, not detector predictions, authorship labels or predictive transfer.",
            }
            (out / "rebuild_report.json").write_text(
                json.dumps(report, indent=2), encoding="utf-8"
            )
        else:
            config = json.loads(args.config.read_text(encoding="utf-8"))
            data_path = args.data_path or ROOT / config["data_path"]
            if not data_path.is_file():
                raise ValueError(
                    f"Input not released at {data_path}; see data/README.md and use --data-path"
                )
            out = output_directory(
                args.output_dir or ROOT / "outputs" / config["run_id"],
                [ROOT / "assets", ROOT / "data", ROOT / "results"],
            )
            from .extraction import extract
            from .plots import render_run

            layer, cell = extract(config, data_path, args.upstream_repo, out)
            render_run(layer, cell, out)
        print(f"Saved {args.command} outputs to {out}")
    except (ValueError, FileNotFoundError, RuntimeError) as error:
        parser.exit(2, str(error) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

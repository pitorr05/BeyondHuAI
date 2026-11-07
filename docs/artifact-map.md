# Artifact map

| Manuscript object | Repository artifact | Reconstruction |
|---|---|---|
| Section III taxonomy/literature | `survey/papers.md`, `survey/catalog.csv`, `survey/references.bib` | Bibliographic snapshot; no inferred screening ledger |
| Section V benchmark scope | `survey/benchmarks.md` | Transcribed scale and source units |
| Detector performance table | `results/detectors/five-detector-comparison.csv` | Reported values; no raw prediction reconstruction |
| Cross-benchmark detector table | `results/detectors/cross-benchmark-comparison.csv` | Separate reported protocol |
| Representation configuration/peak table | `results/representation/summaries/Table_1_Experimental_Overview.csv` | Rebuilt from run CSVs and archived global means |
| Cell concentration | `results/representation/summaries/Table_2_Token_Position_Concentration.csv` | Rebuilt from all layer/position cells |
| Profile alignment | `results/representation/summaries/Table_3_Layer_Profile_Transfer.csv` | Same-backbone numerical layer alignment |
| Complete diagnostic records | `Table_S1_All_Layer_Effects.csv`, `Table_S2_All_Token_Layer_Effects.csv` under summaries | 204 and 42,840 rows |
| Figures 1, 2 and 7 | `assets/paper/` | Supplied artwork; not regenerated |
| Figures 3–6, 8 and 9 | `assets/paper/`, with separate reconstruction in `outputs/` | Archived-data plots; styles may differ |

`assets/manifest.json` connects each copied image to its manuscript file name and checksum. `results/representation/archive-manifest.json` records the released per-run files. Historical NPZ caches are retained where available; two runs have only CSV/PDF/JSON outputs. Missing activation caches are not fabricated.

## Migration from the initial repository layout

| Previous location | Current location |
|---|---|
| Root benchmark JSON files | `data/benchmark/` |
| `Repre/` | `data/paired/` |
| `Exper/` run directories | `results/representation/runs/<run-id>/` |
| `Exper/` aggregate CSVs | `results/representation/summaries/` |
| Root `insight.py` shell wrapper | Root CLI entry point plus `analysis/` Python modules |
| Root converter with fixed local paths | Format/selection utilities in `analysis/data.py`; original metadata issues documented |
| `Paper/` local PDF collection | Publication links and BibTeX in `survey/` |
| Original worksheet | `results/detectors/archive/original-worksheet.xlsx` (historical) |

The initial layout remains in Git history. The author's manuscript working directories and local PDF library are not moved or modified by this repository reorganization.

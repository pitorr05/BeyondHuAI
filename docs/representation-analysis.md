# Representation diagnostics

## Scope

This is the coordinate-pooled activation analysis in Section VI.C and the diagnostic appendix. It is distinct from the trained or reference-fitted detector decision functions in the other experiments. The code does not implement PAAR.

The released archive has eight runs: DetectRL/0.5B, 1.5B and 7B with 274 documents per class; HC3/0.5B with 200 and 500 per class; HC3/1.5B and 7B with 500 per class; and RAID/7B with 500 per class. The [run catalog](../results/representation/run_catalog.csv) specifies cache and input availability.

## Reconstruct from archived measurements

```bash
python -m pip install -r requirements-analysis.txt
python -m analysis.insight rebuild --output-dir outputs/rebuilt
```

The five reconstructed tables are compared by record keys and numeric values against `results/representation/summaries/`. Their row counts are 8, 8, 7, 204 and 42,840. Floating-point comparisons use relative tolerance 1e-8 and absolute tolerance 1e-10. Rebuild does not invent missing records or resample bootstrap intervals from summary rows.

The global signed contrast is retained from the archived `analysis_summary.json`; layer and cell statistics come from each run's CSVs. This preserves the recorded floating-point pooling result rather than replacing it with an independently rounded mean of means.

Plots in `outputs/` use full, explicitly labeled ranges. Historical `activation_insights.pdf` files used percentile-based display limits. New plot styling can therefore differ from those archived PDFs and from the fixed artwork in `assets/paper/`; the numerical records remain the comparison target. Confidence interval endpoints are drawn directly because a percentile interval need not contain its point estimate.

## Fresh hidden-state extraction

Extraction is optional. It needs model weights and appropriate hardware; the upstream loader uses float16 and automatic device placement. The CPU rebuild is the tested lightweight path. No claim is made that the GPU extraction reproduces historical measurements bit for bit.

```bash
git clone https://github.com/NLP2CT/RepreGuard.git external/RepreGuard
# In a separate extraction environment (upstream recommends Python 3.10):
python -m pip install -r external/RepreGuard/requirements.txt
python -m pip install -r requirements-extraction.txt

python -m analysis.insight extract \
  --config configs/representation/HC3-0.5B-n200.json \
  --upstream-repo external/RepreGuard \
  --output-dir outputs/hc3-0p5b-new
```

Python 3.10 can use the extraction requirements independently of the pinned CPU-analysis environment. The RepreGuard loader is imported from the external checkout; its source is not vendored or relicensed. Record the upstream revision used in a new run. No upstream revision is retroactively attributed to the historical archive.

HC3 input is available in `data/paired/`. The exact historical DetectRL and RAID input files referenced by the run metadata are not included. Follow the [RepreGuard dataset instructions](https://github.com/NLP2CT/RepreGuard#datasets) and provide the appropriate file explicitly:

```bash
python -m analysis.insight extract \
  --config configs/representation/DetectRL-0.5B-n274.json \
  --upstream-repo external/RepreGuard \
  --data-path /path/to/detectrl_train_dataset_llm_type_mix_llms.json \
  --output-dir outputs/detectrl-0p5b-new
```

The seven general benchmark splits and seven paired-format files are not automatically substituted for missing historical inputs. File names and compatible schemas alone cannot establish sample identity.

## Selection and statistics

Human and machine texts are filtered and stably sorted **independently** by descending character length. Only texts with at least 210 tokenized positions are retained; the first n qualifying texts in each group are selected. This is neither random nor length-matched sampling, and the storage pair index is not treated as a matched experimental unit.

The observer is Qwen2.5-Instruct: layers 2–24 for 0.5B and 2–28 for 1.5B/7B. Extraction preserves the upstream procedure: a single-text forward pass followed by pooling of the first 210 hidden-state positions. It does not truncate the text before that forward pass.

For each document/layer/position, coordinate means, coordinate mean absolutes and coordinate RMS values are collected. Layer contrasts pool positions within each document before computing class means and a pooled within-class standard deviation. Positive differences and Cohen's d mean LLM minus human. The bootstrap resamples documents independently within each class (1,000 iterations, seed 42 in the archived script defaults).

Intervals, counts excluding zero, selected peaks, layer correlations and top-five overlap are exploratory and unadjusted for multiplicity or selection. Numerical layer indices do not establish homologous representations across model sizes. Profile correlation is not predictive transfer, calibration or authorship localization.

## Implementation

`analysis/insight.py` handles the CLI; `data.py` handles loading/selection and safe destinations; `extraction.py` adapts the upstream visualization loader; `statistics.py` handles contrasts/bootstrap/archive reconstruction; `plots.py` writes plots only to an explicit output directory.

Fresh runs record the input checksum, selected text hashes, seed, bootstrap count, package versions, upstream loader hash/commit and available model revision metadata. These records describe the new run only. An incomplete or conflicting historical record is left visible rather than filled with inferred facts.

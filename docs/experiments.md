# Experimental resources

## Detector experiments

The survey reports two evaluation protocols:

| Protocol | Methods | Evaluation data |
|---|---|---|
| [Five-detector comparison](../results/detectors/five-detector-comparison.csv) | RepreGuard, PRDetect, StyleDecipher, Binoculars, Fast-DetectGPT | HC3 and DetectRL |
| [Cross-benchmark comparison](../results/detectors/cross-benchmark-comparison.csv) | PRDetect and the representation-based configuration | HC3, GPT-3.5 mixed, RAID Llama greedy, RAID Llama sampling, RAID Mistral |

| Method | Original implementation |
|---|---|
| RepreGuard | [NLP2CT/RepreGuard](https://github.com/NLP2CT/RepreGuard) |
| PRDetect | [thulx18/PRDetect](https://github.com/thulx18/PRDetect) |
| StyleDecipher | [SiyuanLi00/StyleDecipher](https://github.com/SiyuanLi00/StyleDecipher) |
| Binoculars | [ahans30/Binoculars](https://github.com/ahans30/Binoculars) |
| Fast-DetectGPT | [baoguangsheng/fast-detect-gpt](https://github.com/baoguangsheng/fast-detect-gpt) |

The experiments use these upstream implementations with local data/model configurations. Detector training and evaluation code is maintained in the upstream repositories. All metric columns in the result tables are percentages.

The cross-benchmark protocol reports 2,000 HC3 training samples, 1,000 validation samples, 1,000 test samples, 1,000 GPT-3.5 mixed samples and 2,000 samples in each RAID test configuration. Protocol sample counts and packaged file counts are distinct; [the data catalog](../data/catalog.csv) records the latter. The two protocols retain their separate HC3 results.

The RepreGuard/DetectRL F1 in the five-detector table is **89.82%**, calculated as `2 × 99.95 × 81.56 / (99.95 + 81.56)` from reported precision and recall, as confirmed by the authors. [Result provenance](../results/detectors/provenance.json) records this correction. The underlying prediction logs are unavailable for independent recalculation. Other metric values follow the manuscript. Low-FPR TPR values are ROC-interpolated estimates; the human sample counts do not directly resolve FPR = 0.01%.

## Representation analysis

The coordinate-pooled diagnostics cover eight configurations: DetectRL/0.5B, 1.5B and 7B with 274 documents per class; HC3/0.5B with 200 and 500 per class; HC3/1.5B and 7B with 500 per class; and RAID/7B with 500 per class. [The run catalog](../results/representation/run_catalog.csv) records input and activation-cache availability.

Human and machine texts are selected independently by descending character length, with stable ordering for ties. The first n texts containing at least 210 tokenized positions are retained in each class. The analyzed Qwen2.5-Instruct layers are 2–24 for 0.5B and 2–28 for 1.5B/7B. Each single-text forward pass is followed by pooling of the first 210 hidden-state positions.

Coordinate mean, mean-absolute and RMS statistics are collected per document/layer/position. Layer-level summaries pool positions within documents before computing class contrasts. Positive differences and Cohen's d indicate LLM minus human. Bootstrap intervals resample documents independently within each class; the analysis script defaults are 1,000 iterations and seed 42.

The length-conditioned cohorts are neither random nor length-matched samples. Intervals and selected peaks are exploratory and unadjusted for multiplicity or selection. Profile correlations describe numerical layer alignment, rather than predictive transfer or local authorship labels.

### Rebuilding tables and figures

```bash
python -m pip install -r requirements-analysis.txt
python -m analysis.insight rebuild --output-dir outputs/rebuilt
```

The command reads the per-run CSVs and recorded global means, reconstructs five tables, and compares them with the released summaries. Their row counts are 8, 8, 7, 204 and 42,840. Numeric comparisons use relative tolerance 1e-8 and absolute tolerance 1e-10. Bootstrap endpoints are read from the archive in this mode.

Plots use full, labeled value ranges; archived per-run activation PDFs used percentile-based display limits. The [gallery](figure-gallery.md) preserves the figures used in the manuscript. Reconstructed plots are written separately under `outputs/`; existing nonempty output directories are preserved.

## Hidden-state extraction

Fresh extraction requires model weights and suitable hardware. It uses a separately installed RepreGuard visualization loader with float16 and automatic device placement. Create a separate extraction environment following the upstream Python 3.10 setup:

```bash
git clone https://github.com/NLP2CT/RepreGuard.git external/RepreGuard
python -m pip install -r external/RepreGuard/requirements.txt
python -m pip install -r requirements-extraction.txt

python -m analysis.insight extract \
  --config configs/representation/HC3-0.5B-n200.json \
  --upstream-repo external/RepreGuard \
  --output-dir outputs/hc3-0p5b-new
```

HC3 paired input is included. For the DetectRL and RAID inputs named in the run configurations, follow the [upstream dataset instructions](https://github.com/NLP2CT/RepreGuard#datasets) and supply the corresponding file:

```bash
python -m analysis.insight extract \
  --config configs/representation/DetectRL-0.5B-n274.json \
  --upstream-repo external/RepreGuard \
  --data-path /path/to/detectrl_train_dataset_llm_type_mix_llms.json \
  --output-dir outputs/detectrl-0p5b-new
```

New runs record input and selected-text hashes, package versions, seed, bootstrap count and available model/upstream revision metadata. Historical input hashes and full environment records are unavailable, so new extraction and archive reconstruction are reported separately. CPU reconstruction and the extraction interface have automated tests; the extraction interface uses a simulated model in those tests.

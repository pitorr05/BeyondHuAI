# Reported detector experiments

The detector comparisons were run using clones of the original implementations, with local data/model/configuration changes. **This repository does not provide detector training or evaluation runners.** The released CSVs transcribe the current manuscript and do not constitute newly validated prediction logs.

| Method | Original implementation | Role in the manuscript |
|---|---|---|
| RepreGuard | [NLP2CT/RepreGuard](https://github.com/NLP2CT/RepreGuard) | Five-detector and separate cross-benchmark comparison |
| PRDetect | [thulx18/PRDetect](https://github.com/thulx18/PRDetect) | Five-detector and separate cross-benchmark comparison |
| StyleDecipher | [SiyuanLi00/StyleDecipher](https://github.com/SiyuanLi00/StyleDecipher) | Five-detector comparison |
| Binoculars | [ahans30/Binoculars](https://github.com/ahans30/Binoculars) | Five-detector comparison |
| Fast-DetectGPT | [baoguangsheng/fast-detect-gpt](https://github.com/baoguangsheng/fast-detect-gpt) | Five-detector comparison |

## Two protocols

[Five-detector comparison](../results/detectors/five-detector-comparison.csv) contains five evaluated detector configurations on HC3 and DetectRL. [Cross-benchmark comparison](../results/detectors/cross-benchmark-comparison.csv) contains a separate PRDetect/representation-based experiment on HC3 and four external test configurations. All metric columns are percentages.

The second protocol reports 2,000 HC3 training samples, 1,000 validation samples, 1,000 test samples, 1,000 GPT-3.5 mixed samples and 2,000 samples in each RAID test configuration. Those are reported protocol sizes, not a claim that every currently available file has exactly those records or the same sample identities. The local HC3 benchmark training file contains 8,000 records, and the representation training file contains 2,000 storage pairs.

Backbones are recorded in the five-detector CSV. Exact historical upstream commits, complete per-sample predictions, hardware and all threshold-selection details were not retained in this release. The original worksheet includes a threshold note of -5.76 for its representation-based cross-benchmark table; without full run/selection logs this is a historical note, not a validated threshold-transfer protocol.

The two tables have different HC3 results and are not pooled or treated as a shared run. Low-FPR TPR values are exploratory ROC-interpolated estimates; the human sample counts do not directly resolve FPR = 0.01%.

## Author-confirmed F1 correction

For RepreGuard/DetectRL in the five-detector table, the manuscript now uses F1 **89.82%**, recomputed as `2 × 99.95 × 81.56 / (99.95 + 81.56)` from displayed precision/recall, following author confirmation. It replaces 88.77%; the HC3–DetectRL F1 difference is 5.63 percentage points. It was **not** verified against raw predictions.

[provenance.json](../results/detectors/provenance.json) records this correction and the source manuscript hash. The [original worksheet](../results/detectors/archive/original-worksheet.xlsx) is retained for provenance and contains the superseded value. Other reported metrics are unchanged; their preservation does not certify a particular averaging scheme or numerical consistency.

If complete historical run manifests or prediction logs become available, they can be added with source identifiers. Until then, this release makes the boundary between reported results and independently reconstructable diagnostics explicit.

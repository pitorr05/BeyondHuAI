<div align="center">

# Beyond Human vs AI

**A Systematic Survey of Attribution, Robustness, and Human–AI Co-authorship in Large Language Model Forensics**

Pham Quang Toan · Nguyen Duc Trung · Hoang Chi Hien · Nguyen Quang Chien · Nguyen Kieu Linh

Posts and Telecommunications Institute of Technology, Ha Noi, Vietnam<br>
Correspondence: Nguyen Kieu Linh · [linhnk@ptit.edu.vn](mailto:linhnk@ptit.edu.vn)

[![Code: MIT](https://img.shields.io/badge/code-MIT-315f84)](LICENSE)
[![Validation](https://github.com/pitorr05/BeyondHuAI/actions/workflows/validate.yml/badge.svg)](https://github.com/pitorr05/BeyondHuAI/actions/workflows/validate.yml)

[Survey resources](survey/papers.md) · [Benchmarks](survey/benchmarks.md) · [Representation analysis](docs/representation-analysis.md) · [Figures](docs/figure-gallery.md) · [Citation](#citation)

</div>

This repository accompanies our manuscript on the gap between **detecting machine-generated text** and **establishing authorship evidence**. It brings together the literature reviewed in the survey, released data subsets, reported detector comparisons, and document-level representation diagnostics.

The manuscript is in preparation. This repository does not claim an accepted venue or a published DOI.

<p align="center">
  <img src="assets/paper/motivation_authorship_evidence.png" alt="Alternative writing histories can lead to an observed final text; detection alone does not identify the history." width="900">
</p>

## What is released

| Resource | Contents | Start here |
|---|---|---|
| Survey library | 82 cited sources, organized by the manuscript's method groups and supporting topics | [Papers](survey/papers.md), [BibTeX](survey/references.bib) |
| Benchmarks and data | Scope/scale of benchmark resources; 14 local dataset files with schemas, counts and checksums | [Benchmark map](survey/benchmarks.md), [data catalog](data/catalog.csv) |
| Detector comparisons | Two distinct protocols transcribed from the manuscript; no detector training/evaluation runners | [Protocol and provenance](docs/detector-experiments.md) |
| Representation diagnostics | Eight Qwen2.5 configurations across HC3, DetectRL and RAID; 204 layer records and 42,840 layer–position records | [Run catalog](results/representation/run_catalog.csv) |
| Figures | Nine immutable copies of the manuscript artwork and CPU scripts for rebuilding diagnostic plots | [Gallery](docs/figure-gallery.md), [artifact map](docs/artifact-map.md) |

The survey follows three method groups: **zero-shot**, **training-based**, and **watermarking**. Model access, development requirements and reliability evidence are examined across these groups. The repository follows that organization rather than imposing a second taxonomy.

## Rebuild the released diagnostics

Python **3.11 or newer** is recommended for the CPU analysis environment. From the repository root:

```bash
python -m pip install -r requirements-analysis.txt
python -m analysis.insight rebuild
```

The command checks the reconstructed tables against the released summaries, then writes CSVs and diagnostic PDF/PNG plots to `outputs/rebuilt/`. It requires neither a GPU nor model weights. It does **not** rerun detectors or recompute historical bootstrap intervals from cached CSVs.

```bash
# Tables only; choose a separate, empty output directory.
python -m analysis.insight rebuild --tables-only --output-dir outputs/tables-only

# Inspect the optional extraction interface without loading a model.
python -m analysis.insight extract --help
```

Outputs are kept separate from released inputs and artwork. Existing nonempty output directories are not overwritten. The root `insight.py` is a compatibility entry point for the same subcommands.

Fresh hidden-state extraction uses a separately installed RepreGuard visualization loader and suitable model hardware. See [the extraction guide](docs/representation-analysis.md#fresh-hidden-state-extraction) for dependencies, input availability and the eight configuration files.

## What the diagnostics show

Coordinate-pooled hidden states can differ in **magnitude**, **positional concentration**, and **cross-dataset profile alignment**. These properties need not agree. The released layer statistics describe the selected human/machine cohorts; they are not RepreScores or local authorship predictions.

<p align="center">
  <img src="assets/paper/Figure_A_Layer_Effect_Profiles.png" alt="Layer-wise signed effect profiles across datasets and Qwen2.5 backbones." width="950">
</p>

The protocol selects each class independently by descending character length, retains texts with at least 210 tokenized positions, and analyzes the selected hidden layers. Documents are the resampling units. Bootstrap intervals, peak selection and profile comparisons are descriptive, with the sampling and multiplicity limitations discussed in the manuscript.

Reported detector comparisons are a separate source of evidence. For example, the GPT-3.5 mixed configuration illustrates that higher AUROC can coexist with lower accuracy under the evaluated decision rules:

<p align="center">
  <img src="assets/paper/motivation_ranking_decisions.png" alt="Ranking and decision outcomes differ for PRDetect and RepreGuard on the evaluated GPT-3.5 mixed configuration." width="650">
</p>

See [the detector results](results/detectors/) for the two protocol tables and their provenance. The author-confirmed RepreGuard–DetectRL F1 correction is recorded explicitly; the original worksheet is preserved as a historical source, not as the current results table.

## PAAR: a proposed research direction

Process-Aware Authorship Reconstruction (PAAR) connects local contribution claims with text evidence, contrastive checks, available version records and claim-specific review. **PAAR is a proposed reference architecture, not a validated implementation released by this repository.**

<details>
<summary>View the PAAR reference architecture</summary>
<p align="center">
  <img src="assets/paper/paar_framework.png" alt="Proposed PAAR architecture connecting representation, structural and rewrite-response evidence to local claims and evidence assessment." width="950">
</p>
</details>

## Data and reproducibility boundaries

- Benchmark files contain individual texts; representation input files contain human/AI storage pairs. Record counts must not be compared without their units.
- Some historical metadata is incomplete or inconsistent. The [data notes](data/README.md) identify those cases without silently relabeling the archive.
- Complete original prediction logs and the exact historical environment are not released. The repository distinguishes reconstruction from archived measurements, optional new activation extraction, and reported detector results.
- Paper PDFs and LaTeX/build files are not needed to use this repository. The reference library links to original publications instead of redistributing the local PDF collection.

## Citation

Use the manuscript title and author list below when referring to this companion resource. Update the entry when a public manuscript identifier or publication becomes available. GitHub's **Cite this repository** menu provides a separate software citation via [CITATION.cff](CITATION.cff).

```bibtex
@misc{pham2026beyondhuai,
  title  = {Beyond Human vs AI: A Systematic Survey of Attribution, Robustness,
            and Human--AI Co-authorship in Large Language Model Forensics},
  author = {Pham, Quang Toan and Nguyen, Duc Trung and Hoang, Chi Hien
            and Nguyen, Quang Chien and Nguyen, Kieu Linh},
  year   = {2026},
  note   = {Manuscript in preparation; companion repository},
  url    = {https://github.com/pitorr05/BeyondHuAI}
}
```

## Contributions and licensing

Corrections to references, resource links and artifact documentation are welcome. Please include a primary source and explain which manuscript topic or released artifact is affected; see [CONTRIBUTING.md](CONTRIBUTING.md).

The original analysis code is released under [MIT](LICENSE). Dataset contents, third-party code and manuscript artwork are not relicensed by the code license. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

We acknowledge the original detector and benchmark authors and the resource organization of [NLP2CT's survey](https://github.com/NLP2CT/LLM-generated-Text-Detection), [Yang et al.'s survey library](https://github.com/Xianjun-Yang/Awesome_papers_on_LLMs_detection), and [AIGTD-Survey](https://github.com/Nicozwy/AIGTD-Survey). All descriptions here are written for BeyondHuAI's scope and artifacts.

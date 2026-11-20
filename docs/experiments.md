# Experimental resources

The survey includes four empirical components (Section VI of the manuscript). This guide describes their protocols, released results and how to rebuild them.

| Component | Manuscript | Released results |
|---|---|---|
| Five-detector comparison on HC3 and DetectRL | Table 8 | [five-detector-comparison.csv](../results/detectors/five-detector-comparison.csv) |
| Cross-benchmark ranking and decisions | Table 9, Fig. 2 | [cross-benchmark-comparison.csv](../results/detectors/cross-benchmark-comparison.csv) |
| Document scores and graded AI contribution | Table 10, Fig. 3, Fig. 4 | [score_vs_ai_ratio.csv](../results/contribution/score_vs_ai_ratio.csv), [policy_disagreement.csv](../results/contribution/policy_disagreement.csv) |
| Representation diagnostics on eight Qwen2.5 configurations | Tables 11–12, 16, Figs. 5–6, 8–9 | [summaries](../results/representation/summaries/), [run catalog](../results/representation/run_catalog.csv) |

## Detector experiments

| Method | Backbone | Development regime | Original implementation |
|---|---|---|---|
| RepreGuard | [Qwen2.5-0.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct) | Probing direction from reference pairs | [NLP2CT/RepreGuard](https://github.com/NLP2CT/RepreGuard) |
| PRDetect | [RoBERTa-base](https://huggingface.co/FacebookAI/roberta-base) | Syntax-tree classifier | [thulx18/PRDetect](https://github.com/thulx18/PRDetect) |
| StyleDecipher | [GPT-OSS-20B](https://huggingface.co/openai/gpt-oss-20b) | Rewrite/style features + XGBoost | [SiyuanLi00/StyleDecipher](https://github.com/SiyuanLi00/StyleDecipher) |
| Binoculars | [GPT-Neo-2.7B](https://huggingface.co/EleutherAI/gpt-neo-2.7B) | Zero-shot | [ahans30/Binoculars](https://github.com/ahans30/Binoculars) |
| Fast-DetectGPT | [GPT-Neo-2.7B](https://huggingface.co/EleutherAI/gpt-neo-2.7B) | Zero-shot | [baoguangsheng/fast-detect-gpt](https://github.com/baoguangsheng/fast-detect-gpt) |

**Five-detector comparison.** Each benchmark provides 2,000 training samples for methods with fitted components and 1,000 test samples. RepreGuard values are means over five bootstrap resamples, following its original evaluation protocol. F1 is computed as 2PR/(P + R); all metric columns are percentages.

**Cross-benchmark comparison.** PRDetect and RepreGuard are evaluated on HC3 and four shared external test sets: GPT-3.5 mixed (1,000 texts, 500 per class) and RAID Llama greedy, Llama sampling and Mistral (2,000 texts each, 1,000 per class). On HC3, PRDetect uses about 8,000 training, 1,000 validation and 1,000 test texts, and RepreGuard uses 2,000 training, 500 validation and 1,000 test human–machine pairs. Decision rules are fixed on HC3 and applied unchanged to every external set: RepreGuard uses its HC3 threshold (τ = −5.76), and PRDetect uses its HC3-trained classifier. Accuracy and F1 on the external sets therefore measure threshold transfer as well as score ordering. The released splits are listed in [data/catalog.csv](../data/catalog.csv), and the protocol metadata in [provenance.json](../results/detectors/provenance.json).

## Document scores and graded AI contribution

**Score versus AI-word ratio (Table 10, Fig. 4).** The EditLens corpus (validation and test splits, 8,515 documents: 2,791 human-written, 2,925 AI-edited and 2,799 AI-generated) is analyzed with the detector scores released by its authors for Binoculars, Fast-DetectGPT, the EditLens RoBERTa-large regressor and Pangram (v3.2). Binoculars is negated so that higher values indicate machine text. Each word of an AI-edited document is labeled by a word-level diff against its human source: retained words are human, inserted or replaced words are AI. The released table reports Spearman correlations over all documents and over the AI-edited subset, and the mean 10th–90th percentile range of the AI-word ratio within score deciles.

**Attribution policy (Fig. 3).** Two policies are compared on APT-Eval (human texts polished by an LLM at four degrees) and Beemo (machine outputs edited by human experts, binned by the share of edited words). Under the word policy, retained words keep the author of the previous version and inserted or replaced words go to the editor; under the sentence policy, any sentence containing an edited word goes entirely to the editor. The released table reports the AI share under the word policy, the share of relabeled words and the 90th percentile of the per-document change.

Corpus texts remain with their upstream releases (EditLens, [APT-Eval](https://aclanthology.org/2025.findings-acl.1303/), [Beemo](https://aclanthology.org/2025.naacl-long.357/)) under their respective licenses; this repository releases aggregate results only.

## Representation analysis

The coordinate-pooled diagnostics cover eight configurations: DetectRL/0.5B, 1.5B and 7B with 274 documents per class; HC3/0.5B with 200 and 500 per class; HC3/1.5B and 7B with 500 per class; and RAID/7B with 500 per class. [The run catalog](../results/representation/run_catalog.csv) lists backbones, layers, seeds and inputs.

Human and machine texts are selected independently by descending character length, with stable ordering for ties. The first n texts containing at least 210 tokenized positions are retained in each class. The analyzed Qwen2.5-Instruct layers are 2–24 for 0.5B and 2–28 for 1.5B/7B, and each forward pass is followed by pooling of the first 210 hidden-state positions.

Coordinate mean, mean-absolute and RMS statistics are collected per document, layer and position. Layer-level summaries pool positions within documents before computing class contrasts; positive differences and Cohen's d indicate LLM minus human. Percentile 95% intervals come from 1,000 within-class bootstrap resamples of documents (seed 42). Profile alignment across corpora is measured by Pearson r, Spearman ρ, sign agreement and top-5 layer overlap.

### Rebuilding tables and figures

```bash
python -m pip install -r requirements-analysis.txt
python -m analysis.insight rebuild --output-dir outputs/rebuilt
```

The command reads the per-run CSVs and recorded global means, reconstructs five tables (8, 8, 7, 204 and 42,840 rows) and compares them with the released summaries at relative tolerance 1e-8 and absolute tolerance 1e-10. The [gallery](figure-gallery.md) shows all manuscript figures; reconstructed plots are written under `outputs/`.

## Hidden-state extraction

Fresh extraction requires model weights and a GPU. It uses the RepreGuard visualization loader with float16 and automatic device placement, in an environment following the upstream Python 3.10 setup:

```bash
git clone https://github.com/NLP2CT/RepreGuard.git external/RepreGuard
python -m pip install -r external/RepreGuard/requirements.txt
python -m pip install -r requirements-extraction.txt

python -m analysis.insight extract \
  --config configs/representation/HC3-0.5B-n200.json \
  --upstream-repo external/RepreGuard \
  --output-dir outputs/hc3-0p5b-new
```

The HC3 paired input is included. For DetectRL and RAID, obtain the inputs named in the run configurations through the [RepreGuard dataset instructions](https://github.com/NLP2CT/RepreGuard#datasets) and pass them with `--data-path`:

```bash
python -m analysis.insight extract \
  --config configs/representation/DetectRL-0.5B-n274.json \
  --upstream-repo external/RepreGuard \
  --data-path /path/to/detectrl_train_dataset_llm_type_mix_llms.json \
  --output-dir outputs/detectrl-0p5b-new
```

Each run records input and selected-text hashes, package versions, seed, bootstrap count and model revision metadata. CPU reconstruction and the extraction interface are covered by automated tests.

# Data

[catalog.csv](catalog.csv) lists the 14 files, record formats, counts, source labels and SHA-256 checksums.

## Formats

- `benchmark/`: JSONL records with `text` and `label`. HC3 labels are `hc3human`/`hc3chatgpt`; other benchmark files use `human`/`machine`.
- `paired/`: JSON arrays with `human_text`, `direct_prompt` and source metadata. Each record contains two text fields. Representation analysis selects these fields independently; a storage pair is not a matched editing event.

| File family | Benchmark texts | Paired-format records |
|---|---:|---:|
| HC3 train | 8,000 | 2,000 pairs |
| HC3 validation | 1,000 | 500 pairs |
| HC3 test | 1,000 | 1,000 pairs |
| GPT-3.5 mixed test | 1,000 | 500 pairs |
| Each RAID test file | 2,000 | 1,000 pairs |

Benchmark and paired files have separate record units and split histories. Evaluation sample counts are described in [the experimental guide](../docs/experiments.md#detector-experiments).

## Metadata and diagnostic inputs

The paired RAID sampling and Mistral files contain the original `llm_type=llama_greedy` value, which conflicts with their file configurations. Some non-HC3 activation summaries also retain a generic HC3 note. These inconsistencies are identified in the catalogs; the released text and run files are unchanged.

The historical DetectRL mixed-LLM training input and RAID llama-chat sampling/no-penalty input referenced by the diagnostic summaries are obtained separately through [RepreGuard](https://github.com/NLP2CT/RepreGuard#datasets). Place them in `data/local/` or use `--data-path`. The local benchmark splits are separate resources from these diagnostic inputs.

## Sources and terms

Primary resources: [HC3](https://github.com/Hello-SimpleAI/chatgpt-comparison-detection), [DetectRL](https://github.com/NLP2CT/DetectRL), and [RAID](https://github.com/liamdugan/raid). Dataset texts retain their upstream terms and attribution. The repository's MIT license applies to original code and documentation.

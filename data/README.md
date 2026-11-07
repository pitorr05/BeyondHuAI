# Released data files

[catalog.csv](catalog.csv) gives each file's format, record unit, count, label/source distribution, SHA-256 and metadata notes. These copies retain the contents of the existing BeyondHuAI data release; the MIT code license does not apply to underlying dataset texts.

## Formats and counts

`benchmark/` contains JSONL records with `text` and `label`. Read physical newline-delimited records; Unicode line separators inside text are not record delimiters. HC3 uses `hc3human`/`hc3chatgpt`; the other local benchmark files use `human`/`machine`.

`paired/` contains JSON arrays with `human_text` and `direct_prompt`, alongside metadata. Each storage record has two text fields. A pairing is not by itself proof of a shared prompt, matched editing event or co-authorship history. The diagnostic protocol selects and sorts the fields independently.

| File family | Benchmark text records | Paired-format records |
|---|---:|---:|
| HC3 train | 8,000 | 2,000 pairs |
| HC3 validation | 1,000 | 500 pairs |
| HC3 test | 1,000 | 1,000 pairs |
| GPT-3.5 mixed test | 1,000 | 500 pairs |
| Each RAID test file | 2,000 | 1,000 pairs |

The benchmark and paired versions must not be asserted to be identical splits merely because their names match. The paired HC3 test file, for example, represents 2,000 text slots while the benchmark test file has 1,000 individual records. Historical subset IDs are not recovered by selecting a prefix of an available file.

## Known metadata issues

The paired RAID sampling and Mistral files retain `llm_type=llama_greedy` from the original conversion script. This conflicts with their file names/configurations. The original converter paired class lists by position and hardcoded source labels; its metadata is not ground truth for model attribution. No historical text or label is silently repaired in this release.

Some archived activation summaries also contain a generic HC3 note for non-HC3 runs. Run identity comes from the catalog and recorded input/model configuration, with that inconsistency preserved in the original JSON.

## Missing diagnostic inputs

The exact historical DetectRL mixed-LLM training input and RAID llama-chat sampling/no-penalty input referenced by the diagnostic summaries are not packaged. Obtain them through the original [RepreGuard dataset instructions](https://github.com/NLP2CT/RepreGuard#datasets), place them under ignored `data/local/`, or pass an explicit `--data-path`. A newly obtained input is not claimed to be byte-identical to a historical input without a recorded historical hash.

## Sources and use

Primary resources: [HC3](https://github.com/Hello-SimpleAI/chatgpt-comparison-detection), [DetectRL](https://github.com/NLP2CT/DetectRL), [RAID](https://github.com/liamdugan/raid). Local sampling/conversion metadata is separate from those upstream resources. No upstream dataset license is replaced by this repository's software license; retain the original attribution and applicable terms.

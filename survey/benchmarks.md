# Benchmark scope and evaluation targets

Scope and scale below are transcribed from the manuscript. Counts retain the source paper’s unit; they are not the sizes of this repository’s local subsets. See [the data catalog](../data/catalog.csv) for packaged file counts.

| Resource | Venue/year | Generators | Domains | Languages | Reported scale |
|---|---|---:|---:|---:|---|
| [HC3](https://arxiv.org/abs/2301.07597) | arXiv 2023 | 1 | 6 | 2 | ~125k |
| [MGTBench](https://doi.org/10.1145/3658644.3670344) | ACM CCS 2024 | 6 | 3 | 1 | ~21k |
| [M4](https://aclanthology.org/2024.eacl-long.83/) | EACL 2024 | 6 | 7 | 7 | ~147k |
| [M4GT-Bench](https://aclanthology.org/2024.acl-long.218/) | ACL 2024 | 9 | 6 | 9 | ~218k (T1) |
| [MULTITuDE](https://aclanthology.org/2023.emnlp-main.616/) | EMNLP 2023 | 8 | 1 | 11 | 74,081 |
| [MultiSocial](https://aclanthology.org/2025.acl-long.36/) | ACL 2025 | 7 | 1 | 22 | 472k |
| [WETBench](https://aclanthology.org/2025.wikinlp-1.6/) | WikiNLP 2025 | 4 | 1 | 3 | 102k |
| [DivScore](https://aclanthology.org/2025.emnlp-main.971/) | EMNLP 2025 | 4 | 2 | 1 | 4k human refs. |
| [RAID](https://aclanthology.org/2024.acl-long.674/) | ACL 2024 | 11 | 8 | 1 | ~6.2M |
| [Stumbling Blocks](https://aclanthology.org/2024.acl-long.160/) | ACL 2024 | 5 | 1 | 1 | 10k |
| [DetectRL](https://doi.org/10.52202/079017-3186) | NeurIPS 2024 | 4 | 4 | 1 | 235.2K |
| [DetectRL-X](https://aclanthology.org/2026.acl-long.1773/) | ACL 2026 | 4 | 6 | 8 | ~3.46M |
| [MAGE](https://aclanthology.org/2024.acl-long.3/) | ACL 2024 | 27 | 10 | 1 | ~447k |
| [EvoBench](https://aclanthology.org/2025.findings-acl.754/) | Findings ACL 2025 | 29 | 5 | 1 | 43.5k |
| [Beemo](https://aclanthology.org/2025.naacl-long.357/) | NAACL 2025 | 10 | 5 | 1 | 19.6k |
| [HART](https://arxiv.org/abs/2503.00258) | arXiv 2025 | 6 | 4 | 5 | 32k |
| [OpenTuringBench](https://aclanthology.org/2025.emnlp-main.1354/) | EMNLP 2025 | 7 | 1 | 1 | 543k |
| [SeqXGPT](https://aclanthology.org/2023.emnlp-main.73/) | EMNLP 2023 | 5 | 5 | 1 | 30k |
| [HACo-Det](https://aclanthology.org/2025.acl-long.1069/) | ACL 2025 | 4 | 4 | 1 | 11.2k |
| [PASTED](https://aclanthology.org/2024.findings-acl.423/) | Findings ACL 2024 | 2 | 10 | 1 | 83k |
| [GPABench2](https://www.ittc.ku.edu/~bluo/pubs/liu2024checkgpt.pdf) | ACM CCS 2024 | 1 | 3 | 1 | 2.39M |

Binary detection, source attribution, local contribution labels, ordinary human editing, unseen-source evaluation, low-FPR protocols and language-specific reporting are different capabilities. Dataset size alone establishes none of them. See Section V of the manuscript for the capability map and counting notes.

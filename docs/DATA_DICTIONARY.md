# Data dictionary

## `artifacts/paired_items.csv`

One row represents one matched pre/post item within a model--dataset--configuration cell.

| Field group | Meaning |
|---|---|
| `model`, `dataset`, `config` | Evaluation cell identifiers |
| `method`, `fewshot_k`, `sc_k` | Inference-method metadata |
| `pair_index` | Pair identifier within the retained cell |
| `pre_*`, `post_*` | Measurements before and after SFT |
| `*_format` | Compliance with the archived output contract |
| `*_relaxed` | Correctness under archived fallback extraction |
| `*_strict` | Joint compliance and correctness under the archived strict instrument |
| `*_tokens` | Recorded generated-token count |
| `*_task_id`, `*_example_index` | Dataset item identifiers |
| `*_question`, `*_gold` | Task text and reference answer |
| `*_prompt`, `*_completion`, `*_pred` | Retained prompts, completions, and extracted predictions |
| `*_execution_status`, `*_test_pass_rate`, `*_tests` | Code-evaluation metadata where available |
| `*_state` | Archived evaluator state |

All retained rows remain in the relevant denominators. Missing extraction, malformed output, execution failure, and test failure are not silently removed.

## `artifacts/paired_cell_results.csv`

One row per model--dataset--configuration cell. It contains pre/post rates, paired changes, confidence intervals, discordant-pair counts, and McNemar p/q values for strict success, fallback correctness, and compliance.

## MBPP functional files

- `mbpp_functional_paired_items.csv`: paired execution outcomes and failure statuses.
- `mbpp_functional_cell_results.csv`: cell-level pre/post pass@1 changes and uncertainty.

Functional records cover 11,700 pairs from 13 checkpoints. Execution correctness is kept separate from format compliance and parser-derived correctness.

## Manifests and provenance

- `run_manifest.csv` and `artifacts_v2/run_manifest_v2.csv` describe source-file identities, pairing rules, seeds, decoding settings, and recoverable training metadata.
- `artifacts/provenance/` contains the canonical audit records and source workbooks.
- `provenance/SHA256SUMS_original_evidence_archive.txt` records identities from the earlier evidence archive; `MANIFEST.sha256` records this repository snapshot.

## Human-validation sample

`revision_priority_analysis/parser_validation_sample_300.csv` is an **unannotated** stratified sample. Its human-label columns are empty. It is not evidence of completed human validation, adjudication, agreement, or parser accuracy.

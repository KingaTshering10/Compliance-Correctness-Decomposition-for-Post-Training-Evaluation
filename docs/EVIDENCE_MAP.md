# Evidence map

| Reported quantity or claim | Authoritative artifact |
|---|---|
| 49,140 paired responses | `artifacts/paired_items.csv`; `artifacts/analysis_summary.json` |
| 14 checkpoints, four datasets, nine configurations | `artifacts/paired_items.csv`; `artifacts/run_manifest.csv` |
| 495 cells and 55 model--dataset blocks | `artifacts/analysis_summary.json` |
| Strict success change: +12.12 pp | `artifacts/analysis_summary.json`; `artifacts/paired_cell_results.csv` |
| Compliance change: +34.78 pp | `artifacts/analysis_summary.json`; `artifacts/paired_cell_results.csv` |
| Valid-but-wrong change: +22.66 pp | Exact contrast `Delta F - Delta S` from the two preceding quantities |
| Parser-derived correctness change: +3.57 pp | `artifacts/analysis_summary.json` |
| Compliance-minus-parser-correctness contrast: +31.22 pp | `artifacts_ccd/ccd_revision_summary.json` |
| Paired transition taxonomy | `artifacts/analysis_summary.json`; `artifacts_v2/transition_taxonomy_pooled.csv` |
| Robustness to weighting | `artifacts_ccd/weighting_sensitivity.csv` |
| Hierarchical bootstrap intervals | `artifacts_ccd/hierarchical_bootstrap_ccd.csv` |
| Leave-one-model-out analysis | `artifacts_ccd/leave_one_model_out.csv` |
| MBPP functional pass@1: 18.99% to 15.33% | `artifacts/analysis_summary.json`; `artifacts/mbpp_functional_paired_items.csv` |
| MBPP functional transitions and failure accounting | `artifacts_ccd/mbpp_pass_failure_transition_accounting.csv`; `artifacts_ccd/mbpp_pass_syntax_summary.json` |
| Generation-ceiling sensitivity | `artifacts_v2/mbpp_generation_ceiling_audit.csv`; `artifacts_v2/mbpp_generation_ceiling_summary.json` |
| Training-dose metadata coverage | `docs/DOSE_SENSITIVITY_STATUS.md`; `revision_priority_analysis/dose_metadata_needed.csv` |
| Parser-validation protocol and sample | `docs/PARSER_VALIDATION_PROTOCOL.md`; `revision_priority_analysis/parser_validation_sample_300.csv` |

## Interpretation boundary

The gap `Delta F - Delta S = Delta(F - S)` is an accounting identity: it is the change in compliant outputs that do not receive strict correctness credit. It is not causal evidence that compliance training damaged reasoning or capability. Parser-derived and execution-based correctness are different instruments and should not be conflated.

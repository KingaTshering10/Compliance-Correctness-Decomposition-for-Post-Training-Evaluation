# Training-dose sensitivity status

The supplied `artifacts_v2/run_manifest_v2.csv` contains complete `sft_train_examples`, `sft_max_steps`, `train_batch`, and `grad_accum` for 5/55 model-dataset recipes, and only one MBPP recipe.

A study-wide dose regression is therefore not currently defensible. The nine inference configurations share the same training recipe and must not be treated as nine independent dose observations.

Files:
- `revision_priority_analysis/dose_available_manifest_rows.csv`: the five complete recipes.
- `revision_priority_analysis/dose_metadata_needed.csv`: the 50 recipes needing one or more dose fields.
- `revision_priority_analysis/dose_sensitivity_template.py`: analysis that stops until the manifest is complete enough, then aggregates configurations within recipe before relating D/ΔC/ΔF to effective epochs and maximum steps.

Effective epochs:
`steps * (train_batch * grad_accum) / sft_train_examples`.

For MBPP, repeat at recipe/model level using functional Δpass@1. Do not infer a dose slope from the single currently complete MBPP recipe.

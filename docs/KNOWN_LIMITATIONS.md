# Known limitations

- The study reuses a finite set of benchmark items across inference configurations and related model families; outputs are not independent draws from a model population.
- Only one historical training seed is available for most recipes, so the uncertainty estimates do not measure training-seed variability.
- Complete training-dose metadata are available for only 5 of 55 model--dataset recipes.
- Parser-derived correctness for noncompliant natural-language responses has not been independently validated by completed human annotation.
- The 300-item parser-validation file is an unannotated template, not a completed audit.
- MBPP functional evaluation uses retained original-test outcomes. Finite tests can miss defects, and no EvalPlus-augmented result is supplied.
- Generation-ceiling filtering changes the evaluated population and cannot reconstruct truncated completions.
- Base checkpoints, adapters, full training notebooks, and exact runtime images are not included, so the package does not support exact end-to-end reruns of every historical experiment.
- The repository has no declared license. Redistribution rights for benchmark text, model outputs, venue style files, and figures must be reviewed before public release.

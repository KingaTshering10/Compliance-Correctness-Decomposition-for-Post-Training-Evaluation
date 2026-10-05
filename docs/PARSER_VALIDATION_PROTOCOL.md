# Parser validation protocol

Use `revision_priority_analysis/parser_validation_sample_300.csv`.

- 300 pre-stage items, 75 per dataset.
- Sample is stratified across the archived pre-stage CCD states as far as raw-completion coverage permits; format-invalid states are deliberately represented because relaxed extraction matters there.
- Use two independent human annotators.
- Show question/task and raw model completion.
- Hide the current parser output, current C/F/S labels, and the other annotator's label.
- Ask: “What final answer does this completion actually express?” Allow `ambiguous/unrecoverable`.
- MBPP: annotate the candidate expressed, not whether the code is correct; correctness is execution-based.
- Adjudicate disagreements.
- Report per-dataset and pooled extractor-vs-adjudicated exact agreement, number/share ambiguous, and inter-annotator agreement.
- Do not substitute an LLM judge for the human validation requested by the reviewer.

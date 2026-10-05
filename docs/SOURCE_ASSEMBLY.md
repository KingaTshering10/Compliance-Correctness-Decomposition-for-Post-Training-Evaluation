# Source assembly record

This repository was assembled from two supplied ZIP archives.

## Manuscript archive

The NeurIPS archive supplied the authoritative `main.tex`, bibliography, venue style file, figure assets, figure-redrawing script, and compiled manuscript. The superseded `ACL main.tex` and `previous-main.tex` drafts were excluded to avoid ambiguity about the authoritative paper. ACL-only style files were also excluded because the retained manuscript does not use them.

## Evidence archive

The ARR evidence archive supplied the paired records, manifests, analysis scripts, robustness outputs, provenance workbooks, parser-validation materials, and dose-metadata audit.

The archive's original README and top-level checksum file were not retained as release metadata because they referenced files absent from the supplied ZIP, including `main2.tex`, `CCD_ACL_Revised.pdf`, and pre-generated table/figure directories. This repository replaces them with accurate documentation and `MANIFEST.sha256`.

## Cleaning and validation

- Removed macOS metadata (`__MACOSX`, `._*`, and `.DS_Store`) and LaTeX build intermediates.
- Found no model checkpoints, adapters, private keys, access tokens, or absolute personal filesystem paths in the retained files.
- Regenerated the CCD analysis outputs and figures successfully with `analysis_ccd_revision.py`.
- Regenerated the secondary revision analyses successfully.
- Compiled the retained manuscript with pdfLaTeX/BibTeX through `latexmk`.
- Corrected one malformed loss-expression denominator and restored automatic equation numbering without changing the reported experimental results.

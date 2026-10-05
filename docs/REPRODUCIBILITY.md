# Reproducibility guide

## Supported reproduction

The repository supports reproduction of the **post-hoc CCD analysis** from the retained paired records. The main script reads:

- `artifacts/paired_items.csv`
- `artifacts/paired_cell_results.csv`
- `artifacts/mbpp_functional_paired_items.csv`
- `artifacts/mbpp_functional_cell_results.csv`

It writes summaries to `artifacts_ccd/` and figures to `figures_ccd/`.

## Environment

Python 3.10 or later is recommended. Install the package names from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-analysis.txt
```

The requirements file records package names rather than exact versions because exact environment metadata was not included in the source archive. Record resolved versions with `python -m pip freeze` when producing a new release.

## Validation and analysis

```bash
python scripts/validate_artifacts.py
python analysis_ccd_revision.py
python revision_priority_analysis/revision_priority_analysis.py
```

The validation script checks the expected number of paired records, checkpoints, datasets, configurations, cells, and model--dataset blocks; verifies unique pairing keys; verifies matched task IDs; checks `S = F x C` for the archived strict instrument; and checks the MBPP functional subset.

## Manuscript compilation

A TeX distribution with `latexmk`, pdfLaTeX, BibTeX, TikZ, and the packages imported by `paper/main.tex` is required.

```bash
cd paper
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

## Integrity verification

From the repository root:

```bash
shasum -a 256 -c MANIFEST.sha256
```

`MANIFEST.sha256` describes the packaged release. Regenerating figures may change PDF metadata and therefore their hashes even when plotted values are unchanged.

## Unsupported end-to-end claims

The repository does not include every original training notebook, base-model checkpoint, adapter, runtime image, or generation log. The retained records support auditing and reanalysis, not exact reconstruction of every historical SFT and inference run.

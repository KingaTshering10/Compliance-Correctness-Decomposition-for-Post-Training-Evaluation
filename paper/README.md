# Manuscript source

`main.tex` is the authoritative manuscript in this repository. It uses the included `neurips_2026.sty`, `references.bib`, and assets in `Figures/`.

Compile with:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

`paper.pdf` is the validated compiled snapshot. The superseded `ACL main.tex` and `previous-main.tex` drafts found in the source archive were intentionally excluded to avoid presenting multiple files as authoritative.

The source remains anonymous. Do not add a personally identifying repository URL during double-blind review unless the venue explicitly permits it.

# Build and deposit notes

## Scope
This file records the operational steps for building the PDFs, running the native audit checks, assembling the canonical source archive, and preparing release assets.

## Prerequisites
- TeX Live / TinyTeX with XeLaTeX and `latexmk`
- Python 3
- `zip`

## Source entry points
- `main.tex`
- `supplement-a.tex`
- `supplement-b.tex`
- `supplement-c.tex`

## Local PDF build
```bash
latexmk -xelatex -interaction=nonstopmode -halt-on-error main.tex
latexmk -xelatex -interaction=nonstopmode -halt-on-error supplement-a.tex
latexmk -xelatex -interaction=nonstopmode -halt-on-error supplement-b.tex
latexmk -xelatex -interaction=nonstopmode -halt-on-error supplement-c.tex
```

## Native audit
```bash
python3 audit_pack/verify_native_examples_sympy.py
```

## Source archive
The GitHub workflow builds the canonical source archive and publishes it as the `source-zip` artifact.

## Release assets
The GitHub workflow attaches these release assets on a published GitHub release:
- `main.pdf`
- `supplement-a.pdf`
- `supplement-b.pdf`
- `supplement-c.pdf`
- canonical source archive (`source-zip`)
- optional `native-audit-pack.zip`

## Zenodo
Zenodo metadata is defined by `.zenodo.json`. The repository-side DOI reference is stored in `.zenodo_doi` after archival.

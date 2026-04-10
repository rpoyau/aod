# Build and deposit notes

## Scope
This file records the operational steps for building the PDFs, running the audit checks, assembling the canonical source archive, and preparing release assets.

## Prerequisites
- TeX Live / TinyTeX with XeLaTeX and `latexmk`
- Python 3
- `sympy`
- `zip`

## Source entry points
- `main.tex`
- `supplement-a/main.tex`
- `supplement-b/main.tex`
- `supplement-c/main.tex`

## Local PDF build
```bash
latexmk -xelatex -interaction=nonstopmode -halt-on-error main.tex
latexmk -cd -xelatex -interaction=nonstopmode -halt-on-error supplement-a/main.tex
cp supplement-a/main.pdf supplement-a.pdf
latexmk -cd -xelatex -interaction=nonstopmode -halt-on-error supplement-b/main.tex
cp supplement-b/main.pdf supplement-b.pdf
latexmk -cd -xelatex -interaction=nonstopmode -halt-on-error supplement-c/main.tex
cp supplement-c/main.pdf supplement-c.pdf
```

## Audit
Install the audit dependency first:
```bash
python3 -m pip install -r requirements-ci.txt
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
- optional audit zip (`native-audit-pack.zip`)

## Zenodo
Zenodo metadata is defined by `.zenodo.json`. The repository-side DOI reference is stored in `.zenodo_doi` after archival.

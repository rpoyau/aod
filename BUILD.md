# Build and deposit notes

## Scope
This file records the operational steps for building the public PDFs, running the audit checks, assembling the canonical source archive, and preparing release assets.

## Prerequisites
- TeX Live / TinyTeX with XeLaTeX and `latexmk`
- Python 3
- `sympy`
- `zip`

## Public build targets
- `main.tex`
- `manual/main.tex`

## Local PDF build
```bash
latexmk -xelatex -interaction=nonstopmode -halt-on-error main.tex
latexmk -cd -xelatex -interaction=nonstopmode -halt-on-error manual/main.tex
cp manual/main.pdf manual.pdf
```

## Audit
Install the audit dependency first:
```bash
python3 -m pip install -r requirements-ci.txt
python3 audit_pack/verify_examples_sympy.py
```

## Source archive
The GitHub workflow builds the canonical source archive and publishes it as the `source-zip` artifact.

## Release assets
The GitHub workflow attaches these release assets on a published GitHub release:
- `main.pdf`
- `manual.pdf`
- canonical source archive (`source-zip`)
- optional audit zip (`audit-pack.zip`)

The supplement PDFs are retained for source/internal use and are not part of the public downstream release set.

## Zenodo
Zenodo metadata is defined by `.zenodo.json`. The repository-side DOI reference is stored in `.zenodo_doi` after archival.

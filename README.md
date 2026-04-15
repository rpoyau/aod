# Alpha↔Omega Dynamics
## The Hidden Temporal Dynamics of Stokes
### 43°C

This repository is the **canonical source tree** for the AOD family in AFC/AF form. It contains the theorem note and the downstream manual together with source fragments, notebooks, audit materials, workflow metadata, and release helpers. Exact/default-form rows remain authoritative throughout; where converted witnesses are used, they are attached after the cited row.

## Public documents

- `main.tex` → `main.pdf` — theorem/calculus source
- `manual/main.tex` → `manual.pdf` — downstream/public manual

## Canonical source tree

- `main.tex` — main theorem note
- `manual/` — downstream manual source package
- `supplement-a/` — retained source fragments and support material
- `supplement-b/` — retained source fragments and support material
- `supplement-c/` — retained source fragments and support material
- `sections/`, `consequences/`, `examples/`, `appendices/` — main-note TeX source tree
- `notebooks/` — root executable notebooks for main-note support
- `audit_pack/` — machine-readable audit rows and verifier files
- `.github/workflows/` — GitHub Actions build workflow
- `scripts/` — source-archive helper scripts
- `.zenodo.json` — Zenodo metadata
- `.zenodo_doi` — concept DOI reference file
- `BUILD.md` — build, audit, release, and deposit notes

## Release assets

Public release assets are:

1. `main.pdf`
2. `manual.pdf`

Optional release assets may include:
- canonical source archive (`source-zip`)
- audit archive (`audit-pack.zip`)

The supplement PDFs are not public downstream release authorities once the manual is live.

## Notebook routing

- `notebooks/examples-01-03.ipynb` — cut / closure / backlog checks
- `supplement-a/notebooks/` — companion notebooks for worked rows retained in source
- `supplement-b/notebooks/` — companion notebooks for conversion/render material retained in source
- `supplement-c/notebooks/` — grouped regime notebooks retained in source

See `notebooks/README.md` for the current source-side notebook routing map.

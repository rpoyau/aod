# Alpha↔Omega Dynamics
## The Hidden Temporal Dynamics of Stokes
### 43°C

This repository is the **canonical source tree** for the AOD note in AFC/AF form. It contains the TeX source for the main native note, the three supplements, the executable notebooks, the native audit materials, and the metadata/helper files used for release deposition. Native rows remain authoritative throughout; where converted witnesses are used, they are attached after the cited native row.

## Source entry points

- `main.tex` → `main.pdf`
- `supplement-a/main.tex` → `supplement-a.pdf`
- `supplement-b/main.tex` → `supplement-b.pdf`
- `supplement-c/main.tex` → `supplement-c.pdf`

## Canonical source tree

- `main.tex` — main native note
- `supplement-a/` — Supplement A subpackage (source entry point: `supplement-a/main.tex`)
- `supplement-b/` — Supplement B subpackage (source entry point: `supplement-b/main.tex`)
- `supplement-c/` — Supplement C subpackage (source entry point: `supplement-c/main.tex`)
- `sections/`, `consequences/`, `examples/`, `appendices/` — main-note TeX source tree
- `notebooks/` — root executable notebooks for main-note support
- `notebooks/STYLE_GUIDE.md` — shared notebook style guide
- `audit_pack/` — native machine-readable audit rows and verifier files
- `.github/workflows/` — GitHub Actions build workflow
- `scripts/` — source-archive helper scripts
- `.zenodo.json` — Zenodo metadata
- `.zenodo_doi` — concept DOI reference file
- `BUILD.md` — build, audit, release, and deposit notes

## Package order

1. `main.pdf` — compact native derivation shell
2. `supplement-a.pdf` — native worked examples and figure witnesses
3. `supplement-b.pdf` — verification bindings and derived temporal-unit conversions attached after the cited native row
4. `supplement-c.pdf` — native regime tests, with converted witnesses attached only after the cited native row where needed
5. `notebooks/` — root notebook layer for main-note support
6. `supplement-a/notebooks/` — Supplement A notebook layer
7. `supplement-b/notebooks/` — Supplement B notebook layer
8. `supplement-c/notebooks/` — grouped Supplement C notebook layer
9. `audit_pack/` — native audit rows and verifier files

## Notebooks

- `notebooks/E1-E3.ipynb` — active-cut / closure / backlog checks
- `supplement-a/notebooks/E4-E6.ipynb` — native loss-channel / B* / collision-export checks
- `supplement-a/notebooks/E7-E9-bindings.ipynb` — field / confinement / family / routing checks
- `supplement-b/notebooks/E10-E11D.ipynb` — recurrent-ring and temporal-conversion rendering checks

See `notebooks/README.md` for the notebook routing map.

## Supplement subpackages

Supplement A is maintained in `supplement-a/`.
Supplement B is maintained in `supplement-b/`.
Supplement C is maintained in `supplement-c/`, with grouped regime notebooks under `supplement-c/notebooks/`.

## Supplement C subpackage

Supplement C is maintained as a self-contained subpackage under `supplement-c/`.
Its grouped regime notebooks live under `supplement-c/notebooks/solar/`, `hydrogen/`, `nucleus/`, `galactic/`, `bacteria/`, and `saturn/`.

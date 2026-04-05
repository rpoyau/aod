# Alpha↔Omega Dynamics
## The Hidden Temporal Dynamics of Stokes
### 43°C

This repository is the **canonical source tree** for the AOD note in AFC/AF form. It contains the TeX source for the main native note, the three supplements, the executable notebooks, the native audit materials, and the metadata/helper files used for release deposition.

## Source entry points

- `main.tex` → `main.pdf`
- `supplement-a.tex` → `supplement-a.pdf`
- `supplement-b.tex` → `supplement-b.pdf`
- `supplement-c/main.tex` → `supplement-c.pdf`

## Canonical source tree

- `main.tex` — main native note
- `supplement-a.tex` — Supplement A: native worked examples and figure witnesses
- `supplement-b.tex` — Supplement B: verification bindings and derived temporal-unit conversions
- `supplement-c/` — Supplement C source (main, sections, examples, notebooks)
- `sections/`, `consequences/`, `examples/`, `appendices/` — TeX source tree
- `notebooks/` — executable notebooks for native AOD tests
- `notebooks/STYLE_GUIDE.md` — official notebook style guide
- `audit_pack/` — native machine-readable audit rows and verifier files
- `supplement-b-artifacts/` — support data for Supplement B temporal-conversion rows
- `.github/workflows/` — GitHub Actions build workflow
- `scripts/` — source-archive helper scripts
- `.zenodo.json` — Zenodo metadata
- `.zenodo_doi` — concept DOI reference file
- `BUILD.md` — build, audit, release, and deposit notes

## Package order

1. `main.pdf` — compact native derivation shell
2. `supplement-a.pdf` — native worked examples and figure witnesses
3. `supplement-b.pdf` — verification bindings and derived temporal-unit conversions
4. `supplement-c.pdf` — additional native regime tests
5. `notebooks/` — executable notebook layer for E-series AOD-native tests
6. `supplement-c/notebooks/` — executable notebook layer for C-series native regime tests
7. `audit_pack/` — native audit rows and verifier files

## Notebooks

- `E1-E3.ipynb` — active-cut / closure / backlog checks  
- `E4-E6.ipynb` — native rest-channel / B* / collision-export checks  
- `E7-E9-bindings.ipynb` — field / confinement / family / routing checks  
- `E10-E11D.ipynb` — recurrent-ring and temporal-conversion rendering checks  

See `notebooks/README.md` for the E-series notebook index, visual outputs, and verification map.\nSee `supplement-c/README.md` and `supplement-c/notebooks/` for the C-series regime-test notebook layer.
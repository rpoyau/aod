# Alpha↔Omega Dynamics
## The Hidden Temporal Dynamics of Stokes
### 43°C

This repository is the **source package** for the AOD note in AFC/AF form.
It contains the TeX source for the main native note, the two companion supplements,
the collab notebooks, the native audit materials, and the GitHub/Zenodo metadata
used to build and archive the release package.

## Source entry points

- `main.tex` → `main.pdf`
- `supplement-a.tex` → `supplement-a.pdf`
- `supplement-b.tex` → `supplement-b.pdf`

## Source contents

- `main.tex` — main native addendum
- `supplement-a.tex` — Supplement A: native worked examples and figure witnesses
- `supplement-b.tex` — Supplement B: application and SI parity examples
- `sections/`, `consequences/`, `examples/`, `appendices/` — TeX source tree
- `notebooks/` — executable notebooks for native AOD tests
- `audit_pack/` — native machine-readable audit rows and verifier files
- `supplement-b-artifacts/` — downstream example data for Supplement B
- `.github/workflows/` — GitHub Actions build workflow
- `scripts/` — release-bundle helper script
- `.zenodo.json` — Zenodo metadata for GitHub/Zenodo archiving
- `.zenodo_doi` — source-only concept DOI reference file
- `BUILD.md` — build and deposit notes

## Package order

1. `main.pdf` — compact native derivation shell
2. `supplement-a.pdf` — native worked examples and figure witnesses
3. `supplement-b.pdf` — downstream verification / SI / application companion
4. `notebooks/` — executable notebook layer for AOD-native tests
5. `audit_pack/` — machine-readable native audit rows and verifier files

## Collabs

- `E1–E3.ipynb` — active-cut / closure / backlog checks  [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/rpoyau/aod/blob/main/notebooks/E1-E3.ipynb)  
  Local file: [`notebooks/E1-E3.ipynb`](notebooks/E1-E3.ipynb)
- `E4–E6.ipynb` — native rest-channel / B* / collision-export checks  [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/rpoyau/aod/blob/main/notebooks/E4-E6.ipynb)  
  Local file: [`notebooks/E4-E6.ipynb`](notebooks/E4-E6.ipynb)
- `E7–E9-bindings.ipynb` — field / confinement / family / binding checks  [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/rpoyau/aod/blob/main/notebooks/E7-E9-bindings.ipynb)  
  Local file: [`notebooks/E7-E9-bindings.ipynb`](notebooks/E7-E9-bindings.ipynb)
- `E10–E11D.ipynb` — recurrent-ring and downstream rendering checks  [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/rpoyau/aod/blob/main/notebooks/E10-E11D.ipynb)  
  Local file: [`notebooks/E10-E11D.ipynb`](notebooks/E10-E11D.ipynb)

See `notebooks/README.md` for the notebook index, visual outputs, and verification map.

## Notes

This source package is intended to be rebuilt locally or in CI. Compiled PDFs and
reader-facing bundle assets belong to the release package, not to this source tree.

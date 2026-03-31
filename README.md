# Alpha↔Omega Dynamics
## The Hidden Temporal Dynamics of Stokes
### 43°C

This repository is the **canonical source tree** for the AOD note in AFC/AF form. It contains the TeX source for the main native note, the two supplements, the executable notebooks, the native audit materials, and the metadata/helper files used for release deposition.

## Source entry points

- `main.tex` → `main.pdf`
- `supplement-a.tex` → `supplement-a.pdf`
- `supplement-b.tex` → `supplement-b.pdf`

## Canonical source tree

- `main.tex` — main native note
- `supplement-a.tex` — Supplement A: native worked examples and figure witnesses
- `supplement-b.tex` — Supplement B: downstream verification and application examples
- `sections/`, `consequences/`, `examples/`, `appendices/` — TeX source tree
- `notebooks/` — executable notebooks for native AOD tests
- `audit_pack/` — native machine-readable audit rows and verifier files
- `supplement-b-artifacts/` — downstream support data for Supplement B
- `.github/workflows/` — GitHub Actions build workflow
- `scripts/` — source-archive helper scripts
- `.zenodo.json` — Zenodo metadata
- `.zenodo_doi` — concept DOI reference file
- `BUILD.md` — build, audit, release, and deposit notes

## Package order

1. `main.pdf` — compact native derivation shell
2. `supplement-a.pdf` — native worked examples and figure witnesses
3. `supplement-b.pdf` — downstream verification and application companion
4. `notebooks/` — executable notebook layer for AOD-native tests
5. `audit_pack/` — native audit rows and verifier files

## Notebooks

- `E1-E3.ipynb` — active-cut / closure / backlog checks  
  Local: [`notebooks/E1-E3.ipynb`](notebooks/E1-E3.ipynb)  
  [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/rpoyau/aod/blob/main/notebooks/E1-E3.ipynb)
- `E4-E6.ipynb` — native rest-channel / B* / collision-export checks  
  Local: [`notebooks/E4-E6.ipynb`](notebooks/E4-E6.ipynb)  
  [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/rpoyau/aod/blob/main/notebooks/E4-E6.ipynb)
- `E7-E9-bindings.ipynb` — field / confinement / family / binding checks  
  Local: [`notebooks/E7-E9-bindings.ipynb`](notebooks/E7-E9-bindings.ipynb)  
  [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/rpoyau/aod/blob/main/notebooks/E7-E9-bindings.ipynb)
- `E10-E11D.ipynb` — recurrent-ring and downstream rendering checks  
  Local: [`notebooks/E10-E11D.ipynb`](notebooks/E10-E11D.ipynb)  
  [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/rpoyau/aod/blob/main/notebooks/E10-E11D.ipynb)

See `notebooks/README.md` for the notebook index, visual outputs, and verification map.

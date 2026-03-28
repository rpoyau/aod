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
- `collabs/` — executable notebooks for native AOD tests
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
4. `collabs/` — executable notebook layer for AOD-native tests
5. `audit_pack/` — machine-readable native audit rows and verifier files

## Collabs

[![Collab E1–E3](https://img.shields.io/badge/collab-E1--E3-blue)](collabs/E1-E3.ipynb)
[![Collab E4–E6](https://img.shields.io/badge/collab-E4--E6-blue)](collabs/E4-E6.ipynb)
[![Collab E7–E9](https://img.shields.io/badge/collab-E7--E9-blue)](collabs/E7-E9-bindings.ipynb)
[![Collab E10–E11D](https://img.shields.io/badge/collab-E10--E11D-blue)](collabs/E10-E11D.ipynb)

See `collabs/README.md` for the notebook index and routing notes.

## Notes

This source package is intended to be rebuilt locally or in CI. Compiled PDFs and
reader-facing bundle assets belong to the release package, not to this source tree.

# Alpha↔Omega Temporal Dynamics (AOD): The Hidden Temporal Dynamics of Stokes
## Addendum to AFC Stokes

[![Build PDFs and release bundle](https://github.com/OWNER/REPO/actions/workflows/build.yml/badge.svg)](https://github.com/OWNER/REPO/actions/workflows/build.yml)
[![Zenodo DOI](https://zenodo.org/badge/DOI/DOI_PLACEHOLDER.svg)](https://doi.org/DOI_PLACEHOLDER)

Replace `OWNER/REPO` and `DOI_PLACEHOLDER` after the first Zenodo archive.

This repository contains the release package for the AOD addendum in AFC/AF form. Enable the repository in Zenodo’s GitHub integration, publish a GitHub release, and Zenodo will archive that release using the metadata in `.zenodo.json`.

## Entry points

- `main.tex` → `main.pdf`
- `supplement-a.tex` → `supplement-a.pdf`
- `supplement-b.tex` → `supplement-b.pdf`

## Package contents

- `main.tex` — main native addendum
- `supplement-a.tex` — Supplement A: native worked examples and figure witnesses
- `supplement-b.tex` — Supplement B: downstream application / SI parity companion
- `main.pdf` — compiled main note
- `supplement-a.pdf` — compiled Supplement A
- `supplement-b.pdf` — compiled Supplement B
- `sections/`, `consequences/`, `examples/`, `appendices/` — source tree
- `collabs/` — executable notebooks for review and reproducibility
- `audit_pack/` — native machine-readable audit rows and verifier files
- `supplement-b-artifacts/` — downstream example data for Supplement B
- `.github/workflows/` — GitHub Actions build workflow
- `scripts/` — release-bundle helper script
- `.zenodo.json` — Zenodo metadata file used by GitHub/Zenodo archiving
- `.zenodo_doi` — concept DOI reference file

## Collabs

[![Collab E1–E3](https://img.shields.io/badge/collab-E1--E3-blue)](collabs/E1-E3.ipynb)
[![Collab E4–E6](https://img.shields.io/badge/collab-E4--E6-blue)](collabs/E4-E6.ipynb)
[![Collab E7–E9](https://img.shields.io/badge/collab-E7--E9-blue)](collabs/E7-E9-bindings.ipynb)
[![Collab E10–E11D](https://img.shields.io/badge/collab-E10--E11D-blue)](collabs/E10-E11D.ipynb)

See `collabs/README.md` for the full notebook index and routing notes.

## Build and release

The single workflow `.github/workflows/build.yml`:
- compiles `main.tex`, `supplement-a.tex`, and `supplement-b.tex`
- uploads the compiled PDFs as workflow artifacts
- builds a curated repo-root release bundle ZIP
- uploads a zipped native audit pack
- on published GitHub releases, attaches the PDFs and ZIP assets to the release

Zenodo GitHub integration then archives the published GitHub release automatically for repositories enabled in Zenodo.

## Notes

Only current release files should be kept in the final deposited source tree. Historical review artifacts and stale changelogs should be excluded from the release source bundle.

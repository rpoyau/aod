# Alpha↔Omega Dynamics (AOD): The Hidden Temporal Dynamics of Stokes
## Addendum to AFC Stokes

[![Build PDFs and release bundle](https://github.com/OWNER/REPO/actions/workflows/build.yml/badge.svg)](https://github.com/OWNER/REPO/actions/workflows/build.yml)
[![Zenodo release bundle deposit](https://github.com/OWNER/REPO/actions/workflows/release-zenodo.yml/badge.svg)](https://github.com/OWNER/REPO/actions/workflows/release-zenodo.yml)
[![Zenodo DOI](https://zenodo.org/badge/DOI/DOI_PLACEHOLDER.svg)](https://doi.org/DOI_PLACEHOLDER)

Replace `OWNER/REPO` and `DOI_PLACEHOLDER` after first release.

This repository contains the release package for the AOD addendum in AFC/AF form.

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
- `.github/workflows/` — GitHub Actions build and Zenodo deposit workflows
- `scripts/` — release-bundle and Zenodo helper scripts
- `.zenodo.json` — Zenodo metadata template
- `.zenodo_doi` — concept DOI file (filled after first successful publish)

## Collabs

See `collabs/README.md` for the notebook index.

## Build and release

### Build workflow

`build.yml` compiles the PDFs on push/PR/manual dispatch and uploads:
- compiled PDFs
- native audit pack
- repo-root release bundle ZIP

### Zenodo workflow

`release-zenodo.yml` rebuilds from the tagged state, creates the release bundle, uploads it to the GitHub Release, and deposits the same bundle to Zenodo (sandbox or production).

## Zenodo metadata files

- `.zenodo.json` — metadata template used by the release workflow
- `.zenodo_doi` — concept DOI file; populated after first successful publish

## Secrets

Set these repository secrets before using the release workflow:
- `ZENODO_TOKEN`
- `ZENODO_SANDBOX_TOKEN`

## Notes

Only current release files should be kept in the final deposited source tree. Historical review artifacts and stale changelogs should be excluded from the release source bundle.

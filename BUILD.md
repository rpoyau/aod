# Build and release

This source tree is version-neutral. Most release artifact filenames are stable (`main.pdf`, `manual.pdf`, `manual-2.pdf`, `MANUAL_I_ROADMAP.md`, `MANUAL_II_ROADMAP.md`, `source.zip`, `tests.txt`). The source archive is flat: unzipping `source.zip` into a repository checkout writes files directly into that checkout. The primary bundle is versioned as `bundle-<version>.zip`, and a compatibility alias `bundle.zip` is also emitted. The release version is read from `CANONICAL_VERSION.txt` and recorded in metadata and manifests.

Typical local build:

```bash
latexmk -xelatex -interaction=nonstopmode -halt-on-error main.tex
latexmk -cd -xelatex -interaction=nonstopmode -halt-on-error manual/main.tex
cp manual/main.pdf manual.pdf
latexmk -cd -xelatex -interaction=nonstopmode -halt-on-error manual-2/main.tex
cp manual-2/main.pdf manual-2.pdf
pytest -q | tee tests.txt
python scripts/build_release_bundle.py --outdir dist --main main.pdf --manual manual.pdf --manual2 manual-2.pdf --tests tests.txt
```

The generated source archive and source-internal paths remain version-neutral. The bundle filename carries the release version while preserving stable internal member names.

The release tests artifact is `tests.txt`. It is produced by the pytest suite; SymPy exact-arithmetic checks are part of that suite. The release builder consumes `tests.txt` directly.

## Artifact order

For Zenodo or other repositories with a default preview/display file, use the main note PDF as the primary artifact and upload/place it first:

```text
main.pdf
```

The Manual I PDF, Manual II PDF, flat source ZIP, versioned bundle ZIP, tests, patch summary, historical Manual-artifact baseline manifest, and SHA-256 manifests accompany the main PDF. The bundle uses stable internal filenames and preserves `main.pdf` as the first member, followed by `manual.pdf`, `manual-2.pdf`, `MANUAL_I_ROADMAP.md`, `MANUAL_II_ROADMAP.md`, and `source.zip`. Every bundle built from the current source embeds only the assets authorized by `manual-2/data/protein/external_payload_bundle_inventory.csv` under `external_payloads/`; `EXTERNAL_PAYLOADS_SHA256.txt` verifies those nested files. Required inventory rows must resolve and match their recorded byte count and SHA-256. Large payloads follow the frozen inline/separate-pack/manifest-only policy.


## Root `.zenodo.json` policy

`.zenodo.json` is committed at the repository root because GitHub-Zenodo synchronization reads metadata from the repository root when a GitHub release is published. The release builder validates this root file and includes it in `source.zip` for archival reproducibility; it does not generate `.zenodo.json` as the only authoritative copy.

Keep source-facing files version-neutral: `main.pdf`, `manual.pdf`, `manual-2.pdf`, `MANUAL_I_ROADMAP.md`, `MANUAL_II_ROADMAP.md`, `source.zip`, `tests.txt`, `patch_summary.txt`, `MANUAL_ARTIFACT_BASELINES_SHA256.txt`, `EXTERNAL_PAYLOADS_SHA256.txt`, `BUNDLE_CONTENTS_SHA256.txt`, and `SHA256.txt`. Publish the bundle as `bundle-<version>.zip`; `bundle.zip` may be emitted as a compatibility alias.

## Zenodo reference synchronization

Zenodo metadata references are generated from `refs.bib`, `manual/refs.bib`, and `manual-2/refs.bib`.
Check synchronization before building release artifacts:

```bash
python3 scripts/sync_zenodo_references.py --check
```

To refresh `.zenodo.json` after editing bibliography files, run:

```bash
python3 scripts/sync_zenodo_references.py
```

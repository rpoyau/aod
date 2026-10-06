# Build and release

This source tree is version-neutral. Release artifact filenames are stable (`main.pdf`, `manual.pdf`, `source.zip`, `bundle.zip`, `tests.txt`). The source archive is flat: unzipping `source.zip` into a repository checkout writes files directly into that checkout so Zenodo latest-file links keep working across revisions. The release version is read from `CANONICAL_VERSION.txt` and recorded in metadata and manifests.

Typical local build:

```bash
latexmk -xelatex -interaction=nonstopmode -halt-on-error main.tex
latexmk -cd -xelatex -interaction=nonstopmode -halt-on-error manual/main.tex
cp manual/main.pdf manual.pdf
python3 scripts/audit_scientific_sources.py . --build-root .
pytest -q | tee tests.txt
python scripts/build_release_bundle.py --outdir dist --main main.pdf --manual manual.pdf --tests tests.txt
```

The generated release files use stable names; source-internal paths also remain version-neutral.

Build Main before Manual from the same source tree. Manual imports Main's
published equation, section, appendix and table numbers from `main.aux`, using `main.fls` (the
recorder file produced by latexmk by default) to reject missing inputs and
inputs newer than the AUX. Missing files, unknown Main labels and mismatched
reference types stop the Manual build. This timestamp check does not detect
content edits with preserved modification times or within the same timestamp
second. Use clean Main-then-Manual builds for publication. Keep the delivered `main.pdf` and
`manual.pdf` together so their external links resolve to the root pair.

Before packaging publication artifacts, the scientific-source audit checks
both completed builds against their recorded inputs and executed AUX labels.
A canonical display stored in an uninvoked macro cannot satisfy this gate.

The release tests artifact is `tests.txt`. It is produced by the pytest suite; SymPy exact-arithmetic checks are part of that suite. The release builder consumes `tests.txt` directly.

## Artifact order

For Zenodo or other repositories with a default preview/display file, use the main note PDF as the primary artifact and upload/place it first:

```text
main.pdf
```

The manual PDF, source ZIP, bundle ZIP, tests, patch summary, and SHA-256 manifests accompany the main PDF. The bundle itself uses stable internal filenames and preserves `main.pdf` as the first member.


## Root `.zenodo.json` policy

`.zenodo.json` is committed at the repository root because GitHub-Zenodo synchronization reads metadata from the repository root when a GitHub release is published. The release builder validates this root file and includes it in `source.zip` for archival reproducibility; it does not generate `.zenodo.json` as the only authoritative copy.

Keep the visible Zenodo files version-neutral: `main.pdf`, `manual.pdf`, `source.zip`, `bundle.zip`, `tests.txt`, `patch_summary.txt`, `BUNDLE_CONTENTS_SHA256.txt`, and `SHA256.txt`.

## Zenodo reference synchronization

Zenodo metadata references are generated from `refs.bib` and `manual/refs.bib`.
Check synchronization before building release artifacts:

```bash
python3 scripts/sync_zenodo_references.py --check
```

To refresh `.zenodo.json` after editing bibliography files, run:

```bash
python3 scripts/sync_zenodo_references.py
```

# Build and release

This source tree is version-neutral. Release artifact filenames are stable (`main.pdf`, `manual.pdf`, `source.zip`, `bundle.zip`, `tests.txt`) so Zenodo latest-file links keep working across revisions. The release version is read from `CANONICAL_VERSION.txt` and recorded in metadata and manifests.

Typical local build:

```bash
latexmk -xelatex -interaction=nonstopmode -halt-on-error main.tex
latexmk -cd -xelatex -interaction=nonstopmode -halt-on-error manual/main.tex
cp manual/main.pdf manual.pdf
pytest -q | tee tests.txt
python scripts/build_release_bundle.py --outdir dist --main main.pdf --manual manual.pdf --tests tests.txt
```

The generated release files use stable names; source-internal paths also remain version-neutral.

The release tests artifact is `tests.txt`. It is produced by the pytest suite; SymPy exact-arithmetic checks are part of that suite. The release builder consumes `tests.txt` directly.

## Artifact order

For Zenodo or other repositories with a default preview/display file, use the main note PDF as the primary artifact and upload/place it first:

```text
main.pdf
```

The manual PDF, source ZIP, bundle ZIP, tests, patch summary, and SHA-256 manifests accompany the main PDF. The bundle itself uses stable internal filenames and preserves `main.pdf` as the first member.

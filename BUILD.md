# Build and release

This source tree is version-neutral. Release artifact filenames are generated from
`CANONICAL_VERSION.txt` by `scripts/build_release_bundle.py`.

Typical local build:

```bash
latexmk -xelatex -interaction=nonstopmode -halt-on-error main.tex
latexmk -cd -xelatex -interaction=nonstopmode -halt-on-error manual/main.tex
cp manual/main.pdf manual.pdf
pytest -q | tee tests.txt
python scripts/build_release_bundle.py --outdir dist --main main.pdf --manual manual.pdf --tests tests.txt
```

The generated release files carry the version string; source-internal paths do not.


The release tests artifact is `tests.txt`. It is produced by the pytest suite; SymPy exact-arithmetic checks are part of that suite. The release builder consumes `tests.txt` directly.

## Artifact order

For Zenodo or other repositories with a default preview/display file, use the main note PDF as the primary artifact and upload/place it first:

```text
AOD_Temporal_Dynamics_<version>_main.pdf
```

The manual PDF, source ZIP, bundle ZIP, tests, patch summary, and SHA-256 manifests accompany the main PDF. The bundle itself uses stable internal filenames and preserves `main.pdf` as the first member.

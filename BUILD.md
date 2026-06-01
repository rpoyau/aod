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

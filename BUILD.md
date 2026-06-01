# Build and release

This source tree is version-neutral. Release artifact filenames are generated from
`CANONICAL_VERSION.txt` by `scripts/build_release_bundle.py`.

Typical local build:

```bash
latexmk -xelatex -interaction=nonstopmode -halt-on-error main.tex
latexmk -cd -xelatex -interaction=nonstopmode -halt-on-error manual/main.tex
cp manual/main.pdf manual.pdf
python -m pytest -q | tee tests.txt
python scripts/build_release_bundle.py --outdir dist --main main.pdf --manual manual.pdf --tests tests.txt
```

The generated release files carry the version string; source-internal paths do not.


The release tests artifact is `tests.txt`. It is produced by the pytest suite; SymPy exact-arithmetic checks are part of that suite. The release builder consumes `tests.txt` directly and does not run tests. Run `python -m pytest -q | tee tests.txt` before invoking `scripts/build_release_bundle.py`; no separate verifier output is used.

The GitHub Actions workflow writes `tests.txt` before invoking the release builder. The builder requires this artifact and does not consume verifier/audit-pack logs.

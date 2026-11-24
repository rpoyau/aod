# Build and release

This source tree is version-neutral. Release artifact filenames are stable (`main.pdf`, `manual.pdf`, `source.zip`, `bundle.zip`, `tests.txt`). The source archive is flat: unzipping `source.zip` into a repository checkout writes files directly into that checkout so Zenodo latest-file links keep working across revisions. The release version is read from `CANONICAL_VERSION.txt` and recorded in metadata and manifests.

## Dependencies and source preparation

The default local and CI publication build is pure **Typst → PDF** and requires no TeXLive installation. Install pinned **Typst 0.15.1** (with Latin Modern fonts), `poppler-utils`, Python 3, and the test dependencies. On Ubuntu, the default build workflow uses:

```bash
sudo apt-get install fonts-lmodern poppler-utils python3 python3-pip python3-venv
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements-ci.txt pytest pandas matplotlib pypdf
```

Only the optional LaTeX compatibility compilation (`--with-latex`) and historical `98ddfa0` baseline parity verification require TeXLive (`sudo apt-get install latexmk texlive-xetex texlive-bibtex-extra texlive-latex-extra`).

Extract `source.zip` into a new empty directory. Git, credentials, and external project records are not required to run the publications, scientific checks or fallback release packaging. Keep `contracts/scientific/`, `tests/`, `typst/`, `latex/`, `archive/latex_baseline_98ddfa0/`, model scripts and datasets with the manuscripts. Current contracts state mathematical obligations and are checked against independent integrity bindings.

## Publication build (Typst primary + optional generated LaTeX compatibility)

Editable manuscript sources live under `typst/` (`typst/main.typ`, `typst/sections/`, `typst/appendices/`, `typst/manual/`, and shared native diagrams under `typst/lib/diagrams/`). The generated LaTeX compatibility tree lives under `latex/` and is produced deterministically from `typst/` by `scripts/typ2tex.py` (do not hand-edit files under `latex/`). The immutable historical scientific LaTeX baseline (`98ddfa0ebb38`) is preserved under `archive/latex_baseline_98ddfa0/` with `BASELINE_MANIFEST.json`.

Default local build (pure Typst → PDF, matching `.github/workflows/build.yml`; no TeXLive required):

```bash
# Build canonical Typst primary PDFs (_build/pub/main.pdf, _build/pub/manual.pdf):
python3 scripts/build_publication.py --outdir _build/pub --check-registry
cp _build/pub/main.pdf main.pdf
cp _build/pub/manual.pdf manual.pdf

# Audit canonical Typst authority, scientific contracts, and derivative latex/ sources:
python3 scripts/audit_scientific_sources.py .
set -o pipefail
python3 -m pytest -q | tee tests.txt
python3 scripts/build_release_bundle.py --outdir dist --main main.pdf --manual manual.pdf --tests tests.txt
```

Optional LaTeX export and XeLaTeX compatibility build (requires TeXLive; in CI, run on demand via `.github/workflows/latex.yml` using `workflow_dispatch`):

```bash
# Check committed latex/ freshness (omit --check-latex to regenerate latex/)
# and compile XeLaTeX compatibility PDFs (dist_latex/latex/main.pdf, dist_latex/latex/manual.pdf):
python3 scripts/build_publication.py --outdir dist_latex --check-registry --with-latex --check-latex
python3 scripts/audit_scientific_sources.py . --build-root latex

# Regenerate or verify generated LaTeX and exported vector diagrams directly:
python3 scripts/export_typst_figures.py --root . --outdir latex/manual/figures/generated
python3 scripts/typ2tex.py --root . --outdir latex --check
```

The generated release files use stable names; source-internal paths also remain version-neutral.

Always build Main before Manual in both representations:

- **Canonical Typst (`dist/main.pdf`, `dist/manual.pdf`):** `scripts/build_typst.py` compiles deterministic PDFs (`--creation-timestamp`, honoring `SOURCE_DATE_EPOCH` and defaulting to `0`), exports `typst/lib/main_registry.json` with `main_sources_sha256` and `main_pdf_filename: "main.pdf"`, and passes `--input expected_main_digest=...` and `--input expected_main_pdf_filename=main.pdf` when compiling `typst/manual/main.typ`. Stale registries, companion filename mismatches, unknown labels, and wrong reference types fail closed.
- **Optional generated LaTeX (`dist_latex/latex/main.pdf`, `dist_latex/latex/manual.pdf`):** `latex/manual/preamble.tex` imports generated Main's published equation, section, appendix and table numbers from `../main.aux`, using `../main.fls` to reject missing or stale Main inputs, and targets sibling `main.pdf`. Copy `latex/manual/main.pdf` to `dist_latex/latex/manual.pdf` alongside `dist_latex/latex/main.pdf` so sibling links resolve within the generated pair.
- **Native diagrams (`latex/manual/figures/generated/*.pdf`):** `scripts/export_typst_figures.py` compiles the shared native diagrams and vector figures under `typst/lib/` into tightly bounded 1-page vector PDFs (zero raster XObjects, extractable text; optional `--format png --ppi 300|600` fallback), while captions and labels remain real LaTeX. Existing PNG/JPEG rasters are staged unchanged without resampling.

Before packaging publication artifacts, `.github/workflows/build.yml` runs `scripts/audit_scientific_sources.py .` to verify canonical `typst/` authority, scientific contracts, and derivative `latex/` source consistency (with optional `--build-root latex` executed `.fls`/`.aux`/`.log` verification in manual `.github/workflows/latex.yml`). The release tests artifact is `tests.txt`, produced by the pytest suite (including SymPy exact-arithmetic checks).

## Parity verification against the preserved 98ddfa0 baseline

Historical `98ddfa0` baseline parity verification is optional and triggered manually in CI via `.github/workflows/latex.yml` (`workflow_dispatch` with `run_baseline_parity=true`). Locally, materialize the immutable historical baseline without Git (requires TeXLive) and verify both canonical Typst and generated LaTeX outputs in normal and optimized Python:

```bash
python3 scripts/materialize_latex_baseline.py --root . --outdir /tmp/aod_baseline_98ddfa0
(cd /tmp/aod_baseline_98ddfa0 && latexmk -xelatex -interaction=nonstopmode -halt-on-error main.tex)
(cd /tmp/aod_baseline_98ddfa0 && latexmk -cd -xelatex -interaction=nonstopmode -halt-on-error manual/main.tex)
cp /tmp/aod_baseline_98ddfa0/manual/main.pdf /tmp/aod_baseline_98ddfa0/manual.pdf
python3 scripts/verify_typst_parity.py --outdir _build/typst_parity \
  --baseline-root /tmp/aod_baseline_98ddfa0 \
  --baseline-main-pdf /tmp/aod_baseline_98ddfa0/main.pdf \
  --baseline-manual-pdf /tmp/aod_baseline_98ddfa0/manual.pdf \
  --generated-latex-main-pdf dist_latex/latex/main.pdf \
  --generated-latex-manual-pdf dist_latex/latex/manual.pdf
python3 -O scripts/verify_typst_parity.py --outdir _build/typst_parity_opt \
  --baseline-root /tmp/aod_baseline_98ddfa0 \
  --baseline-main-pdf /tmp/aod_baseline_98ddfa0/main.pdf \
  --baseline-manual-pdf /tmp/aod_baseline_98ddfa0/manual.pdf \
  --generated-latex-main-pdf dist_latex/latex/main.pdf \
  --generated-latex-manual-pdf dist_latex/latex/manual.pdf
cmp _build/typst_parity/parity_report.json _build/typst_parity_opt/parity_report.json
```

`scripts/verify_typst_parity.py` checks:
- **Gate A** — all 211 historical baseline entries match `archive/latex_baseline_98ddfa0/BASELINE_MANIFEST.json`.
- **Gate A2** — evaluation policy over all Typst units, template/driver digest pins, shared diagram components, and mode-aware content allowlist.
- **Gate B** — ordered source parity (prose, punctuation, literal commands, full math AST, all four shared flowcharts, seven immutable tables, and raster bindings) for both canonical `typst/` and generated `latex/`.
- **Gate C** — rendered PDF parity against the materialized historical baseline (labels, equation numbers/tags, peer links, external URIs, citations, bibliography, source prose clauses, insertion detection, symbol glyph parity, decimals, and opaque black text-paint scan) for canonical Typst PDFs and (when supplied) generated LaTeX compatibility PDFs.
- **Gate D** — all negative controls (including wrong peer filename `wrong_main.pdf`, stale registry, flowchart mutation/bounds, and `typ2tex` provenance/propagation checks).

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

## Reproducibility checks

```bash
python3 manual/scripts/aod_native_closure_wave.py --check-data
python3 manual/scripts/aod_awareness.py --check-data
python3 manual/scripts/aod_cell_measures.py --check-data
python3 manual/scripts/aod_mapping_error.py --check
python3 manual/scripts/aod_temporal_observation.py --check
python3 manual/scripts/aod_temporal_anchor.py --check-data
python3 manual/scripts/aod_temporal_metrology.py --check
python3 scripts/sync_zenodo_references.py --check
```

Generated fixture results are run reports. They are validated against the unchanged runner and canonical inputs; they are not scientific specifications. The registered current scientific contracts remain in `contracts/scientific/`.

The source packager uses the complete tracked source in a Git checkout and the documented source surfaces in an unpacked archive. Both paths include the tests and scientific contracts, preserve executable file modes, and omit generated build products and temporary output. Place detached logs and release bundles outside the source tree when comparing independent builds.

The mapping report includes authenticated original MAP-21/22 finite laws.
Its exact probe, historical scientific dependencies and expected output are
retained as a pinned scientific subset. Anchor replay uses original scientific
sources and histories through a separately bound admission adapter, preserving
the numerical diagnostics and four population/exposure cases. Source releases
include these subsets; detached task archives are not execution dependencies.

The complete original archives remain separately auditable when supplied
explicitly from project history:

```bash
python3 scripts/audit_historical_archive.py metrology /path/to/original_replay_r01.zip
python3 scripts/audit_historical_archive.py anchor /path/to/original_anchor_r02.zip
```

The second command executes the unmodified historical audit and compares all
five original outputs. This archival operation is distinct from normal
scientific replay and is not required by the scientific source release.

Temporal predictions use `ObservationContext`; evaluation requires the independent
`original_context`. The active temporal report is schema 3, governed by
`contracts/scientific/TEMPORAL_OBSERVATION.json`. Generic map and error-budget
contracts remain version 2. Recreate callers from their original complete histories
and preparation; a scalar-count record cannot be migrated into native admission.

The additive metrology companion uses `contracts/scientific/TEMPORAL_METROLOGY.json`
and frozen profiles in `manual/data/temporal_metrology/`. Its `--check` command
is read-only; `--write-data` intentionally regenerates only its new report.
Run `tests/test_metrology.py` normally and under `python3 -O -m pytest` when
changing that interface, together with the inherited scientific and consumer
checks. Phase fixtures, historical input reductions and source-reported
uncertainties retain distinct evidence classes; their replay is not a physical
frequency or lifetime prediction.

The same companion also validates the additive comparison assessment. Run
`tests/test_comparison.py` in both interpreter modes when changing its
influence, interval, environment or reference-dependency checks. The existing
observation interface and historical source profiles remain valid. Downstream
consumers pinned to an earlier producer identity require an explicit source
rebind before their strict integration command can accept this candidate.

## Optional Rust exact core (S4)

An optional, strictly `std`-only, zero-float, zero-`unsafe` Rust exact-arithmetic core lives under `crates/aod-core/`. It is not required for canonical Typst publication builds, scientific source audits, or the Stage 2 Python reference engine (`manual/engine/`), which remains 100% independent of Rust.

When a Rust toolchain is installed, run offline/locked verification with Cargo build output directed under `_build/cargo-target` so `crates/aod-core/target/` is never created in the source tree:

```bash
CARGO_TARGET_DIR=_build/cargo-target cargo test --manifest-path crates/aod-core/Cargo.toml --offline --locked
mkdir -p _build/s4
CARGO_TARGET_DIR=_build/cargo-target cargo run --manifest-path crates/aod-core/Cargo.toml --offline --locked -- \
  --verify-vectors --check-zero-float --report _build/s4/rust_report_debug.json
CARGO_TARGET_DIR=_build/cargo-target cargo run --manifest-path crates/aod-core/Cargo.toml --offline --locked --release -- \
  --verify-vectors --check-zero-float --report _build/s4/rust_report_release.json
cmp _build/s4/rust_report_debug.json _build/s4/rust_report_release.json
```

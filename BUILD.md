# Build and release

This source tree is version-neutral. Release artifact filenames are stable (`main.pdf`, `manual.pdf`, `source.zip`, `bundle.zip`, `tests.txt`). The source archive is flat: unzipping `source.zip` into a repository checkout writes files directly into that checkout so Zenodo latest-file links keep working across revisions. The release version is read from `CANONICAL_VERSION.txt` and recorded in metadata and manifests.

## Dependencies and source preparation

Install XeLaTeX, latexmk, BibTeX support, Python 3 and the test dependencies. On Ubuntu, the publication workflow uses:

```bash
sudo apt-get install latexmk texlive-xetex texlive-bibtex-extra texlive-latex-extra python3 python3-pip python3-venv
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements-ci.txt pytest pandas matplotlib
```

Extract `source.zip` into a new empty directory. Git, credentials, and external project records are not required to run the publications, scientific checks or fallback release packaging. Keep `contracts/scientific/`, `tests/`, model scripts and datasets with the manuscripts. Current contracts state mathematical obligations and are checked against independent integrity bindings.

Typical local build (Bash):

```bash
latexmk -xelatex -interaction=nonstopmode -halt-on-error main.tex
latexmk -cd -xelatex -interaction=nonstopmode -halt-on-error manual/main.tex
cp manual/main.pdf manual.pdf
python3 scripts/audit_scientific_sources.py . --build-root .
set -o pipefail
python3 -m pytest -q | tee tests.txt
python3 scripts/build_release_bundle.py --outdir dist --main main.pdf --manual manual.pdf --tests tests.txt
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

## Additive native Typst publication and parity checks (M4 Objective 1)

Native Typst sources live under `typst/` alongside the retained LaTeX baseline (`main.tex`, `manual/main.tex`, `refs.bib`, `manual/refs.bib`, figures, and `manual/data/` remain unchanged). Canonical release promotion is separate from this additive migration.

Build the native Typst pair (`typst 0.15.1`, Latin Modern fonts) and verify direct parity against the retained LaTeX baseline:

```bash
python3 scripts/build_typst.py --outdir _build/typst --check-registry
python3 scripts/verify_typst_parity.py --outdir _build/typst_parity --baseline-main-pdf main.pdf --baseline-manual-pdf manual.pdf
python3 -O scripts/verify_typst_parity.py --outdir _build/typst_parity_opt --baseline-main-pdf main.pdf --baseline-manual-pdf manual.pdf
cmp _build/typst_parity/parity_report.json _build/typst_parity_opt/parity_report.json
```

`scripts/build_typst.py` compiles deterministic PDFs (`--creation-timestamp`, honoring `SOURCE_DATE_EPOCH` and defaulting to `0`) under unambiguous native filenames (`main_typst.pdf`, `manual_typst.pdf`) alongside the retained LaTeX pair (`main.pdf`, `manual.pdf`). It exports `typst/lib/main_registry.json` from `typst/main.typ` with both `main_sources_sha256` and `main_pdf_filename` (`main_typst.pdf`), and passes `--input expected_main_digest=...` and `--input expected_main_pdf_filename=main_typst.pdf` when compiling `typst/manual/main.typ`, rejecting stale Main registries, companion filename mismatches, unknown labels, and wrong Main reference types. Both publication paths are packaged into `source.zip` and reconstruct outside Git.

`scripts/verify_typst_parity.py` reports `PASS` only when both retained baseline PDFs are supplied, every negative control runs, and every source prose clause is verified in the rendering; otherwise it emits an explicit `PARTIAL_NON_ACCEPTANCE_*` verdict. Its gates are:

- **A** — the 211 protected baseline files are unchanged.
- **A2** — evaluation policy:
  - every Typst unit matches its `typst/manifest.json` digest;
  - the template and driver files (`typst/lib/aod_schema.typ`, both preambles, both `main.typ`) are pinned by digest inside the verifier;
  - no undeclared `.typ` files exist;
  - content files pass a mode-aware allowlist with no `show`/`let`/`context`, no argument spreads (`..`) or parenthesized callees, no fill/opacity/hide/place/overlay primitives, positive literal layout lengths, in-bounds `#aod-flowchart` geometry, reviewed text sizes only, and only surface-preamble imports and manifest includes.
- **B** — ordered source parity: prose, punctuation, literal commands, the full math AST (preserving explicit grouping, matrix/array delimiters and augment bars, distinct `bar`/`macron` vs `overline`, upright bold vs bold-italic, and exact `emptyset` without aliasing `diameter`), all four TikZ vs `#aod-flowchart` diagrams (ordered node prose/math ASTs and directed edge topology), the seven immutable tables cell by cell, and figure image bindings to protected baseline images.
- **C** — rendered parity against the retained PDFs:
  - labels, exact numbered block-equation counts (zero unintended unlabeled numbered equations) and per-label equation numbers matched against LaTeX sequential numbering/tags, and peer links;
  - clickable external `/URI` destination sets and exact inline citation bracket sequences;
  - bibliography;
  - source prose clauses, each count-matched against the baseline (any non-baseline-anchored or unverified clause emits a non-acceptance partial verdict);
  - insertion detection: word 4-grams (17-entry layout allowlist) and out-of-source words of at least 4 letters that exceed their baseline count (explicit per-word allowlist). Latin ligatures are decomposed on both sides. Because pdftotext versions space math runs differently (poppler 22, 24 and 26 were tested), the word check excludes Typst words containing Unicode mathematical alphanumerics, and it counts a word inside a longer out-of-vocabulary baseline token (for example `tAdmfib` from `⊔Admﬁb`) as a baseline occurrence;
  - relation and symbol glyph parity for `+ < > ≤ ≥ ↔ × ∞ ≡ ∅` (and zero `⌀`);
  - decimals;
  - a PDF text-paint scan requiring opaque black fill (`ExtGState /ca == 1`), no zero-area clipping path (`W`/`W*`), render mode 0 and text of at least 4 pt.
- **D** — 29 negative controls. Each must be rejected by its intended check; the 3 that depend on the baseline are recorded as skipped when no baseline PDFs are given.

Residual limits:

- Rendered `−`, `=`, `∈`, `·`, `∂` and `∑` counts differ between the engines. They are covered by the source math AST and the evaluation policy, not by rendered counts.
- Rendered insertion of fewer than four consecutive source-vocabulary words with no new out-of-source word is below the rendered detectors' resolution. That class is excluded by the template pins and content policy (Gate A2) together with source parity (Gate B), not detected in the PDF.
- Words typeset in math alphanumerics are outside the rendered word check. Their content is bound by the source math AST (Gate B) and the evaluation policy (Gate A2).
- Overlay primitives are forbidden by the policy, not detected in the PDF.
- Raster figure pixels are bound by protected file digest, not compared visually.
- Layout and visual review remain separate human checks.

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

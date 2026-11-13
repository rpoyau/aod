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
python3 manual/scripts/aod_m3_temporal.py --check
python3 manual/scripts/aod_m3_anchor.py --check-data
python3 manual/scripts/aod_m3_metrology.py --check
python3 scripts/sync_zenodo_references.py --check
```

Generated fixture results are run reports. They are validated against the unchanged runner and canonical inputs; they are not scientific specifications. The registered current scientific contracts remain in `contracts/scientific/`.

The source packager uses the complete tracked source in a Git checkout and the documented source surfaces in an unpacked archive. Both paths include the tests and scientific contracts, preserve executable file modes, and omit generated build products and temporary output. Place detached logs and release bundles outside the source tree when comparing independent builds.

The M3 mapping report includes authenticated original MAP-21/22 finite laws.
The anchor check replays the supplied historical experiment and four declared
population/exposure cases from retained engine inputs. The two ZIP files in
`manual/data/m3/historical_metrology/` and `manual/data/m3/temporal_anchor/`
are immutable source dependencies and are included in the source archive.

Temporal predictions use `ObservationContext`; evaluation requires the independent
`original_context`. The active temporal report is schema 3, governed by
`contracts/scientific/TEMPORAL_OBSERVATION.json`. Generic map and error-budget
contracts remain version 2. Recreate callers from their original complete histories
and preparation; a scalar-count record cannot be migrated into native admission.

The additive metrology companion uses `contracts/scientific/TEMPORAL_METROLOGY.json`
and frozen profiles in `manual/data/m3/temporal_metrology/`. Its `--check` command
is read-only; `--write-data` intentionally regenerates only its new report.
Run `tests/test_m3_metrology.py` normally and under `python3 -O -m pytest` when
changing that interface, together with the inherited scientific and consumer
checks. Phase fixtures, historical input reductions and source-reported
uncertainties retain distinct evidence classes; their replay is not a physical
frequency or lifetime prediction.

The same companion also validates the additive comparison assessment. Run
`tests/test_m3_comparison.py` in both interpreter modes when changing its
influence, interval, environment or reference-dependency checks. The existing
observation interface and historical source profiles remain valid. Downstream
consumers pinned to an earlier producer identity require an explicit source
rebind before their strict integration command can accept this candidate.

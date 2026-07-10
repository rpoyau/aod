# AGENTS.md — AOD v40.04 release-candidate branch

## Repository and branch

- Repository: `rpoyau/aod`
- Release-candidate branch: `v40.04`
- Stable branch: `main`
- Work only on `v40.04` or a task branch created from `v40.04`.
- Never push directly to `main`.
- Do not merge to `main`; the project owner performs the point-release merge.

## Authority and source discipline

- Scientific and axiom authority is the project owner.
- AF, AFC, General Mechanics, and the accepted AOD stable baseline are source-bound inputs.
- Do not introduce new axioms, hidden premises, native resonance claims, empirical claims, or interpretation beyond the authorized milestone.
- Treat project-provided dependency payloads as trusted unless the active delta changes their bytes.
- Strictly validate the evolving AOD source, touched delta, generated artifacts, manifests, and milestone tests.

## Current release line

- Release line: `v40.04`
- Current reviewed source milestone: `v40.04r03`
- Current scope: Foundation Doctrine and D.E.C. Reporting Overlay
- Next planned source milestone: Manual-II Worked Example Reshape
- Bundle phase state is not repository source state. REVIEW, FEEDBACK, and GO are bundle-instance surfaces; keep the Git source as authored source.

## Foundation doctrine

Preserve these typed statements:

- Temporal flow is duon-current cadence across relational distinction between anchored fields.
- Measured time is relational tick count under a declared clock process.
- SADAR is a boundary-scoped returned-current, pressure, and attention-balance object.
- Frequency, SI time, wavelength, and energy coordinates appear only through declared lane-specific operators.
- `tau_cycle` is the phase-cycle coordinate; `pi = tau_cycle / 2` is a declared display coordinate.
- SPARC is a 2D observable-data fixture under a declared projection/readout policy.
- Manual I/Main define doctrine. Manual II applies doctrine through worked D.E.C. examples and compact artifacts.

## Closed lanes

Unless the project owner explicitly authorizes a lane, keep these closed:

- target joins
- SI report activation
- metric report activation
- residuals
- scores
- empirical comparisons
- subject/reference phase locks
- native resonance periods
- hyperfine C6 pass/fail claims

## Build and verification

Install dependencies using the environment setup script, then use:

```bash
latexmk -xelatex -interaction=nonstopmode -halt-on-error main.tex
latexmk -cd -xelatex -interaction=nonstopmode -halt-on-error manual/main.tex
cp manual/main.pdf manual.pdf
latexmk -cd -xelatex -interaction=nonstopmode -halt-on-error manual-2/main.tex
cp manual-2/main.pdf manual-2.pdf
pytest -q
python3 scripts/sync_zenodo_references.py --check
```

Before committing a milestone, run the applicable validators:

```bash
python3 tools/validate_surface_synchronization.py .
python3 tools/validate_carried_scaffolds.py .
python3 tools/validate_manual_pdf_layout.py . --render-check
```

When validating a complete emitted bundle, also run:

```bash
python3 tools/validate_complete_bundle.py .
python3 tools/validate_phase_bundle.py .
python3 tools/validate_cycle_bundle.py .
python3 tools/validate_upstream_release_lock.py . --allow-pending
```

## Authoring rules

- Use exact integer, rational, algebraic, or symbolic representations where the lane requires exactness.
- Do not silently replace exact rows with decimal approximations.
- Keep native rows separate from declared coordinate maps, conversion/projection errors, empirical residuals, and scores.
- Use deterministic generators for machine-readable ledgers.
- Update `governance/RELEASE_METADATA_STATE.json` first, then synchronize generated metadata surfaces.
- Preserve carried scaffold anchors unless the owner explicitly retires them.
- Run PDF layout validation after LaTeX changes.
- Keep `source.zip` flat and free of generated LaTeX build products.

## Review guidelines

- Treat candidate identity, active lane, stable baseline, source-tree hashes, root/source duplicated surfaces, manifests, and PDF layout as blocking controls.
- Treat project dependency payloads as nonblocking when untouched.
- Flag only scope-relevant defects.
- Do not infer empirical validity from bundle/process validity.
- Emit exact affected paths, expected state, observed state, repair instruction, and verification command for each blocking finding.

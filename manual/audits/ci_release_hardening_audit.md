# CI and release hardening audit

This audit records the manual-local hardening pass for the active source tree.

## CI checks

The public workflow installs the Python requirements, runs the audit verifier, executes every active manual exact-row test under `manual/tests/`, builds the theorem note and manual PDFs, builds the source bundle, and checks bundle artifact hygiene outside `archive/`.

Manual exact-row tests currently include:

- `manual/tests/test_05f_wire_current_boundary_transport.py`
- `manual/tests/test_05g_05h_application_scaffolds.py`
- `manual/tests/test_05i_integer_collision_vertex.py`

## Temporal-duration direction row

Transport rows record relative temporal-duration change as `(Delta s, Delta n)` with direction supplied by declared incidence data on the same retained relation.

## Source bundle check

The source bundle check confirms the presence of the active manual, exact-row tests, audit verifier, and CI requirements file. It also checks the bundle for generated artifact hygiene.

## Archive status

The `archive/` tree is preserved as historical source material. Active provenance remains manual-local through raw setup, script, derived rows, figures, tests, and audits.

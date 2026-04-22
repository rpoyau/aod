# Phase III wire/current exact audit

Manual-local source package for the Stage III wire/current worked row.

## Source path

- Raw setup: `manual/data/raw/05f_wire_current_setup.json`
- Script: `manual/code/05f_wire_current_boundary_transport.py`
- Exact CSV: `manual/data/derived/05f_wire_current_exact.csv`
- Report CSV: `manual/data/derived/05f_wire_current_report.csv`
- Trace CSV: `manual/data/derived/05f_wire_current_trace.csv`
- Notebook: `manual/notebooks/05f_wire_current_boundary_transport.ipynb`
- Tests: `manual/tests/test_05f_wire_current_boundary_transport.py`

## Exact audit identities

The two-sided retained probe cut satisfies:

- `r = 0 -> u_tr = 0 -> w_perp = 0`
- `r -> -r -> J_flux -> -J_flux and w_perp -> -w_perp`
- `chi -> -chi -> w_perp -> -w_perp`
- `w_perp_plus + w_perp_minus = 0`
- `J_duon + J_tetron + J_other = J_flux`

The script and test file evaluate these with `fractions.Fraction`.

## Current exact witness values

- `J_flux = 2501/453600`
- `w_perp_plus = 3151/37800`
- `w_perp_minus = -3151/37800`

The PNG figures are visual renderings of the rational rows and are not source inputs.
## Source hygiene

Generated bibliography files (`manual/main.bbl`, `manual/main.blg`) are not source artifacts. The release bundle excludes `.bbl` and `.blg` suffixes.

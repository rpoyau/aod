# Phase IV later-application scaffold audit

Phase IV adds manual-local scaffold rows and exact toy collision examples after the Phase III wire/current implementation. The main note calculus is not changed.

## Active artifacts

Matter-regime scaffold:
- `manual/data/raw/05g_matter_regime_setup.json`
- `manual/code/05g_matter_regime_scaffold.py`
- `manual/data/derived/05g_matter_regime_scaffold.csv`
- `manual/figures/matter/01_matter_transport_scaffold.png`
- `manual/tests/test_05g_05h_phaseIV_scaffolds.py`

Planetary-shell and ring-refinement scaffold:
- `manual/data/raw/05h_planetary_shell_setup.json`
- `manual/code/05h_planetary_shell_scaffold.py`
- `manual/data/derived/05h_planetary_shell_scaffold.csv`
- `manual/data/derived/05h_saturn_galactic_ring_refinements.csv`
- `manual/figures/planetary/01_earth_moon_shell_scaffold.png`
- `manual/figures/planetary/02_saturn_galactic_ring_refinements.png`
- `manual/tests/test_05g_05h_phaseIV_scaffolds.py`

Integer collision examples:
- `manual/data/raw/05i_duon_collision_setup.json`
- `manual/code/05i_integer_collision_vertex.py`
- `manual/data/derived/05i_duon_collision_exact.csv`
- `manual/data/derived/05i_duon_collision_trace.csv`
- `manual/figures/collision/01_integer_collision_outcomes.png`
- `manual/tests/test_05i_integer_collision_vertex.py`

## Status

- Matter-regime rows remain classification scaffold rows.
- Planetary-shell rows remain scaffold rows.
- Saturn and galactic ring rows remain scaffold/source-normalized-pending rows.
- The integer collision rows are exact toy rows for Appendix D vertex auditing.
- No external electromagnetic, gravitational, SI, or benchmark interpretation is attached by Phase IV.

## Test commands

```bash
python3 manual/tests/test_05g_05h_phaseIV_scaffolds.py
python3 manual/tests/test_05i_integer_collision_vertex.py
```

Both tests passed in the Phase IV execution environment.

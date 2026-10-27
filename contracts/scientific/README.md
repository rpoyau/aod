# Scientific contracts

These records bind the current rendered manuscript, executable models and exact fixture provenance. They do not supply additional dynamics or substitute for the manuscript definitions.

- `CANONICAL_BINDINGS.json` binds 44 concept groups, 81 canonical formulas, five supplemental displays, 72 ordered dependencies, unique definitions, first uses, appendix structure, Manual examples and protected source bytes.
- `OWNERSHIP_AND_FIXTURES.json` binds current Main/Manual ownership and all 47 awareness rows. Immutable legacy identifiers and original row digests retain fixture provenance; current row digests bind the executable inputs.
- `AWARENESS_ACTIVE_CAUSAL_SPEC.json` and `OPERATIVE_SELF_SCHEMA.json` specify the declared finite-model intervention and its operational scope.
- `ROUND_TRIP_PHASE_FACTOR_SPEC.json`, `FOURIER_SCOPE.md`, `METROLOGY_BOUNDARY.md` and `UPDATE_CAUSAL_ORDER.md` state mathematical and reporting boundaries.
- `HISTORICAL_TOY_SOURCE_STATUS.csv` preserves the execution status of source-unavailable historical examples, distinct from the 47 executable fixtures.

Run `python3 scripts/audit_scientific_sources.py .` and `python3 -m pytest -q` from the source root. Contract bytes are pinned independently in the checker; editing a contract cannot authorize a source mutation. The source package contains all validation inputs and requires no external project records.

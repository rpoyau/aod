# Scientific contracts

These records bind the current rendered manuscript, executable models and exact fixture provenance. They do not supply additional dynamics or substitute for the manuscript definitions.

- `CANONICAL_BINDINGS.json` binds 44 concept groups, 81 canonical formulas, five supplemental displays, 72 declared prerequisite edges, unique definitions, active model examples and protected source bytes. Prerequisite edges record logical dependencies; they do not require a particular page order, heading or folder layout.
- `OWNERSHIP_AND_FIXTURES.json` binds current Main/Manual ownership and all 47 awareness rows. Immutable legacy identifiers and original row digests retain fixture provenance; current row digests bind the executable inputs.
- `AWARENESS_ACTIVE_CAUSAL_SPEC.json` and `OPERATIVE_SELF_SCHEMA.json` specify the declared finite-model intervention and its operational scope.
- `ROUND_TRIP_PHASE_FACTOR_SPEC.json`, `FOURIER_SCOPE.md`, `METROLOGY_BOUNDARY.md` and `UPDATE_CAUSAL_ORDER.md` state mathematical and reporting boundaries.
- `HISTORICAL_TOY_SOURCE_STATUS.csv` preserves the execution status of source-unavailable historical examples, distinct from the 47 executable fixtures.

Run `python3 scripts/audit_scientific_sources.py .` and `python3 -m pytest -q` from the source root. Contract bytes are pinned independently in the checker; editing a contract cannot authorize a source mutation. The source package contains all validation inputs and requires no external project records.

Source hashes establish the reviewed version. Mathematical checks separately verify exact arithmetic and model behavior under the declared assumptions. Neither a matching hash nor a preferred prose arrangement proves a scientific claim.

## Cell measures and mappings

`CELL_MEASURE_SPEC.json` declares the finite cell completion, incidences, weights and fold properties. `MAP_CONTRACT.json` and `ERROR_BUDGET.json` specify typed mapping records and the distinction between exact results, bounds, uncertainty and unknown applicability. `M3_MATHEMATICAL_BINDINGS.json` binds the new active mathematical statements and their source bytes. All are registered explicitly and have independent checker digests.

The worked records in `manual/data/m3/` are reproduced by `aod_cell_measures.py`, `aod_mapping_error.py` and `aod_m3_temporal.py` in `manual/scripts/`. Their tests exercise rejected inputs and mathematical counterexamples as well as positive cases. A declared cubical metric, exact finite probability law or conditional SI observation map is not an independent physical prediction.

`TEMPORAL_OBSERVATION.json` binds the temporal observation context and frozen calibration domain. Historical metrology replay and temporal-anchor records retain their original source archives separately from current executable results. Their finite-law and count-transfer checks do not establish a physical clock calibration.

`TEMPORAL_METROLOGY.json` governs the additive observation companion. It distinguishes
reclosures, shed-packet events, oscillator phase advances, calibrated population
estimates and nuclear timestamps. `aod_m3_metrology.py --check` replays exact
finite-window phase fixtures and source-bound H/Cs reductions. Published
uncertainties retain their experimental provenance; they do not supply a finite
joint probability model. Existing temporal schema 3 and generic map/error
version 2 remain unchanged. The companion does not establish a physical
closure-to-cycle map or isotope-specific dynamics.

The additive comparison assessment records each influence's input/setup/output
location, correction ownership, residual uncertainty, interval, environmental
transfer and shared-reference dependencies. It validates source-bound
declarations without applying corrections, constructing a joint uncertainty
model or certifying an independent physical prediction. A materiality bound
screens one influence only; unresolved inputs stay unresolved.

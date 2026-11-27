# Execution Plan (`02_plan.md`) — `BND-P2-01`

**Milestone**: `M4_5-uow-overhaul` | **Phase**: `P2-tesseract-volume-pi` | **Bundle**: `BND-P2-01`

## Scope Verification & Resolved Spec Reconciliation
- **Write Set** (`scope.write_set`): `manual/engine/sectors/manual_dec_examples.py`, `crates/aod-core/src/manual_dec_ops.rs`, `manual/scripts/aod_cell_measures.py`, `manual/data/cell_measures/cells_geometry.json`, `manual/data/boundary_sadar/cell_measures_staircase_fold_dec.csv`, `contracts/scientific/CELL_MEASURE_SPEC.json`, `manual/engine/vectors/rational_core.jsonl`, `contracts/scientific/CANONICAL_BINDINGS.json`, `scripts/audit_ontology_compaction.py`, `typst/representation_change_ledger.json`, `typst/figure_inventory.json`, `manual/engine/sectors/tier1_adapters.py`, `manual/engine/registry.py`, `crates/aod-core/tests/integration_vectors.rs`, `tests/test_cells.py`, `tests/test_tesseract_pi.py`.
- **4D Staircase 3-Boundary Exactness**: Compute and emit **both**:
  1. `B3_staircase = 8 * V3_plus = 64 * N3_out(n) / n^3` (exact exposed 3-boundary of outer 4-ball staircase $S_{4,n}^+$, verified by literal neighbor-absence `exposed_faces_by_occupancy` for $n \in \{1, 2, 4\}$: `64, 64, 51`, converging to $\frac{32}{3}\pi \approx 33.5103 \neq 2\pi^2$), with exact falsifier `B3_stair_minus_4V4plus = B3_staircase - 4 * V4_plus > 0` for all $n \ge 2$ (`0` at $n = 1$).
  2. `B3_tesseract_box = 64` and `B3_box_minus_4V4plus = 64 - 4 * V4_plus` (exact exposed 3-boundary of bounding 4-cube $[-1,1]^4$).

## Execution DAG

### Node 1 — Python S2 (`manual/engine/sectors/manual_dec_examples.py`)
- Import `TritWord`, `TritRatio` from `manual.engine.ternary`.
- `_verify_q4_unit_cube()`: enumerate all 81 elementary cells of $Q_4$, compute `[16, 32, 24, 8, 1]`, Euler characteristic $= 1$, and verify $\partial^2 c = 0$ via `_cubical_boundary` for every cell.
- `_eval_cellular_fold_chain_map()`: build explicit complexes $K_2 = Q_L \cup Q_R$ (6V, 7E, 2F) and $L_2 = Q_*$ (4V, 4E, 1F), exact integer boundary matrices $B_2^K, B_1^K, B_2^L, B_1^L$ and induced fold matrices $F_2, F_1, F_0$ from $f(x,y) = (\min(x,2-x), y)$ with orientation reversal on $Q_R$; verify $B_1^K B_2^K = 0$, $B_1^L B_2^L = 0$, $B_2^L F_2 = F_1 B_2^K$, $B_1^L F_1 = F_0 B_1^K$, and $F_1(B_2^K c_{\mathrm{top}}) = 0$; derive `(fold_occupied_area=2, fold_image_area=1, fold_retained_multiplicity=2, fold_oriented_top_sum=0, fold_seam_cancelled=1, fold_surviving_boundary_edges=3, chain_map_commutes=1)` strictly from matrix multiplication (zero hardcoded output literals).
- `_tesseract_4d_orthant_counts(n)` (Route A sorted-orthant multinomial cross-checked against Route B 3D-column `isqrt` counts + $N_{3,\mathrm{out}}$): compute in `TritWord`/`TritRatio` ($B_{\mathrm{core}}$, zero Machin $\arctan$):
  - `V4_minus`, `V4_plus`, `V4_width` ($\le 64/n$), `V3_plus`
  - `pi_sq_lower = 2 * V4_minus`, `pi_sq_upper = 2 * V4_plus`
  - `pi_4d_lower = isqrt_floor(32 * N_in) / n^2`, `pi_4d_upper = isqrt_ceil(32 * N_out) / n^2`
  - `pi_cross_lower = 2 * V4_minus / A2_plus`, `pi_cross_upper = 2 * V4_plus / A2_minus` (`None` at $n=1$)
  - `B3_staircase = 8 * V3_plus`, `B3_stair_minus_4V4plus`, `B3_tesseract_box = 64`, `B3_box_minus_4V4plus`
  - Dyadic monotonicity checks on consecutive $n \to 2n$ levels.
- Quarantined $B_{\mathrm{ext}}$ Machin verification strictly after frozen geometry (`V4_minus <= lo^2/2 < hi^2/2 <= V4_plus`, `pi_4d_lower <= lo < hi <= pi_4d_upper`, `pi_cross_lower <= lo < hi <= pi_cross_upper` for $n \ge 2$, `B3_staircase > 2*hi^2`, `32/3*lo - 2*hi^2 > 0` -> `axial_4d_gap_positive = 1`).
- `build_cell_measures_csv_rows()`: preserve all 7 existing 2D columns verbatim and append the 13 exact 4D columns (`V4_minus_exact`, `V4_plus_exact`, `V4_width_exact`, `B3_staircase_exact`, `B3_stair_minus_4V4plus`, `B3_tesseract_box`, `B3_box_minus_4V4plus`, `pi_4d_lower_exact`, `pi_4d_upper_exact`, `pi_4d_lower_dec6`, `pi_4d_upper_dec6`, `pi_cross_lower_exact`, `pi_cross_upper_exact` with `"null"` for `None`).

### Node 2 — Rust S4 (`crates/aod-core/src/manual_dec_ops.rs`)
- 1-to-1 `std`-only, `#![forbid(unsafe_code)]`, zero-float mirror using `crate::ternary::{TritWord, TritRatio}` and arbitrary-precision `isqrt_floor_bigint`/`isqrt_ceil_bigint`, `verify_q4_unit_cube`, `eval_cellular_fold_chain_map` (exact matrix algebra), and `tesseract_4d_orthant_counts` (Route A == Route B).

### Node 3 & Node 4 — Open `G6` (`CELL_MEASURE_SPEC.json`, `aod_cell_measures.py`, `cells_geometry.json`, `tier1_adapters.py`, `registry.py`)
- Update `contracts/scientific/CELL_MEASURE_SPEC.json`: add `"tesseract_4d_ball"` section and update `scope_limits`.
- Update `manual/scripts/aod_cell_measures.py`: add `tesseract_ball_counts`, `independent_tesseract_ball_counts`, `tesseract_ball_tops` + literal `exposed_faces_by_occupancy` verification for $n \in \{1, 2, 4\}$, `validate_tesseract_refinement`, `tesseract_ball_level` (reference-free), `compare_tesseract_reference` ($B_{\mathrm{ext}}$), `shared_coefficient_4d_control`, 3 new hostile 4D negative controls (total 12), and opened `"G6"` report section (`"status": "opened_declared_verification_model"`).
- Regenerate `manual/data/cell_measures/cells_geometry.json` via `--write-data` and verify `--check-data` under normal and `-O` Python.
- Sync `manual/engine/sectors/tier1_adapters.py` (`len(neg_controls) == 12`, `doc["G6"]["status"] == "opened_declared_verification_model"`, `len(doc["G6"]["levels"]) == 6`, return `tesseract_4d_levels: 6`) and `manual/engine/registry.py` (`("negative_controls", 12)`, `("tesseract_4d_levels", 6)`, `"G6_4d_tesseract_to_pi_declared_model_only"`).

### Node 5 — Regenerate CSV & Update `RC-035`
- Regenerate `manual/data/boundary_sadar/cell_measures_staircase_fold_dec.csv` from `build_cell_measures_csv_rows()`.
- Update `RC-035` in `manual/engine/vectors/rational_core.jsonl` (`expected_outcome.exact_value` synced identically with Python S2 and Rust S4).

### Node 6 — Acyclic SHA-256 Contract Chain
1. Compute `D_SPEC = sha256(contracts/scientific/CELL_MEASURE_SPEC.json)` and `D_CSV = sha256(manual/data/boundary_sadar/cell_measures_staircase_fold_dec.csv)`.
2. Update `contracts/scientific/CANONICAL_BINDINGS.json` (`frozen_sha256["manual/data/boundary_sadar/cell_measures_staircase_fold_dec.csv"] = D_CSV`).
3. Compute `D_CANON = sha256(contracts/scientific/CANONICAL_BINDINGS.json)`.
4. Update `scripts/audit_ontology_compaction.py` (`CONTRACT_SHA256["CELL_MEASURE_SPEC.json"] = D_SPEC`, `CONTRACT_SHA256["CANONICAL_BINDINGS.json"] = D_CANON`).
5. Update `typst/representation_change_ledger.json` (`CANONICAL_BINDINGS.json` `new_sha256 = D_CANON`, `cell_measures_staircase_fold_dec.csv` `sha256 = D_CSV`).
6. Update `typst/figure_inventory.json` (`cell-staircase-fold-boundary` `data_sources[0]["sha256"] = D_CSV`).

### Node 7 & Node 8 — Tests & Full Validation
- Update `tests/test_cells.py` (12 negative controls, `G6` opened, literal neighbor oracle $B_{3,\mathrm{stair},4}^+ = 51 \neq 64$, monkeypatch reference-free proof).
- Create zero-bare-assert `tests/test_tesseract_pi.py` (AST 0-assert self-check, hand-derived $n=1,2,4$ oracles, Machin-free $B_{\mathrm{core}}$ check, $B_{3,\mathrm{stair}}$ vs $B_{3,\mathrm{box}}$ falsifiers, fold chain-map commutation + sign-flip negative control, CSV & `RC-035` parity, Python S2 vs Rust S4 parity).
- Add Rust integration test `test_rc035_4d_tesseract_pi_and_cellular_fold_chain_map` in `crates/aod-core/tests/integration_vectors.rs`.
- Execute all 7 validation commands in `00_bundle.toml` inside `/home/antigravity/rpoyau/wt-BND-P2-01` and confirm 100% PASS!

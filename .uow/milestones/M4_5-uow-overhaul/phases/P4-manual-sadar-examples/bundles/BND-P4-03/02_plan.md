# Execution Plan: BND-P4-03 — Manual §1, §11–§15 Vector Alignment, SPARC G0 Exact Update, and Live CSV D.E.C. Tables

## SCOPE GAPS & OUT-OF-SCOPE DEFERRALS
- No missing files block `BND-P4-03`. All edits strictly confined to the 6 `scope.write_set` files:
  `00_scope.typ`, `04_boundary_current_applications.typ`, `05_solar_system_field_tests.typ`, `06_field_dynamics_applications.typ`, `07_galactic_lensing_plan.typ`, `09_prediction_test_fixture_registry.typ`.
- Out-of-scope figures/tables (`field_dynamics_boundary_feynman.typ`, `registry_engine_coverage_atlas.typ`, `wire_moving_boundary_feynman.typ`, `five_boundary_calculation_spine.typ`, `sparc_summary_table.typ`) are deferred to `BND-P5-02`; keep all `#include` statements verbatim.

## 1. Exact Locks (MUST Hold With Zero Drift)
- Global: `main_labels == 455`, `manual_labels == 281`, `manual_mainref_uses == 172`.
- Leave `typst/manual/sections/00_scope.typ` lines 1–273 **byte-for-byte untouched** (locks all 4 owned anchors & 3 SHA-256 locked equations in `OWNERSHIP_AND_FIXTURES.json`).
- Exact per-file counts `(labels, #main*, #aod-cite, #secref, #tabref, #appref, #eqref, #bare-ref)`:
  - `00_scope.typ`: `(19, 0, 0, 2, 0, 0, 4, 0)`
  - `04_boundary_current_applications.typ`: `(14, 5, 0, 1, 0, 0, 0, 0)`
  - `05_solar_system_field_tests.typ`: `(15, 3, 3, 2, 0, 1, 0, 0)`
  - `06_field_dynamics_applications.typ`: `(32, 0, 2, 5, 1, 2, 0, 0)`
  - `07_galactic_lensing_plan.typ`: `(23, 2, 2, 3, 0, 0, 0, 0)`
  - `09_prediction_test_fixture_registry.typ`: `(7, 0, 5, 4, 0, 0, 0, 2)`

## 2. Execution DAG
```text
[Step 1: 00_scope.typ (§1)] ───────────────────────────┐
[Step 2: 04_boundary_current_applications.typ (§11)] ──┤
[Step 3: 05_solar_system_field_tests.typ (§12)] ───────┼──> [Step 7: Pre-Flight] ──> [Step 8: 3 Validation Cmds] ──> [Step 9: 144 ppi PNG QA]
[Step 4: 06_field_dynamics_applications.typ (§13)] ────┤
[Step 5: 07_galactic_lensing_plan.typ (§14)] ──────────┤
[Step 6: 09_prediction_test_fixture_registry.typ (§15)]┘
```

### Step 1 — `typst/manual/sections/00_scope.typ` (§1, lines 274–325 only)
- Update L280 to fifty-three golden vectors: `RC-001` through `RC-045` (45 `rational_core`) and `SD-001` through `SD-008` (8 `symbolic_and_display`).
- Update `<tab:manual-chapter-dec-boundary-index>` with proportional `fr` widths `(15fr, 32fr, 20fr, 33fr)`, `7.8pt`, `raw-wrap`, and 16 ground-truth rows fixing EVERY scrambled vector ID:
  - §4: `RC-025`, `RC-026`, `RC-045` (`dec_chiral_flip_continuous_walk.csv` + `ternary_swar_and_trit_ratio`)
  - §8: `RC-030`, `RC-038` (`dimonhexon_double_slit_ring_paths.csv`, `short_window_rcd_dec_ledger.csv`)
  - §9: `RC-027`--`RC-029`, `SD-007` (`tau_five_boundary_sadar_trace.csv`, `higgs_baryon_overlap_saddle_scan.csv`, `rest_energy_sadar_debris_atlas.csv`)
  - §10: `RC-031`, `RC-039` (`hydrogen_shell_exact_series.csv`, `hydrogen_shell_dec_transitions.csv`)
  - §11: `RC-032` (`scoped_wire_and_moving_boundary_walk.csv`)
  - §12: `RC-040` (`solar_o0_boundary_dec_audit.csv`)
  - §13: `RC-041`, `SD-008` (`run_tumble_q4_dec_walk.csv`, `sparc_pooled_primary_exact.csv`)
  - §14: `RC-020`, `RC-042` (`lensing_ray_chiral_dec_walk.csv`)
  - App. A (`RC-014`, `RC-043`, `cycle_shedding_exact_rational_summary.csv`), App. B (`SD-007`, `rest_energy_sadar_debris_atlas.csv`), App. C (`RC-044`, `coordinate_phase_3d_dec_walk.csv`).

### Step 2 — `typst/manual/sections/04_boundary_current_applications.typ` (§11)
- Align calculation card with `RC-032` (moving-boundary `8 - 3 + 2 = 7` and 4-cut electron-wire walk `4 -> 4 -> 8 -> 13`) while keeping external wire/fluid/plasma apparatus adapter quarantine explicit.
- Replace `RC-030`/`RC-031` on L219 & L252 with `RC-032` (ZERO `RC-030`/`RC-031` remaining).
- Bind `<tab:manual-wire-moving-boundary-dec>` LIVE to `csv("/manual/data/boundary_sadar/scoped_wire_and_moving_boundary_walk.csv")` (5 rows, proportional `fr` columns `(27fr, 7fr, 7fr, 9fr, 14fr, 18fr, 18fr)`, `8.0pt`).

### Step 3 — `typst/manual/sections/05_solar_system_field_tests.typ` (§12)
- Tighten General Mechanics framing around `RC-040` preserving `HOLD_MISSING_NATIVE_SOLAR_PRODUCER` firewall.
- Bind `<tab:manual-solar-dec-boundary-audit>` LIVE to `csv("/manual/data/boundary_sadar/solar_o0_boundary_dec_audit.csv")` (3 rows, proportional `fr` columns `(15fr, 15fr, 16fr, 12fr, 14fr, 8fr, 20fr)`, `7.5pt`, `raw-wrap`).

### Step 4 — `typst/manual/sections/06_field_dynamics_applications.typ` (§13)
- Eliminate ALL occurrences of `64.70291920`, `1523`, `1521`, `66.1613`, `pandas`, `RC-025`, and `RC-032`.
- L436 & L447 & L674: bind declared `G0` SPARC pooled primary exact rational score from `sparc_pooled_primary_exact.csv` (`SD-008`, backed by per-bin oracles `RC-015` and `RC-016`): **`MAPE_U = 26.57055342%`** (`230`-digit numerator over `228`-digit denominator across all `209` positive-$U^{\mathrm{obs}}$ radial bins in exact `TritWord`/`TritRatio` arithmetic, zero free halo fitting). Keep `sparc_declaration_controls.csv` clearly separated without inventing `66.1613%`.
- L510: fix `RC-025` -> `RC-027` with derived 50-microslot $Q_4 \times \mu$ rotor ($50 \times 50 = 2500$ joint microslots, `(650, 703, 1147)/2500` -> `(19/50, 31/50)` on $X_{\mathrm{exo}}$).
- L674: fix `RC-032` -> `SD-008` alongside `RC-041`.
- Bind `<tab:manual-field-dynamics-dec-spine>` LIVE-filtered from `csv("/manual/data/boundary_sadar/run_tumble_q4_dec_walk.csv")` across checkpoints `("0", "2", "3", "5", "7", "8", "16", "20")` (`8` rows, proportional `fr` columns `(6fr, 12fr, 14fr, 11fr, 23fr, 8fr, 8fr, 9fr, 9fr)`, `8.0pt`).

### Step 5 — `typst/manual/sections/07_galactic_lensing_plan.typ` (§14)
- Bind `RC-020` (SWELLS K1 exact $\Delta^{\mathbb{Z}}=(0,4,-4)$, $\sum m = 8$, Tau non-conflation $23/50 - 9/20 = 1/100$) in §14.5 and `RC-042` alongside `RC-020` in §14.8, preserving $L3/K4$ hold at $B_{\mathrm{SWELLS}}$.
- Bind `<tab:manual-lensing-dec-ray-walk>` LIVE to `csv("/manual/data/boundary_sadar/lensing_ray_chiral_dec_walk.csv")` (4 rows, proportional `fr` columns `(11fr, 9fr, 10fr, 10fr, 9fr, 11fr, 9fr, 10fr, 21fr)`, `8.5pt`).

### Step 6 — `typst/manual/sections/09_prediction_test_fixture_registry.typ` (§15)
- Update L71 (`RC-025`–`RC-045`, `SD-007`–`SD-008`, 20 frozen CSVs under `manual/data/boundary_sadar` + `manual/engine/ternary.py`), L192 & L199 ("fifty-three", `RC-001`–`RC-045` + `SD-001`–`SD-008`).
- Replace `<tab:manual-engine-dec-master-registry>` with the exact 22-row, 53-vector master table (`columns: (16fr, 10fr, 40fr, 34fr)`, `7.8pt`, `raw-wrap`) covering EVERY vector `RC-001`–`RC-045` + `SD-001`–`SD-008` (including dedicated `RC-045` `ternary_swar_and_trit_ratio` row and `SD-008` `26.57055342%` `230/228` digits) and ALL 20 frozen CSVs under `manual/data/boundary_sadar/`.

### Steps 7–9 — Static Pre-Flight, Bundle Validation & 144 ppi PNG Visual QA
1. Static check: write_set confinement, exact labels (`110` across 6 files), `00_scope.typ` L1–273 byte-identical, exact `#main*`/`#aod-cite` counts, zero forbidden tokens (`64.70291920`, `1523`, `1521`, `66.1613`, `pandas`, `RC-025`/`RC-032` in §13, `RC-030`/`RC-031` in §11, `fifty-two` in §15), all 4 live CSV bindings present.
2. Run all 3 validation commands in `00_bundle.toml` (`audit_scientific_sources.py`, `build_publication.py --outdir _build/pub --check-registry`, `pytest tests/test_active_scientific_sources.py tests/test_mathematical_bindings.py`).
3. Rasterize every rendered page containing modified tables/prose across §1, §11, §12, §13, §14, and §15 of `_build/pub/manual.pdf` at `144 ppi` PNG into `/tmp/bnd_p4_03_qa/` via `pdftoppm`, visually inspect EVERY PNG via `view_file` (iterating `fr` weights/wrapping until ZERO overflows or collisions), then delete `_build/pub` and `/tmp/bnd_p4_03_qa` so `git status` shows ONLY the 6 `scope.write_set` files.

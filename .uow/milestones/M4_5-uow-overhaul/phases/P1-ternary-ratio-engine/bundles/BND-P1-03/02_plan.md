# Execution Plan: `BND-P1-03` (Live `TritWord`/`ChiralPair4`/`TritRatio` SADAR Kernels, Derived Tau Rotor, $C_6$ Path-Pair Enumerator, & Declared `G0` SPARC `SD-008`)

## Scope Verification & SCOPE GAPS

**SCOPE GAPS: None.** Every required edit lies strictly inside `scope.write_set`:
- `manual/engine/sectors/boundary_sadar.py`
- `crates/aod-core/src/sadar_sim.rs`
- `manual/engine/vectors/rational_core.jsonl`
- `manual/engine/vectors/symbolic_and_display.jsonl`
- `manual/data/boundary_sadar/sparc_pooled_primary_exact.csv`
- `contracts/scientific/CANONICAL_BINDINGS.json`
- `typst/representation_change_ledger.json`
- `typst/figure_inventory.json`
- `crates/aod-core/tests/integration_vectors.rs`
- `tests/test_ternary_engine.py`
- `tests/test_s2_reference_engine.py`
- `tests/test_s4_rust_exact_core.py`

## Policy & Mathematical Invariants

1. Zero floats, zero bare `assert` in `manual/engine/` and Python engine test files, normal == `-O` Python byte-identical.
2. `crates/aod-core/` remains 100% `std`-only, `#![forbid(unsafe_code)]`, zero external crates, zero warnings under `RUSTFLAGS='-D warnings'`, debug == release byte-identical.
3. 2-bit lane preservation (`00=0_D`, `01=+1`, `10=-1`, `11=0_H`), O(1) SWAR negation preserving `00`/`11`, zero forbidden experimental namespace tokens.
4. All 19 non-SPARC `manual/data/boundary_sadar/*.csv` remain byte-for-byte identical while built dynamically from live engine results.
5. Zero hardcoded `cross_map`/`sat_clip` literals in `RC-030`, zero `shed_endo_slots..sensor_missing_slots` input assertions in `RC-027`, zero hardcoded CSV row literals or Tau fraction strings in `build_boundary_sadar_tables`.

## Execution DAG

- **T1 (`manual/engine/sectors/boundary_sadar.py`)**:
  - Helpers: `_trit_pair`, `_pair_slash`, `_signed_rat_str`, `_dion_label`, `_trit_lcm`, `_sum_trit_ratios_balanced` (denominator grouping + pairwise binary tree reduction), `_run_q4_mu_impedance_rotor(rd_lo, rd_hi)` (`n_mu=50`, `cap_4d=200`, `ChiralPair4` + `TritWord`, deriving `(13, 37)` for `9->61` and `(19, 31)` for `61->137`), `_enumerate_c6_two_step_paths(target_k, half_cap=3)`.
  - Upgrade `eval_dec_chiral_flip_walk` (`RC-025`), `eval_dec_two_carrier_chiral_stokes` (`RC-026`), `_run_deterministic_q4_cavity_trace` & `eval_sadar_pp_tau_five_boundary` (`RC-027`, deriving `raw_cuts=28=11+17` via `TritWord.burn_contiguous_dwell(False)` and deriving `13/37`, `19/31` from the 50-microslot rotor, rejecting conflicting optional slot keys), `eval_frg_dimonhexon_double_slit_ring` (`RC-030`, genuine $C_6$ path-pair enumeration via `TritWord` + `burn_contiguous_dwell(False)` + `ChiralPair4` + `TritWord.from_chiral_pairs`), `eval_scoped_wire_and_moving_boundary` (`RC-032`), and `eval_sparc_pooled_primary_exact` (`SD-008`, declared `G0` SPARC law $U_{\mathrm{obs}}=V_{\mathrm{obs}}^2$, $U_{\mathrm{bar}}=V_{\mathrm{gas}}^2 + \frac{1}{2}V_{\mathrm{disk}}^2 + \frac{7}{10}V_{\mathrm{bul}}^2$, $U_{AO}=U_{\mathrm{bar}} + 8r(|V_{\mathrm{gas}}|+|V_{\mathrm{disk}}|+|V_{\mathrm{bul}}|)$ via exact `TritWord` scaling + `_sum_trit_ratios_balanced`, yielding `"26.57055342"` 230/228 digits in sub-second time).
  - Refactor `build_boundary_sadar_tables` to assemble `dec_chiral_flip_continuous_walk.csv`, `tau_five_boundary_sadar_trace.csv`, `scoped_wire_and_moving_boundary_walk.csv`, and `sparc_pooled_primary_exact.csv` dynamically from live engine results (zero hardcoded row dicts or Tau fraction strings).
- **T2 (`crates/aod-core/src/sadar_sim.rs`)**:
  - 1-to-1 `std`-only zero-unsafe Rust mirror of all helpers (`trit_pair_json`, `trit_lcm`, deterministic `sum_trit_ratios_balanced` using `Vec<(TritWord, TritWord)>`, `run_q4_mu_impedance_rotor`, `enumerate_c6_two_step_paths`) and all 6 ops (`RC-025/026/027/030/032`, `SD-008`).
- **T3 (Vectors & SPARC CSV)**:
  - Regenerate `manual/data/boundary_sadar/sparc_pooled_primary_exact.csv` (verify all other 19 CSVs byte-identical).
  - Update `RC-027` inputs in `manual/engine/vectors/rational_core.jsonl` to `{"lead_lag":8,"window_duons":3}`.
  - Update `SD-008` expected `MAPE_U_exact` (230/228 digits), `MAPE_U_8dp = "26.57055342"`, and `max_abs_integer_digits = 230` in `manual/engine/vectors/symbolic_and_display.jsonl`.
- **T4 (Acyclic SHA-256 Contract Chain)**:
  - Compute `H_sparc = sha256(sparc_pooled_primary_exact.csv)`.
  - Update `contracts/scientific/CANONICAL_BINDINGS.json` (`frozen_sha256`), then compute `H_cb = sha256(CANONICAL_BINDINGS.json)`.
  - Update `typst/representation_change_ledger.json` (`H_sparc` + `CANONICAL_BINDINGS.json` `new_sha256 = H_cb`) and `typst/figure_inventory.json` (`field-dynamics-boundary-feynman` `H_sparc`).
- **T5 (Tests)**:
  - Update `crates/aod-core/tests/integration_vectors.rs`, `tests/test_ternary_engine.py`, `tests/test_s2_reference_engine.py`, `tests/test_s4_rust_exact_core.py` (zero bare `assert` in Python) covering Tau rotor, cavity `28=11+17`, conflicting slot rejection, $C_6$ path-pair enumerator + static zero-`cross_map` check, declared `G0` SPARC (`26.57055342`, negative `V_gas`, zero `V_obs` skip), and 20/20 live CSV parity.
- **T6 (Validation)**:
  - Run all 6 validation commands from `00_bundle.toml` inside `/home/antigravity/rpoyau/wt-BND-P1-03`.

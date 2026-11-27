# Execution Plan — BND-P3-02 (`P3-relational-time`)

## SCOPE GAPS & SPEC DISCREPANCIES

1. **`phase.toml` summary vs. `00_bundle.toml` frozen invariant (`manual2/scripts`)**:
   - `manual/scripts/aod_temporal_observation.py` (line 582) is in `scope.read_only` and frozen byte-for-byte (SHA-256 pinned in `manual/data/temporal_observation/temporal.json`, `manual/data/experimental_comparison/experimental_input_comparison.json`, and `manual/scripts/aod_temporal_anchor.py`).
   - **Resolution**: Do **NOT** edit `manual/scripts/aod_temporal_observation.py`. Satisfy `00_bundle.toml` strictly by implementing the self-contained cut-by-cut causal capacity-drop engine (`_step_cut40_causal_intervention` / `step_cut40_causal_intervention`) directly inside `RC-037` in S2 Python and S4 Rust.
2. **Exported static figure PDF outside `write_set`**:
   - Update only `data_sources[0].sha256` (`temporal_si_bridge_dec_ledger.csv`) in `typst/figure_inventory.json`; do not touch `latex/manual/figures/generated/temporal-si-bridge-feynman.pdf`.
   - Updating `typst/figure_inventory.json` changes `main_sources_sha256`, so run `PATH="$HOME/.local/bin:$PATH" python3 -B scripts/build_publication.py --outdir _build/pub` before `--check-registry` to refresh `typst/lib/main_registry.json`.
   - `T3_cs133_bridge` live canonical `TritRatio` formatting emits `1/4596315885` and `13788947655` (reduced form matching `RC-037`). `temporal_si_bridge_feynman.typ` reads `rows.at(0..5)` dynamically by column name and compiles cleanly.
3. **Compatibility guarantees**:
   - Preserve all 14 existing `RC-037` `exact_value` keys and exact values; preserve all 6 existing `RC-037` `inputs` keys (all new inputs optional with canonical defaults).
   - Preserve `RC-037`'s exact 3-component `source_binding` string (keeping total `source_binding` components `== 100` across 53 vectors and row 0 `stage_id == "T1_pair_closures"`).
   - Preserve all 7 CSV column names and rows `0..5` (`T1_pair_closures`..`T6_cut40_intervention`) in `temporal_si_bridge_dec_ledger.csv`.

---

## Policy & Architectural Invariants

- **Python (`manual/engine/sectors/manual_dec_examples.py`, `tests/test_relational_time_engine.py`)**:
  - Zero `float`/`complex` literals or types; zero integer-literal `/` true division; zero negative int powers.
  - Zero bare `assert` (`ast.Assert`) in `manual/engine/` AND `tests/test_relational_time_engine.py`.
  - Zero `Fraction` calls in `eval_dec_temporal_si_bridge_bounds`, all RC-037 helpers, and `build_temporal_si_bridge_csv_rows()` (pure `TritWord`/`TritRatio`; must survive monkeypatching `manual_dec_examples.Fraction` and `fractions.Fraction`).
  - Zero forbidden imports or experimental namespace tokens.
- **Rust (`crates/aod-core/src/manual_dec_ops.rs`, `crates/aod-core/tests/integration_vectors.rs`)**:
  - 100% `std`-only, `#![forbid(unsafe_code)]`, zero floats/unsafe/extern/warnings (`RUSTFLAGS="-D warnings"`).
  - `op_dec_temporal_si_bridge_bounds` and all its helpers use exclusively `crate::ternary::{TritWord, TritRatio}` (plus `BigInt` strictly at `JsonValue::Int`/string-parsing boundaries; zero `BigRat` calls).
- **Frozen Files**: Never modify `manual/scripts/aod_temporal_observation.py`, `manual/scripts/aod_temporal_anchor.py`, `manual/data/temporal_anchor/source/`, `manual/data/temporal_observation/temporal.json`, or `manual/data/experimental_comparison/experimental_input_comparison.json`.

---

## Execution DAG

```text
[Step 1] Python S2 RC-037 Engine & Live CSV Builder (manual/engine/sectors/manual_dec_examples.py)
              │
              ├──────────────────────────────┐
              ▼                              ▼
[Step 2] Rust S4 RC-037 Mirror      [Step 3] Regenerate 9-Row Live CSV
  (crates/aod-core/src/               (manual/data/boundary_sadar/
   manual_dec_ops.rs)                  temporal_si_bridge_dec_ledger.csv)
              │                              │
              ▼                              ▼
[Step 4] Update RC-037 Golden Vector  [Step 5] Acyclic SHA-256 Contract Chain
  (manual/engine/vectors/              5a. contracts/scientific/CANONICAL_BINDINGS.json
   rational_core.jsonl)                5b. scripts/audit_ontology_compaction.py
              │                        5c. typst/representation_change_ledger.json
              │                        5d. typst/figure_inventory.json
              │                        5e. typst/lib/main_registry.json
              ├──────────────────────────────┘
              ▼
[Step 6] Dual Test Suites (tests/test_relational_time_engine.py + crates/aod-core/tests/integration_vectors.rs)
              │
              ▼
[Step 7] Full Validation Gate (all 7 commands in 00_bundle.toml) + clean _build/
```

---

## Detailed Specification by Deliverable

### Step 1 & Step 2 — RC-037 Engine Upgrade (Python S2 + Rust S4 Parity)

#### 1.1 Exact Input JSON Schema

Required fields:
- `compared_cuts`: `list[int]` (exact ints rejecting `bool`, `len >= 2`, strictly increasing, `>= 2` cuts in `(u, v]`)
- `ref_cuts`: `list[int]` (same rules)
- `f_cs_hz`: exact int `> 0`
- `cal_ref`: exact int `> 0`
- `field_a`: `[na_cal, na_val]`, exact ints, `na_cal > 0`, `na_val >= 0`
- `field_b`: `[nb_cal, nb_val]`, exact ints, `nb_cal > 0`, `nb_val >= 0`

Optional fields (canonical defaults):
- `window`: `[int, int]`, `u < v`, default `[0, 30]`
- `compared_bias`: `[str, str]` or `[int, int]` (`den > 0`), default `["1", "4"]`
- `ref_bias`: `[str, str]` or `[int, int]` (`den > 0`), default `["-1", "4"]`
- `rcd_rd`: exact int `>= 1`, default `3`
- `rcd_c_reflections`: list of exact ints `>= 0`, default `[1, 1]`
- `rcd_r_reflections`: list of exact ints `>= 0`, default `[2, 2]`
- `a_c`: rational pair (`sign() > 0`), default `["1", "1"]`
- `a_r`: rational pair (`sign() > 0`), default `["1", "1"]`
- `causal_window`: `[c_lo, c_hi]`, `c_lo < c_hi`, default `[0, 100]`
- `causal_outer_plus`: non-empty strictly increasing exact ints, default `[16, 32, 48, 64, 80, 96]`
- `causal_outer_minus`: non-empty strictly increasing exact ints with `>= 1` cut in `(c_lo, c_hi]`, default `[15, 30, 45, 60, 75]`
- `intervention_cut`: exact int with `c_lo < intervention_cut < c_hi`, default `40`
- `observed_advance`: optional object with keys subset of `{"compared","reference","split_left","split_right","signed_control"}`; each value has `{"winding": int >= 0, "phase_start": pair in [0,1), "phase_end": pair in [0,1)}`; defaults:
  - `compared`: `winding=4, phase_start=["2","3"], phase_end=["1","6"]` -> `7/2`
  - `reference`: `winding=8, phase_start=["1","4"], phase_end=["3","4"]` -> `17/2`
  - `split_left`: `winding=2, phase_start=["2","3"], phase_end=["5","6"]` -> `13/6`
  - `split_right`: `winding=2, phase_start=["5","6"], phase_end=["1","6"]` -> `4/3`
  - `signed_control`: `winding=0, phase_start=["3","4"], phase_end=["1","4"]` -> `-1/2`

Strict rational pair parser (`_parse_trit_pair` / `parse_trit_pair`): 2-element list/array of either two canonical decimal integer strings (`"0"` or optional `"-"` + `[1-9][0-9]*`) or two exact integers (rejecting `bool`/mixed types); parse directly into `TritWord`, require `den > 0`, return `TritRatio`.

#### 1.2 Half-Open `(u, v]` Filtering & Anchor Exclusion
- Require `len(cuts) >= 2`, strict monotonicity `cuts[i] < cuts[i+1]`, `u < v`.
- `in_window_all = [k for k in cuts if u < k <= v]`; require `len(in_window_all) >= 2`.
- Exclude initial anchor `cuts[0]`: count `k in cuts[1:]` with `u < k <= v` using `TritWord` increments; verify `tw_count.sign() > 0`.

#### 1.3 Cadence Ratios, Biases, Directional RCD, Stipulated SI Gains & Cross-Field Transfer
All strictly in `TritWord`/`TritRatio`:
- `biz_c_over_r = TritRatio(tw_nc, tw_nr)` (`3/2`), `biz_r_over_c = TritRatio(tw_nr, tw_nc)` (`2/3`), product `== 1`.
- `lag_forward = TritRatio(tw_nc.sub(tw_nr), TritWord.ONE).add(compared_bias.sub(ref_bias))` (`3/2`), `lag_reverse = lag_forward.neg()` (`-3/2`).
- `rcd_c_given_r = rcd_rd + sum(rcd_c_reflections)` (`5`), `rcd_r_given_c = rcd_rd + sum(rcd_r_reflections)` (`7`).
- `t_sec = tr_nr.mul(a_r).div(tr_fcs)` (`1/4596315885`), `nu_bar = tr_nc.mul(a_c).div(t_sec)` (`13788947655/1`).
- `pred_a = (cal_ref / na_cal) * na_val` (`768/29`), `rel_a = (pred_a - cal_ref) / cal_ref` (`-5/29`).
- `pred_b = (cal_ref / nb_cal) * nb_val` (`3264/151`), `rel_b = (pred_b - cal_ref) / cal_ref` (`-49/151`).

#### 1.4 Cut-by-Cut Causal Capacity-Drop Simulation (`_step_cut40_causal_intervention` / `step_cut40_causal_intervention`)
- Step integer cuts `k = c_lo ..= c_hi` with `capacity_threshold = 2`, `effective_capacity = 2`, `outer_plus_retained = True`, `retention_status = "retained"`, `queued_capacity_drop = False`, `tw_plus = 0`, `tw_minus = 0`:
  1. Consume `queued_capacity_drop` from `k - 1`: set `effective_capacity = 1`, `queued_capacity_drop = False`; since `1 < 2`, if `disconnect_feedback` keep `outer_plus_retained = True` & `retention_status = "retained_feedback_disconnected_mutation"`, else set `outer_plus_retained = False` & `retention_status = "lost_by_declared_capacity_rule"`.
  2. If `k > c_lo`: increment `tw_plus` if `k in outer_plus_set and outer_plus_retained`; increment `tw_minus` if `k in outer_minus_set`.
  3. Set `intervention_queued_here = (apply_intervention and k == intervention_cut)`; if true, set `queued_capacity_drop = True` (strictly 1-cut response lag to `k + 1`).
  4. Record `CutRecord(cut, effective_capacity, outer_plus_retained, retention_status, count_plus, count_minus, intervention_queued)`.
- Replay validator (`_validate_causal_capacity_trace`) re-runs honest trace (`disconnect_feedback=False`), checks capacity-loss invariant & full trace equality; raises `ValueError` / `CoreError::ValueError` on mismatch.
- Run `baseline` (`apply=False`), `intervention` (`apply=True, disconnect=False`), `disconnected` (`apply=True, disconnect=True`). Validate `baseline` and `intervention`; confirm `disconnected` fails replay validation (`replay_validation_rejected == True`) and collapses back to `baseline.counts`/`baseline.ratio`.
- Dynamically compute `common_prefix_through` (largest `k` with `baseline[j] == intervention[j] == disconnected[j]` for all `j <= k`, default `39`) and `first_divergent_cut` (smallest `k` where observable tuple `(effective_capacity, outer_plus_retained, retention_status, count_plus, count_minus)` differs between `baseline` and `intervention`, verifying equality for all `k <= intervention_cut`, default `41`).

#### 1.5 Observed-Advance Endpoint Law $A(W) = C(W) + \phi_1 - \phi_0$
- Validate `winding >= 0`, `0 <= phase_start, phase_end < 1`, `A_r > 0`, split continuity (`split_left.phase_start == compared.phase_start`, `split_left.phase_end == split_right.phase_start`, `split_right.phase_end == compared.phase_end`, `split_left.winding + split_right.winding == compared.winding`), and `A_L + A_R == A_c`.
- Outputs: `observed_advance_compared = 7/2`, `observed_advance_ref = 17/2`, `observed_advance_ratio = 7/17`, `observed_advance_split_sum = 7/2`, `observed_advance_clipped = 0/1` (`max(0, A_signed)`), `observed_advance_signed = -1/2`.

#### 1.6 Complete Output JSON Schema (28 Keys — Byte-Identical S2 & S4)
All 14 legacy keys (`delta_bip_compared`, `delta_bip_ref`, `biz_c_over_r`, `biz_r_over_c`, `lag_forward`, `lag_reverse`, `T_seconds`, `nu_bar_hz`, `transfer_A_pred`, `transfer_A_rel_resid`, `transfer_B_pred`, `transfer_B_rel_resid`, `intervention_ratio_before`, `intervention_ratio_after`) + 14 new keys (`window`, `rcd_c_given_r`, `rcd_r_given_c`, `intervention_common_prefix_through`, `intervention_first_divergent_cut`, `intervention_counts_before`, `intervention_counts_after`, `intervention_disconnect_rejected`, `observed_advance_compared`, `observed_advance_ref`, `observed_advance_ratio`, `observed_advance_split_sum`, `observed_advance_clipped`, `observed_advance_signed`).

---

### Step 3 — Live 9-Row CSV Generation (`build_temporal_si_bridge_csv_rows`)
- Calls `eval_dec_temporal_si_bridge_bounds(cfg)` live (zero `Fraction`, zero hardcoded computed numeric strings).
- Preserves 7-column header `stage_id,boundary_B,lineage_pair,delta_bip,exact_quantity,reverse_or_resid,status_gate` and rows `0..5` (`T1_pair_closures`..`T6_cut40_intervention`), plus appends live rows:
  - Row 6: `T7_directional_rcd` (`B_rcd(RD=3)`, `c_refs(1,1) vs r_refs(2,2)`, `RCD_c|r=5,RCD_r|c=7`, `5`, `7`, `AUTHENTICATED_DIRECTIONAL_RCD`)
  - Row 7: `T8_observed_advance_si` (`B_phase(A=C+phi1-phi0)`, `A_c=7/2 vs A_r=17/2`, `split=7/2;clip=0`, `7/17`, `-1/2`, `EXACT_OBSERVED_ADVANCE_ADDITIVE`)
  - Row 8: `T9_causal_disconnect_control` (`B_causal_hostile(prefix<=39)`, `disconnect_feedback_mutation`, `(6,5)->(6,5)`, `6/5`, `REJECTED_REPLAY_VALIDATION`, `HOSTILE_DISCONNECT_REJECTED`)
- Regenerate `manual/data/boundary_sadar/temporal_si_bridge_dec_ledger.csv` via `_rows_to_csv_text(build_temporal_si_bridge_csv_rows())`.

### Step 4 — Update `RC-037` in `manual/engine/vectors/rational_core.jsonl`
- Update line 37 `expected_outcome.exact_value` to all 28 keys (preserving exact `source_binding` string and total 100 components across 53 vectors) and update `overflow_note`.

### Step 5 — Acyclic SHA-256 Contract Chain
1. Compute `H_csv` of `manual/data/boundary_sadar/temporal_si_bridge_dec_ledger.csv`.
2. Update `contracts/scientific/CANONICAL_BINDINGS.json` (`frozen_sha256["manual/data/boundary_sadar/temporal_si_bridge_dec_ledger.csv"] = H_csv`).
3. Compute `H_cb` of `contracts/scientific/CANONICAL_BINDINGS.json`.
4. Update `scripts/audit_ontology_compaction.py` (`CONTRACT_SHA256["CANONICAL_BINDINGS.json"] = H_cb`), `typst/representation_change_ledger.json` (`CANONICAL_BINDINGS.json` `new_sha256 = H_cb` & `temporal_si_bridge_dec_ledger.csv` `sha256 = H_csv`), and `typst/figure_inventory.json` (`temporal-si-bridge-feynman` `data_sources[0].sha256 = H_csv`).
5. Run `PATH="$HOME/.local/bin:$PATH" python3 -B scripts/build_publication.py --outdir _build/pub` to refresh `typst/lib/main_registry.json`, then verify `--check-registry` passes.

### Step 6 & Step 7 — Dual Tests & Full Validation Gate
- Create zero-bare-assert `tests/test_relational_time_engine.py` covering all 8 test groups (golden/types, poisoned-`Fraction` proof, half-open window & anchor exclusion, biases/RCD/gains, dynamic causal intervention & hostile disconnect, observed-advance additivity/signed/clipped, live CSV & static AST hygiene, and S2 vs S4 exact parity via `aod-core --eval-op dec_temporal_si_bridge_bounds --input-json ...`).
- Add `test_rc037_relational_time_trit_ratio_and_causal_intervention` in `crates/aod-core/tests/integration_vectors.rs` (including static check for zero `BigRat` and zero hardcoded `(6,5)`/`(2,5)` in `op_dec_temporal_si_bridge_bounds`).
- Run all 7 validation commands in `00_bundle.toml`, then clean `_build/` before returning.

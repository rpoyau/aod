# Execution Plan — `BND-P4-04` (`P4-manual-sadar-examples`)

**Bundle ID**: `BND-P4-04`
**Base Commit**: `3f12bf47cfa388f7914926916005f98d191e7705` (`uow/BND-P4-03`)
**Scope**: Resolve App. C `beta_a = 5` MSB-$x$ vs stale `beta_a = 4` LSB-$x$ mismatch in `RC-044` across Python S2, Rust S4, `rational_core.jsonl`, `coordinate_phase_3d_dec_walk.csv`, contracts, and Manual App. C prose; refactor Manual App. A (exact rational `RC-014`/`RC-043` framing & live CSV), App. B (`SD-007`/`SD-004`/`SD-005` & §9 `RC-027..RC-029` quarantine citations), and App. C (live CSV & `RC-012`/`RC-013`/`RC-044` alignment); visually verify App. A–C rendered pages at 144 ppi PNG.

---

## 1. Exact File-by-File Edit Plan (`scope.write_set` only — 11 files)

### 1.1 `manual/engine/sectors/manual_dec_examples.py` (L2736–2836 only)
- **Do NOT modify `_octant_3d` (L2413)** — it is used by `RC-041` (run-tumble LSB-$x$).
- Add private helper `_octant_3d_trit(dx: TritWord, dy: TritWord, dz: TritWord, bit_order: str) -> int` in the `RC-044` section:
  - Uses `dx.sign() < 0`, `dy.sign() < 0`, `dz.sign() < 0`.
  - `"msb_x"`: `(4 if dx.sign() < 0 else 0) | (2 if dy.sign() < 0 else 0) | (1 if dz.sign() < 0 else 0)` — matches `RC-012` (`manual/data/brownian/octant_delta3.csv`).
  - `"lsb_x"`: `(1 if dx.sign() < 0 else 0) | (2 if dy.sign() < 0 else 0) | (4 if dz.sign() < 0 else 0)` — matches `RC-013` (run-tumble contrast).
- Upgrade `eval_dec_coordinate_phase_3d_walk(inputs: dict[str, object]) -> dict[str, object]`:
  - **Strict S2/S4 parity input validation**:
    - Missing `"points"` -> `ValueError`; present non-`list` `"points"` -> `TypeError`; `len(points) < 2` -> `ValueError`.
    - Missing `"beta_a"` -> `ValueError`; `beta_a = require_exact_int(inputs["beta_a"], name="beta_a")` (`TypeError` on `None`/`bool`/`float`/`str`); `beta_a <= 0` -> `ValueError`.
    - Optional `"octant_bit_order"` via sentinel `_MISSING_OPT`: absent -> `"msb_x"`; present non-`str` (including `None`, `int`, `bool`, `list`, `dict`) -> `TypeError`; present `str` not in `{"msb_x", "lsb_x"}` -> `ValueError`.
    - Each `points[idx]`: non-`list` -> `TypeError`; `len != 3` -> `ValueError`; each coordinate parsed via `require_exact_int` (`TypeError` on non-exact-int) and converted immediately to `TritWord.from_int(...)`.
  - **Pure `TritWord` / `TritRatio` arithmetic (ZERO `Fraction`, ZERO floats, ZERO bare `assert`)**:
    - For each lag-1 step `i = 0..n_steps-1`:
      - `dx = x1 - x0`, `dy = y1 - y0`, `dz = z1 - z0` (`TritWord`).
      - `dx2 = dx * dx`, `dy2 = dy * dy`, `dz2 = dz * dz`, `q_i = dx2 + dy2 + dz2` (`TritWord`).
      - `sum_dx2 += dx2`, `sum_dy2 += dy2`, `sum_dz2 += dz2`, `sum_q += q_i` (`TritWord`).
      - `th = q_i.to_int() % beta_a` (`phase_counts[th] += 1`).
      - `oc = _octant_3d_trit(dx, dy, dz, bit_order)` (`octant_counts[oc] += 1`).
    - Guard stationary walk: if `sum_q.sign() <= 0`, raise `ValueError("sum_Q must be positive for axis ratios R_x, R_y, R_z")`.
    - Integer-balanced comparators `IntBalance(n_steps, 8)` and `IntBalance(n_steps, beta_a)` computed with `TritWord`:
      - `phase_DeltaZ = [comp_th[th] - phase_counts[th]]`, verify `sum == 0`, `phase_delta3_M = sum(abs(x))`.
      - `octant_DeltaZ = [comp_oct[q] - octant_counts[q]]`, verify `sum == 0`, `octant_delta3_M = sum(abs(x))`.
    - Exact `TritRatio` outputs via `_trit_pair(TritRatio(...))`:
      - `R_Q_ratio = _trit_pair(TritRatio(sum_q, TritWord.from_int(n_steps)))`
      - `R_x_ratio = _trit_pair(TritRatio(sum_dx2, sum_q))`
      - `R_y_ratio = _trit_pair(TritRatio(sum_dy2, sum_q))`
      - `R_z_ratio = _trit_pair(TritRatio(sum_dz2, sum_q))`
    - Return exact 14-key dict:
      `step_count`, `Q_values`, `sum_Q`, `R_Q_ratio`, `R_x_ratio`, `R_y_ratio`, `R_z_ratio`, `phase_counts`, `phase_DeltaZ`, `phase_delta3_M`, `octant_bit_order`, `octant_counts`, `octant_DeltaZ`, `octant_delta3_M`.
    - Call `require_no_floats(out)` before returning.
- Upgrade `build_coordinate_phase_3d_csv_rows() -> list[dict[str, str]]`:
  - Evaluate the canonical 9-point `Z^3` track through `eval_dec_coordinate_phase_3d_walk({"points": pts_list, "beta_a": 5, "octant_bit_order": "msb_x"})` AND contrast `"lsb_x"` to cross-verify every step live (`Q_values`, `sum_Q == 20`, `phase_delta3_M == 10`, `octant_delta3_M == 10`).
  - Emit exact 8 rows with columns:
    `step_i,from_xyz,to_xyz,delta_xyz,Q_lag1,theta_mod5,octant_msb_x,octant_lsb_x`.
  - Step-4 `(-1,1,1)` yields `octant_msb_x=4, octant_lsb_x=1`; Step-6 `(1,-1,1)` yields `octant_msb_x=2, octant_lsb_x=2`; all other steps yield `0, 0`.

### 1.2 `crates/aod-core/src/manual_dec_ops.rs` (`// RC-044:` section L2731–EOF only)
- **Do NOT modify `octant_3d` (L253)** — it is used by `RC-041`.
- Add private `fn octant_3d_trit(dx: &TritWord, dy: &TritWord, dz: &TritWord, bit_order: &str) -> usize` in the `RC-044` section.
- Upgrade `pub fn op_dec_coordinate_phase_3d_walk(inputs: &BTreeMap<String, JsonValue>) -> Result<JsonValue, CoreError>`:
  - **ZERO `BigRat` usage** (100% `TritWord` & `TritRatio`, serialized via `trit_pair_json(&TritRatio)`).
  - Exact input error-class parity with Python S2:
    - `require_array(inputs, "points")?` (`ValueError` on missing, `TypeError` on non-array); `len < 2` -> `ValueError`.
    - `require_i64(inputs, "beta_a")?` (`ValueError` on missing, `TypeError` on non-int/null/bool); `beta_a <= 0` -> `ValueError`.
    - Optional `"octant_bit_order"`:
      - `None` (key absent) -> `"msb_x"`.
      - `Some(JsonValue::Str(s))` -> accept `"msb_x"` or `"lsb_x"`, else `Err(CoreError::ValueError(...))`.
      - `Some(other)` (including `JsonValue::Null`) -> `Err(CoreError::TypeError(...))`.
    - Each `points[idx]`: non-array -> `Err(CoreError::TypeError(...))`; `len != 3` -> `Err(CoreError::ValueError(...))`; each element parsed via `require_json_int` -> `TritWord::from_bigint(...)`.
  - Compute `dx, dy, dz`, `dx^2, dy^2, dz^2`, `q_i`, `sum_q`, `sum_dx2`, `sum_dy2`, `sum_dz2` in `TritWord`.
  - Stationary guard: if `sum_q.sign() <= 0`, return `Err(CoreError::ValueError("sum_Q must be positive for axis ratios R_x, R_y, R_z".to_string()))`.
  - Compute `phase_counts`, `phase_DeltaZ`, `phase_delta3_M`, `octant_counts`, `octant_DeltaZ`, `octant_delta3_M` and `R_Q_ratio`, `R_x_ratio`, `R_y_ratio`, `R_z_ratio` via `TritRatio::new(...)` + `trit_pair_json(...)`.
  - Emit exact 14-key JSON object matching Python S2 byte-for-byte.

### 1.3 `manual/engine/vectors/rational_core.jsonl` (Line 44 `RC-044` only)
- Update `RC-044`:
  - `inputs`: `points` (same 9 points), `"beta_a": 5`, `"octant_bit_order": "msb_x"`.
  - `expected_outcome.exact_value` (14 keys):
    - `"step_count": 8`, `"Q_values": [2, 2, 2, 3, 3, 3, 2, 3]`, `"sum_Q": 20`
    - `"R_Q_ratio": ["5", "2"]`, `"R_x_ratio": ["2", "5"]`, `"R_y_ratio": ["7", "20"]`, `"R_z_ratio": ["1", "4"]`
    - `"phase_counts": [0, 0, 4, 4, 0]`, `"phase_DeltaZ": [2, 2, -2, -3, 1]`, `"phase_delta3_M": 10`
    - `"octant_bit_order": "msb_x"`, `"octant_counts": [6, 0, 1, 0, 1, 0, 0, 0]`, `"octant_DeltaZ": [-5, 1, 0, 1, 0, 1, 1, 1]`, `"octant_delta3_M": 10`
  - Preserve `source_binding` (`3` semicolon-separated components so total across all `53` vectors remains `100`).

### 1.4 `manual/data/boundary_sadar/coordinate_phase_3d_dec_walk.csv` & Acyclic SHA-256 Chain
- Regenerate `manual/data/boundary_sadar/coordinate_phase_3d_dec_walk.csv` from `build_coordinate_phase_3d_csv_rows()` (8 rows, header `step_i,from_xyz,to_xyz,delta_xyz,Q_lag1,theta_mod5,octant_msb_x,octant_lsb_x`).
- Compute new SHA-256 of `coordinate_phase_3d_dec_walk.csv` -> update `contracts/scientific/CANONICAL_BINDINGS.json` (`frozen_sha256["manual/data/boundary_sadar/coordinate_phase_3d_dec_walk.csv"]`, preserving `192` total entries).
- Compute new SHA-256 of `contracts/scientific/CANONICAL_BINDINGS.json` -> update `scripts/audit_ontology_compaction.py` (`EXPECTED_CONTRACT_SHA256["CANONICAL_BINDINGS.json"]`).
- Update `typst/representation_change_ledger.json` for `coordinate_phase_3d_dec_walk.csv` (and `CANONICAL_BINDINGS.json` if pinned in ledger).

### 1.5 `crates/aod-core/tests/integration_vectors.rs`
- Add `test_rc044_coordinate_phase_3d_walk_trit_ratio_and_bit_order_parity`:
  1. Evaluates canonical 9-point track with omitted `octant_bit_order` and explicit `"msb_x"`, proving exact equality with `RC-012` (`Q_values`, `phase_DeltaZ`, `octant_DeltaZ`, `phase_delta3_M == 10`, `octant_delta3_M == 10`, `R_Q == 5/2`, `R_x == 2/5`, `R_y == 7/20`, `R_z == 1/4`).
  2. Evaluates explicit `"lsb_x"` contrast (`octant_counts == [6, 1, 1, 0, 0, 0, 0, 0]`, `octant_DeltaZ == [-5, 0, 0, 1, 1, 1, 1, 1]`, `octant_delta3_M == 10`), matching `RC-013` LSB-$x$ rule.
  3. Verifies `TypeError` on explicit `JsonValue::Null`/int/bool `octant_bit_order`, non-array `points`, non-array point element, non-int coordinate/beta_a; verifies `ValueError` on unknown `octant_bit_order` string, missing required keys, `len(points) < 2`, wrong point length, `beta_a <= 0`, and stationary walk (`sum_Q == 0`).
  4. Static source-text check on `crates/aod-core/src/manual_dec_ops.rs` from `fn op_dec_coordinate_phase_3d_walk` to EOF confirming `TritWord` & `TritRatio` usage and **zero** `BigRat` / `pair_json` tokens.

### 1.6 Manual Appendices A, B, and C (Typst Refactoring)
- **`typst/manual/appendices/A_simulation_fixtures_and_tau_prediction_context.typ`**:
  - Preserve L1–109 verbatim (protects all 3 owned anchors in `OWNERSHIP_AND_FIXTURES.json`: `<app:cycle-shedding-demo-demonstration>`, `<fig:v39-cycle-shedding-simulation>`, `<app:rd-tests:support-reductions>`, plus all `#main*` citations and `test_typst_parity.py:315`).
  - Refactor §`manual:simfix:exact-rational-dec` (L110–143):
    - Bind BOTH exact rational cycle-shedding vectors `#raw("RC-014")` (single-step algebraic recurrence oracle) and `#raw("RC-043")` (four-tick chained exact rational summary & CSV), explicitly contrasting exact rational arithmetic against the rounded six-decimal display of the 90-tick summary table above (`O_t + R_t = X_t` identically at every tick; total shed `6447/15625`, outward `199857/781250 = 31/50`, local `122493/781250 = 19/50`).
    - Replace hardcoded table rows in `<tab:manual-app-a-exact-shedding-dec>` with live `csv("/manual/data/boundary_sadar/cycle_shedding_exact_rational_summary.csv")` rendering (`text(size: 8pt)` with proportional `fr`/clean column layout so zero horizontal clipping occurs).
- **`typst/manual/appendices/B_quarantined_external_comparison.typ`**:
  - Preserve L1–214 verbatim (all labels, `#main*`, `#aod-cite`, tables, and F1–F5 audits).
  - Refactor §`manual:qext:dec-quarantine-firewall` (L216–255):
    - Eliminate the misplaced `#raw("RC-025")` citations on L218 and L252 (since `RC-025` is chiral Stokes disoma exchange, NOT rest-energy/external comparison!).
    - Bind cleanly to `#raw("SD-007")` (9-carrier `Qext` exact rational target rates and round-trip `eta_ext` cancellation), `#raw("SD-004")` / `#raw("SD-005")` (tau `Qext` target normalization & round-trip identity), and §9 rest-energy native vectors `#raw("RC-027")` (Tau 50-microslot rotor), `#raw("RC-028")` (debris/Higgs saddle), and `#raw("RC-029")` (10-carrier atlas).
    - Keep `<fig:manual-qext-quarantine-firewall>` and `<tab:manual-qext-precision-ledger>` intact with clean wrapping and zero overflow.
- **`typst/manual/appendices/C_3d_coordinate_phase_cycle_delta3_fixture.typ`**:
  - Preserve L1–208 verbatim (all labels, equations, `aod_3d_coordinate_phase_delta3.py` target, and `test_manual_brownian_phase_delta3.py` / `test_manual_run_tumble_tracer_current.py` invariants).
  - Refactor §`manual:app-c:dec-lag1-walk` (L211–248):
    - Eliminate ALL stale `Q mod 4`, `beta_a = 4`, and `theta_mod4` references.
    - Declare the five-boundary stack with `$B_(Q mod 5)$`:
      `B_(lattice) -> B_(Delta x) -> B_(Q mod 5) -> B_(delta_3) -> B_(ext)`.
    - State exact `beta_a = 5` alignment between `#raw("RC-044")` and Brownian canonical vector `#raw("RC-012")` (`manual/data/brownian/octant_delta3.csv`): `Q_values = [2,2,2,3,3,3,2,3]`, `sum_Q = 20`, `R_Q = 5/2`, axis ratios `R_x = 2/5, R_y = 7/20, R_z = 1/4`, `phase_counts = [0,0,4,4,0]`, `phase_DeltaZ = [2,2,-2,-3,1]`, `M_(delta_3,theta) = 10`; and explicitly contrast MSB-$x$ (`4(a<0)+2(b<0)+(c<0)`, `octant_counts = [6,0,1,0,1,0,0,0]`, `octant_DeltaZ = [-5,1,0,1,0,1,1,1]`, `M_(delta_3,oct) = 10`, matching `#raw("RC-012")`) against run-tumble LSB-$x$ (`(a<0)+2(b<0)+4(c<0)`, `octant_counts = [6,1,1,0,0,0,0,0]`, step 4 `(-1,1,1) -> 1` vs `4`, matching `#raw("RC-013")`), plus endpoint chord squared norm `6^2 + 5^2 + 5^2 = 86`.
    - Replace hardcoded rows in `<tab:manual-app-c-3d-dec-ledger>` with live `csv("/manual/data/boundary_sadar/coordinate_phase_3d_dec_walk.csv")` displaying all 8 columns (`Step i`, `From`, `To`, `Delta`, `Q_lag1`, `theta = Q mod 5`, `Octant (MSB-x)`, `Octant (LSB-x)`).

---

## 2. Verification & Visual QA Protocol
1. Run all 6 validation commands in `00_bundle.toml` (`audit_scientific_sources.py`, `build_publication.py --check-registry`, `cargo test` with `RUSTFLAGS="-D warnings"`, S2 normal vs `-O` `cmp`, S4 debug vs release `cmp`, targeted `pytest`).
2. Render the exact pages of `_build/pub/manual.pdf` covering Appendices A, B, and C at `144 ppi` via `pdftoppm -png -r 144` into `/tmp/p404_png/` and visually inspect EVERY rendered Appendix A–C page with `view_file` confirming zero overlaps, zero clipping, and zero margin overflows.
3. Verify zero untracked build artifacts left outside `_build/` before handing back for Role 4 Adversarial Review and Role 5 Validation.

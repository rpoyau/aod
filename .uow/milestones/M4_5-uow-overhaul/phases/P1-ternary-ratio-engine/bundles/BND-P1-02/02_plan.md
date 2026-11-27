# Execution Plan: `BND-P1-02` — Std-Only Rust Ternary-on-Binary Core & Cross-Language Golden Vector `RC-045`

## Execution DAG

```text
S1: crates/aod-core/src/ternary.rs  (std-only packed multi-u64 SWAR + TritRatio + unit tests)
 ├──▶ S2: crates/aod-core/src/lib.rs (declare pub mod ternary)
 │     └──▶ S3: crates/aod-core/src/ops.rs (op_ternary_swar_and_trit_ratio + eval_operation dispatch)
 └──▶ S4: manual/engine/sectors/boundary_sadar.py (eval_ternary_swar_and_trit_ratio)
       └──▶ S5: manual/engine/vectors.py (dispatch + 44->45 / 52->53 count pins)
             └──▶ S6: manual/engine/vectors/rational_core.jsonl (append RC-045)
                   └──▶ S7: Count pins & parity tests across:
                            - crates/aod-core/src/vectors.rs
                            - crates/aod-core/tests/integration_vectors.rs
                            - tests/test_s2_reference_engine.py
                            - tests/test_s4_rust_exact_core.py
                            - tests/test_ternary_engine.py
```

All 11 target files are in `scope.write_set`. Zero files outside `scope.write_set` are modified.

---

## Policy & Invariant Constraints

1. **Zero floats**: No float types, decimal literals, or implicit float coercions anywhere in `crates/aod-core/` or `manual/engine/` (including comments/docstrings).
2. **Zero bare `assert` in Python**: `manual/engine/` and `tests/test_ternary_engine.py` (plus `test_s2_reference_engine.py` / `test_s4_rust_exact_core.py`) must use explicit `require`/`require_type`/`require_exact_int` or `_check(...)` helpers so normal Python and `python3 -O` execute identical checks and byte-identical reports.
3. **Std-only zero-unsafe Rust**: `crates/aod-core/` remains `#![forbid(unsafe_code)]`, 100% `std`-only, zero external crates (`Cargo.lock` untouched, `cargo_lock_packages == 1`), zero `extern`, zero compiler warnings under `RUSTFLAGS='-D warnings'`, and byte-identical debug vs release CLI reports.
4. **Zero forbidden experimental namespace tokens** across all edited/created files.
5. **Canonical 2-bit lane ontology**: `0b00` (`0_D` dwell), `0b01` (`+1` alpha), `0b10` (`-1` omega), `0b11` (`0_H` structural hinge / saturation / carry-barrier, preserved by O(1) SWAR negation).
6. **`TritRatio` backing invariant**: `TritRatio` stores `(TritWord, TritWord)` plus `(LaneMask, LaneMask)` hinge metadata; never wraps `BigRat` (Rust) or `Fraction` (Python) as backing storage.

---

## Step S1: Implement `crates/aod-core/src/ternary.rs`

- Constants: `TRIT_DWELL = 0b00`, `TRIT_ALPHA = 0b01`, `TRIT_OMEGA = 0b10`, `TRIT_HINGE = 0b11`, `TRIT_LANE_MASK = 0b11`, `TRIT_LANE_BITS = 2`, `LANES_PER_LIMB = 32`, `MASK_01 = 0x5555_5555_5555_5555u64`, `MASK_10 = 0xAAAA_AAAA_AAAA_AAAAu64`, `MASK_11 = 0xFFFF_FFFF_FFFF_FFFFu64`.
- Lane primitives: `validate_trit_lane`, `trit_lane_to_signed`, `signed_to_trit_lane`, `negate_trit_lane`, `trit_lane_symbol`, `symbol_to_trit_lane`.
- Per-limb O(1) SWAR primitives: `swar_negate_limb` (`((limb & MASK_01) << 1) | ((limb >> 1) & MASK_01)`), `swar_hinge_mask_limb` (`(limb & (limb >> 1)) & MASK_01`), `swar_alpha_mask_limb`, `swar_omega_mask_limb`, `swar_polar_mask_limb`, `swar_dwell_mask_limb`, `swar_double_lane_mask_limb`.
- Arbitrary-width `LaneMask` (`limbs: Vec<u64>`, 01-aligned) + `swar_*_bigint` helpers.
- Fast `BigInt` <-> `Vec<u64>` & balanced base-3 `TritWord::from_bigint` / `to_bigint` using `RADIX16 = 3^16`, `RADIX32 = 3^32` (zero overflow, fast `BigInt::div_rem_euclid` with 1-limb u32 divisor).
- Multi-limb pure-SWAR bit-plane arithmetic: `swar_csa3_limb_unshifted`, `swar_csa3_planes`, `swar_add_planes`, `swar_mul_csa_leaf`, `swar_mul_planes` (CSA leaf `<= 64` trits + Karatsuba `> 64` trits), `swar_divmod_pos_planes`, `swar_bal_rem_pos_planes`, `swar_gcd_planes` (O(1) factor-of-3 stripping), `swar_div_exact_pos_planes`.
- Public structs:
  - `ChiralPair4` (`lo_lane`, `hi_lane`, `raw4`, `net_charge`, `has_hinge`, `is_saturated`, `chiral_flip`, `from_bits`, `to_bits`, `from_lanes`, `to_trit_word`, `from_trit_word`, `Neg`).
  - `BarrierAddResult` (`result`, `hinge_mask`, `blocked_alpha_mask`, `blocked_omega_mask`, `blocked_carry_mask`, `had_blocked_carry`).
  - `TritWord` (`limbs: Vec<u64>`, `width: usize`; constructors, SWAR masks/counts, `neg`, `sign`, `abs_word`, `cmp_value`, `same_value`, `to_canonical`, `burn_contiguous_dwell`, `add`, `sub`, `mul`, `divmod_floor`, `gcd`, `add_hinge_barrier` with exact cross-limb carry tracking, `Neg`/`Add`/`Sub`/`Mul`).
  - `Trit2MicroRatio` (`num_lane`, `den_lane`, all 16 states, `0b11` preserved, `exact_bigrat`, `to_trit_ratio`, `neg`, `reciprocal`).
  - `TritRatio` (`num: TritWord`, `den: TritWord`, `num_hinge_mask: LaneMask`, `den_hinge_mask: LaneMask`; Henrici pre-reduction on `add`/`sub`, pre-multiply cross-cancellation on `mul`/`checked_div`, `reciprocal` swaps masks, `PartialEq`/`Eq`/`Hash`/`Ord` on canonical `(num, den)`, `structural_eq`, `with_cleared_metadata`).
- Comprehensive Rust `#[cfg(test)] mod tests` covering lanes, multi-limb SWAR (`width = 0..100`), all 16 `ChiralPair4` & `Trit2MicroRatio` states, cross-limb `burn_contiguous_dwell` & `add_hinge_barrier`, 230-digit/483-trit codec & Karatsuba/divmod/gcd, and `TritRatio` field laws + metadata propagation.

---

## Step S2–S5: Wiring (`lib.rs`, `ops.rs`, `boundary_sadar.py`, `vectors.py`)

- `crates/aod-core/src/lib.rs`: declare `pub mod ternary;`.
- `crates/aod-core/src/ops.rs`: implement `op_ternary_swar_and_trit_ratio` and dispatch `"ternary_swar_and_trit_ratio"`.
- `manual/engine/sectors/boundary_sadar.py`: implement top-level `eval_ternary_swar_and_trit_ratio(inputs)` with identical typed JSON output.
- `manual/engine/vectors.py`: dispatch `"ternary_swar_and_trit_ratio"`, update count checks `44 -> 45` (`range(1, 46)`).

---

## Step S6: Append `RC-045` to `manual/engine/vectors/rational_core.jsonl`

- `case_id`: `"RC-045"`, `operation`: `"ternary_swar_and_trit_ratio"`, `source_binding`: `"manual/engine/ternary.py#swar_negate;manual/engine/sectors/boundary_sadar.py#eval_ternary_swar_and_trit_ratio"` (2 `.py` selectors -> `98 -> 100` total components).
- `inputs`:
  - `swar_symbols`: `"H+0-000H-+"`
  - `chiral_pair_bits`: `[13, 15, 6]`
  - `barrier_a_symbols`: `"+H-+H++"`, `barrier_b_symbols`: `"+0--0++"`
  - `big_a`: `"2970000000000000000000000000000000000000297"`, `big_b`: `"-297000000000000000000000000000000000000594"`
  - `micro_ratio_bits`: `[9, 7, 13, 15]`
  - `ratio_a_num_symbols`: `"H+-0"`, `ratio_a_den_symbols`: `"H0-00"`, `ratio_b_num_symbols`: `"H0+--0"`, `ratio_b_den_symbols`: `"H00+---"`
- Verify exact analytically computed `expected_outcome` matches BOTH Python and Rust independently.

---

## Step S7: Count-Pin Updates & Parity Tests

- Update vector counts (`44->45`, `52->53`, `51->52`, `98->100`) in:
  - `crates/aod-core/src/vectors.rs`
  - `crates/aod-core/tests/integration_vectors.rs` (plus `RC-045` integration test)
  - `tests/test_s2_reference_engine.py`
  - `tests/test_s4_rust_exact_core.py`
- Add zero-bare-assert Python-vs-Rust `RC-045` parity tests in `tests/test_ternary_engine.py`.

---

## Validation Matrix

1. `mkdir -p _build/s2 _build/s4 && CARGO_TARGET_DIR=_build/cargo-target RUSTFLAGS='-D warnings' cargo test --manifest-path crates/aod-core/Cargo.toml --offline --locked`
2. `python3 -B -m manual.engine --sector boundary_sadar --check-zero-float --verify-vectors --report _build/s2/b2_py_norm.json && python3 -B -O -m manual.engine --sector boundary_sadar --check-zero-float --verify-vectors --report _build/s2/b2_py_opt.json && cmp _build/s2/b2_py_norm.json _build/s2/b2_py_opt.json`
3. `CARGO_TARGET_DIR=_build/cargo-target cargo run --manifest-path crates/aod-core/Cargo.toml --offline --locked -- --verify-vectors --check-zero-float --report _build/s4/b2_rs_dbg.json && CARGO_TARGET_DIR=_build/cargo-target cargo run --manifest-path crates/aod-core/Cargo.toml --offline --locked --release -- --verify-vectors --check-zero-float --report _build/s4/b2_rs_rel.json && cmp _build/s4/b2_rs_dbg.json _build/s4/b2_rs_rel.json`
4. `python3 -B -m pytest -q tests/test_ternary_engine.py tests/test_s2_reference_engine.py tests/test_s4_rust_exact_core.py -k 'not (test_g6_source_zip_extraction or test_s2_f1_diagnostics or test_s4_g6_source_zip or test_s4_f1)'`
5. `python3 -B -O -m pytest -q tests/test_ternary_engine.py`

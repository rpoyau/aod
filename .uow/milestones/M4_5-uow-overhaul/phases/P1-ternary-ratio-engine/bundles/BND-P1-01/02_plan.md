# Execution Plan: `BND-P1-01` — Canonical 2-Bit/4-Bit Trit-on-Binary SWAR Arithmetic & Exact `TritRatio`

- **Milestone**: `M4_5-uow-overhaul`
- **Phase**: `P1-ternary-ratio-engine`
- **Bundle**: `BND-P1-01`
- **Base Commit**: `8dffdb831d72faa7da99e28f0bab35e133ef2c6b`

## Scope Check

- **Write Set** (`scope.write_set`):
  1. `manual/engine/ternary.py` (new)
  2. `manual/engine/__init__.py` (edit: add re-exports)
  3. `tests/test_ternary_engine.py` (new)
- **Read-Only Inputs**: `manual/engine/numeric.py`, `manual/engine/policy.py`, `manual/engine/schema.py`
- **Scope Gaps**: None. All required fail-closed validators (`require`, `require_type`, `require_exact_int`) already exist in `manual/engine/numeric.py`, and `manual/engine/policy.py` requires no edits.

---

## Policy & Invariant Constraints (Hard Gates)

1. **Zero floats / zero complex / zero forbidden symbols** (`manual/engine/policy.py`):
   - `manual/engine/ternary.py` and `manual/engine/__init__.py` MUST pass `audit_source_tree(Path("manual/engine"))` with `violation_count == 0`.
   - **Forbidden imports**: `math`, `cmath`, `numpy`, `scipy`, `pandas`, `matplotlib`, `decimal`, `importlib`, `builtins`, `sympy`, `manual.scripts`, and the forbidden experimental namespace.
     - *Allowed stdlib imports in `ternary.py`*: `from __future__ import annotations`, `from dataclasses import dataclass`, `from fractions import Fraction`, `from functools import lru_cache`, `from typing import Final, Mapping, Sequence`.
     - *Note*: `math.gcd` is forbidden; exact GCD is implemented natively in balanced base-3 SWAR.
   - **Forbidden AST names/attrs**: NEVER reference `float`, `complex`, `eval`, `exec`, `__import__`, `compile`, `__builtins__` as `ast.Name` or `ast.Attribute` inside `manual/engine/ternary.py` (even inside `isinstance(...)`, because `TYPE_GUARD_ALLOWLIST_ENTRIES` only allowlists `policy.py`). Use `require_exact_int` / `require_type` from `manual.engine.numeric`.
   - **Forbidden literals/ops**: Zero float/complex literals; zero integer-literal `/` or `/=`; zero negative integer literal `**` or `**=`.
   - **Zero `__float__` / `__complex__`**: None of `ChiralPair4`, `TritWord`, `Trit2MicroRatio`, `TritRatio`, or `BarrierAddResult` may implement `__float__` or `__complex__`.
   - **Zero forbidden experimental namespace tokens** anywhere in code, comments, docstrings, or tests.
2. **Zero bare `assert` statements**:
   - `manual/engine/ternary.py`: use `require`, `require_type`, `require_exact_int` exclusively.
   - `tests/test_ternary_engine.py`: use non-strippable `_check(condition: bool, message: str = "check failed") -> None` raising `AssertionError(message)` and `_check_raises(...)`; zero `ast.Assert` nodes so normal and `-O` Python run identical checks.
3. **Preservation of `11` (`0_H` structural hinge / saturation / carry-barrier)**:
   - `0b11` is a first-class valid 2-bit lane everywhere (`validate_trit_lane`, `ChiralPair4`, `TritWord`, `Trit2MicroRatio`, `TritRatio` metadata) and is never rejected.
4. **No `Fraction` backing store on `TritRatio`**:
   - `TritRatio` MUST store `(num: TritWord, den: TritWord)` plus hinge metadata masks; `Fraction` is used strictly at conversion boundaries `from_fraction` / `to_fraction`.
5. **Zero uncommitted build artifacts**: Clean `_build/s2/` after validation if untracked.

---

## Execution DAG

```text
[Step 1] manual/engine/ternary.py — Lane constants, bit-plane & O(1) SWAR primitives
   │
   ├──► [Step 2] manual/engine/ternary.py — ChiralPair4 (4-bit chiral-hinge lane container)
   │
   └──► [Step 3] manual/engine/ternary.py — TritWord (packed 2-bit word, SWAR ops,
        │                                   burn_contiguous_dwell, balanced base-3 codec,
        │                                   exact arithmetic + hinge carry-barrier mode)
        │
        ├──► [Step 4] manual/engine/ternary.py — Trit2MicroRatio & TritRatio
        │
        └──► [Step 5] manual/engine/__init__.py — Canonical public re-exports
                  │
                  └──► [Step 6] tests/test_ternary_engine.py — Exhaustive zero-assert test suite
                            │
                            └──► [Step 7] Full 4-command verification & byte-identical -O check
```

---

## Step 1: 2-Bit Lane Encoding & O(1) SWAR Primitives (`manual/engine/ternary.py`)

### 1.1 Canonical 2-Bit Lane Constants

| Constant | Value | Bits `(hi, lo)` | Signed Value `lo - hi` | Symbol | Role |
|---|---|---|---|---|---|
| `TRIT_DWELL` | `0b00` (`0`) | `(0, 0)` | `0` | `"0"` | `0_D` dwell (neutral) |
| `TRIT_ALPHA` | `0b01` (`1`) | `(0, 1)` | `+1` | `"+"` | `+1` alpha polarity |
| `TRIT_OMEGA` | `0b10` (`2`) | `(1, 0)` | `-1` | `"-"` | `-1` omega polarity |
| `TRIT_HINGE` | `0b11` (`3`) | `(1, 1)` | `0` | `"H"` | `0_H` structural hinge / saturation / carry-barrier |

Additional constants:
- `TRIT_LANE_MASK: Final[int] = 0b11`
- `TRIT_LANE_BITS: Final[int] = 2`
- `VALID_TRIT_LANES: Final[frozenset[int]] = frozenset({TRIT_DWELL, TRIT_ALPHA, TRIT_OMEGA, TRIT_HINGE})`

### 1.2 Lane-Level Functions

- `validate_trit_lane(lane: int, *, name: str = "lane") -> int`
- `trit_lane_to_signed(lane: int) -> int`: `(lane & 1) - ((lane >> 1) & 1)`
- `signed_to_trit_lane(value: int) -> int`: `0 -> 0b00`, `1 -> 0b01`, `-1 -> 0b10`
- `negate_trit_lane(lane: int) -> int`: `((lane & 0b01) << 1) | ((lane >> 1) & 0b01)`
- `trit_lane_symbol(lane: int) -> str`: `0b00->"0"`, `0b01->"+"`, `0b10->"-"`, `0b11->"H"`
- `symbol_to_trit_lane(symbol: str) -> int`

### 1.3 O(1) SWAR Mask & Operation Formulas

For any non-negative lane count `width >= 0` (cached via `@lru_cache(maxsize=256)`):
- `swar_mask_01(width: int) -> int`: `((1 << (2 * width)) - 1) // 3`
- `swar_mask_10(width: int) -> int`: `swar_mask_01(width) << 1`
- `swar_mask_11(width: int) -> int`: `(1 << (2 * width)) - 1`
- `swar_double_lane_mask(mask_01_hits: int) -> int`: `mask_01_hits | (mask_01_hits << 1)`
- `swar_negate(packed: int, width: int) -> int`: `((packed & m01) << 1) | ((packed >> 1) & m01)`
- `swar_hinge_mask(w, width, *, doubled=False)`: `h = (w & (w >> 1)) & m01`
- `swar_alpha_mask(w, width, *, doubled=False)`: `a = (w & ~(w >> 1)) & m01`
- `swar_omega_mask(w, width, *, doubled=False)`: `o = ((~w) & (w >> 1)) & m01`
- `swar_polar_mask(w, width, *, doubled=False)`: `p = (w ^ (w >> 1)) & m01`
- `swar_dwell_mask(w, width, *, doubled=False)`: `d = (~(w | (w >> 1))) & m01`

---

## Step 2: 4-Bit Chiral-Hinge Container `ChiralPair4` (`manual/engine/ternary.py`)

`@dataclass(frozen=True, slots=True)` class `ChiralPair4(lo_lane: int, hi_lane: int)`:
- Properties: `raw4`, `net_charge`, `has_hinge`, `is_saturated`
- Methods: `chiral_flip()`, `__neg__()`, `to_bits()`, `from_bits(bits)`, `from_lanes(lo_lane, hi_lane)`, `to_trit_word()`, `from_trit_word(word)`.

---

## Step 3: Arbitrary-Width Packed 2-Bit Word `TritWord` (`manual/engine/ternary.py`)

- `@dataclass(frozen=True, slots=True)` class `TritWord(packed: int, width: int)`
- Class constants/constructors: `zero()`, `one()`, `neg_one()`, `from_int(value)`, `from_lanes(lanes)`, `from_symbols(text, *, msb_first=True)`, `from_packed_pair(pair)`, `from_packed_dict(data)`, `from_chiral_pairs(pairs, *, width=None)`
- SWAR masks & counts: `dwell_mask`, `alpha_mask`, `omega_mask`, `polar_mask`, `hinge_mask`, `has_hinge`, `dwell_count`, `alpha_count`, `omega_count`, `polar_count`, `hinge_count`
- O(1) SWAR ops: `neg()`, `sign()`, `abs_word()`, `cmp(other)`, `same_value(other)`, `to_canonical()`
- Live dwell compaction: `burn_contiguous_dwell(self, *, keep_single_dwell: bool = True) -> TritWord`
- Fast balanced base-3 codec: byte-aligned 4-trit radix-81 lookup tables (`_BAL4_TO_BYTE`, `_BYTE_TO_BAL4`) + divide-and-conquer at $3^{4k}$ for `from_int` / `to_int`
- Pure-SWAR bit-plane arithmetic:
  - `add`, `sub`, `neg`, `abs_word`
  - `BarrierAddResult` & `add_hinge_barrier(self, other)` (blocks carries at `0_H` `11` barrier lanes, records `blocked_alpha_mask`, `blocked_omega_mask`, `hinge_mask`, preserves `11` lanes)
  - `mul` (3-to-2 balanced ternary SWAR CSA leaves `<= 64` trits + balanced base-3 Karatsuba `> 64` trits)
  - `divmod_floor`, `__floordiv__`, `__mod__`, `__divmod__` (balanced non-restoring bit-plane division + 4-quadrant floor sign fix)
  - `gcd` (O(1) trailing-zero-trit factor-of-3 stripping + balanced non-restoring remainder loop)
- Strict dunders & serialization: `lane_at`, `lanes`, `to_msb_lanes`, `to_symbols`, `to_packed_pair`, `to_packed_dict`, `to_chiral_pairs`.

---

## Step 4: `Trit2MicroRatio` & `TritRatio` (`manual/engine/ternary.py`)

- `Trit2MicroRatio(num_lane: int, den_lane: int)`: `raw4`, `num_signed`, `den_signed`, `num_is_hinge`, `den_is_hinge`, `has_hinge`, `is_saturated`, `is_defined`, `is_singular`, `to_bits`, `from_bits`, `to_chiral_pair`, `from_chiral_pair`, `neg`, `reciprocal`, `exact_value`, `to_trit_ratio`.
- `TritRatio`: immutable class backed strictly by `(_num: TritWord, _den: TritWord, _num_hinge_mask: int, _den_hinge_mask: int)` (NEVER `Fraction`), canonical positive coprime `den`, `zero`, `one`, `from_ints`, `from_fraction`, `to_fraction`, `canonical_pair`, `canonical_str`, `to_int_pair`, `neg`, `abs_ratio`, `reciprocal`, `add` (Henrici pre-reduction), `sub`, `mul` (pre-multiply cross-cancellation), `div`, `sign`, `cmp`, `__eq__`/`__hash__`, `structural_eq`, `with_cleared_metadata`, ordering dunders.

---

## Step 5: Re-Exports (`manual/engine/__init__.py`)

Re-export all canonical ternary constants, functions, and classes in alphabetically sorted `__all__`.

---

## Step 6: Exhaustive Zero-Bare-Assert Tests (`tests/test_ternary_engine.py`)

Non-strippable `_check(...)` & `_check_raises(...)` covering policy audit, AST zero-assert check, lane primitives, all 16 `ChiralPair4` states, exhaustive 4-lane SWAR masks & `burn_contiguous_dwell`, codec/serialization, full `[-45, 45]^2` arithmetic grid, carry chains, `add_hinge_barrier`, >128-bit and 230-digit (483-trit) exactness & performance, all 16 `Trit2MicroRatio` states, and `TritRatio` field laws + metadata preservation.

---

## Step 7: Validation Matrix

1. `python3 -B scripts/audit_scientific_sources.py .`
2. `mkdir -p _build/s2 && python3 -B -m manual.engine --sector boundary_sadar --check-zero-float --verify-vectors --report _build/s2/b1_norm.json && python3 -B -O -m manual.engine --sector boundary_sadar --check-zero-float --verify-vectors --report _build/s2/b1_opt.json && cmp _build/s2/b1_norm.json _build/s2/b1_opt.json`
3. `python3 -B -m pytest -q tests/test_ternary_engine.py tests/test_s2_reference_engine.py`
4. `python3 -B -O -m pytest -q tests/test_ternary_engine.py`

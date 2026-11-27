"""Role 6 Adversarial QA / Handoff Test Suite for Phase P1 (P1-ternary-ratio-engine).

Deterministic, offline, zero-bare-assert verification of all whole-phase invariants:
1. 0b11 (0_H structural hinge / saturation) preservation under O(1) SWAR negation
   (00->00, 11->11, 01<->10), SWAR masks, live dwell compaction, and carry-barrier
   addition across single- and multi-limb boundaries in both Python S2 and Rust S4.
2. Genuine (TritWord, TritWord) backing of TritRatio (zero Fraction/BigRat backing,
   verified structurally, statically, and via poisoned-Fraction runtime execution)
   with exact rational parity at >128-bit and >=230-digit Karatsuba/codec scales.
3. First-principles derivation of Tau 13/37 and 19/31 partitions from the
   50-microslot Q4 x mu impedance rotor without requiring slot inputs, plus
   fail-closed rejection of all conflicting legacy overrides in Python and Rust.
4. Genuine C_6 two-step path-pair enumeration in RC-030 double-slit ring with zero
   hardcoded cross_map/cross_for/sat_clip lookup tables in Python and Rust.
5. Exact declared G0 SPARC law agreement (26.57055342%, 230/228 digits) across
   raw SPARC .dat files, tier2_exact, Python S2, Rust S4 (debug/release), SD-008,
   and sparc_pooled_primary_exact.csv, with complete retirement of 64.70291920.
6. Byte-identical Python normal == -O and Rust debug == release CLI reports,
   -O negative-control enforcement, and 0 violations in audit_source_tree &
   Rust audit_crate_tree (policy_audit).
"""
from __future__ import annotations

import ast
import csv
from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Callable

import pytest

from manual.engine import (
    SECTOR_MAP,
    TRIT_ALPHA,
    TRIT_DWELL,
    TRIT_HINGE,
    TRIT_LANE_MASK,
    TRIT_OMEGA,
    BarrierAddResult,
    ChiralPair4,
    Trit2MicroRatio,
    TritRatio,
    TritWord,
    audit_source_tree,
    format_rational_fixed,
    loads_zero_float,
    negate_trit_lane,
    parse_printed_rational,
    require_no_floats,
    signed_to_trit_lane,
    swar_alpha_mask,
    swar_double_lane_mask,
    swar_dwell_mask,
    swar_hinge_mask,
    swar_mask_01,
    swar_mask_10,
    swar_mask_11,
    swar_negate,
    swar_omega_mask,
    swar_polar_mask,
    symbol_to_trit_lane,
    trit_lane_symbol,
    trit_lane_to_signed,
    validate_trit_lane,
    verify_all_vectors,
)
from manual.engine.sectors import boundary_sadar as bs
from manual.engine.sectors import tier2_exact
import manual.engine.ternary as ternary_mod
from manual.engine.vectors import (
    RATIONAL_CORE_REL,
    SYMBOLIC_DISPLAY_REL,
    _eval_operation,
    load_vector_file,
)

ROOT = Path(__file__).resolve().parent.parent
CRATE_DIR = ROOT / "crates" / "aod-core"
CARGO_TOML = CRATE_DIR / "Cargo.toml"
TARGET_DIR = ROOT / "_build" / "cargo-target"


def _check(condition: bool, message: str = "QA invariant check failed") -> None:
    if not condition:
        raise AssertionError(message)


def _check_raises(
    exc_type: type[BaseException] | tuple[type[BaseException], ...],
    fn: Callable[[], object],
    message: str = "expected exception was not raised",
) -> BaseException:
    try:
        fn()
    except exc_type as exc:
        return exc
    raise AssertionError(message)


def _cargo_env() -> dict[str, str]:
    return {**os.environ, "CARGO_TARGET_DIR": str(TARGET_DIR)}


@pytest.fixture(scope="module")
def rust_binaries() -> dict[str, Path]:
    """Ensure offline debug and release aod-core binaries are built and available."""
    if shutil.which("cargo") is None or shutil.which("rustc") is None:
        if os.environ.get("AOD_REQUIRE_RUST", "").strip() in {"1", "true", "TRUE", "yes"}:
            _check(False, "AOD_REQUIRE_RUST=1 set, but cargo/rustc are unavailable")
        pytest.skip("Rust toolchain (cargo/rustc) not installed")

    env = _cargo_env()
    out: dict[str, Path] = {}
    for mode, extra_args in (("debug", []), ("release", ["--release"])):
        proc = subprocess.run(
            [
                "cargo",
                "build",
                "--manifest-path",
                str(CARGO_TOML),
                "--offline",
                "--locked",
                *extra_args,
            ],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=240,
        )
        _check(
            proc.returncode == 0,
            f"cargo build ({mode}) failed (rc={proc.returncode}):\n{proc.stderr}",
        )
        bin_path = TARGET_DIR / mode / "aod-core"
        _check(bin_path.is_file(), f"compiled Rust binary missing: {bin_path}")
        out[mode] = bin_path
    return out


def _run_rust_eval_op(bin_path: Path, operation: str, inputs: dict[str, object]) -> object:
    proc = subprocess.run(
        [str(bin_path), "--eval-op", operation, "--input-stdin"],
        input=json.dumps(inputs, sort_keys=True),
        cwd=ROOT,
        env=_cargo_env(),
        capture_output=True,
        text=True,
        timeout=90,
    )
    _check(
        proc.returncode == 0,
        f"Rust --eval-op {operation} failed (rc={proc.returncode}):\n{proc.stderr}",
    )
    parsed = loads_zero_float(proc.stdout)
    require_no_floats(parsed, path=f"rust.{operation}")
    return parsed


def _run_rust_eval_op_expect_fail(
    bin_path: Path,
    operation: str,
    inputs: dict[str, object],
) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        [str(bin_path), "--eval-op", operation, "--input-stdin"],
        input=json.dumps(inputs, sort_keys=True),
        cwd=ROOT,
        env=_cargo_env(),
        capture_output=True,
        text=True,
        timeout=60,
    )
    _check(
        proc.returncode != 0,
        f"Rust --eval-op {operation} unexpectedly succeeded with rc=0 on bad input: {inputs}",
    )
    return proc


def _strip_rust_comments(src: str) -> str:
    no_block = re.sub(r"/\*.*?\*/", "", src, flags=re.DOTALL)
    return re.sub(r"//[^\n]*", "", no_block)


def _ref_balanced_trit_eval(lanes_lsb: tuple[int, ...]) -> int:
    total = 0
    power = 1
    for lane in lanes_lsb:
        total += trit_lane_to_signed(lane) * power
        power *= 3
    return total


# ---------------------------------------------------------------------------
# Invariant 1: 0b11 (0_H Hinge) Preservation & SWAR Multi-Limb Parity
# ---------------------------------------------------------------------------


def test_qa1_exhaustive_lane_chiral_micro_and_6trit_swar_hinge_preservation() -> None:
    """Verify 00->00, 11->11, 01<->10 exhaustively on 2-bit, 4-bit, and all 4096 6-trit words."""
    # Exact 2-bit truth table
    expected_neg = {
        TRIT_DWELL: TRIT_DWELL,
        TRIT_ALPHA: TRIT_OMEGA,
        TRIT_OMEGA: TRIT_ALPHA,
        TRIT_HINGE: TRIT_HINGE,
    }
    expected_signed = {
        TRIT_DWELL: 0,
        TRIT_ALPHA: 1,
        TRIT_OMEGA: -1,
        TRIT_HINGE: 0,
    }
    expected_sym = {
        TRIT_DWELL: "0",
        TRIT_ALPHA: "+",
        TRIT_OMEGA: "-",
        TRIT_HINGE: "H",
    }
    for lane in range(4):
        _check(validate_trit_lane(lane) == lane, f"validate_trit_lane({lane}) failed")
        _check(negate_trit_lane(lane) == expected_neg[lane], f"negate_trit_lane({lane:#b}) mismatch")
        _check(
            negate_trit_lane(negate_trit_lane(lane)) == lane,
            f"negate_trit_lane not involutive at {lane:#b}",
        )
        _check(trit_lane_to_signed(lane) == expected_signed[lane], f"signed decode mismatch at {lane:#b}")
        _check(trit_lane_symbol(lane) == expected_sym[lane], f"symbol mismatch at {lane:#b}")
        _check(symbol_to_trit_lane(expected_sym[lane]) == lane, f"symbol roundtrip mismatch at {lane:#b}")

    # Exhaustive 16-state ChiralPair4 & Trit2MicroRatio truth tables
    for bits in range(16):
        lo = bits & 0b11
        hi = (bits >> 2) & 0b11
        cp = ChiralPair4.from_bits(bits)
        flipped = cp.chiral_flip()
        _check(cp.raw4 == bits and cp.lo_lane == lo and cp.hi_lane == hi)
        _check(flipped.lo_lane == expected_neg[lo] and flipped.hi_lane == expected_neg[hi])
        _check(flipped.chiral_flip() == cp, f"ChiralPair4 flip not involutive for {bits:#06b}")
        _check(flipped.net_charge == -cp.net_charge, f"ChiralPair4 charge sign mismatch for {bits:#06b}")
        _check(flipped.has_hinge == cp.has_hinge, f"ChiralPair4 hinge lost on flip for {bits:#06b}")
        _check(flipped.is_saturated == cp.is_saturated, f"ChiralPair4 saturation lost for {bits:#06b}")
        _check(
            cp.to_trit_word().neg() == flipped.to_trit_word(),
            f"ChiralPair4 vs TritWord neg mismatch for {bits:#06b}",
        )

        mr = Trit2MicroRatio.from_bits(bits)
        mr_neg = mr.neg()
        mr_rec = mr.reciprocal()
        _check(mr_neg.num_lane == expected_neg[lo] and mr_neg.den_lane == hi)
        _check(mr_rec.num_lane == hi and mr_rec.den_lane == lo)
        _check(mr.is_singular == (hi in (TRIT_DWELL, TRIT_HINGE)))
        _check(mr.is_defined == (not mr.is_singular))
        if mr.is_singular:
            _check_raises(ZeroDivisionError, mr.exact_value, f"singular micro-ratio {bits} did not raise")
            _check_raises(ZeroDivisionError, mr.to_trit_ratio, f"singular micro-ratio {bits} converted")
        else:
            tr = mr.to_trit_ratio()
            _check(tr.to_fraction() == mr.exact_value(), f"micro-ratio value mismatch for {bits}")
            _check(
                tr.num_hinge_mask == (1 if lo == TRIT_HINGE else 0),
                f"micro-ratio num_hinge_mask lost for {bits:#06b}",
            )
            _check(tr.den_hinge_mask == 0, f"defined micro-ratio had nonzero den_hinge_mask for {bits}")

    # Exhaustive 4096-state 6-trit SWAR negation & 4-way partition verification
    m01 = swar_mask_01(6)
    m10 = swar_mask_10(6)
    m11 = swar_mask_11(6)
    _check(m01 == 0b010101010101 and m10 == 0b101010101010 and m11 == 0b111111111111)
    for packed in range(1 << 12):
        w = TritWord(packed=packed, width=6)
        w_neg = w.neg()
        neg_p = swar_negate(packed, 6)
        _check(w_neg.packed == neg_p and w_neg.width == 6)
        _check(w_neg.neg() == w, f"TritWord.neg not involutive for {packed:#x}")

        hm = swar_hinge_mask(packed, 6)
        dm = swar_dwell_mask(packed, 6)
        am = swar_alpha_mask(packed, 6)
        om = swar_omega_mask(packed, 6)
        pm = swar_polar_mask(packed, 6)

        # Pairwise disjoint exact partition of mask_01
        _check((hm | dm | am | om) == m01, f"4-way mask union incomplete for {packed:#x}")
        _check(
            (hm & dm) == 0
            and (hm & am) == 0
            and (hm & om) == 0
            and (dm & am) == 0
            and (dm & om) == 0
            and (am & om) == 0,
            f"4-way masks overlapped for {packed:#x}",
        )
        _check(pm == (am | om), f"polar mask mismatch for {packed:#x}")
        _check(
            (
                swar_double_lane_mask(hm)
                | swar_double_lane_mask(dm)
                | swar_double_lane_mask(am)
                | swar_double_lane_mask(om)
            )
            == m11,
            f"doubled mask union mismatch for {packed:#x}",
        )

        # 00->00, 11->11, 01<->10 under O(1) SWAR negation
        _check(w_neg.hinge_mask == hm, f"0b11 hinge mask corrupted by neg at {packed:#x}")
        _check(w_neg.dwell_mask == dm, f"0b00 dwell mask corrupted by neg at {packed:#x}")
        _check(w_neg.alpha_mask == om, f"0b01/0b10 swap mismatch (alpha) at {packed:#x}")
        _check(w_neg.omega_mask == am, f"0b01/0b10 swap mismatch (omega) at {packed:#x}")
        _check(w_neg.polar_mask == pm, f"polar mask changed under neg at {packed:#x}")
        _check(w_neg.to_int() == -w.to_int(), f"neg decoded value mismatch at {packed:#x}")
        _check(w.to_int() == _ref_balanced_trit_eval(w.lanes()), f"radix-81 decode mismatch at {packed:#x}")

        # abs_word preserves 0b11 hinge mask and register width
        w_abs = w.abs_word()
        _check(w_abs.hinge_mask == hm and w_abs.width == 6 and w_abs.to_int() == abs(w.to_int()))

    # Zero-width & all-hinge edge cases + fail-closed invalid inputs
    empty = TritWord(packed=0, width=0)
    _check(
        empty.neg() == empty
        and empty.hinge_mask == 0
        and empty.dwell_mask == 0
        and empty.to_int() == 0
        and empty.burn_contiguous_dwell(keep_single_dwell=True) == empty
        and empty.burn_contiguous_dwell(keep_single_dwell=False) == empty
        and empty.to_canonical() == TritWord.ZERO,
        "width=0 edge case failed",
    )
    for w_len in (1, 31, 32, 33, 64, 65):
        all_h = TritWord.from_symbols("H" * w_len)
        _check(all_h.neg() == all_h, f"all-H word width={w_len} changed under neg")
        _check(all_h.hinge_count == w_len and all_h.polar_count == 0 and all_h.dwell_count == 0)
        _check(all_h.to_int() == 0 and all_h.sign() == 0)
        _check(all_h.burn_contiguous_dwell(keep_single_dwell=True) == all_h)
        _check(all_h.burn_contiguous_dwell(keep_single_dwell=False) == all_h)

    _check_raises(TypeError, lambda: validate_trit_lane(True))  # type: ignore[arg-type]
    _check_raises(TypeError, lambda: validate_trit_lane(1.0))  # type: ignore[arg-type]
    _check_raises(ValueError, lambda: validate_trit_lane(-1))
    _check_raises(ValueError, lambda: validate_trit_lane(4))
    _check_raises(ValueError, lambda: symbol_to_trit_lane("1"))
    _check_raises(ValueError, lambda: swar_double_lane_mask(0b10))
    _check_raises(ValueError, lambda: swar_double_lane_mask(0b11))
    _check_raises(ValueError, lambda: TritWord(packed=0b100, width=1))


def test_qa1_multilimb_swar_hinge_and_carry_barrier_python_vs_rust_parity(
    rust_binaries: dict[str, Path],
) -> None:
    """Adversarial multi-limb (31/32/33/63/64/65/96 lanes) & dual-polarity carry-barrier parity."""
    # Case A: Hinges and contiguous dwell runs straddling limb 0/1 (lane 31/32) and limb 1/2 (lane 63/64)
    # Plus carry ripple through all 32 '+' lanes of limb 0 crashing directly into 'H' at lane 32 (limb 1 bit 0),
    # AND simultaneous direct omega collision + incoming alpha carry on the SAME hinge lane!
    cases: list[dict[str, object]] = [
        {
            # Empty swar_symbols edge case + dual-polarity collision on same hinge lane (lane 1)
            # barrier_a (MSB..LSB): "+H+" -> lane 2='+', lane 1='H', lane 0='+'
            # barrier_b (MSB..LSB): "0-+" -> lane 2='0', lane 1='-', lane 0='+'
            # At lane 1: direct '-' (omega) blocked AND carry '+' from lane 0 ('+'+'+'='-' carry '+') blocked!
            "swar_symbols": "",
            "chiral_pair_bits": list(range(16)),
            "barrier_a_symbols": "+H+",
            "barrier_b_symbols": "0-+",
            "big_a": str((3**32 - 1) // 2),
            "big_b": str(-((3**32 + 1) // 2)),
            "micro_ratio_bits": list(range(16)),
            "ratio_a_num_symbols": "H+",
            "ratio_a_den_symbols": "H0-",
            "ratio_b_num_symbols": "H0H+",
            "ratio_b_den_symbols": "H-",
        },
        {
            # Limb-boundary dwell runs & hinges at lanes 0, 31, 32, 63, 64, 95, 96 (width=97, 4 limbs!)
            # Carry ripple across 32 '+' lanes hitting hinge at lane 32 and lane 64, with '-' above lane 64 unperturbed!
            "swar_symbols": (
                "H"
                + "-"
                + ("0" * 30)
                + "H"
                + ("0" * 2)
                + "+"
                + ("0" * 29)
                + "HH"
                + ("0" * 30)
                + "H"
            ),
            "chiral_pair_bits": [0, 3, 5, 10, 12, 13, 14, 15],
            "barrier_a_symbols": "-" + "H" + ("+" * 31) + "H" + ("+" * 32),
            "barrier_b_symbols": "0" + "-" + ("0" * 30) + "+" + "0" + ("0" * 31) + "+",
            "big_a": str((3**96 - 1) // 2),
            "big_b": str((3**96 - 1) // 2),
            "micro_ratio_bits": [0, 3, 7, 11, 13, 15],
            "ratio_a_num_symbols": "H" + ("0" * 64) + "+-+",
            "ratio_a_den_symbols": "H" + ("0" * 32) + "H" + ("0" * 31) + "-+",
            "ratio_b_num_symbols": "H0" + ("0" * 63) + "--+",
            "ratio_b_den_symbols": "H" + ("0" * 65) + "+",
        },
        {
            # Asymmetric operand widths in add_hinge_barrier (hinge in short word vs wide polar word)
            # + worst-case balanced ternary division quotient (all '+' divided by '+----...')
            "swar_symbols": "H" * 65,
            "chiral_pair_bits": [15, 11, 7, 3],
            "barrier_a_symbols": "H",
            "barrier_b_symbols": "+" * 35,
            "big_a": str((3**100 - 1) // 2),
            "big_b": str(-((3**33 + 1) // 2)),
            "micro_ratio_bits": [4, 5, 6, 7, 8, 9, 10, 11],
            "ratio_a_num_symbols": "H0H+",  # +1 with hinges at lanes 1 & 3
            "ratio_a_den_symbols": "H-",    # -1 with hinge at lane 1
            "ratio_b_num_symbols": "+" + ("0" * 32) + "H+",
            "ratio_b_den_symbols": "H" + ("0" * 33) + "+",
        },
    ]

    for idx, payload in enumerate(cases):
        py_out = bs.eval_ternary_swar_and_trit_ratio(payload)
        require_no_floats(py_out, path=f"py.qa1_case_{idx}")
        _check(py_out["swar"]["hinge_preserved_under_neg"] is True)
        _check(py_out["swar"]["dwell_preserved_under_neg"] is True)
        _check(py_out["barrier_add"]["result_preserves_hinges"] is True)

        if idx == 0:
            # Verify simultaneous alpha AND omega collision on lane 1 (mask 0b0100 == 4)
            bar = py_out["barrier_add"]
            _check(bar["hinge_mask"] == 4, f"expected hinge_mask=4, got {bar['hinge_mask']}")
            _check(bar["blocked_alpha_mask"] == 4, f"expected blocked_alpha_mask=4, got {bar}")
            _check(bar["blocked_omega_mask"] == 4, f"expected blocked_omega_mask=4, got {bar}")
            _check(bar["result_symbols"] == "+H-", f"expected '+H-', got {bar['result_symbols']}")
        elif idx == 1:
            # Verify carry from 32 '+' lanes hit hinge at lane 32 (bit 64 = 1<<64)
            # AND carry from 31 '+' lanes + '+' hit hinge at lane 64 (bit 128 = 1<<128)
            # AND top '-' at lane 65 was NOT disturbed by blocked carry!
            bar = py_out["barrier_add"]
            expected_h = (1 << 64) | (1 << 128)
            _check(bar["hinge_mask"] == expected_h, f"cross-limb hinge_mask mismatch: {bar}")
            _check(bar["blocked_alpha_mask"] == expected_h, f"cross-limb blocked_alpha mismatch: {bar}")
            _check(bar["blocked_omega_mask"] == (1 << 128), f"cross-limb blocked_omega mismatch: {bar}")
            _check(
                bar["result_symbols"].startswith("-H"),
                f"carry leaked past lane-64 hinge into lane 65: {bar['result_symbols'][:5]}",
            )
        elif idx == 2:
            # Asymmetric hinge at lane 0 blocks lane 0 of 35 '+'s, leaving 34 '+'s above 'H'
            bar = py_out["barrier_add"]
            _check(bar["result_symbols"] == ("+" * 34) + "H", f"asymmetric barrier mismatch: {bar}")
            _check(bar["blocked_alpha_mask"] == 1 and bar["blocked_omega_mask"] == 0)

        for mode in ("debug", "release"):
            rs_out = _run_rust_eval_op(rust_binaries[mode], "ternary_swar_and_trit_ratio", payload)
            _check(
                rs_out == py_out,
                f"QA1 case {idx} Python vs Rust ({mode}) parity mismatch:\nPY={py_out}\nRS={rs_out}",
            )

    # Hinged-zero TritRatio metadata propagation & fail-closed reciprocal/division in Python and Rust
    z_hinged = TritRatio(TritWord.from_symbols("H0H"), TritWord.from_symbols("H-"))
    _check(z_hinged == TritRatio.ZERO and not z_hinged.structural_eq(TritRatio.ZERO))
    _check(z_hinged.num_hinge_mask == 0b01_00_01 and z_hinged.den_hinge_mask == 0b01_00)
    x_hinged = TritRatio.from_ints(5, 7, num_hinge_mask=0b01_00, den_hinge_mask=0b01)
    _check((z_hinged + x_hinged) == x_hinged and (x_hinged + z_hinged) == x_hinged)
    _check((z_hinged + x_hinged).num_hinge_mask == 0b01_01_01)
    _check((z_hinged + x_hinged).den_hinge_mask == 0b01_01)
    _check((z_hinged * x_hinged) == TritRatio.ZERO and (x_hinged * z_hinged) == TritRatio.ZERO)
    _check((z_hinged * x_hinged).num_hinge_mask == 0b01_01_01)
    _check_raises(ZeroDivisionError, z_hinged.reciprocal)
    _check_raises(ZeroDivisionError, lambda: x_hinged / z_hinged)

    for bad_zero_key in ("ratio_a_num_symbols", "ratio_b_num_symbols"):
        bad_zero_payload = dict(cases[2], **{bad_zero_key: "H0H"})
        _check_raises(ZeroDivisionError, lambda p=bad_zero_payload: bs.eval_ternary_swar_and_trit_ratio(p))
        for mode in ("debug", "release"):
            _run_rust_eval_op_expect_fail(rust_binaries[mode], "ternary_swar_and_trit_ratio", bad_zero_payload)


# ---------------------------------------------------------------------------
# Invariant 2: TritRatio Backed Strictly by (TritWord, TritWord) at >230-Digit Scale
# ---------------------------------------------------------------------------


def test_qa2_trit_ratio_strict_tritword_backing_no_fraction_and_no_bigrat() -> None:
    """Prove TritRatio is backed strictly by (TritWord, TritWord) structurally, via AST, and at runtime."""
    # 1. Python slot & immutability structure
    _check(
        TritRatio.__slots__ == ("_num", "_den", "_num_hinge_mask", "_den_hinge_mask"),
        f"unexpected TritRatio.__slots__: {TritRatio.__slots__}",
    )
    sample = TritRatio.from_ints(-(10**140 + 7), 10**140 + 9)
    _check(not hasattr(sample, "__dict__"), "TritRatio must not carry an instance __dict__")
    _check(isinstance(sample.num, TritWord) and isinstance(sample.den, TritWord))
    _check(not isinstance(sample.num, Fraction) and not isinstance(sample.den, Fraction))
    _check_raises(AttributeError, lambda: setattr(sample, "_num", TritWord.ZERO))
    _check_raises(AttributeError, lambda: delattr(sample, "_num"))

    # 2. AST proof: inside class TritRatio, Fraction is ONLY allowed in from_fraction & to_fraction
    ternary_src = (ROOT / "manual" / "engine" / "ternary.py").read_text(encoding="utf-8")
    ternary_tree = ast.parse(ternary_src, filename="manual/engine/ternary.py")
    tr_cls = next(
        (n for n in ternary_tree.body if isinstance(n, ast.ClassDef) and n.name == "TritRatio"),
        None,
    )
    _check(tr_cls is not None, "TritRatio class not found in manual/engine/ternary.py")
    for item in tr_cls.body:
        if isinstance(item, ast.FunctionDef):
            if item.name in {"from_fraction", "to_fraction"}:
                continue
            for sub in ast.walk(item):
                if isinstance(sub, ast.Name) and sub.id == "Fraction":
                    _check(
                        False,
                        f"TritRatio.{item.name} references Fraction at line {sub.lineno}",
                    )

    # 3. Runtime Poisoned-Fraction Proof: replace manual.engine.ternary.Fraction with a trap
    #    and run full 230-digit & hinged TritRatio field arithmetic!
    class _PoisonFraction:
        def __init__(self, *args: object, **kwargs: object) -> None:
            raise RuntimeError("TritRatio arithmetic illegally invoked Fraction!")

    orig_fraction = ternary_mod.Fraction
    try:
        ternary_mod.Fraction = _PoisonFraction  # type: ignore[assignment]
        big_n1 = 10**230 + 3**40 * 17 + 1
        big_d1 = 3**35 * (10**210 + 19)
        big_n2 = -(3**35 * (10**225 + 23))
        big_d2 = 10**228 + 3**30 * 29 + 1

        r1 = TritRatio.from_ints(big_n1, big_d1, num_hinge_mask=0b01_00, den_hinge_mask=0b01)
        r2 = TritRatio.from_ints(big_n2, big_d2, num_hinge_mask=0b01_00_00, den_hinge_mask=0b01_00)
        r_add = r1 + r2
        r_sub = r1 - r2
        r_mul = r1 * r2
        r_div = r1 / r2
        r_rec = r1.reciprocal()
        r_neg = -r1
        r_abs = abs(r2)
        _ = r1.cmp(r2)
        _ = (r1 == r1.with_cleared_metadata(), r1.structural_eq(r1.with_cleared_metadata()), hash(r1))
        add_pair = r_add.canonical_pair()
        sub_pair = r_sub.canonical_pair()
        mul_pair = r_mul.canonical_pair()
        div_pair = r_div.canonical_pair()
        rec_pair = r_rec.canonical_pair()
        neg_pair = r_neg.canonical_pair()
        abs_pair = r_abs.canonical_pair()
        _check(isinstance(r_add.num, TritWord) and isinstance(r_add.den, TritWord))
        _check(r_div.num_hinge_mask == (0b01_00 | 0b01_00) and r_div.den_hinge_mask == (0b01 | 0b01_00_00))
        _check((r_add - r2) == r1 and (r_mul / r2) == r1 and (r_div * r2) == r1)
        _check((r_rec * r1) == TritRatio.ONE)
    finally:
        ternary_mod.Fraction = orig_fraction

    # Cross-check poisoned-run outputs against independent Fraction oracle AFTER restoring Fraction
    f1 = Fraction(big_n1, big_d1)
    f2 = Fraction(big_n2, big_d2)
    for label, pair, ref_f in (
        ("add", add_pair, f1 + f2),
        ("sub", sub_pair, f1 - f2),
        ("mul", mul_pair, f1 * f2),
        ("div", div_pair, f1 / f2),
        ("rec", rec_pair, Fraction(1, 1) / f1),
        ("neg", neg_pair, -f1),
        ("abs", abs_pair, abs(f2)),
    ):
        _check(
            pair == (str(ref_f.numerator), str(ref_f.denominator)),
            f"230-digit TritRatio {label} diverged from exact Fraction oracle",
        )
        _check(math.gcd(int(pair[0]), int(pair[1])) == 1 and int(pair[1]) > 0)

    # 4. Rust TritRatio struct field audit: strictly TritWord + LaneMask (zero BigRat field)
    rs_ternary = _strip_rust_comments((CRATE_DIR / "src" / "ternary.rs").read_text(encoding="utf-8"))
    struct_m = re.search(r"pub\s+struct\s+TritRatio\s*\{([^}]*)\}", rs_ternary, flags=re.DOTALL)
    _check(struct_m is not None, "pub struct TritRatio not found in crates/aod-core/src/ternary.rs")
    struct_body = struct_m.group(1)
    _check("BigRat" not in struct_body, f"Rust TritRatio struct must not contain BigRat: {struct_body}")
    _check("num: TritWord" in struct_body and "den: TritWord" in struct_body, f"unexpected TritRatio fields: {struct_body}")
    _check("num_hinge_mask: LaneMask" in struct_body and "den_hinge_mask: LaneMask" in struct_body)

    # 5. Live SADAR modules must have zero Fraction (Python) and zero BigRat (Rust)
    bs_src = (ROOT / "manual" / "engine" / "sectors" / "boundary_sadar.py").read_text(encoding="utf-8")
    bs_tree = ast.parse(bs_src, filename="manual/engine/sectors/boundary_sadar.py")
    for node in ast.walk(bs_tree):
        if isinstance(node, ast.ImportFrom) and node.module == "fractions":
            _check(False, "boundary_sadar.py must not import from fractions")
        if isinstance(node, ast.Name) and node.id == "Fraction":
            _check(False, f"boundary_sadar.py references Fraction at line {node.lineno}")
    rs_sadar = _strip_rust_comments((CRATE_DIR / "src" / "sadar_sim.rs").read_text(encoding="utf-8"))
    _check("BigRat" not in rs_sadar, "crates/aod-core/src/sadar_sim.rs must not reference BigRat")


def test_qa2_230_digit_and_karatsuba_codec_boundary_arithmetic_parity(
    rust_binaries: dict[str, Path],
) -> None:
    """Test >128-bit and >=230-digit codec/Karatsuba/divmod/GCD/TritRatio extremes across S2 and S4."""
    # Exact codec & limb boundary integers in balanced base-3: +-(3^k - 1)/2 and +-(3^k + 1)/2
    boundary_ints = [
        0,
        1,
        -1,
        (3**16 - 1) // 2,
        (3**16 + 1) // 2,
        -((3**16 - 1) // 2),
        -((3**16 + 1) // 2),
        (3**32 - 1) // 2,
        (3**32 + 1) // 2,
        -((3**32 - 1) // 2),
        -((3**32 + 1) // 2),
        (3**64 - 1) // 2,
        (3**64 + 1) // 2,
        -((3**64 + 1) // 2),
        (3**96 - 1) // 2,
        -((3**96 + 1) // 2),
        10**230 + 3**50 + 17,
        -(10**235 - 3**45 + 29),
    ]
    for n in boundary_ints:
        w = TritWord.from_int(n)
        _check(w.to_int() == n, f"TritWord round-trip failed at {n}")
        _check(w.neg().to_int() == -n, f"TritWord neg round-trip failed at {n}")
        _check(w.sign() == (1 if n > 0 else (-1 if n < 0 else 0)))

    # 4-sign worst-case balanced non-restoring division & Karatsuba stress (>230 digits!)
    u_hi = (3**500 - 1) // 2  # 239 decimal digits, 500 trits (>15 Rust u64 limbs!)
    v_lo = (3**180 + 1) // 2  # 86 decimal digits, 181 trits
    for su in (1, -1):
        for sv in (1, -1):
            a = su * u_hi
            b = sv * v_lo
            wa = TritWord.from_int(a)
            wb = TritWord.from_int(b)
            _check((wa + wb).to_int() == a + b)
            _check((wa - wb).to_int() == a - b)
            _check((wa * wb).to_int() == a * b)
            q_w, r_w = wa.divmod_floor(wb)
            _check((q_w.to_int(), r_w.to_int()) == divmod(a, b), f"divmod mismatch signs=({su},{sv})")
            _check(wa.gcd(wb).to_int() == math.gcd(a, b), f"gcd mismatch signs=({su},{sv})")

    # Actual 230/228-digit SPARC rational fed into TritRatio field axioms
    sparc_n = int(
        "19418935744607809539298996280943513035460534246642062017593537417469319370928813319384441709506654603638069918936535773220649044555882142043710526135948813143174665941692006549524930116907143430554473022105725637749842925705727597"
    )
    sparc_d = int(
        "730844233269509409446890190568111715084017268476516898218283946252243342223131955482069069223085251400724609762599686906693997067144334442031289136388772664030978895997633846254682718493607537413097602276304528821582284800000000"
    )
    _check(len(str(sparc_n)) == 230 and len(str(sparc_d)) == 228)
    r_sparc = TritRatio.from_ints(sparc_n, sparc_d)
    r_shift = TritRatio.from_ints(-(3**50 * 7**12 + 1), 3**50 * 5**14)
    _check(r_sparc.canonical_pair() == (str(sparc_n), str(sparc_d)))
    _check(((r_sparc + r_shift) - r_shift) == r_sparc)
    _check(((r_sparc * r_shift) / r_shift) == r_sparc)
    _check((r_sparc / r_shift) * (r_shift / r_sparc) == TritRatio.ONE)

    # Cross-language S2 vs S4 (debug & release) parity at 239-digit / 500-trit scale
    payload_239: dict[str, object] = {
        "swar_symbols": "H+-" * 25,
        "chiral_pair_bits": [1, 6, 13, 15],
        "barrier_a_symbols": "+" * 33 + "H" + "-" * 33,
        "barrier_b_symbols": "+" + ("0" * 32) + "0" + ("0" * 32) + "-",
        "big_a": str(u_hi),
        "big_b": str(-v_lo),
        "micro_ratio_bits": [7, 9, 13, 15],
        "ratio_a_num_symbols": "H" + TritWord.from_int(sparc_n).to_symbols(msb_first=True),
        "ratio_a_den_symbols": "H" + TritWord.from_int(sparc_d).to_symbols(msb_first=True),
        "ratio_b_num_symbols": "H" + TritWord.from_int(-(3**50 * 7**12 + 1)).to_symbols(msb_first=True),
        "ratio_b_den_symbols": "H" + TritWord.from_int(3**50 * 5**14).to_symbols(msb_first=True),
    }
    py_239 = bs.eval_ternary_swar_and_trit_ratio(payload_239)
    for mode in ("debug", "release"):
        rs_239 = _run_rust_eval_op(rust_binaries[mode], "ternary_swar_and_trit_ratio", payload_239)
        _check(rs_239 == py_239, f"239-digit S2 vs Rust ({mode}) ternary parity mismatch")

    # Fail-closed zero-denominator (both 0_D and multi-lane 0_H) in Python & Rust
    _check_raises(ZeroDivisionError, lambda: TritRatio(TritWord.ONE, TritWord.from_symbols("0H0")))
    _check_raises(ZeroDivisionError, lambda: TritRatio(TritWord.ONE, TritWord.from_symbols("HHH")))
    _check_raises(ZeroDivisionError, lambda: TritRatio(TritWord.from_symbols("H0H"), TritWord.ONE).reciprocal())
    bad_den_payload = dict(payload_239, ratio_a_den_symbols="0H0H")
    _check_raises(ZeroDivisionError, lambda: bs.eval_ternary_swar_and_trit_ratio(bad_den_payload))
    for mode in ("debug", "release"):
        _run_rust_eval_op_expect_fail(rust_binaries[mode], "ternary_swar_and_trit_ratio", bad_den_payload)


# ---------------------------------------------------------------------------
# Invariant 3: Tau 13/37 & 19/31 Derived from 50-Microslot Rotor + Fail-Closed Overrides
# ---------------------------------------------------------------------------


def test_qa3_tau_rotor_first_principles_derivation_and_fail_closed_overrides(
    rust_binaries: dict[str, Path],
) -> None:
    """Prove 13/37 and 19/31 are algorithmically derived from the 50-microslot rotor in S2 and S4."""
    # 1. Confirm committed RC-027 vector omits all legacy slot fields
    _, rc_rows = load_vector_file(ROOT / RATIONAL_CORE_REL)
    rc027 = next(r for r in rc_rows if r["case_id"] == "RC-027")
    _check(
        rc027["inputs"] == {"lead_lag": 8, "window_duons": 3},
        f"RC-027 must use rotor-only inputs, got {rc027['inputs']}",
    )

    # 2. AST proof: eval_sadar_pp_tau_five_boundary & _run_q4_mu_impedance_rotor do not hardcode
    #    13, 19, 31, 37, 650, 703, or 1147 as integer literals
    bs_src = (ROOT / "manual" / "engine" / "sectors" / "boundary_sadar.py").read_text(encoding="utf-8")
    bs_tree = ast.parse(bs_src, filename="manual/engine/sectors/boundary_sadar.py")
    forbidden_tau_literals = {13, 19, 31, 37, 650, 703, 1147}
    for fn_name in ("_run_q4_mu_impedance_rotor", "eval_sadar_pp_tau_five_boundary"):
        fn_node = next(
            (n for n in bs_tree.body if isinstance(n, ast.FunctionDef) and n.name == fn_name),
            None,
        )
        _check(fn_node is not None, f"{fn_name} missing from boundary_sadar.py")
        found_bad = [
            (n.lineno, n.value)
            for n in ast.walk(fn_node)
            if isinstance(n, ast.Constant)
            and type(n.value) is int
            and n.value in forbidden_tau_literals
        ]
        _check(not found_bad, f"hardcoded Tau slot/partition literals in {fn_name}: {found_bad}")

    # 3. Independent simulation of 50-microslot Q4 x mu rotor lane-by-lane + non-hardcoding falsifiers
    def _ref_rotor(rd_lo: int, rd_hi: int) -> tuple[int, int, tuple[int, ...]]:
        delta = rd_hi - rd_lo
        cap = 200
        acc = 0
        lo_lane = TRIT_ALPHA
        lanes: list[int] = []
        for _ in range(50):
            acc += delta
            if acc >= cap:
                acc -= cap
                lo_lane = negate_trit_lane(lo_lane)
                lanes.append(TRIT_HINGE)
            else:
                lanes.append(lo_lane)
        return lanes.count(TRIT_HINGE), 50 - lanes.count(TRIT_HINGE), tuple(lanes)

    # Canonical Stage 1 (RD 1:2=9 -> RD 3:3=61) and Stage 2 (RD 3:3=61 -> RD 3:4=137)
    c1, e1, w1 = bs._run_q4_mu_impedance_rotor(9, 61)
    ref_c1, ref_e1, ref_l1 = _ref_rotor(9, 61)
    _check((c1, e1) == (13, 37) == (ref_c1, ref_e1) and w1.lanes() == ref_l1)
    _check(w1.width == 50 and w1.hinge_count == 13 and w1.polar_count == 37 and w1.dwell_count == 0)

    c2, e2, w2 = bs._run_q4_mu_impedance_rotor(61, 137)
    ref_c2, ref_e2, ref_l2 = _ref_rotor(61, 137)
    _check((c2, e2) == (19, 31) == (ref_c2, ref_e2) and w2.lanes() == ref_l2)
    _check(w2.width == 50 and w2.hinge_count == 19 and w2.polar_count == 31 and w2.dwell_count == 0)

    # Non-hardcoding falsifier on non-Tau RD intervals
    for rd_lo, rd_hi, exp_cap, exp_esc in (
        (5, 9, 1, 49),     # delta=4 -> 50*4/200 = 1 capture at final microslot
        (1, 51, 12, 38),   # delta=50 -> floor(2500/200) = 12 captures
        (10, 110, 25, 25), # delta=100 -> exact 50/50 alternating captures
        (7, 203, 49, 1),   # delta=196 -> 49 captures, 1 escape
    ):
        gc, ge, gw = bs._run_q4_mu_impedance_rotor(rd_lo, rd_hi)
        rc, re_esc, rl = _ref_rotor(rd_lo, rd_hi)
        _check((gc, ge) == (exp_cap, exp_esc) == (rc, re_esc) and gw.lanes() == rl)

    # Rotor bounds fail-closed checks
    _check_raises(ValueError, lambda: bs._run_q4_mu_impedance_rotor(0, 61))
    _check_raises(ValueError, lambda: bs._run_q4_mu_impedance_rotor(61, 61))
    _check_raises(ValueError, lambda: bs._run_q4_mu_impedance_rotor(100, 61))
    _check_raises(ValueError, lambda: bs._run_q4_mu_impedance_rotor(1, 201))

    # 4. Rotor-only execution across varied (lead_lag, window_duons) in Python & Rust debug/release
    for lead_lag, n_duons in ((8, 3), (4, 2), (12, 5)):
        base_in = {"lead_lag": lead_lag, "window_duons": n_duons}
        py_tau = bs.eval_sadar_pp_tau_five_boundary(base_in)
        _check(py_tau["endo_retained_fraction"] == ["13", "50"])
        _check(py_tau["exo_outward_fraction"] == ["37", "50"])
        _check(py_tau["visible_conditional_exo"] == ["19", "50"])
        _check(py_tau["miss_tau_conditional_exo"] == ["31", "50"])
        _check(py_tau["partition_2500_numerators"] == [650, 703, 1147])
        for mode in ("debug", "release"):
            rs_tau = _run_rust_eval_op(rust_binaries[mode], "sadar_pp_tau_five_boundary", base_in)
            _check(rs_tau == py_tau, f"Tau rotor parity mismatch for {base_in} in Rust {mode}")

    # 5. Matching overrides succeed identically; ALL conflicting overrides fail closed in Python & Rust
    base_in = {"lead_lag": 8, "window_duons": 3}
    py_base = bs.eval_sadar_pp_tau_five_boundary(base_in)
    matching_cases = [
        {**base_in, "shed_endo_slots": 13},
        {**base_in, "shed_exo_slots": 37},
        {**base_in, "sensor_visible_slots": 19},
        {**base_in, "sensor_missing_slots": 31},
        {
            **base_in,
            "shed_endo_slots": 13,
            "shed_exo_slots": 37,
            "sensor_visible_slots": 19,
            "sensor_missing_slots": 31,
        },
    ]
    for match_in in matching_cases:
        _check(bs.eval_sadar_pp_tau_five_boundary(match_in) == py_base)
        for mode in ("debug", "release"):
            _check(_run_rust_eval_op(rust_binaries[mode], "sadar_pp_tau_five_boundary", match_in) == py_base)

    conflicting_cases: list[tuple[str, object]] = [
        ("shed_endo_slots", 12),
        ("shed_endo_slots", 14),
        ("shed_endo_slots", 37),
        ("shed_endo_slots", 0),
        ("shed_endo_slots", -13),
        ("shed_exo_slots", 36),
        ("shed_exo_slots", 38),
        ("shed_exo_slots", 13),
        ("sensor_visible_slots", 18),
        ("sensor_visible_slots", 20),
        ("sensor_visible_slots", 31),
        ("sensor_missing_slots", 30),
        ("sensor_missing_slots", 32),
        ("sensor_missing_slots", 19),
        ("shed_endo_slots", True),
    ]
    for bad_key, bad_val in conflicting_cases:
        bad_in = {**base_in, bad_key: bad_val}
        _check_raises(
            (ValueError, TypeError),
            lambda payload=bad_in: bs.eval_sadar_pp_tau_five_boundary(payload),
            f"Python accepted conflicting Tau override {bad_key}={bad_val!r}",
        )
        for mode in ("debug", "release"):
            _run_rust_eval_op_expect_fail(rust_binaries[mode], "sadar_pp_tau_five_boundary", bad_in)


# ---------------------------------------------------------------------------
# Invariant 4: RC-030 Double-Slit Genuine C_6 Path-Pair Enumeration (Zero Lookups)
# ---------------------------------------------------------------------------


def test_qa4_rc030_double_slit_zero_lookup_tables_and_genuine_c6_enumeration(
    rust_binaries: dict[str, Path],
) -> None:
    """Prove RC-030 has zero hardcoded cross_map/cross_for/sat_clip tables and genuinely enumerates C_6."""
    # 1. Static AST & non-comment Rust source verification
    bs_src = (ROOT / "manual" / "engine" / "sectors" / "boundary_sadar.py").read_text(encoding="utf-8")
    for forbidden_tok in ("cross_map", "cross_for", "sat_clip"):
        _check(forbidden_tok not in bs_src, f"boundary_sadar.py contains forbidden token {forbidden_tok!r}")

    bs_tree = ast.parse(bs_src, filename="manual/engine/sectors/boundary_sadar.py")
    slit_fn = next(
        (
            n
            for n in bs_tree.body
            if isinstance(n, ast.FunctionDef) and n.name == "eval_frg_dimonhexon_double_slit_ring"
        ),
        None,
    )
    _check(slit_fn is not None, "eval_frg_dimonhexon_double_slit_ring not found")
    # Verify NO dict literals and NO bin-value lookup constants (31, 35, 18, 26, -12, -8) inside RC-030 evaluator
    dicts_in_slit = [n.lineno for n in ast.walk(slit_fn) if isinstance(n, ast.Dict) and n.keys]
    # Note: the return dict literal is allowed (string keys); forbid any dict with integer keys!
    int_key_dicts = [
        n.lineno
        for n in ast.walk(slit_fn)
        if isinstance(n, ast.Dict)
        and any(isinstance(k, ast.Constant) and type(k.value) is int for k in n.keys)
    ]
    _check(not int_key_dicts, f"integer-key lookup dict in RC-030 at lines {int_key_dicts}")
    _check(len(dicts_in_slit) == 1, f"unexpected extra dict literals in RC-030 at lines {dicts_in_slit}")
    bad_bin_consts = [
        (n.lineno, n.value)
        for n in ast.walk(slit_fn)
        if isinstance(n, ast.Constant) and type(n.value) is int and n.value in {9, 12, 14, 16, 18, 25, 26, 31, 35}
    ]
    _check(not bad_bin_consts, f"hardcoded RC-030 bin value constants found: {bad_bin_consts}")

    rs_sadar_clean = _strip_rust_comments((CRATE_DIR / "src" / "sadar_sim.rs").read_text(encoding="utf-8"))
    for forbidden_tok in ("cross_map", "cross_for", "sat_clip"):
        _check(forbidden_tok not in rs_sadar_clean, f"sadar_sim.rs contains forbidden token {forbidden_tok!r}")
    rs_slit_m = re.search(
        r"pub\s+fn\s+op_frg_dimonhexon_double_slit_ring\b.*?(?=\npub\s+fn\s+|\Z)",
        rs_sadar_clean,
        flags=re.DOTALL,
    )
    _check(rs_slit_m is not None, "op_frg_dimonhexon_double_slit_ring not found in sadar_sim.rs")
    _check(
        "match " not in rs_slit_m.group(0),
        "op_frg_dimonhexon_double_slit_ring must not use match lookup table",
    )

    # 2. Algorithmic generalization check on _enumerate_c6_two_step_paths across multiple half_cap values
    for half_cap in (1, 2, 3, 4):
        for target_k in range(-2 * half_cap, 2 * half_cap + 1):
            paths = bs._enumerate_c6_two_step_paths(target_k, half_cap=half_cap)
            expected_pairs = [
                (s1, target_k - s1)
                for s1 in range(-half_cap, half_cap + 1)
                if -half_cap <= target_k - s1 <= half_cap
            ]
            _check([(s1, s2) for s1, s2, _ in paths] == expected_pairs)
            for s1, s2, bw in paths:
                _check(bw.dwell_count == 0, f"unburned 0_D dwell remained at half_cap={half_cap}, k={target_k}")
                _check(bw.hinge_count == 0)
                _check(bw.width == abs(s1) + abs(s2))
                _check(bw.alpha_count - bw.omega_count == target_k)
    _check_raises(ValueError, lambda: bs._enumerate_c6_two_step_paths(0, half_cap=0))

    # 3. Exact RC-030 parity, mirror symmetry, and comparator perturbation sensitivity
    o_canon = [8, 11, 19, 59, 79, 95, 80, 58, 21, 10, 8]
    canon_in = {"screen_half_span": 5, "hexon_cap": 6, "comparator_O": o_canon}
    py_slit = bs.eval_frg_dimonhexon_double_slit_ring(canon_in)
    _check(py_slit["S_k"] == [4, 9, 16, 25, 31, 35, 31, 25, 16, 9, 4])
    _check(py_slit["T0_k"] == [8, 18, 32, 50, 62, 70, 62, 50, 32, 18, 8])
    _check(py_slit["C_cross_k"] == [0, -8, -12, 8, 18, 26, 18, 8, -12, -8, 0])
    _check(py_slit["T_cross_k"] == [8, 10, 20, 58, 80, 96, 80, 58, 20, 10, 8])
    _check(py_slit["Delta_Z_k"] == [0, -1, 1, -1, 1, 1, 0, 0, -1, 0, 0])
    _check(py_slit["sum_T0"] == 410 and py_slit["sum_C_cross"] == 38 and py_slit["sum_T_cross"] == 448)
    _check(py_slit["sum_Delta_Z"] == 0 and py_slit["sum_m_k"] == 6)

    # Exact bilateral symmetry S_{-k} == S_k and C_cross_{-k} == C_cross_k
    for key in ("S_k", "T0_k", "C_cross_k", "T_cross_k"):
        vals = py_slit[key]
        _check(vals == list(reversed(vals)), f"RC-030 {key} broke mirror symmetry: {vals}")

    # Perturbed comparator with sum_Delta_Z == 0 and sum_m_k == 6 proves Delta_Z_k is computed live
    o_shifted = [11, 10, 20, 58, 80, 96, 80, 58, 20, 10, 5]
    shifted_in = {"screen_half_span": 5, "hexon_cap": 6, "comparator_O": o_shifted}
    py_shifted = bs.eval_frg_dimonhexon_double_slit_ring(shifted_in)
    _check(py_shifted["Delta_Z_k"] == [-3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3])
    _check(py_shifted["sum_Delta_Z"] == 0 and py_shifted["sum_m_k"] == 6)

    for mode in ("debug", "release"):
        _check(_run_rust_eval_op(rust_binaries[mode], "frg_dimonhexon_double_slit_ring", canon_in) == py_slit)
        _check(_run_rust_eval_op(rust_binaries[mode], "frg_dimonhexon_double_slit_ring", shifted_in) == py_shifted)


# ---------------------------------------------------------------------------
# Invariant 5: SD-008 SPARC Exact G0 Law Parity (26.57055342%, 230/228 Digits)
# ---------------------------------------------------------------------------


def test_qa5_sd008_sparc_g0_law_cross_consistency_and_retirement(
    rust_binaries: dict[str, Path],
) -> None:
    """Verify SD-008 matches tier2_exact G0 identically across S2, S4, CSV, and raw .dat; 64.70291920 retired."""
    # 1. Independent Fraction evaluation of tier2_exact.py's declared G0 law directly from raw .dat files
    raw_bins: list[dict[str, str]] = []
    ref_rel_sum = Fraction(0)
    ref_scored = 0
    neg_vgas_count = 0
    for gal in ("NGC2403", "NGC3198", "NGC6503", "NGC2841", "DDO154"):
        dat_path = ROOT / "manual" / "data" / "sparc" / f"{gal}_rotmod.dat"
        _check(dat_path.is_file(), f"missing SPARC dat: {dat_path}")
        for line in dat_path.read_text(encoding="utf-8").splitlines():
            st = line.strip()
            if not st or st.startswith("#"):
                continue
            parts = st.split()
            r_s, vo_s, vg_s, vd_s, vb_s = parts[0], parts[1], parts[3], parts[4], parts[5]
            raw_bins.append({"r_kpc": r_s, "V_obs": vo_s, "V_gas": vg_s, "V_disk": vd_s, "V_bul": vb_s})
            r_v = parse_printed_rational(r_s)
            vo = parse_printed_rational(vo_s)
            vg = parse_printed_rational(vg_s)
            vd = parse_printed_rational(vd_s)
            vb = parse_printed_rational(vb_s)
            if vg < 0:
                neg_vgas_count += 1
            u_obs = vo * vo
            if u_obs > 0:
                u_bar = vg * vg + Fraction(1, 2) * vd * vd + Fraction(7, 10) * vb * vb
                u_ao = u_bar + Fraction(8, 1) * r_v * (abs(vg) + abs(vd) + abs(vb))
                ref_rel_sum += abs(u_ao - u_obs) / u_obs
                ref_scored += 1

    _check(len(raw_bins) == 209 and ref_scored == 209, f"expected 209 SPARC bins, got {ref_scored}")
    _check(neg_vgas_count > 0, "expected real negative V_gas rows in SPARC dataset")
    ref_mape = Fraction(100, 1) * ref_rel_sum / Fraction(ref_scored, 1)
    ref_num_s = str(ref_mape.numerator)
    ref_den_s = str(ref_mape.denominator)
    ref_8dp = format_rational_fixed(ref_mape, 8)
    _check(len(ref_num_s) == 230 and len(ref_den_s) == 228, f"expected 230/228 digits, got {len(ref_num_s)}/{len(ref_den_s)}")
    _check(ref_8dp == "26.57055342", f"expected 26.57055342, got {ref_8dp}")
    _check(math.gcd(ref_mape.numerator, ref_mape.denominator) == 1)

    # 2. Cross-check tier2_exact sparc_five_galaxy sector passes & per-bin CSV matches 209 bins
    t2_sparc = tier2_exact.run_tier2_sector(SECTOR_MAP["sparc_five_galaxy"], ROOT)
    _check(t2_sparc["check_outcome"] == "PASS", f"tier2_exact sparc_five_galaxy failed: {t2_sparc}")
    per_bin_path = ROOT / "manual" / "data" / "derived" / "sparc_five_galaxy_per_bin.csv"
    per_bin_rows = list(csv.DictReader(per_bin_path.read_text(encoding="utf-8").splitlines()))
    _check(len(per_bin_rows) == 209, f"expected 209 per-bin SPARC rows, got {len(per_bin_rows)}")

    # 3. Cross-check Python S2, SD-008 JSONL, Rust S4 (debug & release), and committed CSV
    _, sd_rows = load_vector_file(ROOT / SYMBOLIC_DISPLAY_REL)
    sd008 = next(r for r in sd_rows if r["case_id"] == "SD-008")
    _check(sd008["inputs"]["bins"] == raw_bins, "SD-008 inputs diverge from raw SPARC .dat files")

    py_sparc = bs.eval_sparc_pooled_primary_exact(sd008["inputs"])
    _check(py_sparc["N_total"] == 209 and py_sparc["N_scored"] == 209)
    _check(py_sparc["MAPE_U_exact"] == [ref_num_s, ref_den_s])
    _check(py_sparc["MAPE_U_8dp"] == "26.57055342")
    _check(py_sparc == sd008["expected_outcome"]["exact_value"])

    for mode in ("debug", "release"):
        rs_sparc = _run_rust_eval_op(rust_binaries[mode], "sparc_pooled_primary_exact", sd008["inputs"])
        _check(rs_sparc == py_sparc, f"SD-008 Rust ({mode}) vs Python S2 mismatch")

    csv_path = ROOT / "manual" / "data" / "boundary_sadar" / "sparc_pooled_primary_exact.csv"
    csv_bytes = csv_path.read_bytes()
    csv_rows = list(csv.DictReader(csv_bytes.decode("utf-8").splitlines()))
    _check(len(csv_rows) == 1, f"expected 1 row in sparc_pooled_primary_exact.csv, got {len(csv_rows)}")
    csv_row = csv_rows[0]
    _check(csv_row["N_total"] == "209" and csv_row["N_scored"] == "209")
    _check(csv_row["MAPE_U_num"] == ref_num_s and csv_row["MAPE_U_den"] == ref_den_s)
    _check(csv_row["MAPE_U_display_8dp"] == "26.57055342")

    # Verify SHA-256 pinning in CANONICAL_BINDINGS.json & figure_inventory.json
    csv_sha = hashlib.sha256(csv_bytes).hexdigest()
    cb_doc = loads_zero_float((ROOT / "contracts" / "scientific" / "CANONICAL_BINDINGS.json").read_text(encoding="utf-8"))
    _check(
        cb_doc["frozen_sha256"]["manual/data/boundary_sadar/sparc_pooled_primary_exact.csv"] == csv_sha,
        "CANONICAL_BINDINGS.json SHA-256 mismatch for sparc_pooled_primary_exact.csv",
    )

    # 4. Complete retirement of stale 64.70291920 token
    for rel in (
        "manual/data/boundary_sadar/sparc_pooled_primary_exact.csv",
        "manual/engine/vectors/symbolic_and_display.jsonl",
        "manual/engine/sectors/boundary_sadar.py",
        "crates/aod-core/src/sadar_sim.rs",
        "contracts/scientific/CANONICAL_BINDINGS.json",
    ):
        txt = (ROOT / rel).read_text(encoding="utf-8")
        _check("64.70291920" not in txt, f"retired SPARC score 64.70291920 still present in {rel}")

    # 5. Adversarial synthetic G0 bins (negative V_obs/V_gas/V_disk/V_bul, zero V_obs skip, odd denominators)
    synth_a = {
        "bins": [
            {"r_kpc": "1.375", "V_obs": "-82.5", "V_gas": "-4.25", "V_disk": "-51.125", "V_bul": "-19.75"},
            {"r_kpc": "0.25", "V_obs": "0.00", "V_gas": "10.0", "V_disk": "20.0", "V_bul": "30.0"},
            {"r_kpc": "4.0625", "V_obs": "120.25", "V_gas": "9.5", "V_disk": "77.375", "V_bul": "0.0"},
        ]
    }
    synth_b = {
        "bins": [
            {"r_kpc": "1.375", "V_obs": "82.5", "V_gas": "4.25", "V_disk": "51.125", "V_bul": "19.75"},
            {"r_kpc": "0.25", "V_obs": "0", "V_gas": "-10.0", "V_disk": "-20.0", "V_bul": "-30.0"},
            {"r_kpc": "4.0625", "V_obs": "120.25", "V_gas": "-9.5", "V_disk": "-77.375", "V_bul": "0.0"},
        ]
    }
    py_sa = bs.eval_sparc_pooled_primary_exact(synth_a)
    py_sb = bs.eval_sparc_pooled_primary_exact(synth_b)
    _check(py_sa == py_sb and py_sa["N_total"] == 3 and py_sa["N_scored"] == 2)
    for mode in ("debug", "release"):
        _check(_run_rust_eval_op(rust_binaries[mode], "sparc_pooled_primary_exact", synth_a) == py_sa)
        _check(_run_rust_eval_op(rust_binaries[mode], "sparc_pooled_primary_exact", synth_b) == py_sa)

    # Empty & all-zero V_obs fail closed in both Python and Rust
    for bad_sparc in (
        {"bins": []},
        {"bins": [{"r_kpc": "1.0", "V_obs": "0", "V_gas": "5", "V_disk": "10", "V_bul": "2"}]},
    ):
        _check_raises(ValueError, lambda b=bad_sparc: bs.eval_sparc_pooled_primary_exact(b))
        for mode in ("debug", "release"):
            _run_rust_eval_op_expect_fail(rust_binaries[mode], "sparc_pooled_primary_exact", bad_sparc)


# ---------------------------------------------------------------------------
# Invariant 6: Normal == -O, Debug == Release Byte-Identical + Audits 0 Violations
# ---------------------------------------------------------------------------


def test_qa6_byte_identical_cli_reports_audits_and_whole_phase_parity(
    tmp_path: Path,
    rust_binaries: dict[str, Path],
) -> None:
    """Verify Python normal==-O, Rust debug==release, audit_source_tree & audit_crate_tree 0 violations."""
    # 1. Direct Python audit_source_tree: 0 violations
    src_audit = audit_source_tree(ROOT / "manual" / "engine")
    _check(src_audit["status"] == "PASS", f"audit_source_tree failed: {src_audit}")
    _check(src_audit["violation_count"] == 0 and src_audit["violations"] == [], f"audit_source_tree violations: {src_audit}")

    # 2. Zero bare assert across ALL of manual/engine/ AND this QA suite (self-audit)
    py_files_to_audit = sorted((ROOT / "manual" / "engine").rglob("*.py")) + [
        ROOT / "tests" / "test_ternary_engine.py",
        Path(__file__).resolve(),
    ]
    for py_path in py_files_to_audit:
        tree = ast.parse(py_path.read_text(encoding="utf-8"), filename=str(py_path))
        bare_asserts = [n.lineno for n in ast.walk(tree) if isinstance(n, ast.Assert)]
        _check(not bare_asserts, f"bare assert found in {py_path.relative_to(ROOT)} at lines {bare_asserts}")

    # 3. Python normal vs -O byte-identical full boundary_sadar + all-53-vectors CLI reports
    s2_norm = tmp_path / "s2_norm.json"
    s2_opt = tmp_path / "s2_opt.json"
    for flags, out_path in (
        (["-B"], s2_norm),
        (["-B", "-O"], s2_opt),
    ):
        proc = subprocess.run(
            [
                sys.executable,
                *flags,
                "-m",
                "manual.engine",
                "--sector",
                "boundary_sadar",
                "--check-zero-float",
                "--verify-vectors",
                "--report",
                str(out_path),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=120,
        )
        _check(proc.returncode == 0, f"Python {flags} CLI failed:\n{proc.stderr}")

    norm_bytes = s2_norm.read_bytes()
    opt_bytes = s2_opt.read_bytes()
    _check(norm_bytes == opt_bytes, "Python normal vs -O CLI reports are NOT byte-identical")
    s2_rep = loads_zero_float(norm_bytes.decode("utf-8"))
    require_no_floats(s2_rep, path="s2_report")
    _check(s2_rep["zero_float_policy_audit"]["status"] == "PASS")
    _check(s2_rep["zero_float_policy_audit"]["violation_count"] == 0)
    _check(s2_rep["vectors_verification"]["status"] == "PASS")
    _check(s2_rep["vectors_verification"]["rational_core_count"] == 45)
    _check(s2_rep["vectors_verification"]["symbolic_and_display_count"] == 8)
    _check(s2_rep["vectors_verification"]["total_vectors"] == 53)
    _check(s2_rep["vectors_verification"]["passed_vectors"] == 53)
    _check(s2_rep["vectors_verification"]["failed_vectors"] == 0)
    _check(s2_rep["sectors"][0]["sector_id"] == "boundary_sadar")
    _check(s2_rep["sectors"][0]["check_outcome"] == "PASS")

    # 4. Explicit python3 -B -O subprocess enforces non-strippable negative controls
    opt_neg_script = (
        "from manual.engine import TritRatio, TritWord, TRIT_HINGE\n"
        "from manual.engine.sectors.boundary_sadar import eval_sadar_pp_tau_five_boundary\n"
        "if __debug__:\n"
        "    raise SystemExit('expected -O mode')\n"
        "caught = 0\n"
        "try:\n"
        "    TritRatio(TritWord.ONE, TritWord(TRIT_HINGE, 1))\n"
        "except ZeroDivisionError:\n"
        "    caught += 1\n"
        "try:\n"
        "    TritWord(packed=0b1111, width=1)\n"
        "except ValueError:\n"
        "    caught += 1\n"
        "try:\n"
        "    eval_sadar_pp_tau_five_boundary({'lead_lag': 8, 'window_duons': 3, 'shed_endo_slots': 12})\n"
        "except ValueError:\n"
        "    caught += 1\n"
        "if caught != 3:\n"
        "    raise SystemExit(f'expected 3 exceptions under -O, caught {caught}')\n"
    )
    opt_neg_proc = subprocess.run(
        [sys.executable, "-B", "-O", "-c", opt_neg_script],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    _check(
        opt_neg_proc.returncode == 0,
        f"-O negative-control subprocess failed:\n{opt_neg_proc.stderr}",
    )

    # 5. Rust debug vs release byte-identical CLI reports + audit_crate_tree (policy_audit) 0 violations
    s4_dbg = tmp_path / "s4_dbg.json"
    s4_rel = tmp_path / "s4_rel.json"
    for mode, out_path in (("debug", s4_dbg), ("release", s4_rel)):
        proc = subprocess.run(
            [
                str(rust_binaries[mode]),
                "--verify-vectors",
                "--check-zero-float",
                "--repo-root",
                str(ROOT),
                "--report",
                str(out_path),
            ],
            cwd=ROOT,
            env=_cargo_env(),
            capture_output=True,
            text=True,
            timeout=120,
        )
        _check(proc.returncode == 0, f"Rust {mode} CLI failed:\n{proc.stderr}")

    dbg_bytes = s4_dbg.read_bytes()
    rel_bytes = s4_rel.read_bytes()
    _check(dbg_bytes == rel_bytes, "Rust debug vs release CLI reports are NOT byte-identical")
    s4_rep = loads_zero_float(dbg_bytes.decode("utf-8"))
    require_no_floats(s4_rep, path="s4_report")
    _check(s4_rep["overall_status"] == "PASS", f"Rust overall_status != PASS: {s4_rep}")
    pa = s4_rep["policy_audit"]
    _check(pa["status"] == "PASS" and pa["violation_count"] == 0 and pa["violations"] == [], f"audit_crate_tree failed: {pa}")
    _check(pa["cargo_lock_packages"] == 1, f"crates/aod-core must have 0 external dependencies: {pa}")
    _check("src/lib.rs" in pa["forbid_unsafe_checked_files"], f"forbid(unsafe_code) check missing: {pa}")
    vv = s4_rep["vectors_verification"]
    _check(
        vv["status"] == "PASS"
        and vv["rational_core_count"] == 45
        and vv["symbolic_and_display_count"] == 8
        and vv["total_vectors"] == 53
        and vv["passed_vectors"] == 53
        and vv["failed_vectors"] == 0,
        f"Rust vectors_verification unexpected: {vv}",
    )

    # 6. Full cross-language S2 vs S4 (debug & release) parity across ALL Phase 1 golden vectors
    #    (RC-025..RC-032, RC-045, SD-007, SD-008) + verify_all_vectors in-process check
    inproc_vv = verify_all_vectors(ROOT)
    _check(inproc_vv["status"] == "PASS" and inproc_vv["passed_vectors"] == 53 and inproc_vv["failed_vectors"] == 0)

    _, rc_rows = load_vector_file(ROOT / RATIONAL_CORE_REL)
    _, sd_rows = load_vector_file(ROOT / SYMBOLIC_DISPLAY_REL)
    phase1_ids = {f"RC-{i:03d}" for i in range(25, 33)} | {"RC-045", "SD-007", "SD-008"}
    seen: set[str] = set()
    for rec in (*rc_rows, *sd_rows):
        cid = str(rec["case_id"])
        if cid not in phase1_ids:
            continue
        seen.add(cid)
        op = str(rec["operation"])
        inputs = rec["inputs"]
        _check(isinstance(inputs, dict))
        py_val = _eval_operation(op, inputs)
        _check(py_val == rec["expected_outcome"]["exact_value"], f"{cid} Python oracle mismatch")
        for mode in ("debug", "release"):
            rs_val = _run_rust_eval_op(rust_binaries[mode], op, inputs)
            _check(rs_val == py_val, f"{cid} ({op}) Python vs Rust ({mode}) mismatch")
    _check(seen == phase1_ids, f"missing Phase 1 golden vectors: {sorted(phase1_ids - seen)}")

    # Extra RC-025 negative chirality (-1) parity check (exercises O(1) SWAR flip D_Omega -> D_alpha)
    rc025 = next(r for r in rc_rows if r["case_id"] == "RC-025")
    rc025_neg = dict(rc025["inputs"], initial_chirality=-1)
    py_neg25 = bs.eval_dec_chiral_flip_walk(rc025_neg)
    _check(
        py_neg25["chirality_before"] == -1
        and py_neg25["chirality_after"] == 1
        and py_neg25["dion_before"] == [-1, 1]
        and py_neg25["dion_after"] == [1, -1]
        and py_neg25["structural_hinge_preserved"] is True
        and py_neg25["prior_return_retained"] is True,
    )
    for mode in ("debug", "release"):
        _check(_run_rust_eval_op(rust_binaries[mode], "dec_chiral_flip_walk", rc025_neg) == py_neg25)

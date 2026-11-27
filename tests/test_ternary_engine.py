"""Exhaustive zero-bare-assert test suite for manual/engine/ternary.py.

Every check uses the non-strippable ``_check`` / ``_check_raises`` helpers so
normal Python and ``python3 -B -O`` execute identical verification checks.
"""
from __future__ import annotations

import ast
from fractions import Fraction
from pathlib import Path
import time
from typing import Callable

import manual.engine as engine_pkg
from manual.engine import (
    TRIT_ALPHA,
    TRIT_DWELL,
    TRIT_HINGE,
    TRIT_LANE_BITS,
    TRIT_LANE_MASK,
    TRIT_OMEGA,
    VALID_TRIT_LANES,
    BarrierAddResult,
    ChiralPair4,
    Trit2MicroRatio,
    TritRatio,
    TritWord,
    audit_source_tree,
    negate_trit_lane,
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
)
import manual.engine.ternary as ternary_mod


def _check(condition: bool, message: str = "check failed") -> None:
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


def _ref_gcd(a: int, b: int) -> int:
    x = -a if a < 0 else a
    y = -b if b < 0 else b
    while y:
        x, y = y, x % y
    return x


def _ref_burn_lanes(lanes: tuple[int, ...], *, keep_single_dwell: bool) -> tuple[int, ...]:
    out: list[int] = []
    prev_dwell = False
    for lane in lanes:
        if lane == TRIT_DWELL:
            if keep_single_dwell and not prev_dwell:
                out.append(TRIT_DWELL)
            prev_dwell = True
        else:
            out.append(lane)
            prev_dwell = False
    return tuple(out)


def test_policy_audit_ast_zero_assert_and_exports() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    engine_root = repo_root / "manual" / "engine"
    report = audit_source_tree(engine_root)
    _check(report["status"] == "PASS", f"policy audit failed: {report['violations']}")
    _check(report["violation_count"] == 0, f"expected 0 violations, got {report['violation_count']}")

    for rel in (
        Path("manual/engine/ternary.py"),
        Path("manual/engine/__init__.py"),
        Path("tests/test_ternary_engine.py"),
    ):
        tree = ast.parse((repo_root / rel).read_text(encoding="utf-8"), filename=str(rel))
        asserts = [node for node in ast.walk(tree) if isinstance(node, ast.Assert)]
        _check(not asserts, f"bare assert found in {rel}: lines {[n.lineno for n in asserts]}")

    _check(
        engine_pkg.__all__ == sorted(engine_pkg.__all__),
        "manual.engine.__all__ must be sorted",
    )
    _check(
        ternary_mod.__all__ == sorted(ternary_mod.__all__),
        "manual.engine.ternary.__all__ must be sorted",
    )
    for sym in ternary_mod.__all__:
        _check(sym in engine_pkg.__all__, f"{sym} missing from manual.engine.__all__")
        _check(
            getattr(engine_pkg, sym) is getattr(ternary_mod, sym),
            f"re-exported symbol {sym} identity mismatch",
        )

    for cls in (ChiralPair4, TritWord, Trit2MicroRatio, TritRatio, BarrierAddResult):
        _check(not hasattr(cls, "__float__"), f"{cls.__name__} must not define __float__")
        _check(not hasattr(cls, "__complex__"), f"{cls.__name__} must not define __complex__")

    _check(
        TritRatio.__slots__ == ("_num", "_den", "_num_hinge_mask", "_den_hinge_mask"),
        f"unexpected TritRatio.__slots__: {TritRatio.__slots__}",
    )
    sample = TritRatio.from_ints(7, 11)
    for slot_name in TritRatio.__slots__:
        slot_val = getattr(sample, slot_name)
        _check(
            not isinstance(slot_val, Fraction),
            f"TritRatio slot {slot_name} must never store Fraction",
        )
    _check(isinstance(sample._num, TritWord), "_num must be TritWord")
    _check(isinstance(sample._den, TritWord), "_den must be TritWord")
    _check_raises(AttributeError, lambda: setattr(sample, "_num", TritWord.ONE))
    _check_raises(AttributeError, lambda: delattr(sample, "_num"))


def test_lane_constants_and_primitives() -> None:
    _check(TRIT_DWELL == 0b00, "TRIT_DWELL must be 0b00")
    _check(TRIT_ALPHA == 0b01, "TRIT_ALPHA must be 0b01")
    _check(TRIT_OMEGA == 0b10, "TRIT_OMEGA must be 0b10")
    _check(TRIT_HINGE == 0b11, "TRIT_HINGE must be 0b11")
    _check(TRIT_LANE_MASK == 0b11, "TRIT_LANE_MASK must be 0b11")
    _check(TRIT_LANE_BITS == 2, "TRIT_LANE_BITS must be 2")
    _check(VALID_TRIT_LANES == frozenset({0, 1, 2, 3}), "VALID_TRIT_LANES mismatch")

    expected_signed = {0b00: 0, 0b01: 1, 0b10: -1, 0b11: 0}
    expected_neg = {0b00: 0b00, 0b01: 0b10, 0b10: 0b01, 0b11: 0b11}
    expected_sym = {0b00: "0", 0b01: "+", 0b10: "-", 0b11: "H"}

    for lane in range(4):
        _check(validate_trit_lane(lane) == lane, f"validate_trit_lane failed on {lane}")
        _check(
            trit_lane_to_signed(lane) == expected_signed[lane],
            f"trit_lane_to_signed failed on {lane}",
        )
        _check(
            negate_trit_lane(lane) == expected_neg[lane],
            f"negate_trit_lane failed on {lane}",
        )
        _check(
            negate_trit_lane(negate_trit_lane(lane)) == lane,
            f"negate_trit_lane not involutive on {lane}",
        )
        sym = trit_lane_symbol(lane)
        _check(sym == expected_sym[lane], f"trit_lane_symbol failed on {lane}")
        _check(symbol_to_trit_lane(sym) == lane, f"symbol_to_trit_lane roundtrip failed on {sym}")

    _check(signed_to_trit_lane(0) == TRIT_DWELL, "signed_to_trit_lane(0)")
    _check(signed_to_trit_lane(1) == TRIT_ALPHA, "signed_to_trit_lane(1)")
    _check(signed_to_trit_lane(-1) == TRIT_OMEGA, "signed_to_trit_lane(-1)")

    for bad_int in (-2, -1, 4, 5, 100):
        _check_raises(ValueError, lambda v=bad_int: validate_trit_lane(v))
    for bad_val in (-2, 2, 3):
        _check_raises(ValueError, lambda v=bad_val: signed_to_trit_lane(v))
    for bad_type in (True, False, 0.0, 1.0, "0", None):
        _check_raises(TypeError, lambda v=bad_type: validate_trit_lane(v))  # type: ignore[arg-type]
        _check_raises(TypeError, lambda v=bad_type: signed_to_trit_lane(v))  # type: ignore[arg-type]
    for bad_sym in ("", "00", "1", "h", "x"):
        _check_raises(ValueError, lambda s=bad_sym: symbol_to_trit_lane(s))
    _check_raises(TypeError, lambda: symbol_to_trit_lane(0))  # type: ignore[arg-type]


def test_chiral_pair4_all_16_states() -> None:
    hinge_states = 0
    saturated_states = 0
    for bits in range(16):
        lo = bits & 0b11
        hi = (bits >> 2) & 0b11
        p = ChiralPair4.from_bits(bits)
        p2 = ChiralPair4.from_lanes(lo, hi)
        _check(p == p2, f"from_bits vs from_lanes mismatch at {bits}")
        _check(p.lo_lane == lo and p.hi_lane == hi, f"lane mismatch at {bits}")
        _check(p.raw4 == bits and p.to_bits() == bits, f"raw4/to_bits mismatch at {bits}")
        _check(
            p.net_charge == trit_lane_to_signed(lo) + trit_lane_to_signed(hi),
            f"net_charge mismatch at {bits}",
        )
        expected_hinge = (lo == TRIT_HINGE) or (hi == TRIT_HINGE)
        expected_sat = (lo == TRIT_HINGE) and (hi == TRIT_HINGE)
        _check(p.has_hinge is expected_hinge, f"has_hinge mismatch at {bits}")
        _check(p.is_saturated is expected_sat, f"is_saturated mismatch at {bits}")
        if p.has_hinge:
            hinge_states += 1
        if p.is_saturated:
            saturated_states += 1

        flipped = p.chiral_flip()
        _check(flipped == -p, f"__neg__ must equal chiral_flip at {bits}")
        _check(flipped.chiral_flip() == p, f"chiral_flip not involutive at {bits}")
        _check(flipped.net_charge == -p.net_charge, f"chiral_flip net_charge mismatch at {bits}")
        _check(flipped.has_hinge == p.has_hinge, f"chiral_flip must preserve has_hinge at {bits}")
        _check(
            flipped.is_saturated == p.is_saturated,
            f"chiral_flip must preserve is_saturated at {bits}",
        )
        _check(
            flipped.lo_lane == negate_trit_lane(lo) and flipped.hi_lane == negate_trit_lane(hi),
            f"chiral_flip lane swap mismatch at {bits}",
        )

        w = p.to_trit_word()
        _check(w == TritWord(packed=bits, width=2), f"to_trit_word mismatch at {bits}")
        _check(ChiralPair4.from_trit_word(w) == p, f"from_trit_word roundtrip failed at {bits}")
        _check(flipped.to_trit_word() == w.neg(), f"chiral_flip vs TritWord.neg mismatch at {bits}")

    _check(hinge_states == 7, f"expected 7 hinge states in ChiralPair4, got {hinge_states}")
    _check(saturated_states == 1, f"expected 1 saturated state, got {saturated_states}")

    _check(
        ChiralPair4.from_trit_word(TritWord.ONE) == ChiralPair4(TRIT_ALPHA, TRIT_DWELL),
        "1-lane TritWord conversion to ChiralPair4 failed",
    )
    _check(
        ChiralPair4.from_trit_word(TritWord(0, 0)) == ChiralPair4(TRIT_DWELL, TRIT_DWELL),
        "0-lane TritWord conversion to ChiralPair4 failed",
    )
    _check_raises(ValueError, lambda: ChiralPair4.from_trit_word(TritWord(0, 3)))
    _check_raises(ValueError, lambda: ChiralPair4.from_bits(-1))
    _check_raises(ValueError, lambda: ChiralPair4.from_bits(16))
    _check_raises(TypeError, lambda: ChiralPair4.from_bits(True))
    _check_raises(TypeError, lambda: ChiralPair4.from_bits(1.0))  # type: ignore[arg-type]
    _check_raises(TypeError, lambda: ChiralPair4.from_trit_word(0))  # type: ignore[arg-type]


def test_swar_masks_and_burn_contiguous_dwell_exhaustive_4_lanes() -> None:
    _check(swar_mask_01(0) == 0 and swar_mask_10(0) == 0 and swar_mask_11(0) == 0, "width 0 masks")
    _check(swar_mask_01(4) == 0b01_01_01_01, "swar_mask_01(4)")
    _check(swar_mask_10(4) == 0b10_10_10_10, "swar_mask_10(4)")
    _check(swar_mask_11(4) == 0b11_11_11_11, "swar_mask_11(4)")
    _check(swar_double_lane_mask(0b01_00_01_00) == 0b11_00_11_00, "swar_double_lane_mask")
    _check_raises(TypeError, lambda: swar_mask_01(True))
    _check_raises(ValueError, lambda: swar_mask_01(-1))
    _check_raises(ValueError, lambda: swar_double_lane_mask(0b10))
    _check_raises(ValueError, lambda: swar_negate(0b100, 1))

    m01 = swar_mask_01(4)
    for raw in range(256):
        w = TritWord(packed=raw, width=4)
        lanes = tuple((raw >> (2 * i)) & 0b11 for i in range(4))
        _check(w.lanes() == lanes, f"lanes() mismatch at {raw}")
        _check(w.to_msb_lanes() == tuple(reversed(lanes)), f"to_msb_lanes mismatch at {raw}")

        exp_dwell = sum((1 << (2 * i)) for i, l in enumerate(lanes) if l == TRIT_DWELL)
        exp_alpha = sum((1 << (2 * i)) for i, l in enumerate(lanes) if l == TRIT_ALPHA)
        exp_omega = sum((1 << (2 * i)) for i, l in enumerate(lanes) if l == TRIT_OMEGA)
        exp_hinge = sum((1 << (2 * i)) for i, l in enumerate(lanes) if l == TRIT_HINGE)
        exp_polar = exp_alpha | exp_omega

        _check(w.dwell_mask == exp_dwell and swar_dwell_mask(raw, 4) == exp_dwell, f"dwell {raw}")
        _check(w.alpha_mask == exp_alpha and swar_alpha_mask(raw, 4) == exp_alpha, f"alpha {raw}")
        _check(w.omega_mask == exp_omega and swar_omega_mask(raw, 4) == exp_omega, f"omega {raw}")
        _check(w.hinge_mask == exp_hinge and swar_hinge_mask(raw, 4) == exp_hinge, f"hinge {raw}")
        _check(w.polar_mask == exp_polar and swar_polar_mask(raw, 4) == exp_polar, f"polar {raw}")

        _check(
            swar_dwell_mask(raw, 4, doubled=True) == swar_double_lane_mask(exp_dwell),
            f"doubled dwell {raw}",
        )
        _check(
            swar_alpha_mask(raw, 4, doubled=True) == swar_double_lane_mask(exp_alpha),
            f"doubled alpha {raw}",
        )
        _check(
            swar_omega_mask(raw, 4, doubled=True) == swar_double_lane_mask(exp_omega),
            f"doubled omega {raw}",
        )
        _check(
            swar_hinge_mask(raw, 4, doubled=True) == swar_double_lane_mask(exp_hinge),
            f"doubled hinge {raw}",
        )
        _check(
            swar_polar_mask(raw, 4, doubled=True) == swar_double_lane_mask(exp_polar),
            f"doubled polar {raw}",
        )

        _check(
            (exp_dwell | exp_alpha | exp_omega | exp_hinge) == m01,
            f"SWAR mask partition incomplete at {raw}",
        )
        _check(
            w.dwell_count + w.alpha_count + w.omega_count + w.hinge_count == 4,
            f"lane count sum mismatch at {raw}",
        )
        _check(w.polar_count == w.alpha_count + w.omega_count, f"polar count mismatch at {raw}")
        _check(w.has_hinge == (exp_hinge != 0), f"has_hinge mismatch at {raw}")

        exp_val = sum(trit_lane_to_signed(l) * (3**i) for i, l in enumerate(lanes))
        _check(w.to_int() == exp_val, f"to_int mismatch at {raw}: {w.to_int()} != {exp_val}")
        exp_sign = 1 if exp_val > 0 else (-1 if exp_val < 0 else 0)
        _check(w.sign() == exp_sign, f"sign mismatch at {raw}")
        _check(bool(w) == (exp_val != 0), f"bool(w) mismatch at {raw}")

        neg_w = w.neg()
        _check(neg_w.packed == swar_negate(raw, 4), f"neg vs swar_negate mismatch at {raw}")
        _check(neg_w.width == 4, f"neg width mismatch at {raw}")
        _check(neg_w.to_int() == -exp_val, f"neg value mismatch at {raw}")
        _check(neg_w.hinge_mask == w.hinge_mask, f"neg must preserve 11 hinge mask at {raw}")
        _check(neg_w.dwell_mask == w.dwell_mask, f"neg must preserve 00 dwell mask at {raw}")
        _check(neg_w.neg() == w, f"neg involution failed at {raw}")
        _check(w.abs_word().to_int() == abs(exp_val), f"abs_word value mismatch at {raw}")
        _check(w.abs_word().hinge_mask == w.hinge_mask, f"abs_word hinge preserve failed at {raw}")

        canon = w.to_canonical()
        _check(canon == TritWord.from_int(exp_val), f"to_canonical mismatch at {raw}")
        _check(w.same_value(canon), f"same_value with canonical failed at {raw}")
        _check(canon.hinge_mask == 0, f"canonical word must have 0 hinges at {raw}")

        # Exhaustive burn_contiguous_dwell verification (both modes + idempotence)
        b_keep = w.burn_contiguous_dwell(keep_single_dwell=True)
        _check(
            b_keep.lanes() == _ref_burn_lanes(lanes, keep_single_dwell=True),
            f"burn_contiguous_dwell(keep_single_dwell=True) mismatch at {raw}",
        )
        _check(
            b_keep.burn_contiguous_dwell(keep_single_dwell=True) == b_keep,
            f"burn_contiguous_dwell(True) not idempotent at {raw}",
        )
        _check(
            b_keep.hinge_count == w.hinge_count and b_keep.polar_count == w.polar_count,
            f"burn_contiguous_dwell(True) lost hinge/polar trace at {raw}",
        )

        b_drop = w.burn_contiguous_dwell(keep_single_dwell=False)
        _check(
            b_drop.lanes() == _ref_burn_lanes(lanes, keep_single_dwell=False),
            f"burn_contiguous_dwell(keep_single_dwell=False) mismatch at {raw}",
        )
        _check(
            b_drop.burn_contiguous_dwell(keep_single_dwell=False) == b_drop,
            f"burn_contiguous_dwell(False) not idempotent at {raw}",
        )
        _check(b_drop.dwell_count == 0, f"burn_contiguous_dwell(False) left dwell at {raw}")
        _check(
            b_drop.hinge_count == w.hinge_count and b_drop.polar_count == w.polar_count,
            f"burn_contiguous_dwell(False) lost hinge/polar trace at {raw}",
        )

    # Long dwell compaction traces
    long_trace = TritWord.from_symbols("00000+0000H00000-00000HH000")
    _check(
        long_trace.burn_contiguous_dwell().to_symbols() == "0+0H0-0HH0",
        "long contiguous dwell burn (keep_single_dwell=True) failed",
    )
    _check(
        long_trace.burn_contiguous_dwell(keep_single_dwell=False).to_symbols() == "+H-HH",
        "long contiguous dwell burn (keep_single_dwell=False) failed",
    )
    _check(
        TritWord.from_symbols("00000").burn_contiguous_dwell() == TritWord.ZERO,
        "all-dwell xxxxx->x burn failed",
    )
    _check(
        TritWord.from_symbols("00000").burn_contiguous_dwell(keep_single_dwell=False)
        == TritWord(0, 0),
        "all-dwell full burn failed",
    )
    _check(
        TritWord(0, 0).burn_contiguous_dwell() == TritWord(0, 0),
        "empty TritWord burn failed",
    )


def test_trit_word_constants_codec_and_serialization() -> None:
    _check(TritWord.ZERO == TritWord.zero() == TritWord(0, 1), "TritWord.ZERO mismatch")
    _check(TritWord.ONE == TritWord.one() == TritWord(1, 1), "TritWord.ONE mismatch")
    _check(TritWord.NEG_ONE == TritWord.neg_one() == TritWord(2, 1), "TritWord.NEG_ONE mismatch")
    _check(TritWord.zero(4) == TritWord(0, 4), "TritWord.zero(4) mismatch")

    # Small integer codec roundtrip + radix-81 / power-of-3 boundaries
    test_ints: list[int] = list(range(-500, 501))
    for k in (1, 2, 3, 4, 8, 12, 16, 32, 64, 65, 81, 128, 200):
        half_p3 = (3**k - 1) // 2
        test_ints.extend([half_p3 - 1, half_p3, half_p3 + 1, -(half_p3 - 1), -half_p3, -(half_p3 + 1)])
    for c in (1, 2, 4, 15, 16, 17, 32, 64, 121):
        half_p81 = (81**c - 1) // 2
        test_ints.extend([half_p81, half_p81 + 1, -half_p81, -(half_p81 + 1)])

    for n in test_ints:
        w = TritWord.from_int(n)
        _check(w.to_int() == n, f"from_int/to_int mismatch for {n}")
        _check(int(w) == n, f"int(w) mismatch for {n}")
        _check(w.hinge_mask == 0, f"from_int must not emit hinges for {n}")
        _check(w.to_canonical() == w, f"from_int must be canonical for {n}")
        _check(w.neg().to_int() == -n, f"neg mismatch for {n}")

    # Serialization round-trips including hinges and odd/even widths
    for sym in ("", "0", "+", "-", "H", "0+H-", "H0+-0H+", "00H++--H"):
        w = TritWord.from_symbols(sym, msb_first=True)
        _check(len(w) == len(sym), f"len mismatch for {sym!r}")
        _check(w.to_symbols(msb_first=True) == sym, f"msb symbols roundtrip failed for {sym!r}")
        _check(
            w.to_symbols(msb_first=False) == sym[::-1],
            f"lsb symbols mismatch for {sym!r}",
        )
        _check(
            TritWord.from_symbols(sym[::-1], msb_first=False) == w,
            f"from_symbols lsb failed for {sym!r}",
        )
        _check(TritWord.from_lanes(w.lanes()) == w, f"from_lanes lsb failed for {sym!r}")
        _check(
            TritWord.from_lanes(w.to_msb_lanes(), msb_first=True) == w,
            f"from_lanes msb failed for {sym!r}",
        )
        for idx in range(w.width):
            _check(w.lane_at(idx) == w.lanes()[idx], f"lane_at({idx}) mismatch for {sym!r}")
        _check(
            TritWord.from_packed_pair(w.to_packed_pair()) == w,
            f"packed_pair roundtrip failed for {sym!r}",
        )
        pdict = w.to_packed_dict()
        require_no_floats(pdict)
        _check(
            TritWord.from_packed_dict(pdict) == w,
            f"packed_dict roundtrip failed for {sym!r}",
        )
        _check(
            TritWord.from_packed_dict({"packed": w.packed, "width": w.width}) == w,
            f"minimal packed_dict roundtrip failed for {sym!r}",
        )
        pairs = w.to_chiral_pairs()
        _check(
            TritWord.from_chiral_pairs(pairs, width=w.width) == w,
            f"chiral_pairs roundtrip failed for {sym!r}",
        )

    # Fail-closed validation checks
    _check_raises(
        ValueError,
        lambda: TritWord.from_packed_dict({"packed": 1, "width": 1, "symbols": "-"}),
    )
    _check_raises(
        ValueError,
        lambda: TritWord.from_packed_dict({"packed": 3, "width": 1, "hinge_mask": 0}),
    )
    _check_raises(
        ValueError,
        lambda: TritWord.from_packed_dict({"packed": 0, "width": 1, "extra": 1}),
    )
    _check_raises(
        ValueError,
        lambda: TritWord.from_chiral_pairs([ChiralPair4(TRIT_ALPHA, TRIT_ALPHA)], width=1),
    )
    _check_raises(ValueError, lambda: TritWord.ONE.lane_at(-1))
    _check_raises(ValueError, lambda: TritWord.ONE.lane_at(1))
    _check_raises(TypeError, lambda: TritWord.from_int(True))
    _check_raises(TypeError, lambda: TritWord.from_int(1.0))  # type: ignore[arg-type]
    _check_raises(TypeError, lambda: TritWord.ONE + 1)  # type: ignore[operator]
    _check_raises(TypeError, lambda: TritWord.ONE + 1.5)  # type: ignore[operator]
    _check_raises(TypeError, lambda: TritWord.ONE * True)  # type: ignore[operator]
    _check_raises(ZeroDivisionError, lambda: TritWord.ONE // TritWord.ZERO)
    _check_raises(ZeroDivisionError, lambda: TritWord.ONE % TritWord.ZERO)
    _check_raises(ZeroDivisionError, lambda: divmod(TritWord.ONE, TritWord.ZERO))


def test_trit_word_full_arithmetic_grid() -> None:
    words = {n: TritWord.from_int(n) for n in range(-45, 46)}
    for a in range(-45, 46):
        wa = words[a]
        for b in range(-45, 46):
            wb = words[b]
            add_w = wa + wb
            sub_w = wa - wb
            mul_w = wa * wb
            _check(add_w.to_int() == a + b, f"add failed for ({a}, {b})")
            _check(sub_w.to_int() == a - b, f"sub failed for ({a}, {b})")
            _check(mul_w.to_int() == a * b, f"mul failed for ({a}, {b})")

            exp_cmp = 1 if a > b else (-1 if a < b else 0)
            _check(wa.cmp(wb) == exp_cmp, f"cmp failed for ({a}, {b})")
            _check((wa < wb) == (a < b), f"< failed for ({a}, {b})")
            _check((wa <= wb) == (a <= b), f"<= failed for ({a}, {b})")
            _check((wa > wb) == (a > b), f"> failed for ({a}, {b})")
            _check((wa >= wb) == (a >= b), f">= failed for ({a}, {b})")

            g_w = wa.gcd(wb)
            _check(g_w.to_int() == _ref_gcd(a, b), f"gcd failed for ({a}, {b})")

            if b != 0:
                q_w, r_w = wa.divmod_floor(wb)
                eq, er = divmod(a, b)
                _check(
                    q_w.to_int() == eq and r_w.to_int() == er,
                    f"divmod_floor failed for ({a}, {b}): got ({q_w.to_int()}, {r_w.to_int()}), expected ({eq}, {er})",
                )
                _check((wa // wb) == q_w and (wa % wb) == r_w, f"// or % mismatch for ({a}, {b})")


def test_carry_chains_and_add_hinge_barrier() -> None:
    # Full balanced carry chains across varying widths
    for k in (1, 2, 4, 8, 16, 32, 65, 130):
        max_k = (3**k - 1) // 2
        w_max = TritWord.from_int(max_k)
        w_min = TritWord.from_int(-max_k)
        _check((w_max + TritWord.ONE).to_int() == max_k + 1, f"pos carry chain failed at k={k}")
        _check((w_min - TritWord.ONE).to_int() == -max_k - 1, f"neg carry chain failed at k={k}")
        _check((w_max + w_max).to_int() == 2 * max_k, f"double max carry chain failed at k={k}")

    # No hinges: barrier add == standard add
    a0 = TritWord.from_int(17)
    b0 = TritWord.from_int(-29)
    res0 = a0.add_hinge_barrier(b0)
    _check(isinstance(res0, BarrierAddResult), "add_hinge_barrier must return BarrierAddResult")
    _check(res0.result == a0.add(b0), "barrier add without hinges must match standard add")
    _check(
        res0.hinge_mask == 0
        and res0.blocked_alpha_mask == 0
        and res0.blocked_omega_mask == 0
        and not res0.had_blocked_carry,
        "barrier add without hinges must have zero masks",
    )

    # Segmented positive overflow blocked at 0_H lane 1, upper segment isolated
    a1 = TritWord.from_symbols("+H+")
    b1 = TritWord.from_symbols("+H+")
    res1 = a1.add_hinge_barrier(b1)
    _check(res1.result.to_symbols() == "+-H-", f"unexpected barrier result: {res1.result.to_symbols()}")
    _check(res1.hinge_mask == 0b00_01_00, f"unexpected hinge_mask: {res1.hinge_mask:#b}")
    _check(
        res1.blocked_alpha_mask == 0b00_01_00,
        f"unexpected blocked_alpha_mask: {res1.blocked_alpha_mask:#b}",
    )
    _check(res1.blocked_omega_mask == 0, "blocked_omega_mask should be 0")
    _check(res1.had_blocked_carry and res1.blocked_carry_mask == 0b00_01_00, "blocked_carry_mask")
    _check(res1.result.hinge_mask == res1.hinge_mask, "result must preserve all 11 hinge lanes")

    # Multi-lane carry chain hitting both an omega barrier (lane 3) and alpha barrier (lane 6)
    a2 = TritWord.from_symbols("+H++H---")
    b2 = TritWord.from_symbols("+H0+H00-")
    # Lanes:
    # 0..2: --- (-13) + 00- (-1) = -14 -> carries -1 into lane 3 (H!), low 3 lanes = +++ (+13 - 27 = -14)
    # 3: H barrier (blocks omega carry at bit 6 = 1 << 6)
    # 4..5: ++ (+4) + 0+ (+1) = +5 -> carries +1 into lane 6 (H!), lanes 4..5 = -- (-4 + 9 = +5)
    # 6: H barrier (blocks alpha carry at bit 12 = 1 << 12)
    # 7: + (+1) + + (+1) = +- (+2) at lanes 7..8
    res2 = a2.add_hinge_barrier(b2)
    _check(
        res2.result.to_symbols() == "+-H--H+++",
        f"multi-barrier result mismatch: {res2.result.to_symbols()}",
    )
    _check(res2.hinge_mask == ((1 << 6) | (1 << 12)), "multi-barrier hinge_mask mismatch")
    _check(res2.blocked_omega_mask == (1 << 6), "multi-barrier blocked_omega_mask mismatch")
    _check(res2.blocked_alpha_mask == (1 << 12), "multi-barrier blocked_alpha_mask mismatch")
    _check(res2.result.hinge_mask == res2.hinge_mask, "multi-barrier hinges must be preserved")

    # Direct polar injection colliding with a 0_H barrier lane
    res3 = TritWord.from_symbols("H").add_hinge_barrier(TritWord.from_symbols("+"))
    _check(res3.result.to_symbols() == "H", "direct collision must preserve H lane")
    _check(res3.blocked_alpha_mask == 0b01 and res3.blocked_omega_mask == 0, "direct alpha block")


def test_large_magnitude_gt128bit_and_230digit_exactness_and_perf() -> None:
    # Cross Karatsuba (>64 trits) and radix-81 DC (>16 bytes) thresholds
    big_pairs = [
        ((1 << 130) + 1234567890123456789, -(1 << 129) - 9876543210987654321),
        (3**64 + 7, 3**65 - 11),
        (-(3**128 - 1) // 2, (3**129 + 1) // 2),
        # 230-digit (~483-trit) integers
        (10**230 + 31415926535897932384626433832795028841971, 10**229 + 27182818284590452353602874713526624977572),
        (-(10**230 - 99999999999999999999999999999999999999), 3**30 * (10**190 + 137)),
    ]

    t0 = time.monotonic()
    for a, b in big_pairs:
        wa = TritWord.from_int(a)
        wb = TritWord.from_int(b)
        _check(wa.to_int() == a and wb.to_int() == b, "large codec roundtrip failed")
        _check((wa + wb).to_int() == a + b, "large add mismatch")
        _check((wa - wb).to_int() == a - b, "large sub mismatch")
        _check((wa * wb).to_int() == a * b, "large mul (Karatsuba) mismatch")
        q, r = wa.divmod_floor(wb)
        eq, er = divmod(a, b)
        _check(q.to_int() == eq and r.to_int() == er, "large divmod_floor mismatch")
        _check(wa.gcd(wb).to_int() == _ref_gcd(a, b), "large gcd mismatch")
        _check(wa.cmp(wb) == (1 if a > b else (-1 if a < b else 0)), "large cmp mismatch")

    # Verify 483-trit product specifically hits Karatsuba width > 480
    huge_a = TritWord.from_int(10**230 + 17)
    huge_b = TritWord.from_int(10**230 - 29)
    _check(huge_a.width >= 480 and huge_b.width >= 480, f"expected >=480 trits, got {huge_a.width}")
    prod = huge_a * huge_b
    _check(prod.to_int() == (10**230 + 17) * (10**230 - 29), "483-trit mul exactness failed")
    q_h, r_h = prod.divmod_floor(huge_a)
    _check(q_h == huge_b and r_h == TritWord.ZERO, "483-trit exact division roundtrip failed")

    # Large TritRatio check (230-digit numerator/denominator)
    ra = TritRatio.from_ints(10**230 + 17, 10**229 + 13)
    rb = TritRatio.from_ints(-(10**228 + 19), 3**40 * (10**180 + 7))
    fa = Fraction(10**230 + 17, 10**229 + 13)
    fb = Fraction(-(10**228 + 19), 3**40 * (10**180 + 7))
    _check((ra + rb).to_fraction() == fa + fb, "230-digit TritRatio add mismatch")
    _check((ra * rb).to_fraction() == fa * fb, "230-digit TritRatio mul mismatch")
    _check((ra / rb).to_fraction() == fa / fb, "230-digit TritRatio div mismatch")
    elapsed = time.monotonic() - t0
    _check(elapsed < 10.0, f"230-digit ternary suite too slow: {elapsed:.2f}s")


def test_trit2_micro_ratio_all_16_states() -> None:
    defined_count = 0
    singular_count = 0
    hinge_count = 0
    saturated_count = 0

    for bits in range(16):
        n_lane = bits & 0b11
        d_lane = (bits >> 2) & 0b11
        m = Trit2MicroRatio(num_lane=n_lane, den_lane=d_lane)
        _check(Trit2MicroRatio.from_bits(bits) == m, f"from_bits mismatch at {bits}")
        _check(m.raw4 == bits and m.to_bits() == bits, f"raw4/to_bits mismatch at {bits}")
        _check(m.num_signed == trit_lane_to_signed(n_lane), f"num_signed at {bits}")
        _check(m.den_signed == trit_lane_to_signed(d_lane), f"den_signed at {bits}")
        _check(m.num_is_hinge == (n_lane == TRIT_HINGE), f"num_is_hinge at {bits}")
        _check(m.den_is_hinge == (d_lane == TRIT_HINGE), f"den_is_hinge at {bits}")
        _check(m.has_hinge == (m.num_is_hinge or m.den_is_hinge), f"has_hinge at {bits}")
        _check(m.is_saturated == (m.num_is_hinge and m.den_is_hinge), f"is_saturated at {bits}")
        _check(m.is_defined == (not m.is_singular), f"defined/singular partition at {bits}")

        if m.is_defined:
            defined_count += 1
        else:
            singular_count += 1
        if m.has_hinge:
            hinge_count += 1
        if m.is_saturated:
            saturated_count += 1

        cp = m.to_chiral_pair()
        _check(cp == ChiralPair4(n_lane, d_lane), f"to_chiral_pair mismatch at {bits}")
        _check(Trit2MicroRatio.from_chiral_pair(cp) == m, f"from_chiral_pair mismatch at {bits}")

        neg_m = m.neg()
        _check(neg_m == -m and neg_m.neg() == m, f"neg involution failed at {bits}")
        _check(
            neg_m.num_lane == negate_trit_lane(n_lane) and neg_m.den_lane == d_lane,
            f"neg lanes mismatch at {bits}",
        )

        rec_m = m.reciprocal()
        _check(
            rec_m == Trit2MicroRatio(d_lane, n_lane) and rec_m.reciprocal() == m,
            f"reciprocal mismatch at {bits}",
        )

        if m.is_defined:
            ev = m.exact_value()
            _check(ev == Fraction(m.num_signed, m.den_signed), f"exact_value mismatch at {bits}")
            _check(neg_m.exact_value() == -ev, f"neg exact_value mismatch at {bits}")
            tr = m.to_trit_ratio()
            _check(tr.to_fraction() == ev, f"to_trit_ratio value mismatch at {bits}")
            expected_nh = 0b01 if m.num_is_hinge else 0
            _check(
                tr.num_hinge_mask == expected_nh and tr.den_hinge_mask == 0,
                f"to_trit_ratio hinge preservation failed at {bits}",
            )
            if ev != 0:
                _check(rec_m.exact_value() == Fraction(1, 1) / ev, f"reciprocal value at {bits}")
        else:
            _check_raises(ZeroDivisionError, m.exact_value)
            _check_raises(ZeroDivisionError, m.to_trit_ratio)

    _check(defined_count == 8 and singular_count == 8, "expected 8 defined and 8 singular states")
    _check(hinge_count == 7 and saturated_count == 1, "expected 7 hinge and 1 saturated state")


def test_trit_ratio_field_laws_and_metadata_preservation() -> None:
    _check(TritRatio.ZERO == TritRatio.zero() == TritRatio.from_ints(0, 7), "ZERO canonicalization")
    _check(TritRatio.ONE == TritRatio.one() == TritRatio.from_ints(-9, -9), "ONE canonicalization")
    _check(TritRatio.from_ints(0, -5).canonical_pair() == ("0", "1"), "zero canonical_pair")
    _check(TritRatio.from_ints(0, -5).canonical_str() == "0", "zero canonical_str")
    _check(TritRatio.from_ints(6, -9).canonical_pair() == ("-2", "3"), "reduced neg canonical_pair")
    _check(TritRatio.from_ints(6, -9).canonical_str() == "-2/3", "reduced neg canonical_str")
    _check(TritRatio.from_ints(-12, -4).canonical_str() == "3", "integer canonical_str")
    _check(TritRatio.from_ints(-12, -4).to_int_pair() == (3, 1), "to_int_pair")
    _check(not bool(TritRatio.ZERO) and bool(TritRatio.ONE), "__bool__ on TritRatio")

    # Exhaustive rational grid covering coprime denominators, Henrici g > 1 (both g2 == 1 and g2 > 1),
    # cross-cancellable fractions, negatives, zero, and unit fractions
    raw_pairs = [
        (0, 1),
        (1, 1),
        (-1, 1),
        (1, 2),
        (-1, 2),
        (1, 3),
        (-2, 3),
        (5, 6),
        (-5, 6),
        (1, 6),
        (7, 10),
        (3, 10),
        (-7, 12),
        (11, 15),
        (14, 27),
        (-25, 36),
        (35, 18),
    ]
    ratios = [TritRatio.from_ints(n, d) for n, d in raw_pairs]
    fracs = [Fraction(n, d) for n, d in raw_pairs]

    for i, (ra, fa) in enumerate(zip(ratios, fracs)):
        _check(TritRatio.from_fraction(fa) == ra, f"from_fraction mismatch at {i}")
        _check(ra.to_fraction() == fa, f"to_fraction mismatch at {i}")
        _check((-ra).to_fraction() == -fa, f"neg mismatch at {i}")
        _check(abs(ra).to_fraction() == abs(fa), f"abs mismatch at {i}")
        _check(ra.sign() == (1 if fa > 0 else (-1 if fa < 0 else 0)), f"sign mismatch at {i}")
        _check(ra.den.sign() > 0, f"den must be positive at {i}")
        _check(ra.num.gcd(ra.den) == TritWord.ONE, f"num/den must be coprime at {i}")
        if fa != 0:
            _check(ra.reciprocal().to_fraction() == Fraction(1, 1) / fa, f"reciprocal at {i}")
            _check((ra * ra.reciprocal()) == TritRatio.ONE, f"multiplicative inverse at {i}")
        else:
            _check_raises(ZeroDivisionError, ra.reciprocal)

        for j, (rb, fb) in enumerate(zip(ratios, fracs)):
            s = ra + rb
            d = ra - rb
            p = ra * rb
            _check(s.to_fraction() == fa + fb, f"add mismatch ({fa}, {fb})")
            _check(d.to_fraction() == fa - fb, f"sub mismatch ({fa}, {fb})")
            _check(p.to_fraction() == fa * fb, f"mul mismatch ({fa}, {fb})")
            _check(s.den.sign() > 0 and s.num.gcd(s.den) == TritWord.ONE, "add reduced invariant")
            _check(p.den.sign() > 0 and p.num.gcd(p.den) == TritWord.ONE, "mul reduced invariant")
            if fb != 0:
                q = ra / rb
                _check(q.to_fraction() == fa / fb, f"div mismatch ({fa}, {fb})")
                _check(q.den.sign() > 0 and q.num.gcd(q.den) == TritWord.ONE, "div reduced invariant")
            else:
                _check_raises(ZeroDivisionError, lambda x=ra, y=rb: x / y)

            exp_cmp = 1 if fa > fb else (-1 if fa < fb else 0)
            _check(ra.cmp(rb) == exp_cmp, f"cmp mismatch ({fa}, {fb})")
            _check((ra == rb) == (fa == fb), f"== mismatch ({fa}, {fb})")
            _check((ra < rb) == (fa < fb), f"< mismatch ({fa}, {fb})")
            _check((ra <= rb) == (fa <= fb), f"<= mismatch ({fa}, {fb})")
            _check((ra > rb) == (fa > fb), f"> mismatch ({fa}, {fb})")
            _check((ra >= rb) == (fa >= fb), f">= mismatch ({fa}, {fb})")

    # Distributivity & associativity spot checks
    r1, r2, r3 = TritRatio.from_ints(7, 12), TritRatio.from_ints(-5, 18), TritRatio.from_ints(11, 30)
    _check((r1 + r2) + r3 == r1 + (r2 + r3), "addition associativity")
    _check((r1 * r2) * r3 == r1 * (r2 * r3), "multiplication associativity")
    _check(r1 * (r2 + r3) == (r1 * r2) + (r1 * r3), "distributivity")

    # Hinge metadata preservation, value equality vs structural_eq, and with_cleared_metadata
    w_num_hinge = TritWord.from_symbols("+H+")  # +9 + 0 + 1 = +10, hinge at lane 1 (0b0100)
    w_den_hinge = TritWord.from_symbols("H++")  # +3 + 1 = +4, hinge at lane 2 (0b010000)
    rh1 = TritRatio(w_num_hinge, w_den_hinge)
    _check(rh1.to_int_pair() == (5, 2), f"expected (5, 2), got {rh1.to_int_pair()}")
    _check(rh1.num_hinge_mask == 0b01_00, "num_hinge_mask lost")
    _check(rh1.den_hinge_mask == 0b01_00_00, "den_hinge_mask lost")
    _check(rh1.has_hinge, "has_hinge must be True")

    clean = rh1.with_cleared_metadata()
    _check(not clean.has_hinge, "with_cleared_metadata must zero masks")
    _check(rh1 == clean and hash(rh1) == hash(clean), "__eq__/__hash__ must compare exact value")
    _check(not rh1.structural_eq(clean), "structural_eq must distinguish hinge metadata")
    _check(rh1.structural_eq(rh1), "structural_eq reflexive")

    rh_neg = -rh1
    _check(
        rh_neg.num_hinge_mask == 0b01_00 and rh_neg.den_hinge_mask == 0b01_00_00,
        "neg must preserve hinge masks",
    )
    rh_rec = rh1.reciprocal()
    _check(
        rh_rec.num_hinge_mask == 0b01_00_00 and rh_rec.den_hinge_mask == 0b01_00,
        "reciprocal must swap num/den hinge masks",
    )
    _check(rh_rec.reciprocal().structural_eq(rh1), "reciprocal involution must preserve metadata")

    rh2 = TritRatio.from_ints(3, 4, num_hinge_mask=0b01, den_hinge_mask=0b01_00)
    rh_sum = rh1 + rh2
    _check(rh_sum.to_fraction() == Fraction(5, 2) + Fraction(3, 4), "hinged add value")
    _check(
        rh_sum.num_hinge_mask == (0b01_00 | 0b01)
        and rh_sum.den_hinge_mask == (0b01_00_00 | 0b01_00),
        "add must union hinge metadata",
    )
    rh_prod = rh1 * rh2
    _check(rh_prod.to_fraction() == Fraction(15, 8), "hinged mul value")
    _check(
        rh_prod.num_hinge_mask == (0b01_00 | 0b01)
        and rh_prod.den_hinge_mask == (0b01_00_00 | 0b01_00),
        "mul must union hinge metadata",
    )
    rh_div = rh1 / rh2
    _check(rh_div.to_fraction() == Fraction(10, 3), "hinged div value")
    _check(
        rh_div.num_hinge_mask == (0b01_00 | 0b01_00)
        and rh_div.den_hinge_mask == (0b01_00_00 | 0b01),
        "div must propagate swapped divisor hinge metadata",
    )

    # Fail-closed errors on TritRatio
    _check_raises(ZeroDivisionError, lambda: TritRatio(TritWord.ONE, TritWord.ZERO))
    _check_raises(ZeroDivisionError, lambda: TritRatio(TritWord.ONE, TritWord(TRIT_HINGE, 1)))
    _check_raises(ZeroDivisionError, lambda: TritRatio.from_ints(1, 0))
    _check_raises(TypeError, lambda: TritRatio.from_ints(True, 1))
    _check_raises(TypeError, lambda: TritRatio.from_ints(1, 2.0))  # type: ignore[arg-type]
    _check_raises(TypeError, lambda: TritRatio.from_fraction(0.5))  # type: ignore[arg-type]
    _check_raises(ValueError, lambda: TritRatio.from_ints(1, 2, num_hinge_mask=0b10))
    _check_raises(ValueError, lambda: TritRatio.from_ints(1, 2, den_hinge_mask=-1))
    _check_raises(TypeError, lambda: TritRatio.ONE + 1)  # type: ignore[operator]
    _check_raises(TypeError, lambda: TritRatio.ONE * 1.5)  # type: ignore[operator]
    _check_raises(TypeError, lambda: TritRatio.ONE / 2)  # type: ignore[operator]

    # Cancellation to zero preserves hinge metadata for both den == 1 and den > 1
    rh_int = TritRatio.from_ints(5, 1, num_hinge_mask=0b01)
    cancel_int = rh_int + (-rh_int)
    _check(cancel_int == TritRatio.ZERO and cancel_int.num_hinge_mask == 0b01, "den==1 cancel metadata")
    cancel_frac = rh1 + (-rh1)
    _check(
        cancel_frac == TritRatio.ZERO
        and cancel_frac.num_hinge_mask == rh1.num_hinge_mask
        and cancel_frac.den_hinge_mask == rh1.den_hinge_mask,
        "den>1 cancel metadata",
    )


def test_unbalanced_karatsuba_and_hinged_word_arithmetic() -> None:
    u_big = 3**199 + 17 * (3**100) - 54321
    u_mid = -(3**64 + 123456789)
    wu_big = TritWord.from_int(u_big)
    wu_mid = TritWord.from_int(u_mid)
    _check(wu_big.width == 200 and wu_mid.width == 65, "expected unbalanced Karatsuba widths")
    _check((wu_big * wu_mid).to_int() == u_big * u_mid, "unbalanced Karatsuba (200x65) failed")
    _check((wu_mid * wu_big).to_int() == u_mid * u_big, "unbalanced Karatsuba (65x200) failed")

    h_pos = TritWord.from_symbols("H+H+")  # +9 + 1 = +10
    h_neg = TritWord.from_symbols("H-0H")  # -9
    _check((h_pos + h_neg).to_int() == 1, "hinged add failed")
    _check((h_pos - h_neg).to_int() == 19, "hinged sub failed")
    _check((h_pos * h_neg).to_int() == -90, "hinged mul failed")
    _check(h_pos.gcd(h_neg).to_int() == 1, "hinged gcd failed")
    q, r = h_pos.divmod_floor(h_neg)
    _check((q.to_int(), r.to_int()) == divmod(10, -9), "hinged divmod_floor failed")
    _check(h_pos.cmp(TritWord.from_int(10)) == 0, "hinged cmp failed")
    _check_raises(ZeroDivisionError, lambda: h_pos.divmod_floor(TritWord.from_symbols("HH")))


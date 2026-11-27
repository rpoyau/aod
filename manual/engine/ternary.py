"""Canonical 2-bit and 4-bit Trit-on-Binary SWAR arithmetic and exact TritRatio.

Implements the Alpha Omega Dynamics (AOD) 2-bit ternary lane encoding preserving
``0b11`` (``0_H`` structural hinge / saturation / carry-barrier) alongside
``0b00`` (``0_D`` dwell), ``0b01`` (``+1`` alpha), and ``0b10`` (``-1`` omega),
with O(1) SWAR lane-swap negation, O(1) SWAR mask extraction, live dwell
compaction, fast byte-aligned radix-81 balanced base-3 codec, pure-SWAR
bit-plane arithmetic, 4-bit ``ChiralPair4``, 2-trit ``Trit2MicroRatio``, and
exact ``TritRatio`` backed strictly by ``TritWord`` registers.

All validation uses explicit TypeError/ValueError checks (zero bare assert)
and zero floating-point types, literals, or coercions.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
from typing import ClassVar, Final, Mapping, Sequence

from manual.engine.numeric import require, require_exact_int, require_type

# ---------------------------------------------------------------------------
# Canonical 2-Bit Lane Constants
# ---------------------------------------------------------------------------

TRIT_DWELL: Final[int] = 0b00
TRIT_ALPHA: Final[int] = 0b01
TRIT_OMEGA: Final[int] = 0b10
TRIT_HINGE: Final[int] = 0b11

TRIT_LANE_MASK: Final[int] = 0b11
TRIT_LANE_BITS: Final[int] = 2
VALID_TRIT_LANES: Final[frozenset[int]] = frozenset(
    {TRIT_DWELL, TRIT_ALPHA, TRIT_OMEGA, TRIT_HINGE}
)

_LANE_TO_SYMBOL: Final[tuple[str, str, str, str]] = ("0", "+", "-", "H")
_SYMBOL_TO_LANE: Final[dict[str, int]] = {
    "0": TRIT_DWELL,
    "+": TRIT_ALPHA,
    "-": TRIT_OMEGA,
    "H": TRIT_HINGE,
}

_RADIX4: Final[int] = 81
_HALF_RADIX4: Final[int] = 40
_CODEC_DC_THRESHOLD: Final[int] = 16
_KARATSUBA_THRESHOLD: Final[int] = 64


# ---------------------------------------------------------------------------
# Lane-Level Primitives
# ---------------------------------------------------------------------------


def validate_trit_lane(lane: int, *, name: str = "lane") -> int:
    """Validate that ``lane`` is an exact 2-bit trit lane in ``0..3`` (preserving ``0b11``)."""
    val = require_exact_int(lane, name=name)
    require(
        0 <= val <= TRIT_LANE_MASK,
        f"{name} must be a 2-bit trit lane in 0..3, got {val}",
    )
    return val


def trit_lane_to_signed(lane: int) -> int:
    """Decode a 2-bit lane to signed value ``lo - hi`` (``00->0, 01->+1, 10->-1, 11->0``)."""
    val = validate_trit_lane(lane, name="lane")
    return (val & 1) - ((val >> 1) & 1)


def signed_to_trit_lane(value: int) -> int:
    """Encode a signed balanced trit in ``{-1, 0, +1}`` into a canonical 2-bit lane."""
    val = require_exact_int(value, name="value")
    if val == 0:
        return TRIT_DWELL
    if val == 1:
        return TRIT_ALPHA
    if val == -1:
        return TRIT_OMEGA
    raise ValueError(f"signed trit value must be in {{-1, 0, 1}}, got {val}")


def negate_trit_lane(lane: int) -> int:
    """Swap polarity bits of a 2-bit lane, preserving ``00->00`` and ``11->11``."""
    val = validate_trit_lane(lane, name="lane")
    return ((val & 0b01) << 1) | ((val >> 1) & 0b01)


def trit_lane_symbol(lane: int) -> str:
    """Return canonical single-character symbol (``'0'``, ``'+'``, ``'-'``, ``'H'``)."""
    val = validate_trit_lane(lane, name="lane")
    return _LANE_TO_SYMBOL[val]


def symbol_to_trit_lane(symbol: str) -> int:
    """Parse canonical single-character trit symbol into its 2-bit lane value."""
    require_type(isinstance(symbol, str), f"symbol must be str, got {type(symbol).__name__}")
    if symbol not in _SYMBOL_TO_LANE:
        raise ValueError(f"invalid trit lane symbol: {symbol!r}")
    return _SYMBOL_TO_LANE[symbol]


# ---------------------------------------------------------------------------
# O(1) SWAR Mask & Bit-Plane Primitives
# ---------------------------------------------------------------------------


def _validate_width(width: int, *, name: str = "width") -> int:
    w = require_exact_int(width, name=name)
    require(w >= 0, f"{name} must be nonnegative, got {w}")
    return w


def _validate_packed_word(packed: int, width: int) -> tuple[int, int]:
    p = require_exact_int(packed, name="packed")
    w = _validate_width(width, name="width")
    require(p >= 0, f"packed must be nonnegative, got {p}")
    require(
        p.bit_length() <= 2 * w,
        f"packed value {p} exceeds width {w} ({2 * w} bits)",
    )
    return p, w


@lru_cache(maxsize=256)
def _swar_mask_01_cached(width: int) -> int:
    if width == 0:
        return 0
    return ((1 << (2 * width)) - 1) // 3


@lru_cache(maxsize=256)
def _swar_mask_11_cached(width: int) -> int:
    if width == 0:
        return 0
    return (1 << (2 * width)) - 1


def _validate_01_mask(mask: int, *, name: str) -> int:
    m = require_exact_int(mask, name=name)
    require(m >= 0, f"{name} must be nonnegative, got {m}")
    if m:
        lanes = (m.bit_length() + 1) >> 1
        m01 = _swar_mask_01_cached(lanes)
        require(
            (m & ~m01) == 0,
            f"{name} must only set 01-aligned even lane bits, got {m:#b}",
        )
    return m


def swar_mask_01(width: int) -> int:
    """Return ``width``-lane repeating ``0b01`` SWAR mask ``((1 << (2 * width)) - 1) // 3``."""
    return _swar_mask_01_cached(_validate_width(width, name="width"))


def swar_mask_10(width: int) -> int:
    """Return ``width``-lane repeating ``0b10`` SWAR mask ``swar_mask_01(width) << 1``."""
    return _swar_mask_01_cached(_validate_width(width, name="width")) << 1


def swar_mask_11(width: int) -> int:
    """Return ``width``-lane repeating ``0b11`` SWAR mask ``(1 << (2 * width)) - 1``."""
    return _swar_mask_11_cached(_validate_width(width, name="width"))


def swar_double_lane_mask(mask_01_hits: int) -> int:
    """Expand a 01-aligned lane hit mask to cover both bits of every hit 2-bit lane."""
    m = _validate_01_mask(mask_01_hits, name="mask_01_hits")
    return m | (m << 1)


def swar_negate(packed: int, width: int) -> int:
    """O(1) SWAR lane-swap negation preserving ``00->00`` and ``11->11``."""
    p, w = _validate_packed_word(packed, width)
    m01 = _swar_mask_01_cached(w)
    return ((p & m01) << 1) | ((p >> 1) & m01)


def swar_hinge_mask(packed: int, width: int, *, doubled: bool = False) -> int:
    """O(1) SWAR extraction of ``0b11`` (``0_H``) hinge lanes via ``(w & (w >> 1)) & mask_01``."""
    p, w = _validate_packed_word(packed, width)
    require_type(isinstance(doubled, bool), f"doubled must be bool, got {type(doubled).__name__}")
    m01 = _swar_mask_01_cached(w)
    hits = (p & (p >> 1)) & m01
    return (hits | (hits << 1)) if doubled else hits


def swar_alpha_mask(packed: int, width: int, *, doubled: bool = False) -> int:
    """O(1) SWAR extraction of ``0b01`` (``+1`` alpha) lanes via ``(w & ~(w >> 1)) & mask_01``."""
    p, w = _validate_packed_word(packed, width)
    require_type(isinstance(doubled, bool), f"doubled must be bool, got {type(doubled).__name__}")
    m01 = _swar_mask_01_cached(w)
    hits = (p & ~(p >> 1)) & m01
    return (hits | (hits << 1)) if doubled else hits


def swar_omega_mask(packed: int, width: int, *, doubled: bool = False) -> int:
    """O(1) SWAR extraction of ``0b10`` (``-1`` omega) lanes via ``((~w) & (w >> 1)) & mask_01``."""
    p, w = _validate_packed_word(packed, width)
    require_type(isinstance(doubled, bool), f"doubled must be bool, got {type(doubled).__name__}")
    m01 = _swar_mask_01_cached(w)
    hits = ((~p) & (p >> 1)) & m01
    return (hits | (hits << 1)) if doubled else hits


def swar_polar_mask(packed: int, width: int, *, doubled: bool = False) -> int:
    """O(1) SWAR extraction of polar (``01`` or ``10``) lanes via ``(w ^ (w >> 1)) & mask_01``."""
    p, w = _validate_packed_word(packed, width)
    require_type(isinstance(doubled, bool), f"doubled must be bool, got {type(doubled).__name__}")
    m01 = _swar_mask_01_cached(w)
    hits = (p ^ (p >> 1)) & m01
    return (hits | (hits << 1)) if doubled else hits


def swar_dwell_mask(packed: int, width: int, *, doubled: bool = False) -> int:
    """O(1) SWAR extraction of ``0b00`` (``0_D`` dwell) lanes via ``(~(w | (w >> 1))) & mask_01``."""
    p, w = _validate_packed_word(packed, width)
    require_type(isinstance(doubled, bool), f"doubled must be bool, got {type(doubled).__name__}")
    m01 = _swar_mask_01_cached(w)
    hits = (~(p | (p >> 1))) & m01
    return (hits | (hits << 1)) if doubled else hits


# ---------------------------------------------------------------------------
# Fast Byte-Aligned 4-Trit Radix-81 Codec Helpers
# ---------------------------------------------------------------------------


def _build_bal4_tables() -> tuple[tuple[int, ...], tuple[int, ...]]:
    bal4_to_byte: list[int] = [0] * _RADIX4
    for idx in range(_RADIX4):
        x = idx - _HALF_RADIX4
        byte_val = 0
        for lane_i in range(4):
            q, r = divmod(x + 1, 3)
            digit = r - 1
            x = q
            if digit == 1:
                lane = TRIT_ALPHA
            elif digit == -1:
                lane = TRIT_OMEGA
            else:
                lane = TRIT_DWELL
            byte_val |= lane << (2 * lane_i)
        bal4_to_byte[idx] = byte_val

    byte_to_bal4: list[int] = [0] * 256
    for byte_val in range(256):
        d0 = (byte_val & 1) - ((byte_val >> 1) & 1)
        d1 = ((byte_val >> 2) & 1) - ((byte_val >> 3) & 1)
        d2 = ((byte_val >> 4) & 1) - ((byte_val >> 5) & 1)
        d3 = ((byte_val >> 6) & 1) - ((byte_val >> 7) & 1)
        byte_to_bal4[byte_val] = d0 + 3 * d1 + 9 * d2 + 27 * d3

    return tuple(bal4_to_byte), tuple(byte_to_bal4)


_BAL4_TO_BYTE: Final[tuple[int, ...]]
_BYTE_TO_BAL4: Final[tuple[int, ...]]
_BAL4_TO_BYTE, _BYTE_TO_BAL4 = _build_bal4_tables()


@lru_cache(maxsize=256)
def _pow81(chunks: int) -> int:
    return _RADIX4**chunks


def _encode_small_chunks(value: int) -> int:
    packed = 0
    shift = 0
    x = value
    while x != 0:
        q, r = divmod(x + _HALF_RADIX4, _RADIX4)
        packed |= _BAL4_TO_BYTE[r] << shift
        shift += 8
        x = q
    return packed


def _encode_dc(value: int, chunks: int) -> int:
    if value == 0:
        return 0
    if chunks <= _CODEC_DC_THRESHOLD:
        return _encode_small_chunks(value)
    half = chunks >> 1
    base = _pow81(half)
    half_base = base >> 1
    hi_val, lo_off = divmod(value + half_base, base)
    lo_val = lo_off - half_base
    lo_packed = _encode_dc(lo_val, half)
    hi_packed = _encode_dc(hi_val, chunks - half)
    return lo_packed | (hi_packed << (8 * half))


def _decode_bytes_dc(raw: bytes, start: int, end: int) -> int:
    length = end - start
    if length <= _CODEC_DC_THRESHOLD:
        acc = 0
        for idx in range(end - 1, start - 1, -1):
            acc = acc * _RADIX4 + _BYTE_TO_BAL4[raw[idx]]
        return acc
    mid = start + (length >> 1)
    lo = _decode_bytes_dc(raw, start, mid)
    hi = _decode_bytes_dc(raw, mid, end)
    return lo + hi * _pow81(mid - start)


# ---------------------------------------------------------------------------
# Pure-SWAR Bit-Plane Balanced Base-3 Arithmetic Kernels
# ---------------------------------------------------------------------------


def _planes_width(a: int, o: int) -> int:
    u = a | o
    if u == 0:
        return 0
    return ((u.bit_length() - 1) >> 1) + 1


def _planes_sign(a: int, o: int) -> int:
    u = a | o
    if u == 0:
        return 0
    top_bit = u.bit_length() - 1
    return 1 if ((a >> top_bit) & 1) else -1


def _planes_cmp(a1: int, o1: int, a2: int, o2: int) -> int:
    p1 = a1 | (o1 << 1)
    p2 = a2 | (o2 << 1)
    diff = p1 ^ p2
    if diff == 0:
        return 0
    shift = (diff.bit_length() - 1) & ~1
    l1 = (p1 >> shift) & TRIT_LANE_MASK
    l2 = (p2 >> shift) & TRIT_LANE_MASK
    v1 = (l1 & 1) - (l1 >> 1)
    v2 = (l2 & 1) - (l2 >> 1)
    return 1 if v1 > v2 else -1


def _swar_add_planes(a1: int, o1: int, a2: int, o2: int) -> tuple[int, int]:
    """Exact pure-SWAR carry-propagating addition on 01-aligned disjoint bit-planes."""
    while a2 or o2:
        ca = a1 & a2
        co = o1 & o2
        ax = a1 ^ a2
        ox = o1 ^ o2
        cancel = ax & ox
        a1 = (ax ^ cancel) | co
        o1 = (ox ^ cancel) | ca
        a2 = ca << 2
        o2 = co << 2
    return a1, o1


def _swar_csa3_planes(
    a1: int, o1: int, a2: int, o2: int, a3: int, o3: int
) -> tuple[int, int, int, int]:
    """Zero-loop O(1) SWAR 3-to-2 balanced ternary carry-save adder."""
    c12_a = a1 & a2
    c12_o = o1 & o2
    ax12 = a1 ^ a2
    ox12 = o1 ^ o2
    k12 = ax12 & ox12
    s12_a = (ax12 ^ k12) | c12_o
    s12_o = (ox12 ^ k12) | c12_a

    c2_a = s12_a & a3
    c2_o = s12_o & o3
    ax = s12_a ^ a3
    ox = s12_o ^ o3
    k2 = ax & ox
    sa = (ax ^ k2) | c2_o
    so = (ox ^ k2) | c2_a

    ca_raw = c12_a | c2_a
    co_raw = c12_o | c2_o
    c_cancel = ca_raw & co_raw
    ca = ca_raw ^ c_cancel
    co = co_raw ^ c_cancel
    return sa, so, ca << 2, co << 2


def _swar_mul_csa_leaf(a1: int, o1: int, a2: int, o2: int) -> tuple[int, int]:
    """Multiply two balanced plane pairs using 3-to-2 SWAR CSA accumulation."""
    w1 = _planes_width(a1, o1)
    w2 = _planes_width(a2, o2)
    if w1 == 0 or w2 == 0:
        return 0, 0
    if w1 < w2:
        a_mul, o_mul = a1, o1
        a_big, o_big = a2, o2
    else:
        a_mul, o_mul = a2, o2
        a_big, o_big = a1, o1

    sum_a = 0
    sum_o = 0
    car_a = 0
    car_o = 0
    rem = a_mul | o_mul
    while rem:
        lsb = rem & -rem
        rem ^= lsb
        shift = lsb.bit_length() - 1
        if a_mul & lsb:
            pa = a_big << shift
            po = o_big << shift
        else:
            pa = o_big << shift
            po = a_big << shift
        sum_a, sum_o, car_a, car_o = _swar_csa3_planes(
            sum_a, sum_o, car_a, car_o, pa, po
        )
    return _swar_add_planes(sum_a, sum_o, car_a, car_o)


def _swar_mul_planes(a1: int, o1: int, a2: int, o2: int) -> tuple[int, int]:
    """Exact balanced base-3 SWAR multiplication (CSA leaves + Karatsuba > 64 trits)."""
    w1 = _planes_width(a1, o1)
    w2 = _planes_width(a2, o2)
    if w1 == 0 or w2 == 0:
        return 0, 0
    if w1 <= _KARATSUBA_THRESHOLD or w2 <= _KARATSUBA_THRESHOLD:
        return _swar_mul_csa_leaf(a1, o1, a2, o2)

    m = (w1 if w1 >= w2 else w2) >> 1
    shift = 2 * m
    mask_lo = _swar_mask_11_cached(m)

    a1_lo = a1 & mask_lo
    o1_lo = o1 & mask_lo
    a1_hi = a1 >> shift
    o1_hi = o1 >> shift

    a2_lo = a2 & mask_lo
    o2_lo = o2 & mask_lo
    a2_hi = a2 >> shift
    o2_hi = o2 >> shift

    z0_a, z0_o = _swar_mul_planes(a1_lo, o1_lo, a2_lo, o2_lo)
    z2_a, z2_o = _swar_mul_planes(a1_hi, o1_hi, a2_hi, o2_hi)

    s1_a, s1_o = _swar_add_planes(a1_lo, o1_lo, a1_hi, o1_hi)
    s2_a, s2_o = _swar_add_planes(a2_lo, o2_lo, a2_hi, o2_hi)
    z1_full_a, z1_full_o = _swar_mul_planes(s1_a, s1_o, s2_a, s2_o)

    # z1 = z1_full - z0 - z2 using 3-to-2 CSA + single carry-propagate add
    t_a, t_o, tc_a, tc_o = _swar_csa3_planes(
        z1_full_a, z1_full_o, z0_o, z0_a, z2_o, z2_a
    )
    z1_a, z1_o = _swar_add_planes(t_a, t_o, tc_a, tc_o)

    # Combine z0 + (z1 << shift) + (z2 << (2 * shift))
    r_a, r_o, rc_a, rc_o = _swar_csa3_planes(
        z0_a, z0_o, z1_a << shift, z1_o << shift, z2_a << (2 * shift), z2_o << (2 * shift)
    )
    return _swar_add_planes(r_a, r_o, rc_a, rc_o)


def _swar_divmod_pos_planes(
    ua: int, uo: int, va: int, vo: int
) -> tuple[int, int, int, int]:
    """Balanced non-restoring trit-by-trit division for ``U > 0, V > 0``.

    Returns ``(qa, qo, ra, ro)`` satisfying ``U = Q * V + R`` and ``0 <= R < V``.
    """
    cmp_uv = _planes_cmp(ua, uo, va, vo)
    if cmp_uv < 0:
        return 0, 0, ua, uo
    if cmp_uv == 0:
        return 1, 0, 0, 0

    wu = _planes_width(ua, uo)
    wv = _planes_width(va, vo)
    k = wu - wv + 1

    ra, ro = ua, uo
    tra, tro = _swar_add_planes(ua, uo, ua, uo)
    tva, tvo = _swar_add_planes(va, vo, va, vo)
    qa = 0
    qo = 0

    for i in range(k, -1, -1):
        shift = 2 * i
        sva = va << shift
        svo = vo << shift
        if _planes_cmp(tra, tro, sva, svo) > 0:
            qa |= 1 << shift
            ra, ro = _swar_add_planes(ra, ro, svo, sva)
            tra, tro = _swar_add_planes(tra, tro, tvo << shift, tva << shift)
        elif _planes_cmp(tra, tro, svo, sva) < 0:
            qo |= 1 << shift
            ra, ro = _swar_add_planes(ra, ro, sva, svo)
            tra, tro = _swar_add_planes(tra, tro, tva << shift, tvo << shift)

    if _planes_sign(ra, ro) < 0:
        ra, ro = _swar_add_planes(ra, ro, va, vo)
        qa, qo = _swar_add_planes(qa, qo, 0, 1)

    return qa, qo, ra, ro


def _swar_bal_rem_pos_planes(ua: int, uo: int, va: int, vo: int) -> tuple[int, int]:
    """Return balanced remainder magnitude ``|R| <= V // 2`` for ``U > 0, V > 0``."""
    cmp_uv = _planes_cmp(ua, uo, va, vo)
    if cmp_uv == 0:
        return 0, 0
    if cmp_uv < 0:
        tra, tro = _swar_add_planes(ua, uo, ua, uo)
        if _planes_cmp(tra, tro, va, vo) > 0:
            return _swar_add_planes(va, vo, uo, ua)
        return ua, uo

    wu = _planes_width(ua, uo)
    wv = _planes_width(va, vo)
    k = wu - wv + 1

    ra, ro = ua, uo
    tra, tro = _swar_add_planes(ua, uo, ua, uo)
    tva, tvo = _swar_add_planes(va, vo, va, vo)

    for i in range(k, -1, -1):
        shift = 2 * i
        sva = va << shift
        svo = vo << shift
        if _planes_cmp(tra, tro, sva, svo) > 0:
            ra, ro = _swar_add_planes(ra, ro, svo, sva)
            tra, tro = _swar_add_planes(tra, tro, tvo << shift, tva << shift)
        elif _planes_cmp(tra, tro, svo, sva) < 0:
            ra, ro = _swar_add_planes(ra, ro, sva, svo)
            tra, tro = _swar_add_planes(tra, tro, tva << shift, tvo << shift)

    if _planes_sign(ra, ro) < 0:
        return ro, ra
    return ra, ro


def _swar_gcd_planes(a1: int, o1: int, a2: int, o2: int) -> tuple[int, int]:
    """Exact pure-SWAR GCD using O(1) factor-of-3 stripping and balanced remainders."""
    if _planes_sign(a1, o1) < 0:
        a1, o1 = o1, a1
    if _planes_sign(a2, o2) < 0:
        a2, o2 = o2, a2

    u1 = a1 | o1
    u2 = a2 | o2
    if u1 == 0:
        return a2, o2
    if u2 == 0:
        return a1, o1

    tz1 = (u1 & -u1).bit_length() - 1
    tz2 = (u2 & -u2).bit_length() - 1
    common_shift = tz1 if tz1 < tz2 else tz2
    a1 >>= tz1
    o1 >>= tz1
    a2 >>= tz2
    o2 >>= tz2

    while a2 or o2:
        ra, ro = _swar_bal_rem_pos_planes(a1, o1, a2, o2)
        a1, o1 = a2, o2
        ru = ra | ro
        if ru:
            tz = (ru & -ru).bit_length() - 1
            a2 = ra >> tz
            o2 = ro >> tz
        else:
            a2 = 0
            o2 = 0

    return a1 << common_shift, o1 << common_shift


def _swar_div_exact_pos_planes(
    xa: int, xo: int, ga: int, go: int
) -> tuple[int, int]:
    """Exact division of signed ``X`` by positive divisor ``G > 0`` with zero remainder."""
    if xa == 0 and xo == 0:
        return 0, 0
    if ga == 1 and go == 0:
        return xa, xo
    sx = _planes_sign(xa, xo)
    ua, uo = (xo, xa) if sx < 0 else (xa, xo)
    qa, qo, ra, ro = _swar_divmod_pos_planes(ua, uo, ga, go)
    require(ra == 0 and ro == 0, "exact balanced ternary division produced non-zero remainder")
    return (qo, qa) if sx < 0 else (qa, qo)


def _planes_to_canonical_word(a: int, o: int) -> TritWord:
    packed = a | (o << 1)
    if packed == 0:
        return TritWord.ZERO
    width = ((packed.bit_length() - 1) >> 1) + 1
    return TritWord(packed=packed, width=width)


# ---------------------------------------------------------------------------
# 4-Bit Chiral-Hinge Lane Container
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ChiralPair4:
    """Immutable 4-bit chiral-hinge container holding two 2-bit trit lanes."""

    lo_lane: int
    hi_lane: int

    def __post_init__(self) -> None:
        validate_trit_lane(self.lo_lane, name="lo_lane")
        validate_trit_lane(self.hi_lane, name="hi_lane")

    @property
    def raw4(self) -> int:
        return (self.hi_lane << TRIT_LANE_BITS) | self.lo_lane

    @property
    def net_charge(self) -> int:
        return trit_lane_to_signed(self.lo_lane) + trit_lane_to_signed(self.hi_lane)

    @property
    def has_hinge(self) -> bool:
        return self.lo_lane == TRIT_HINGE or self.hi_lane == TRIT_HINGE

    @property
    def is_saturated(self) -> bool:
        return self.lo_lane == TRIT_HINGE and self.hi_lane == TRIT_HINGE

    def chiral_flip(self) -> ChiralPair4:
        """O(1) SWAR lane polarity flip preserving ``0_D`` (``00``) and ``0_H`` (``11``)."""
        return ChiralPair4.from_bits(swar_negate(self.raw4, 2))

    def __neg__(self) -> ChiralPair4:
        return self.chiral_flip()

    def to_bits(self) -> int:
        return self.raw4

    @classmethod
    def from_bits(cls, bits: int) -> ChiralPair4:
        val = require_exact_int(bits, name="bits")
        require(0 <= val <= 0b1111, f"bits must be a 4-bit integer in 0..15, got {val}")
        return cls(
            lo_lane=val & TRIT_LANE_MASK,
            hi_lane=(val >> TRIT_LANE_BITS) & TRIT_LANE_MASK,
        )

    @classmethod
    def from_lanes(cls, lo_lane: int, hi_lane: int) -> ChiralPair4:
        return cls(
            lo_lane=validate_trit_lane(lo_lane, name="lo_lane"),
            hi_lane=validate_trit_lane(hi_lane, name="hi_lane"),
        )

    def to_trit_word(self) -> TritWord:
        return TritWord(packed=self.raw4, width=2)

    @classmethod
    def from_trit_word(cls, word: TritWord) -> ChiralPair4:
        require_type(isinstance(word, TritWord), f"word must be TritWord, got {type(word).__name__}")
        require(
            word.width <= 2,
            f"TritWord width must be <= 2 to convert to ChiralPair4, got {word.width}",
        )
        return cls.from_bits(word.packed)


# ---------------------------------------------------------------------------
# Arbitrary-Width Packed 2-Bit Word & Barrier Add Result
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class BarrierAddResult:
    """Result of carry-barrier addition preserving ``0_H`` (``11``) structural hinges."""

    result: TritWord
    hinge_mask: int
    blocked_alpha_mask: int
    blocked_omega_mask: int

    def __post_init__(self) -> None:
        require_type(
            isinstance(self.result, TritWord),
            f"result must be TritWord, got {type(self.result).__name__}",
        )
        _validate_01_mask(self.hinge_mask, name="hinge_mask")
        _validate_01_mask(self.blocked_alpha_mask, name="blocked_alpha_mask")
        _validate_01_mask(self.blocked_omega_mask, name="blocked_omega_mask")

    @property
    def blocked_carry_mask(self) -> int:
        return self.blocked_alpha_mask | self.blocked_omega_mask

    @property
    def had_blocked_carry(self) -> bool:
        return (self.blocked_alpha_mask | self.blocked_omega_mask) != 0


@dataclass(frozen=True, slots=True)
class TritWord:
    """Immutable arbitrary-width packed 2-bit Trit-on-Binary register."""

    packed: int
    width: int

    ZERO: ClassVar[TritWord]
    ONE: ClassVar[TritWord]
    NEG_ONE: ClassVar[TritWord]

    def __post_init__(self) -> None:
        _validate_packed_word(self.packed, self.width)

    # --- Constructors -------------------------------------------------------

    @classmethod
    def zero(cls, width: int = 1) -> TritWord:
        w = _validate_width(width, name="width")
        return cls.ZERO if w == 1 else cls(packed=0, width=w)

    @classmethod
    def one(cls) -> TritWord:
        return cls.ONE

    @classmethod
    def neg_one(cls) -> TritWord:
        return cls.NEG_ONE

    @classmethod
    def from_int(cls, value: int) -> TritWord:
        n = require_exact_int(value, name="value")
        if n == 0:
            return cls.ZERO
        if n == 1:
            return cls.ONE
        if n == -1:
            return cls.NEG_ONE

        abs_n = -n if n < 0 else n
        if abs_n.bit_length() <= 100:
            packed = _encode_small_chunks(n)
        else:
            chunks = _CODEC_DC_THRESHOLD
            while abs_n > (_pow81(chunks) >> 1):
                chunks <<= 1
            packed = _encode_dc(n, chunks)

        width = ((packed.bit_length() - 1) >> 1) + 1
        return cls(packed=packed, width=width)

    @classmethod
    def from_lanes(cls, lanes: Sequence[int], *, msb_first: bool = False) -> TritWord:
        require_type(
            isinstance(lanes, Sequence) and not isinstance(lanes, (str, bytes, bytearray)),
            f"lanes must be a sequence of 2-bit int lanes, got {type(lanes).__name__}",
        )
        require_type(
            isinstance(msb_first, bool),
            f"msb_first must be bool, got {type(msb_first).__name__}",
        )
        ordered = reversed(lanes) if msb_first else lanes
        packed = 0
        count = 0
        for idx, lane in enumerate(ordered):
            val = validate_trit_lane(lane, name=f"lanes[{idx}]")
            packed |= val << (2 * idx)
            count = idx + 1
        return cls(packed=packed, width=count)

    @classmethod
    def from_symbols(cls, text: str, *, msb_first: bool = True) -> TritWord:
        require_type(isinstance(text, str), f"text must be str, got {type(text).__name__}")
        require_type(
            isinstance(msb_first, bool),
            f"msb_first must be bool, got {type(msb_first).__name__}",
        )
        chars = reversed(text) if msb_first else text
        packed = 0
        for idx, ch in enumerate(chars):
            packed |= symbol_to_trit_lane(ch) << (2 * idx)
        return cls(packed=packed, width=len(text))

    @classmethod
    def from_packed_pair(cls, pair: Sequence[int]) -> TritWord:
        require_type(
            isinstance(pair, (tuple, list)),
            f"pair must be a 2-element tuple or list, got {type(pair).__name__}",
        )
        require(len(pair) == 2, f"pair must have length 2, got {len(pair)}")
        return cls(packed=pair[0], width=pair[1])

    @classmethod
    def from_packed_dict(cls, data: Mapping[str, object]) -> TritWord:
        require_type(isinstance(data, Mapping), f"data must be Mapping, got {type(data).__name__}")
        allowed = {"packed", "width", "symbols", "hinge_mask"}
        extra = set(data.keys()) - allowed
        require(not extra, f"unexpected keys in packed dict: {sorted(extra)}")
        require("packed" in data and "width" in data, "packed dict requires 'packed' and 'width'")
        word = cls(packed=data["packed"], width=data["width"])  # type: ignore[arg-type]
        if "symbols" in data:
            syms = data["symbols"]
            require_type(isinstance(syms, str), f"symbols must be str, got {type(syms).__name__}")
            expected_syms = word.to_symbols(msb_first=True)
            require(
                syms == expected_syms,
                f"symbols mismatch in packed dict: got {syms!r}, expected {expected_syms!r}",
            )
        if "hinge_mask" in data:
            hm = require_exact_int(data["hinge_mask"], name="hinge_mask")
            require(
                hm == word.hinge_mask,
                f"hinge_mask mismatch in packed dict: got {hm}, expected {word.hinge_mask}",
            )
        return word

    @classmethod
    def from_chiral_pairs(
        cls,
        pairs: Sequence[ChiralPair4],
        *,
        width: int | None = None,
    ) -> TritWord:
        require_type(
            isinstance(pairs, Sequence) and not isinstance(pairs, (str, bytes, bytearray)),
            f"pairs must be a sequence of ChiralPair4, got {type(pairs).__name__}",
        )
        packed = 0
        for idx, pair in enumerate(pairs):
            require_type(
                isinstance(pair, ChiralPair4),
                f"pairs[{idx}] must be ChiralPair4, got {type(pair).__name__}",
            )
            packed |= pair.raw4 << (4 * idx)
        w = 2 * len(pairs) if width is None else _validate_width(width, name="width")
        return cls(packed=packed, width=w)

    # --- O(1) SWAR Masks & Lane Counts -------------------------------------

    @property
    def dwell_mask(self) -> int:
        m01 = _swar_mask_01_cached(self.width)
        return (~(self.packed | (self.packed >> 1))) & m01

    @property
    def alpha_mask(self) -> int:
        m01 = _swar_mask_01_cached(self.width)
        return (self.packed & ~(self.packed >> 1)) & m01

    @property
    def omega_mask(self) -> int:
        m01 = _swar_mask_01_cached(self.width)
        return ((~self.packed) & (self.packed >> 1)) & m01

    @property
    def polar_mask(self) -> int:
        m01 = _swar_mask_01_cached(self.width)
        return (self.packed ^ (self.packed >> 1)) & m01

    @property
    def hinge_mask(self) -> int:
        m01 = _swar_mask_01_cached(self.width)
        return (self.packed & (self.packed >> 1)) & m01

    @property
    def has_hinge(self) -> bool:
        return self.hinge_mask != 0

    @property
    def dwell_count(self) -> int:
        return self.dwell_mask.bit_count()

    @property
    def alpha_count(self) -> int:
        return self.alpha_mask.bit_count()

    @property
    def omega_count(self) -> int:
        return self.omega_mask.bit_count()

    @property
    def polar_count(self) -> int:
        return self.polar_mask.bit_count()

    @property
    def hinge_count(self) -> int:
        return self.hinge_mask.bit_count()

    def _to_planes(self) -> tuple[int, int]:
        m01 = _swar_mask_01_cached(self.width)
        w = self.packed
        w1 = w >> 1
        return (w & ~w1) & m01, ((~w) & w1) & m01

    # --- O(1) SWAR Operations & Live Dwell Compaction -----------------------

    def neg(self) -> TritWord:
        """O(1) SWAR lane-swap negation preserving ``00->00``, ``11->11``, and width."""
        m01 = _swar_mask_01_cached(self.width)
        neg_packed = ((self.packed & m01) << 1) | ((self.packed >> 1) & m01)
        return TritWord(packed=neg_packed, width=self.width)

    def sign(self) -> int:
        """O(1) SWAR exact sign in ``{-1, 0, +1}``."""
        p = self.polar_mask
        if p == 0:
            return 0
        top_bit = p.bit_length() - 1
        return 1 if ((self.packed >> top_bit) & 1) else -1

    def abs_word(self) -> TritWord:
        """O(1) SWAR magnitude word preserving ``0_H`` hinges and width."""
        return self.neg() if self.sign() < 0 else self

    def cmp(self, other: TritWord) -> int:
        """O(1) SWAR exact numeric comparison returning ``-1``, ``0``, or ``+1``."""
        require_type(
            isinstance(other, TritWord),
            f"other must be TritWord, got {type(other).__name__}",
        )
        p1 = self.polar_mask
        p2 = other.polar_mask
        c1 = self.packed & (p1 | (p1 << 1))
        c2 = other.packed & (p2 | (p2 << 1))
        diff = c1 ^ c2
        if diff == 0:
            return 0
        shift = (diff.bit_length() - 1) & ~1
        l1 = (c1 >> shift) & TRIT_LANE_MASK
        l2 = (c2 >> shift) & TRIT_LANE_MASK
        v1 = (l1 & 1) - (l1 >> 1)
        v2 = (l2 & 1) - (l2 >> 1)
        return 1 if v1 > v2 else -1

    def same_value(self, other: TritWord) -> bool:
        """Return True iff ``self`` and ``other`` have equal balanced base-3 integer value."""
        return self.cmp(other) == 0

    def to_canonical(self) -> TritWord:
        """Return minimal canonical balanced base-3 word (clearing ``0_H`` and leading ``0_D``)."""
        p = self.polar_mask
        if p == 0:
            return TritWord.ZERO
        clean = self.packed & (p | (p << 1))
        width = ((p.bit_length() - 1) >> 1) + 1
        return TritWord(packed=clean, width=width)

    def burn_contiguous_dwell(self, *, keep_single_dwell: bool = True) -> TritWord:
        """Live dwell compaction (``xxxxx->x``) retaining all ``0_H`` hinges and polar traces.

        When ``keep_single_dwell=True``, every maximal contiguous run of ``0_D`` (``00``)
        lanes collapses to a single ``0_D`` lane while preserving every ``01``, ``10``,
        and ``11`` lane in exact order. When ``keep_single_dwell=False``, all ``0_D``
        lanes are removed while retaining all ``0_H`` hinges and polar lanes.
        """
        require_type(
            isinstance(keep_single_dwell, bool),
            f"keep_single_dwell must be bool, got {type(keep_single_dwell).__name__}",
        )
        if self.width == 0:
            return self
        m01 = _swar_mask_01_cached(self.width)
        d = (~(self.packed | (self.packed >> 1))) & m01
        if d == 0:
            return self
        if keep_single_dwell:
            redundant = d & (d << 2)
            if redundant == 0:
                return self
            keep_mask = (~redundant) & m01
        else:
            keep_mask = (~d) & m01

        out_packed = 0
        out_width = 0
        rem = keep_mask
        src = self.packed
        while rem:
            lsb = rem & -rem
            rem ^= lsb
            bit_pos = lsb.bit_length() - 1
            lane = (src >> bit_pos) & TRIT_LANE_MASK
            out_packed |= lane << (2 * out_width)
            out_width += 1
        return TritWord(packed=out_packed, width=out_width)

    # --- Fast Balanced Base-3 Decode ---------------------------------------

    def to_int(self) -> int:
        """Decode packed word into exact Python ``int`` (``0_D`` and ``0_H`` contribute 0)."""
        if self.packed == 0:
            return 0
        nbytes = (self.packed.bit_length() + 7) >> 3
        raw = self.packed.to_bytes(nbytes, "little")
        return _decode_bytes_dc(raw, 0, nbytes)

    # --- Pure-SWAR Exact Arithmetic & Carry-Barrier Addition ---------------

    def add(self, other: TritWord) -> TritWord:
        require_type(
            isinstance(other, TritWord),
            f"other must be TritWord, got {type(other).__name__}",
        )
        a1, o1 = self._to_planes()
        a2, o2 = other._to_planes()
        sa, so = _swar_add_planes(a1, o1, a2, o2)
        return _planes_to_canonical_word(sa, so)

    def sub(self, other: TritWord) -> TritWord:
        require_type(
            isinstance(other, TritWord),
            f"other must be TritWord, got {type(other).__name__}",
        )
        a1, o1 = self._to_planes()
        a2, o2 = other._to_planes()
        sa, so = _swar_add_planes(a1, o1, o2, a2)
        return _planes_to_canonical_word(sa, so)

    def add_hinge_barrier(self, other: TritWord) -> BarrierAddResult:
        """Add two words while blocking carries across ``0_H`` (``11``) structural hinges.

        Every lane marked ``11`` in either operand acts as an impassable carry-barrier
        and is preserved as ``11`` in ``result``. Blocked ``+1`` (alpha) and ``-1``
        (omega) carries/signals colliding with barrier lanes are recorded in
        ``blocked_alpha_mask`` and ``blocked_omega_mask``.
        """
        require_type(
            isinstance(other, TritWord),
            f"other must be TritWord, got {type(other).__name__}",
        )
        h_mask = self.hinge_mask | other.hinge_mask
        a1, o1 = self._to_planes()
        a2, o2 = other._to_planes()

        if h_mask == 0:
            sa, so = _swar_add_planes(a1, o1, a2, o2)
            return BarrierAddResult(
                result=_planes_to_canonical_word(sa, so),
                hinge_mask=0,
                blocked_alpha_mask=0,
                blocked_omega_mask=0,
            )

        nh = ~h_mask
        blocked_a = (a1 | a2) & h_mask
        blocked_o = (o1 | o2) & h_mask

        cur_a = a1 & nh
        cur_o = o1 & nh
        add_a = a2 & nh
        add_o = o2 & nh

        while add_a or add_o:
            ca = cur_a & add_a
            co = cur_o & add_o
            ax = cur_a ^ add_a
            ox = cur_o ^ add_o
            cancel = ax & ox
            cur_a = (ax ^ cancel) | co
            cur_o = (ox ^ cancel) | ca
            carry_a = ca << 2
            carry_o = co << 2
            blocked_a |= carry_a & h_mask
            blocked_o |= carry_o & h_mask
            add_a = carry_a & nh
            add_o = carry_o & nh

        res_packed = cur_a | (cur_o << 1) | h_mask | (h_mask << 1)
        res_width = ((res_packed.bit_length() - 1) >> 1) + 1 if res_packed else 1
        return BarrierAddResult(
            result=TritWord(packed=res_packed, width=res_width),
            hinge_mask=h_mask,
            blocked_alpha_mask=blocked_a,
            blocked_omega_mask=blocked_o,
        )

    def mul(self, other: TritWord) -> TritWord:
        require_type(
            isinstance(other, TritWord),
            f"other must be TritWord, got {type(other).__name__}",
        )
        a1, o1 = self._to_planes()
        a2, o2 = other._to_planes()
        pa, po = _swar_mul_planes(a1, o1, a2, o2)
        return _planes_to_canonical_word(pa, po)

    def divmod_floor(self, other: TritWord) -> tuple[TritWord, TritWord]:
        """Exact floor division and modulo agreeing with Python ``divmod(a, b)``."""
        require_type(
            isinstance(other, TritWord),
            f"other must be TritWord, got {type(other).__name__}",
        )
        da, do = other._to_planes()
        sd = _planes_sign(da, do)
        if sd == 0:
            raise ZeroDivisionError("TritWord division or modulo by zero")

        na, no = self._to_planes()
        sn = _planes_sign(na, no)
        if sn == 0:
            return TritWord.ZERO, TritWord.ZERO

        ua, uo = (no, na) if sn < 0 else (na, no)
        va, vo = (do, da) if sd < 0 else (da, do)
        qa, qo, ra, ro = _swar_divmod_pos_planes(ua, uo, va, vo)

        if sn > 0 and sd > 0:
            return _planes_to_canonical_word(qa, qo), _planes_to_canonical_word(ra, ro)
        if sn < 0 and sd < 0:
            return _planes_to_canonical_word(qa, qo), _planes_to_canonical_word(ro, ra)

        if ra == 0 and ro == 0:
            return _planes_to_canonical_word(qo, qa), TritWord.ZERO

        # Opposite signs with non-zero remainder: Q = -(Q_pos + 1)
        q1a, q1o = _swar_add_planes(qa, qo, 1, 0)
        q_word = _planes_to_canonical_word(q1o, q1a)
        if sn > 0:
            # + / -: R = R_pos - |D| < 0
            r_a, r_o = _swar_add_planes(ra, ro, vo, va)
        else:
            # - / +: R = |D| - R_pos > 0
            r_a, r_o = _swar_add_planes(va, vo, ro, ra)
        return q_word, _planes_to_canonical_word(r_a, r_o)

    def gcd(self, other: TritWord) -> TritWord:
        """Exact nonnegative greatest common divisor via pure-SWAR balanced base-3 GCD."""
        require_type(
            isinstance(other, TritWord),
            f"other must be TritWord, got {type(other).__name__}",
        )
        a1, o1 = self._to_planes()
        a2, o2 = other._to_planes()
        ga, go = _swar_gcd_planes(a1, o1, a2, o2)
        return _planes_to_canonical_word(ga, go)

    # --- Strict Dunders -----------------------------------------------------

    def __neg__(self) -> TritWord:
        return self.neg()

    def __pos__(self) -> TritWord:
        return self

    def __abs__(self) -> TritWord:
        return self.abs_word()

    def __int__(self) -> int:
        return self.to_int()

    def __bool__(self) -> bool:
        return self.polar_mask != 0

    def __len__(self) -> int:
        return self.width

    def __add__(self, other: object) -> TritWord:
        if isinstance(other, TritWord):
            return self.add(other)
        return NotImplemented

    def __sub__(self, other: object) -> TritWord:
        if isinstance(other, TritWord):
            return self.sub(other)
        return NotImplemented

    def __mul__(self, other: object) -> TritWord:
        if isinstance(other, TritWord):
            return self.mul(other)
        return NotImplemented

    def __floordiv__(self, other: object) -> TritWord:
        if isinstance(other, TritWord):
            return self.divmod_floor(other)[0]
        return NotImplemented

    def __mod__(self, other: object) -> TritWord:
        if isinstance(other, TritWord):
            return self.divmod_floor(other)[1]
        return NotImplemented

    def __divmod__(self, other: object) -> tuple[TritWord, TritWord]:
        if isinstance(other, TritWord):
            return self.divmod_floor(other)
        return NotImplemented

    def __lt__(self, other: object) -> bool:
        if isinstance(other, TritWord):
            return self.cmp(other) < 0
        return NotImplemented

    def __le__(self, other: object) -> bool:
        if isinstance(other, TritWord):
            return self.cmp(other) <= 0
        return NotImplemented

    def __gt__(self, other: object) -> bool:
        if isinstance(other, TritWord):
            return self.cmp(other) > 0
        return NotImplemented

    def __ge__(self, other: object) -> bool:
        if isinstance(other, TritWord):
            return self.cmp(other) >= 0
        return NotImplemented

    # --- Lane & Packed Serialization ----------------------------------------

    def lane_at(self, index: int) -> int:
        idx = require_exact_int(index, name="index")
        require(0 <= idx < self.width, f"lane index {idx} out of range for width {self.width}")
        return (self.packed >> (2 * idx)) & TRIT_LANE_MASK

    def lanes(self) -> tuple[int, ...]:
        return tuple((self.packed >> (2 * idx)) & TRIT_LANE_MASK for idx in range(self.width))

    def to_msb_lanes(self) -> tuple[int, ...]:
        return tuple(
            (self.packed >> (2 * idx)) & TRIT_LANE_MASK for idx in range(self.width - 1, -1, -1)
        )

    def to_symbols(self, *, msb_first: bool = True) -> str:
        require_type(
            isinstance(msb_first, bool),
            f"msb_first must be bool, got {type(msb_first).__name__}",
        )
        lane_seq = self.to_msb_lanes() if msb_first else self.lanes()
        return "".join(_LANE_TO_SYMBOL[lane] for lane in lane_seq)

    def to_packed_pair(self) -> tuple[int, int]:
        return (self.packed, self.width)

    def to_packed_dict(self) -> dict[str, int | str]:
        return {
            "packed": self.packed,
            "width": self.width,
            "symbols": self.to_symbols(msb_first=True),
            "hinge_mask": self.hinge_mask,
        }

    def to_chiral_pairs(self) -> tuple[ChiralPair4, ...]:
        pair_count = (self.width + 1) >> 1
        return tuple(
            ChiralPair4.from_bits((self.packed >> (4 * idx)) & 0b1111)
            for idx in range(pair_count)
        )


TritWord.ZERO = TritWord(packed=TRIT_DWELL, width=1)
TritWord.ONE = TritWord(packed=TRIT_ALPHA, width=1)
TritWord.NEG_ONE = TritWord(packed=TRIT_OMEGA, width=1)


# ---------------------------------------------------------------------------
# 2-Trit Micro-Ratio
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Trit2MicroRatio:
    """Immutable 2-trit micro-ratio preserving ``0b11`` (``0_H``) hinge/saturation lanes."""

    num_lane: int
    den_lane: int

    def __post_init__(self) -> None:
        validate_trit_lane(self.num_lane, name="num_lane")
        validate_trit_lane(self.den_lane, name="den_lane")

    @property
    def raw4(self) -> int:
        return (self.den_lane << TRIT_LANE_BITS) | self.num_lane

    @property
    def num_signed(self) -> int:
        return trit_lane_to_signed(self.num_lane)

    @property
    def den_signed(self) -> int:
        return trit_lane_to_signed(self.den_lane)

    @property
    def num_is_hinge(self) -> bool:
        return self.num_lane == TRIT_HINGE

    @property
    def den_is_hinge(self) -> bool:
        return self.den_lane == TRIT_HINGE

    @property
    def has_hinge(self) -> bool:
        return self.num_is_hinge or self.den_is_hinge

    @property
    def is_saturated(self) -> bool:
        return self.num_is_hinge and self.den_is_hinge

    @property
    def is_defined(self) -> bool:
        return self.den_signed != 0

    @property
    def is_singular(self) -> bool:
        return self.den_signed == 0

    def to_bits(self) -> int:
        return self.raw4

    @classmethod
    def from_bits(cls, bits: int) -> Trit2MicroRatio:
        val = require_exact_int(bits, name="bits")
        require(0 <= val <= 0b1111, f"bits must be a 4-bit integer in 0..15, got {val}")
        return cls(
            num_lane=val & TRIT_LANE_MASK,
            den_lane=(val >> TRIT_LANE_BITS) & TRIT_LANE_MASK,
        )

    def to_chiral_pair(self) -> ChiralPair4:
        return ChiralPair4(lo_lane=self.num_lane, hi_lane=self.den_lane)

    @classmethod
    def from_chiral_pair(cls, pair: ChiralPair4) -> Trit2MicroRatio:
        require_type(
            isinstance(pair, ChiralPair4),
            f"pair must be ChiralPair4, got {type(pair).__name__}",
        )
        return cls(num_lane=pair.lo_lane, den_lane=pair.hi_lane)

    def neg(self) -> Trit2MicroRatio:
        return Trit2MicroRatio(
            num_lane=negate_trit_lane(self.num_lane),
            den_lane=self.den_lane,
        )

    def __neg__(self) -> Trit2MicroRatio:
        return self.neg()

    def reciprocal(self) -> Trit2MicroRatio:
        return Trit2MicroRatio(num_lane=self.den_lane, den_lane=self.num_lane)

    def exact_value(self) -> Fraction:
        if self.is_singular:
            raise ZeroDivisionError("singular Trit2MicroRatio has zero denominator (0_D or 0_H)")
        return Fraction(self.num_signed, self.den_signed)

    def to_trit_ratio(self) -> TritRatio:
        if self.is_singular:
            raise ZeroDivisionError(
                "singular Trit2MicroRatio cannot convert to defined TritRatio"
            )
        return TritRatio(
            TritWord(packed=self.num_lane, width=1),
            TritWord(packed=self.den_lane, width=1),
        )


# ---------------------------------------------------------------------------
# Full Exact Arbitrary-Width Ternary Rational: TritRatio
# ---------------------------------------------------------------------------


class TritRatio:
    """Immutable exact rational backed strictly by coprime ``TritWord`` registers.

    Stores ``(_num, _den, _num_hinge_mask, _den_hinge_mask)`` with canonical
    positive coprime ``_den`` (and zero canonicalized as ``(TritWord.ZERO, TritWord.ONE)``).
    Never uses ``Fraction`` as a backing store; ``Fraction`` is used strictly at
    ``from_fraction`` / ``to_fraction`` conversion boundaries.
    """

    __slots__ = ("_num", "_den", "_num_hinge_mask", "_den_hinge_mask")

    ZERO: ClassVar[TritRatio]
    ONE: ClassVar[TritRatio]

    _num: TritWord
    _den: TritWord
    _num_hinge_mask: int
    _den_hinge_mask: int

    def __init__(
        self,
        num: TritWord,
        den: TritWord = TritWord.ONE,
        *,
        num_hinge_mask: int = 0,
        den_hinge_mask: int = 0,
    ) -> None:
        require_type(
            isinstance(num, TritWord),
            f"num must be TritWord, got {type(num).__name__}",
        )
        require_type(
            isinstance(den, TritWord),
            f"den must be TritWord, got {type(den).__name__}",
        )
        nh = num.hinge_mask | _validate_01_mask(num_hinge_mask, name="num_hinge_mask")
        dh = den.hinge_mask | _validate_01_mask(den_hinge_mask, name="den_hinge_mask")

        da, do = den._to_planes()
        ds = _planes_sign(da, do)
        if ds == 0:
            raise ZeroDivisionError("TritRatio denominator must be non-zero")

        na, no = num._to_planes()
        if ds < 0:
            na, no = no, na
            da, do = do, da

        if na == 0 and no == 0:
            canon_num = TritWord.ZERO
            canon_den = TritWord.ONE
        else:
            ga, go = _swar_gcd_planes(na, no, da, do)
            if not (ga == 1 and go == 0):
                na, no = _swar_div_exact_pos_planes(na, no, ga, go)
                da, do = _swar_div_exact_pos_planes(da, do, ga, go)
            canon_num = _planes_to_canonical_word(na, no)
            canon_den = _planes_to_canonical_word(da, do)

        object.__setattr__(self, "_num", canon_num)
        object.__setattr__(self, "_den", canon_den)
        object.__setattr__(self, "_num_hinge_mask", nh)
        object.__setattr__(self, "_den_hinge_mask", dh)

    @classmethod
    def _from_canonical(
        cls,
        num: TritWord,
        den: TritWord,
        num_hinge_mask: int = 0,
        den_hinge_mask: int = 0,
    ) -> TritRatio:
        inst = object.__new__(cls)
        object.__setattr__(inst, "_num", num)
        object.__setattr__(inst, "_den", den)
        object.__setattr__(inst, "_num_hinge_mask", num_hinge_mask)
        object.__setattr__(inst, "_den_hinge_mask", den_hinge_mask)
        return inst

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError("TritRatio is immutable")

    def __delattr__(self, name: str) -> None:
        raise AttributeError("TritRatio is immutable")

    # --- Properties ---------------------------------------------------------

    @property
    def num(self) -> TritWord:
        return self._num

    @property
    def den(self) -> TritWord:
        return self._den

    @property
    def num_hinge_mask(self) -> int:
        return self._num_hinge_mask

    @property
    def den_hinge_mask(self) -> int:
        return self._den_hinge_mask

    @property
    def has_hinge(self) -> bool:
        return (self._num_hinge_mask | self._den_hinge_mask) != 0

    # --- Constructors & Conversions -----------------------------------------

    @classmethod
    def zero(cls) -> TritRatio:
        return cls.ZERO

    @classmethod
    def one(cls) -> TritRatio:
        return cls.ONE

    @classmethod
    def from_ints(
        cls,
        num: int,
        den: int = 1,
        *,
        num_hinge_mask: int = 0,
        den_hinge_mask: int = 0,
    ) -> TritRatio:
        n = require_exact_int(num, name="num")
        d = require_exact_int(den, name="den")
        if d == 0:
            raise ZeroDivisionError("TritRatio denominator must be non-zero")
        return cls(
            TritWord.from_int(n),
            TritWord.from_int(d),
            num_hinge_mask=num_hinge_mask,
            den_hinge_mask=den_hinge_mask,
        )

    @classmethod
    def from_fraction(
        cls,
        value: Fraction,
        *,
        num_hinge_mask: int = 0,
        den_hinge_mask: int = 0,
    ) -> TritRatio:
        require_type(
            isinstance(value, Fraction),
            f"value must be Fraction, got {type(value).__name__}",
        )
        nh = _validate_01_mask(num_hinge_mask, name="num_hinge_mask")
        dh = _validate_01_mask(den_hinge_mask, name="den_hinge_mask")
        return cls._from_canonical(
            TritWord.from_int(value.numerator),
            TritWord.from_int(value.denominator),
            nh,
            dh,
        )

    def to_fraction(self) -> Fraction:
        return Fraction(self._num.to_int(), self._den.to_int())

    def to_int_pair(self) -> tuple[int, int]:
        return (self._num.to_int(), self._den.to_int())

    def canonical_pair(self) -> tuple[str, str]:
        return (str(self._num.to_int()), str(self._den.to_int()))

    def canonical_str(self) -> str:
        num_s, den_s = self.canonical_pair()
        return num_s if den_s == "1" else f"{num_s}/{den_s}"

    # --- Exact Arithmetic ---------------------------------------------------

    def neg(self) -> TritRatio:
        return TritRatio._from_canonical(
            self._num.neg(),
            self._den,
            self._num_hinge_mask,
            self._den_hinge_mask,
        )

    def abs_ratio(self) -> TritRatio:
        return TritRatio._from_canonical(
            self._num.abs_word(),
            self._den,
            self._num_hinge_mask,
            self._den_hinge_mask,
        )

    def reciprocal(self) -> TritRatio:
        ns = self._num.sign()
        if ns == 0:
            raise ZeroDivisionError("cannot take reciprocal of zero TritRatio")
        if ns > 0:
            new_num = self._den
            new_den = self._num
        else:
            new_num = self._den.neg()
            new_den = self._num.neg()
        return TritRatio._from_canonical(
            new_num,
            new_den,
            self._den_hinge_mask,
            self._num_hinge_mask,
        )

    def add(self, other: TritRatio) -> TritRatio:
        """Exact rational addition using Henrici pre-reduction on ``TritWord`` registers."""
        require_type(
            isinstance(other, TritRatio),
            f"other must be TritRatio, got {type(other).__name__}",
        )
        nh = self._num_hinge_mask | other._num_hinge_mask
        dh = self._den_hinge_mask | other._den_hinge_mask

        aa, ao = self._num._to_planes()
        ba, bo = self._den._to_planes()
        ca, co = other._num._to_planes()
        da, do = other._den._to_planes()

        if aa == 0 and ao == 0:
            return TritRatio._from_canonical(other._num, other._den, nh, dh)
        if ca == 0 and co == 0:
            return TritRatio._from_canonical(self._num, self._den, nh, dh)

        ga, go = _swar_gcd_planes(ba, bo, da, do)
        if ga == 1 and go == 0:
            p1a, p1o = _swar_mul_planes(aa, ao, da, do)
            p2a, p2o = _swar_mul_planes(ca, co, ba, bo)
            na, no = _swar_add_planes(p1a, p1o, p2a, p2o)
            if na == 0 and no == 0:
                return TritRatio._from_canonical(TritWord.ZERO, TritWord.ONE, nh, dh)
            den_a, den_o = _swar_mul_planes(ba, bo, da, do)
            return TritRatio._from_canonical(
                _planes_to_canonical_word(na, no),
                _planes_to_canonical_word(den_a, den_o),
                nh,
                dh,
            )

        b1a, b1o = _swar_div_exact_pos_planes(ba, bo, ga, go)
        d1a, d1o = _swar_div_exact_pos_planes(da, do, ga, go)
        p1a, p1o = _swar_mul_planes(aa, ao, d1a, d1o)
        p2a, p2o = _swar_mul_planes(ca, co, b1a, b1o)
        ta, to = _swar_add_planes(p1a, p1o, p2a, p2o)
        if ta == 0 and to == 0:
            return TritRatio._from_canonical(TritWord.ZERO, TritWord.ONE, nh, dh)

        g2a, g2o = _swar_gcd_planes(ta, to, ga, go)
        if g2a == 1 and g2o == 0:
            na, no = ta, to
            den_a, den_o = _swar_mul_planes(b1a, b1o, da, do)
        else:
            na, no = _swar_div_exact_pos_planes(ta, to, g2a, g2o)
            d2a, d2o = _swar_div_exact_pos_planes(da, do, g2a, g2o)
            den_a, den_o = _swar_mul_planes(b1a, b1o, d2a, d2o)
        return TritRatio._from_canonical(
            _planes_to_canonical_word(na, no),
            _planes_to_canonical_word(den_a, den_o),
            nh,
            dh,
        )

    def sub(self, other: TritRatio) -> TritRatio:
        require_type(
            isinstance(other, TritRatio),
            f"other must be TritRatio, got {type(other).__name__}",
        )
        return self.add(other.neg())

    def mul(self, other: TritRatio) -> TritRatio:
        """Exact rational multiplication using pre-multiply cross-cancellation."""
        require_type(
            isinstance(other, TritRatio),
            f"other must be TritRatio, got {type(other).__name__}",
        )
        nh = self._num_hinge_mask | other._num_hinge_mask
        dh = self._den_hinge_mask | other._den_hinge_mask

        aa, ao = self._num._to_planes()
        ca, co = other._num._to_planes()
        if (aa == 0 and ao == 0) or (ca == 0 and co == 0):
            return TritRatio._from_canonical(TritWord.ZERO, TritWord.ONE, nh, dh)

        ba, bo = self._den._to_planes()
        da, do = other._den._to_planes()

        g1a, g1o = _swar_gcd_planes(aa, ao, da, do)
        if not (g1a == 1 and g1o == 0):
            aa, ao = _swar_div_exact_pos_planes(aa, ao, g1a, g1o)
            da, do = _swar_div_exact_pos_planes(da, do, g1a, g1o)

        g2a, g2o = _swar_gcd_planes(ca, co, ba, bo)
        if not (g2a == 1 and g2o == 0):
            ca, co = _swar_div_exact_pos_planes(ca, co, g2a, g2o)
            ba, bo = _swar_div_exact_pos_planes(ba, bo, g2a, g2o)

        na, no = _swar_mul_planes(aa, ao, ca, co)
        den_a, den_o = _swar_mul_planes(ba, bo, da, do)
        return TritRatio._from_canonical(
            _planes_to_canonical_word(na, no),
            _planes_to_canonical_word(den_a, den_o),
            nh,
            dh,
        )

    def div(self, other: TritRatio) -> TritRatio:
        require_type(
            isinstance(other, TritRatio),
            f"other must be TritRatio, got {type(other).__name__}",
        )
        return self.mul(other.reciprocal())

    # --- Comparison, Equality & Metadata Control ----------------------------

    def sign(self) -> int:
        return self._num.sign()

    def cmp(self, other: TritRatio) -> int:
        require_type(
            isinstance(other, TritRatio),
            f"other must be TritRatio, got {type(other).__name__}",
        )
        s1 = self._num.sign()
        s2 = other._num.sign()
        if s1 != s2:
            return 1 if s1 > s2 else -1
        if s1 == 0:
            return 0
        if self._den == other._den:
            return self._num.cmp(other._num)
        lhs = self._num.mul(other._den)
        rhs = other._num.mul(self._den)
        return lhs.cmp(rhs)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TritRatio):
            return NotImplemented
        return self._num == other._num and self._den == other._den

    def __hash__(self) -> int:
        return hash((self._num, self._den))

    def structural_eq(self, other: TritRatio) -> bool:
        """Compare both exact rational value and preserved ``0_H`` hinge metadata masks."""
        require_type(
            isinstance(other, TritRatio),
            f"other must be TritRatio, got {type(other).__name__}",
        )
        return (
            self._num == other._num
            and self._den == other._den
            and self._num_hinge_mask == other._num_hinge_mask
            and self._den_hinge_mask == other._den_hinge_mask
        )

    def with_cleared_metadata(self) -> TritRatio:
        """Return an equal ``TritRatio`` with zeroed numerator/denominator hinge metadata masks."""
        if self._num_hinge_mask == 0 and self._den_hinge_mask == 0:
            return self
        return TritRatio._from_canonical(self._num, self._den, 0, 0)

    # --- Strict Dunders -----------------------------------------------------

    def __neg__(self) -> TritRatio:
        return self.neg()

    def __pos__(self) -> TritRatio:
        return self

    def __abs__(self) -> TritRatio:
        return self.abs_ratio()

    def __bool__(self) -> bool:
        return self._num.polar_mask != 0

    def __add__(self, other: object) -> TritRatio:
        if isinstance(other, TritRatio):
            return self.add(other)
        return NotImplemented

    def __sub__(self, other: object) -> TritRatio:
        if isinstance(other, TritRatio):
            return self.sub(other)
        return NotImplemented

    def __mul__(self, other: object) -> TritRatio:
        if isinstance(other, TritRatio):
            return self.mul(other)
        return NotImplemented

    def __truediv__(self, other: object) -> TritRatio:
        if isinstance(other, TritRatio):
            return self.div(other)
        return NotImplemented

    def __lt__(self, other: object) -> bool:
        if isinstance(other, TritRatio):
            return self.cmp(other) < 0
        return NotImplemented

    def __le__(self, other: object) -> bool:
        if isinstance(other, TritRatio):
            return self.cmp(other) <= 0
        return NotImplemented

    def __gt__(self, other: object) -> bool:
        if isinstance(other, TritRatio):
            return self.cmp(other) > 0
        return NotImplemented

    def __ge__(self, other: object) -> bool:
        if isinstance(other, TritRatio):
            return self.cmp(other) >= 0
        return NotImplemented

    def __str__(self) -> str:
        return self.canonical_str()

    def __repr__(self) -> str:
        if self.has_hinge:
            return (
                f"TritRatio(num={self._num!r}, den={self._den!r}, "
                f"num_hinge_mask={self._num_hinge_mask}, den_hinge_mask={self._den_hinge_mask})"
            )
        return f"TritRatio(num={self._num!r}, den={self._den!r})"


TritRatio.ZERO = TritRatio._from_canonical(TritWord.ZERO, TritWord.ONE, 0, 0)
TritRatio.ONE = TritRatio._from_canonical(TritWord.ONE, TritWord.ONE, 0, 0)


__all__ = [
    "BarrierAddResult",
    "ChiralPair4",
    "TRIT_ALPHA",
    "TRIT_DWELL",
    "TRIT_HINGE",
    "TRIT_LANE_BITS",
    "TRIT_LANE_MASK",
    "TRIT_OMEGA",
    "Trit2MicroRatio",
    "TritRatio",
    "TritWord",
    "VALID_TRIT_LANES",
    "negate_trit_lane",
    "signed_to_trit_lane",
    "swar_alpha_mask",
    "swar_double_lane_mask",
    "swar_dwell_mask",
    "swar_hinge_mask",
    "swar_mask_01",
    "swar_mask_10",
    "swar_mask_11",
    "swar_negate",
    "swar_omega_mask",
    "swar_polar_mask",
    "symbol_to_trit_lane",
    "trit_lane_symbol",
    "trit_lane_to_signed",
    "validate_trit_lane",
]

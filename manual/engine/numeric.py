"""Typed zero-float public input validators and exact integer/rational helpers.

All validation uses explicit TypeError/ValueError checks (zero bare assert),
so behavior is identical under normal Python and ``python3 -O``.
"""
from __future__ import annotations

from fractions import Fraction
import re

_EXACT_INT_RE = re.compile(r"^(?:0|-?[1-9][0-9]*)$")
_SIGNED_INT_RE = re.compile(r"^(?:0|[+-]?[1-9][0-9]*)$")
_FRACTION_SLASH_RE = re.compile(r"^([+-]?)([0-9]+)/([0-9]+)$")
_DECIMAL_NO_EXP_RE = re.compile(r"^([+-]?)([0-9]+)(?:\.([0-9]+))?$")
_DECIMAL_WITH_EXP_RE = re.compile(
    r"^([+-]?)([0-9]+)(?:\.([0-9]+))?(?:[eE]([+-]?[0-9]+))?$"
)


def require(condition: bool, message: str) -> None:
    """Fail-closed exact condition check active under both normal and -O Python."""
    if not condition:
        raise ValueError(message)


def require_type(condition: bool, message: str) -> None:
    """Fail-closed exact type check active under both normal and -O Python."""
    if not condition:
        raise TypeError(message)


def require_exact_int(value: object, *, name: str = "value") -> int:
    """Accept only an exact Python ``int`` (strictly excluding ``bool`` and ``float``)."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(
            f"{name} must be an exact int (excluding bool), got {type(value).__name__}"
        )
    return value


def parse_exact_int(
    value: object,
    *,
    name: str = "value",
    allow_leading_plus: bool = False,
) -> int:
    """Accept an exact ``int`` (excluding ``bool``) or strict canonical integer string."""
    if isinstance(value, bool):
        raise TypeError(f"{name} must not be bool")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        pattern = _SIGNED_INT_RE if allow_leading_plus else _EXACT_INT_RE
        if not pattern.fullmatch(value):
            raise ValueError(f"{name} is not a canonical integer token: {value!r}")
        return int(value)
    raise TypeError(
        f"{name} must be an exact int or canonical integer str, got {type(value).__name__}"
    )


def parse_printed_rational(
    token: object,
    *,
    name: str = "token",
    allow_fraction_slash: bool = True,
    allow_exponent: bool = False,
) -> Fraction:
    """Parse a printed decimal or rational string losslessly into exact ``Fraction``.

    Strictly accepts ``str`` only (rejects ``float``, ``complex``, ``bool``, ``int``),
    rejects whitespace, non-finite spellings (NaN/Inf), and zero denominators.
    """
    if not isinstance(token, str):
        raise TypeError(
            f"{name} must be a printed str token, got {type(token).__name__}"
        )
    if not token:
        raise ValueError(f"{name} must be a non-empty printed rational token")
    if token != token.strip() or any(ch.isspace() for ch in token):
        raise ValueError(f"{name} must not contain whitespace: {token!r}")

    if "/" in token:
        if not allow_fraction_slash:
            raise ValueError(f"{name} does not allow fraction slash syntax: {token!r}")
        match = _FRACTION_SLASH_RE.fullmatch(token)
        if match is None:
            raise ValueError(f"{name} is not a valid rational token: {token!r}")
        sign_s, num_s, den_s = match.groups()
        den = int(den_s)
        if den <= 0:
            raise ValueError(f"{name} must have a positive denominator: {token!r}")
        num = int(num_s)
        if sign_s == "-":
            num = -num
        return Fraction(num, den)

    pattern = _DECIMAL_WITH_EXP_RE if allow_exponent else _DECIMAL_NO_EXP_RE
    match = pattern.fullmatch(token)
    if match is None:
        raise ValueError(f"{name} is not a valid printed decimal token: {token!r}")

    if allow_exponent:
        sign_s, int_part, frac_part, exp_part = match.groups()
    else:
        sign_s, int_part, frac_part = match.groups()
        exp_part = None

    frac_digits = frac_part or ""
    digits = int(int_part + frac_digits)
    if sign_s == "-":
        digits = -digits
    exp_val = int(exp_part) if exp_part is not None else 0
    scale = len(frac_digits) - exp_val
    if scale >= 0:
        return Fraction(digits, 10**scale)
    return Fraction(digits * (10 ** (-scale)), 1)


def _as_exact_fraction(value: object, *, name: str = "value") -> Fraction:
    """Validate that ``value`` is a ``Fraction`` or exact ``int`` (excluding ``bool``)."""
    if isinstance(value, Fraction):
        return value
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(
            f"{name} must be Fraction or exact int (excluding bool), got {type(value).__name__}"
        )
    return Fraction(value, 1)


def canonical_rational_pair(value: Fraction | int) -> tuple[str, str]:
    """Return canonical ``(num_str, den_str)`` with ``den > 0``, reduced, zero as ``('0', '1')``."""
    q = _as_exact_fraction(value, name="value")
    if q.denominator <= 0:
        raise ValueError("canonical rational denominator must be positive")
    return (str(q.numerator), str(q.denominator))


def canonical_rational_str(value: Fraction | int) -> str:
    """Return canonical exact rational string (``'n'`` if denominator is 1, else ``'n/d'``)."""
    num_s, den_s = canonical_rational_pair(value)
    return num_s if den_s == "1" else f"{num_s}/{den_s}"


def parse_canonical_rational_pair(pair: object, *, name: str = "pair") -> Fraction:
    """Parse canonical ``[num_str, den_str]`` vector encoding into exact ``Fraction``."""
    if not isinstance(pair, (list, tuple)) or len(pair) != 2:
        raise TypeError(f"{name} must be a 2-element sequence of canonical integer strings")
    num_s, den_s = pair
    if not isinstance(num_s, str) or not isinstance(den_s, str):
        raise TypeError(f"{name} entries must be canonical integer strings")
    num = parse_exact_int(num_s, name=f"{name}[0]")
    den = parse_exact_int(den_s, name=f"{name}[1]")
    if den <= 0:
        raise ValueError(f"{name} denominator must be positive, got {den}")
    q = Fraction(num, den)
    if (str(q.numerator), str(q.denominator)) != (num_s, den_s):
        raise ValueError(
            f"{name} is not in reduced canonical form: got ({num_s!r}, {den_s!r}), "
            f"expected ({q.numerator!r}, {q.denominator!r})"
        )
    return q


def round_rational_half_even(value: Fraction | int, decimals: int) -> Fraction:
    """Exact banker's rounding (round half to even) using pure integer arithmetic."""
    q = _as_exact_fraction(value, name="value")
    dec = require_exact_int(decimals, name="decimals")
    if dec < 0:
        raise ValueError(f"decimals must be nonnegative, got {dec}")
    scale = 10**dec
    scaled = q * scale
    num = scaled.numerator
    den = scaled.denominator
    sign = -1 if num < 0 else 1
    abs_num = -num if num < 0 else num
    quot, rem = divmod(abs_num, den)
    twice_rem = 2 * rem
    if twice_rem > den or (twice_rem == den and quot % 2 == 1):
        quot += 1
    return Fraction(sign * quot, scale)


def format_rational_fixed(value: Fraction | int, decimals: int) -> str:
    """Format an exact rational to a fixed-decimal string using exact half-to-even rounding."""
    dec = require_exact_int(decimals, name="decimals")
    rounded = round_rational_half_even(value, dec)
    scale = 10**dec
    scaled_q = rounded * scale
    require(scaled_q.denominator == 1, "rounded scaled value must be an exact integer")
    scaled_int = scaled_q.numerator
    neg = scaled_int < 0
    mag = -scaled_int if neg else scaled_int
    if dec == 0:
        return ("-" if neg else "") + str(mag)
    int_part, frac_part = divmod(mag, scale)
    return ("-" if neg else "") + f"{int_part}.{frac_part:0{dec}d}"


def exact_isclose(
    actual: Fraction | int,
    expected: Fraction | int,
    tol: Fraction | int,
    *,
    rel_tol: Fraction | int | None = None,
) -> bool:
    """Exact rational closeness test replacing floating-point ``math.isclose``."""
    a = _as_exact_fraction(actual, name="actual")
    b = _as_exact_fraction(expected, name="expected")
    abs_tol = _as_exact_fraction(tol, name="tol")
    if abs_tol < 0:
        raise ValueError("tol must be nonnegative")
    rtol = abs_tol if rel_tol is None else _as_exact_fraction(rel_tol, name="rel_tol")
    if rtol < 0:
        raise ValueError("rel_tol must be nonnegative")
    bound = max(rtol * max(abs(a), abs(b)), abs_tol)
    return abs(a - b) <= bound

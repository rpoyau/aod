
from fractions import Fraction


def ttl_d(rho, window):
    return min(rho, window)


def pressure(C3, rho, window):
    return C3 * ttl_d(rho, window)


def pending_overhang(C3, rho, window):
    return C3 * max(Fraction(0), rho - window)


def test_pressure_uses_rcd_scalar_participation():
    assert pressure(Fraction(3), Fraction(7), Fraction(5)) == Fraction(15)


def test_duration_only_pressure_requires_neutral_reflection():
    D = Fraction(4)
    rho_non_neutral = Fraction(7)
    window = Fraction(5)
    assert pressure(Fraction(3), rho_non_neutral, window) != Fraction(3) * min(D, window)
    rho_neutral = D
    assert pressure(Fraction(3), rho_neutral, window) == Fraction(3) * min(D, window)


def test_pending_overhang_burden():
    assert pending_overhang(Fraction(3), Fraction(7), Fraction(5)) == Fraction(6)
    assert pending_overhang(Fraction(3), Fraction(4), Fraction(5)) == Fraction(0)

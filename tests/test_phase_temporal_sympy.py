import sympy as sp


def test_sympy_native_phase_closure_and_common_window_identities():
    p34 = sp.Integer(4) ** 3 + 4
    p33 = sp.Integer(3) ** 3 + 3
    n34 = 2 * p34 + 1
    n33 = 2 * p33 + 1
    common = sp.ilcm(n34, n33)
    assert (p34, n34, p33, n33) == (68, 137, 30, 61)
    assert common == 8357
    assert (common / n34, common / n33) == (61, 137)


def test_sympy_finite_pi_projection_residual_identities_and_enclosure():
    r = sp.Integer(256)
    C = sp.Integer(1608)
    A = sp.Integer(205857)
    residual = r * C - 2 * A
    pi_c = C / (2 * r)
    pi_a = A / r**2
    tau_c = C / r
    tau_a = 2 * A / r**2
    assert residual == -66
    assert pi_c == sp.Rational(201, 64)
    assert pi_a == sp.Rational(205857, 65536)
    assert sp.simplify(pi_c - pi_a - residual / (2 * r**2)) == 0
    assert sp.simplify(tau_c - tau_a - residual / r**2) == 0
    assert pi_c - pi_a == sp.Rational(-33, 65536)
    assert sp.Rational(103993, 33102) < sp.pi < sp.Rational(104348, 33215)

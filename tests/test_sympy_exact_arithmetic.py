import sympy as sp


def test_sympy_exact_dec_kernel_and_hinge_slide_arithmetic():
    weights = [sp.Integer(1), sp.Integer(1), sp.Integer(4), sp.Integer(2)]
    Z = sum(weights)
    assert Z == 8
    assert [w / Z for w in weights] == [sp.Rational(1, 8), sp.Rational(1, 8), sp.Rational(1, 2), sp.Rational(1, 4)]

    slide_weights = [sp.Integer(3), sp.Integer(3), sp.Integer(1)]
    Z_slide = sum(slide_weights)
    probs = [w / Z_slide for w in slide_weights]
    assert Z_slide == 7
    assert probs == [sp.Rational(3, 7), sp.Rational(3, 7), sp.Rational(1, 7)]
    assert probs[0] + probs[1] == sp.Rational(6, 7)
    assert probs[2] == sp.Rational(1, 7)


def test_sympy_exact_field_tunnelling_window_clip():
    P_tunnel = sp.Rational(1, 7)
    RD = sp.Integer(5)
    omega = sp.Integer(2)
    rho_omega = min(RD, omega)
    C3 = sp.Integer(3)
    pD = C3 * rho_omega
    assert rho_omega == 2
    assert pD == 6
    assert P_tunnel * pD == sp.Rational(6, 7)


def test_sympy_exact_tau_and_tritrioseptyro_arithmetic():
    assert sp.Rational(31, 50) == sp.Rational(62, 100)
    Pi = sp.Integer(3) ** 3 + 3
    RD = 2 * Pi + 1
    rho_omega = sp.Integer(7)
    C3H = sp.Integer(3)
    PH = C3H * rho_omega
    QH = C3H * (RD - rho_omega)
    assert Pi == 30
    assert RD == 61
    assert PH == 21
    assert QH == 162
    assert PH - 18 == 3
    assert PH - 24 == -3

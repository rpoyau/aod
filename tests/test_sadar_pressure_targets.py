
from fractions import Fraction


def pi(p, q):
    return q ** p + q


def rd_general(p, q, hinge):
    return 2 * pi(p, q) + hinge


def rd_single_hinge(p, q):
    return rd_general(p, q, 1)


def pressure(C3, rho, window):
    return C3 * min(rho, window)


def test_three_four_path_support_and_rd():
    assert pi(3, 4) == 68
    assert rd_single_hinge(3, 4) == 137


def test_general_branch_hinge_rd():
    assert rd_general(3, 4, 1) == 137
    assert rd_general(3, 4, 3) == 139


def test_fixture_1_2_7_closure_dependence():
    P = pressure(Fraction(3), Fraction(7), Fraction(9))
    assert P == 21
    assert P - 24 == -3
    assert P - 18 == 3


def test_fixture_1_2_9_surplus():
    P = pressure(Fraction(3), Fraction(9), Fraction(9))
    C_close = Fraction(24)
    X_shedding = max(Fraction(0), P - C_close)
    assert P == 27
    assert X_shedding == 3


def test_four_step_closure_decomposition():
    cases = {6: (1, 2), 7: (1, 3), 8: (2, 0), 9: (2, 1), 10: (2, 2)}
    for L, (c, r) in cases.items():
        assert L == 4*c + r

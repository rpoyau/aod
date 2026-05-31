
from fractions import Fraction


def phi(C3, ttl, direction):
    return C3 * ttl * direction


def test_unit_34_alpha_fixture():
    assert phi(Fraction(4), Fraction(1), Fraction(1)) == 4


def test_two_same_direction_fixture():
    assert phi(Fraction(4), Fraction(1), Fraction(1)) + phi(Fraction(4), Fraction(1), Fraction(1)) == 8


def test_opposite_directions_cancel_in_same_scope():
    assert phi(Fraction(4), Fraction(1), Fraction(1)) + phi(Fraction(4), Fraction(1), Fraction(-1)) == 0


def test_component_scopes_retain_vectors_and_enclosing_scope_cancels():
    A_F1 = phi(Fraction(4), Fraction(1), Fraction(1))
    A_F2 = phi(Fraction(4), Fraction(1), Fraction(-1))
    assert A_F1 == 4
    assert A_F2 == -4
    assert A_F1 + A_F2 == 0

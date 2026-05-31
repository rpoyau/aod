import sympy as sp


def skew_flux_matrix(n: int):
    """
    Build a finite B-scoped AFC flux matrix Phi with
    Phi[i,j] = -Phi[j,i] and Phi[i,i] = 0.
    """
    Phi = sp.MutableDenseMatrix.zeros(n, n)
    for a in range(n):
        for b in range(a + 1, n):
            x = sp.Symbol(f"phi_{a+1}{b+1}_B")
            Phi[a, b] = x
            Phi[b, a] = -x
    return sp.Matrix(Phi)


def stokes_residual(Phi, R):
    """
    Computes sum_{i in R} div(i;B) - sum_{i in R, j notin R} phi_ij(B).
    """
    n = Phi.rows
    all_nodes = range(n)
    R = set(R)
    lhs = sum(sum(Phi[i, j] for j in all_nodes) for i in R)
    rhs = sum(Phi[i, j] for i in R for j in all_nodes if j not in R)
    return sp.simplify(lhs - rhs)


def sadar_phi_symbol(a: int, b: int):
    """
    SADAR contents of phi_ab(B) for a < b.
    Orientation is handled by the skew matrix.
    """
    C3 = sp.Symbol(f"C3_{a}{b}")
    rho = sp.Symbol(f"rhoD_{a}{b}_B")
    W = sp.Symbol(f"w_{a}{b}")
    dchi = sp.Symbol(f"dchi_{a}{b}_B")
    inc = sp.Symbol(f"i_{a}{b}_B")
    A = dchi * inc
    return C3 * sp.Min(rho, W) * A


def sadar_flux_matrix(n: int):
    """
    Build Phi(B) using SADAR contents while preserving antisymmetry.
    """
    Phi = sp.MutableDenseMatrix.zeros(n, n)
    for a in range(n):
        for b in range(a + 1, n):
            x = sadar_phi_symbol(a + 1, b + 1)
            Phi[a, b] = x
            Phi[b, a] = -x
    return sp.Matrix(Phi)


def audit_hook(interior_value, boundary_value):
    """
    E(R,B) := <d phi(B), C_R> - <phi(B), partial C_R>.
    """
    return sp.simplify(interior_value - boundary_value)


def test_skew_flux_matrix_is_antisymmetric():
    Phi = skew_flux_matrix(4)
    assert Phi + Phi.T == sp.zeros(4, 4)


def test_stokes_residual_zero_for_arbitrary_flux():
    Phi = skew_flux_matrix(4)
    assert stokes_residual(Phi, {0, 1}) == 0


def test_stokes_residual_zero_for_sadar_flux():
    Phi = sadar_flux_matrix(4)
    assert stokes_residual(Phi, {0, 1}) == 0



def test_residual_detects_orientation_sign_failure():
    Phi = skew_flux_matrix(4)
    Phi[1, 0] = Phi[0, 1]  # break antisymmetry on an internal pair for R={0,1}
    assert stokes_residual(Phi, {0, 1}) != 0


def test_residual_detects_missing_channel():
    BoundaryFlux = sp.Symbol("BoundaryFlux")
    Missing = sp.Symbol("Missing")
    assert audit_hook(BoundaryFlux + Missing, BoundaryFlux) == Missing


def test_dec_transpose_pairing():
    m, n = 5, 4
    partial_k = sp.MatrixSymbol("partial_k", m, n)
    c_R = sp.MatrixSymbol("c_R", n, 1)
    s = sp.MatrixSymbol("s", m, 1)
    lhs = s.T * partial_k * c_R
    rhs = (partial_k.T * s).T * c_R
    assert str(lhs) == str(rhs)

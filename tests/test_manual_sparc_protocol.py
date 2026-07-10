from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parents[1]


def test_fractal_origin_anchor_is_octal():
    text = (ROOT / "appendices" / "A_fractal_address_bip_biz.tex").read_text()
    assert r"\mathtt{00}_8\vdash \mathrm{monon},\mathrm{bip},\mathrm{biz}." in text
    assert r"\mathtt{00}\vdash \mathrm{monon},\mathrm{bip},\mathrm{biz}." not in text


def test_sparc_five_galaxy_registry_status_is_scored():
    text = (ROOT / "manual" / "sections" / "09_prediction_test_fixture_registry.tex").read_text()
    assert "SPARC five-galaxy square-speed 2D observable-data fixture & G0 & SPARC radial rows" in text
    assert "SPARC radical-free square-speed benchmark protocol" not in text or "benchmark dataset pending" not in text.split("SPARC radical-free square-speed benchmark protocol", 1)[1].split("\\", 1)[0]
    assert "SPARC full-sample / extended benchmark & G0/G1 & target data manifest" in text


def test_sparc_field_dynamics_formula_columns_are_active():
    path = ROOT / "manual" / "data" / "derived" / "sparc_five_galaxy_per_bin.csv"
    with path.open(newline="") as f:
        row = next(csv.DictReader(f))
    required = {"lambda_ret", "C_cap", "D_BF", "U_bar", "U_AO"}
    assert required.issubset(row.keys())
    lam = float(row["lambda_ret"])
    assert lam == 1.0
    u_bar = float(row["U_bar"])
    d_bf = float(row["D_BF"])
    u_ao = float(row["U_AO"])
    assert abs(u_ao - (u_bar + 8.0 * d_bf)) < 1e-9

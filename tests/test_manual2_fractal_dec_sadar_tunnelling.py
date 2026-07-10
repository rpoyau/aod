import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEC = ROOT / "manual-2" / "sections"
DEC = ROOT / "manual-2" / "data" / "dec"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_manual2_contains_fractal_coordinate_dec_schema():
    section = read(ROOT / "shared" / "manual_intro_dec_ledger.tex")
    assert "Fractal-coordinate D.E.C. row" in section
    for token in [
        "a\\vdash B|t=(\\partial F,\\{t\\})",
        "\\epsilon\\in Q_4=\\{0,1\\}^4",
        "\\mu\\in\\{-1,0,+1\\}",
        "c=(a,\\epsilon,\\mu)",
        "\\texttt{fractal\\_coord}",
        "\\texttt{epsilon\\_Q4}",
        "\\texttt{mu}",
        "\\texttt{P\\_num}",
        "\\texttt{P\\_den}",
        "\\texttt{P\\_exact}",
    ]:
        assert token in section


def test_manual2_q4_isotropic_and_anisotropic_kernel_examples():
    section = read(ROOT / "shared" / "manual_intro_dec_ledger.tex")
    assert "$Q_4$ isotropic and anisotropic kernels" in section
    assert "P^{\\rm iso}=(1/4,1/4,1/4,1/4)" in section
    assert "w=(1,1,4,2)" in section
    assert "Z=8" in section
    assert "P^{\\rm ani}=(1/8,1/8,1/2,1/4)" in section
    rows = read_csv(DEC / "manual2_dec_tesseract_kernel_example.csv")
    assert len(rows) == 4
    assert [r["P_exact"] for r in rows] == ["1/8", "1/8", "1/2", "1/4"]
    assert {r["fractal_coord"] for r in rows} == {"00_8"}
    assert {r["epsilon_Q4"] for r in rows} == {"0000"}
    assert {r["mu"] for r in rows} == {"0"}
    assert [r["target_epsilon_Q4"] for r in rows] == ["1000", "0100", "0010", "0001"]


def test_manual2_field_tunnelling_hinge_slide_window_clip_fixture():
    section = read(ROOT / "shared" / "manual_intro_dec_ledger.tex")
    assert "Field tunnelling: hinge-slide window clip" in section
    for token in [
        "\\operatorname{adm}(e_0;B|t)=0",
        "\\operatorname{Slide}_{\\mu}(B|t)=\\{(e_1,-1),(e_2,-1),(e_3,+1)\\}",
        "w'=(3,3,1)",
        "P_{\\rm slide}=(3/7,3/7,1/7)",
        "s_{\\rm tunnel}=(e_3,+1)",
        "P_{\\rm tunnel}=1/7",
        "\\rho^D_{\\omega,s_{\\rm tunnel}}=\\min(5,2)=2",
        "p^D_{s_{\\rm tunnel}}=3\\cdot 2=6",
        "T^D_{\\rm tunnel}=(1/7)\\cdot 6=6/7",
    ]:
        assert token in section
    rows = read_csv(DEC / "manual2_field_tunnelling_window_clip_example.csv")
    assert len(rows) == 3
    tunnel = [r for r in rows if r["is_tunnel_branch"] == "1"]
    assert len(tunnel) == 1
    t = tunnel[0]
    assert t["slide_branch"] == "(e3,+1)"
    assert t["P_slide_num"] == "1"
    assert t["P_slide_den"] == "7"
    assert t["rhoD_omega"] == "2"
    assert t["pD"] == "6"
    assert t["T_tunnel_num"] == "6"
    assert t["T_tunnel_den"] == "7"


def test_manual2_dec_to_adar_sadar_bridge_and_expected_sadar():
    section = read(ROOT / "shared" / "manual_intro_dec_ledger.tex")
    assert "D.E.C. row-pair to ADAR and SADAR" in section
    for token in [
        "ADAR_e(B)=(A_e(B),D_e(B),R^{\\rm asym}_e(B))",
        "RCD_e(B)=D_e(B)\\leftrightarrow R^{\\rm asym}_e(B)",
        "\\phi_e(B)=p^D_e(B)A_e(B)",
        "A_F(B)=\\sum_{e\\in F(B)}\\phi_e(B)",
        "A_F^{\\rm exp}(B|t)=\\sum_{e\\in\\mathcal A(c;B|t)}P_e(B|t)p^D_e(B)A_e(B)",
        "$P_e$ is the AFC/D.E.C. kernel weight",
        "$p^D_eA_e$ is the ADAR/SADAR content",
        "$P_ep^D_eA_e$ is the kernel-weighted SADAR expectation",
    ]:
        assert token in section
    rows = read_csv(DEC / "manual2_dec_to_sadar_bridge_example.csv")
    assert len(rows) == 2
    plus = rows[0]
    minus = rows[1]
    assert plus["phi_num"] == "4" and plus["phi_den"] == "1"
    assert plus["expected_phi_num"] == "2" and plus["expected_phi_den"] == "1"
    assert minus["phi_num"] == "-4" and minus["expected_phi_num"] == "-2"


def test_manual2_dec_manifest_includes_new_fractal_dec_assets():
    manifest = json.loads((ROOT / "manual-2" / "data" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["version_scope"] == "v40.02r16"
    dec = manifest["lanes"]["dec_pen_paper"]
    for key in [
        "tesseract_kernel_example",
        "dec_to_sadar_bridge_example",
        "field_tunnelling_window_clip_example",
    ]:
        path = ROOT / dec[key]
        assert path.exists(), key
    assert "fractal-coordinate" in manifest["status"] or "fractal-coordinate" in manifest["claim_discipline"]


def test_manual2_rendering_status_declares_compact_worked_row_rendering():
    section = read(ROOT / "shared" / "manual_intro_dec_ledger.tex")
    roadmap = read(ROOT / "MANUAL_II_ROADMAP.md")
    assert "Manual II is a compact worked-row rendering" in roadmap
    assert "Manual-II-specific worked D.E.C. application rows" in roadmap


def test_manual2_dec_demo_rows_use_exact_fraction_columns():
    for filename in [
        "manual2_dec_tesseract_kernel_example.csv",
        "manual2_dec_to_sadar_bridge_example.csv",
        "manual2_field_tunnelling_window_clip_example.csv",
    ]:
        text = (DEC / filename).read_text(encoding="utf-8")
        assert ".25" not in text
        assert ".5" not in text
        assert ".125" not in text

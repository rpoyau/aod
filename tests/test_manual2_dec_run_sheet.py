
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEC = ROOT / "manual-2" / "sections"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_manual2_application_rows_start_after_frozen_shared_opening():
    main = read(ROOT / "manual-2" / "main.tex")
    assert main.index("sections/00_scope.tex") < main.index("sections/00_dec_ledger.tex")
    assert main.index("sections/00_dec_ledger.tex") < main.index("sections/02_elementary_dec_worked_example.tex")
    assert main.index("sections/02_elementary_dec_worked_example.tex") < main.index("sections/03_gas_dec_trace_application.tex")


def test_section2_uses_dec_table_columns_without_carbon_premise():
    s2 = read(SEC / "02_elementary_dec_worked_example.tex")
    assert "B=B_{336}" in s2
    for token in ["\\texttt{tick}", "\\texttt{B}", "\\texttt{v}", "\\texttt{e}", "\\texttt{v\\_e}", "$\\sigma(e)$", "$\\operatorname{adm}(e;B)$", "$w(e;B)$", "$P(e;B)$", "$\\operatorname{route}(e;B)$"]:
        assert token in s2
    raw_start = s2.index("\\subsection{Write the raw D.E.C. rows}")
    raw_end = s2.index("\\subsection{Normalize the exact kernel}")
    raw_block = s2[raw_start:raw_end]
    assert "Carbon" not in raw_block


def test_section2_normalizes_kernel_and_computes_trace_detector_freeze():
    s2 = read(SEC / "02_elementary_dec_worked_example.tex")
    expected = [
        "Z_B=\\sum_{e'}\\operatorname{adm}(e';B_{336})w(e';B_{336})=3+3=6",
        "P(e_L;B_{336})=\\frac{1\\cdot3}{6}=\\frac12",
        "P(e_R;B_{336})=\\frac{1\\cdot3}{6}=\\frac12",
        "T_{336}=(3,3)",
        "\\mathrm{motif}_{336}=\\texttt{retained\\_capacity\\_pair}",
        "\\mathrm{sadar}_{336}=\\texttt{retained\\_capacity\\_reclosure\\_context}",
        "D_{\\mathrm{cap}}(T_{336})=3+3=6",
        "X_{336}=\\texttt{retained\\_capacity}=6",
    ]
    for item in expected:
        assert item in s2


def test_section2_maps_carbon_only_after_freeze_and_audits_delta3():
    s2 = read(SEC / "02_elementary_dec_worked_example.tex")
    freeze = "X_{336}=\\texttt{retained\\_capacity}=6"
    registry = "\\Pi^{E0}_{\\mathrm{registry}}(6)=(Z=6"
    assert s2.index(freeze) < s2.index(registry)
    assert "\\Delta Z=6-6=0" in s2
    assert "\\delta_3=(0,0)" in s2
    assert "fusion_ladder_336.csv" in s2
    assert "pubchem_element_map.csv" in s2

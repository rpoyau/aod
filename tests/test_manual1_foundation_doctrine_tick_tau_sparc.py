from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")

def test_manual1_defines_tick_tau_and_sparc_doctrine():
    text = read("manual/sections/00_foundation_doctrine_tick_tau_sparc.tex")
    assert "Temporal flow is duon-current cadence across relational distinction" in text
    assert "Measured time is relational tick count under a declared clock process" in text
    assert "SADAR is a boundary-scoped returned-current, pressure, and attention-balance object" in text
    assert r"tau\_cycle} is the native phase-cycle coordinate" in text
    assert "SPARC is a 2D observable-data fixture under declared projection/readout policy" in text
    assert "Derived diagnostic quantities, where declared, are outputs of that projection/readout" in text

def test_main_carries_compact_foundation_doctrine():
    text = read("sections/03_foundation_doctrine_tick_tau_sparc.tex")
    assert "Manual I/Main define the rule; Manual II applies the rule" in text
    assert "pi = tau" not in text  # TeX display uses tau_{\rm cycle}; no ASCII fallback as native row.
    assert "SPARC is a 2D observable-data fixture under declared projection/readout policy" in text
    assert "Conversion error is not empirical residual" in text

def test_manual2_does_not_establish_doctrine_first():
    manual1 = read("manual/sections/00_foundation_doctrine_tick_tau_sparc.tex")
    manual2 = read("manual-2/sections/00_dec_report_coordinate_overlay.tex")
    assert "Manual II uses the foundation doctrine from Manual I/Main" in manual2
    assert "Manual I carries the conceptual classification" in manual1

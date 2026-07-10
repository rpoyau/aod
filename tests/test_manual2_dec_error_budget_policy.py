from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_manual2_overlay_section_states_guardrails():
    text = (ROOT / "manual-2/sections/00_dec_report_coordinate_overlay.tex").read_text(encoding="utf-8")
    assert "The overlay is not a target-join lane" in text
    assert "Conversion error is not empirical residual" in text
    assert "Projection/report error is not target agreement score" in text
    assert "SPARC rows treat the database as a 2D observable-data fixture" in text
    assert "SADAR remains a boundary-scoped returned-current, pressure, and attention-balance object" in text

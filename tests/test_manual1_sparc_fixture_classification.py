from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_live_sparc_fixture_headings_and_registry_use_2d_data_classification():
    field = (ROOT / "manual/sections/06_field_dynamics_applications.tex").read_text(encoding="utf-8")
    lens = (ROOT / "manual/sections/07_galactic_lensing_plan.tex").read_text(encoding="utf-8")
    registry = (ROOT / "manual/sections/09_prediction_test_fixture_registry.tex").read_text(encoding="utf-8")
    assert "SPARC square-speed 2D observable-data fixture" in field
    assert "SPARC5 lens-medium 2D data fixture" in lens
    assert "SPARC five-galaxy square-speed 2D observable-data fixture" in registry
    assert "SPARC5 lens-medium 2D data fixture" in registry
    assert "Derived residual and score outputs, where declared, are diagnostics of the projection/readout" in registry

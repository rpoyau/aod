
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_rest_energy_target_table_is_data_only():
    text = (ROOT / "manual/sections/01_rest_energy_prediction.tex").read_text()
    assert "Measured rest-energy target records" in text
    assert "Measured-data comparison analysis" not in text
    assert "target declared" not in text
    assert "formula" not in text
    assert "E_{x,\\mathrm{ext}}" in text
    assert "Record & Target [MeV]" in text


def test_higgs_candidate_table_is_ranking_only():
    text = (ROOT / "manual/sections/01_rest_energy_prediction.tex").read_text()
    assert "Higgs-support candidate ranking" in text
    assert "Candidate & \\(RD\\) & \\(P^D_H\\) & saddle & \\(Q^D_H\\) & score" in text
    assert "internal selection rule" in text
    assert "no-override internal selection rule" not in text
    assert "candidate-identity override" not in text
    assert "Candidate & \\(\\Pi\\)" not in text
    assert "\\rho^D_\\omega" in text  # retained in selected-candidate trace card
def test_swells_k123_table_uses_reason_notes():
    text = (ROOT / "manual/data/lensing/swells_k1_k2_k3_comparison_table.tex").read_text()
    assert "K1 reason" in text and "K2 reason" in text and "K3 reason" in text
    assert "Reason\\\\" not in text


def test_license_file_present_for_mit_zenodo_metadata():
    assert (ROOT / "LICENSE").exists()
    license_text = (ROOT / "LICENSE").read_text()
    zenodo = (ROOT / ".zenodo.json").read_text()
    assert "MIT License" in license_text
    assert '"license": "MIT"' in zenodo


from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_rest_energy_target_table_is_data_only():
    text = (ROOT / "manual/sections/01_rest_energy_prediction.tex").read_text()
    target_table = text.split(r"\caption{Measured rest-energy target records.}", 1)[1].split(r"\end{table}", 1)[0]
    assert "formula" not in target_table
    assert "E_{x,\\mathrm{ext}}" in text


def test_higgs_candidate_table_is_ranking_only():
    text = (ROOT / "manual/sections/01_rest_energy_prediction.tex").read_text()
    assert "internal selection rule" in text
    assert "\\rho^D_\\omega" in text  # retained in selected-candidate trace card


def test_license_file_present_for_mit_zenodo_metadata():
    assert (ROOT / "LICENSE").exists()
    license_text = (ROOT / "LICENSE").read_text()
    zenodo = (ROOT / ".zenodo.json").read_text()
    assert "MIT License" in license_text
    assert '"license": "mit"' in zenodo

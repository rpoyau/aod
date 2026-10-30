from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def test_zenodo_notes_use_this_version_pdf_links_and_all_versions_doi():
    z = json.loads((ROOT / ".zenodo.json").read_text(encoding="utf-8"))
    notes = z.get("notes", "")
    assert "https://zenodo.org/records/23426642/files/main.pdf?download=1" in notes
    assert "https://zenodo.org/records/23426642/files/manual.pdf?download=1" in notes
    assert 'All versions: <a href="https://doi.org/10.5281/zenodo.20486270">' in notes
    assert "https://doi.org/10.5281/zenodo.20486270/files/" not in notes


def test_readme_uses_this_version_links_not_asset_block():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "https://zenodo.org/records/23426642/files/main.pdf?download=1" in readme
    assert "https://zenodo.org/records/23426642/files/manual.pdf?download=1" in readme
    assert "https://doi.org/10.5281/zenodo.20486270/files/" not in readme
    assert "[![DOI](https://zenodo.org/badge/1012484945.svg)](https://doi.org/10.5281/zenodo.20486270)" in readme

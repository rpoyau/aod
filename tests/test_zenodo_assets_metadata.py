from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def test_zenodo_notes_use_latest_doi_links_only():
    z = json.loads((ROOT / ".zenodo.json").read_text(encoding="utf-8"))
    notes = z.get("notes", "")
    assert "https://doi.org/10.5281/zenodo.20486270/files/main.pdf?download=1" in notes
    assert "https://doi.org/10.5281/zenodo.20486270/files/manual.pdf?download=1" in notes
    assert "Primary display artifact" not in notes
    assert "Default display artifact" not in notes
    assert "Stable release assets" not in notes
    assert "source.zip" not in notes
    assert "bundle.zip" not in notes
    assert "tests.txt" not in notes
    assert "patch_summary.txt" not in notes
    assert "BUNDLE_CONTENTS_SHA256.txt" not in notes
    assert "SHA256.txt" not in notes
    assert "AOD_Temporal_Dynamics_v" not in notes


def test_readme_uses_latest_links_not_asset_block():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "## Latest DOI links" in readme
    assert "https://doi.org/10.5281/zenodo.20486270/files/main.pdf?download=1" in readme
    assert "https://doi.org/10.5281/zenodo.20486270/files/manual.pdf?download=1" in readme
    assert "## Zenodo file assets" not in readme
    assert "## Primary display artifact" not in readme
    latest = readme.split("## Latest DOI links", 1)[1].split("##", 1)[0]
    assert "AOD_Temporal_Dynamics_v" not in latest

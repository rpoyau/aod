from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]

def test_zenodo_notes_name_stable_assets_and_default_main():
    z = json.loads((ROOT / ".zenodo.json").read_text(encoding="utf-8"))
    notes = z.get("notes", "")
    assert "Primary display artifact: main.pdf" in notes
    assert "Manual reference implementation artifact: manual.pdf" in notes
    for name in ["main.pdf", "manual.pdf", "source.zip", "bundle.zip", "tests.txt", "patch_summary.txt", "BUNDLE_CONTENTS_SHA256.txt", "SHA256.txt"]:
        assert name in notes
    assert "AOD_Temporal_Dynamics_v" not in notes

def test_readme_names_stable_assets_and_latest_links():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "## Zenodo file assets" in readme
    assert "primary display artifact is `main.pdf`" in readme
    assert "manual.pdf" in readme
    assert "https://doi.org/10.5281/zenodo.20486270/files/manual.pdf?download=1" in readme
    assert "AOD_Temporal_Dynamics_v" not in readme.split("## Zenodo file assets", 1)[1].split("##",1)[0]

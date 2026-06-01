import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_zenodo_metadata_present_and_title_has_no_revision():
    data = json.loads((ROOT / ".zenodo.json").read_text(encoding="utf-8"))
    assert data["title"] == "Alpha-Omega Dynamics: The Hidden Temporal Dynamics of Stokes"
    assert "v39" not in data["title"]
    assert "The Hidden Temporal Dynamics of Stokes" in data["title"]
    assert data["version"] == "v39.99r74"
    assert data["publication_date"] == "2026-06-01"
    assert "Alpha↔Omega Dynamics (AΩD) is a relational temporal form" in data["description"]
    assert "This release includes the main note, manual, source package, test output, patch summary, bundle, and SHA-256 manifests." in data["description"]
    assert data["upload_type"] == "software"
    assert data["access_right"] == "open"
    assert data["license"] == "MIT"
    assert any(c.get("name") == "Poyau, Reginald" for c in data["creators"])


def test_source_builder_includes_zenodo_metadata_and_build_md():
    builder = (ROOT / "scripts" / "build_release_bundle.py").read_text(encoding="utf-8")
    assert '".zenodo.json"' in builder
    assert '"BUILD.md"' in builder


def test_readme_version_matches_canonical_version_r69():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    canon = (ROOT / "CANONICAL_VERSION.txt").read_text(encoding="utf-8")
    assert "**Version:** v39.99r74" in readme
    assert "Canonical version: v39.99r74" in canon
    assert "AOD_Temporal_Dynamics_v39_99r74" in readme
    assert "**Title:** Alpha-Omega Dynamics" in readme
    assert "**Subtitle:** The Hidden Temporal Dynamics of Stokes" in readme

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def current_version():
    text = (ROOT / "CANONICAL_VERSION.txt").read_text(encoding="utf-8")
    m = re.search(r"Canonical version:\s*(\S+)", text)
    assert m
    return m.group(1)


def current_slug():
    return current_version().lstrip("v").replace(".", "_").replace("-", "_")


def current_prefix():
    return f"AOD_Temporal_Dynamics_v{current_slug()}"


def test_zenodo_metadata_present_and_title_has_no_revision():
    data = json.loads((ROOT / ".zenodo.json").read_text(encoding="utf-8"))
    assert data["title"] == "Alpha↔Omega Dynamics (AΩD)"
    assert "v39" not in data["title"]
    assert "The Hidden Temporal Dynamics of Stokes" not in data["title"]
    assert any(t.get("title") == "The Hidden Temporal Dynamics of Stokes" and t.get("type", {}).get("id") == "subtitle" for t in data.get("additional_titles", []))
    assert any(t.get("title") == "The Art Of The Leprechaun: Fractal Calculus – 𝔖" and t.get("type", {}).get("id") == "alternative-title" for t in data.get("additional_titles", []))
    assert any(t.get("title") == "43 °c" and t.get("type", {}).get("id") == "other" for t in data.get("additional_titles", []))
    assert data["version"] == current_version()
    assert data["publication_date"] == "2026-06-01"
    assert "Alpha↔Omega Dynamics (AΩD) is a relational temporal form" in data["description"]
    assert "## Abstract and Scope" in data["description"]
    assert "## 2. The Application Manual (Reference Implementation Layer)" in data["description"]
    assert "w=(1,1,4,2)" in data["description"] or "w=(1, 1, 4, 2)" in data["description"]
    assert "P_{\\mathrm{slide}}" in data["description"]
    assert "manual.pdf" in data.get("notes", "")
    assert "main.pdf" in data.get("notes", "")
    assert "Axiomatic-Fundamentalism calculus (AFC)" in data["description"]
    assert "Alpha↔Omega Dynamics (AΩD)" in data["description"]
    assert data["upload_type"] == "publication"
    assert data["publication_type"] == "preprint"
    assert data["access_right"] == "open"
    assert data["license"] == "MIT"
    assert any(c.get("name") == "Poyau, Reginald" for c in data["creators"])
    assert "references" in data
    assert any("Axiomatic-Fundamentalism calculus" in r for r in data["references"])
    assert any("Axiomatic-Fundamentalism (AF)" in r for r in data["references"])

    assert data["keywords"] == [
        "axiomatic fundamentalism", "AFC", "AOD", "Stokes", "cut calculus",
        "temporal dynamics", "AΩD", "math-ph", "math-lo"
    ]


def test_source_builder_includes_zenodo_metadata_and_build_md():
    builder = (ROOT / "scripts" / "build_release_bundle.py").read_text(encoding="utf-8")
    assert '".zenodo.json"' in builder
    assert '"BUILD.md"' in builder


def test_readme_version_matches_canonical_version_r69():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    canon = (ROOT / "CANONICAL_VERSION.txt").read_text(encoding="utf-8")
    assert f"**Version:** {current_version()}" in readme
    assert f"Canonical version: {current_version()}" in canon
    assert "main.pdf" in readme
    assert "manual.pdf" in readme
    assert "AOD_Temporal_Dynamics_v" not in readme
    assert "**Title:** Alpha↔Omega Dynamics (AΩD)" in readme
    assert "**Subtitle:** The Hidden Temporal Dynamics of Stokes" in readme


def test_zenodo_references_are_synchronized_with_bib_files():
    import subprocess, sys
    result = subprocess.run([sys.executable, str(ROOT / "scripts" / "sync_zenodo_references.py"), "--check"], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_readme_references_are_synchronized_with_zenodo_references():
    data = json.loads((ROOT / ".zenodo.json").read_text(encoding="utf-8"))
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "References are synchronized from `refs.bib` and `manual/refs.bib`." in readme
    for ref in data["references"]:
        assert f"- {ref}" in readme

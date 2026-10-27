from pathlib import Path
import json
import re
import zipfile

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


def test_readme_names_this_version_pdf_links():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "## This version" in readme
    assert "https://zenodo.org/records/23426642/files/main.pdf?download=1" in readme
    assert "https://zenodo.org/records/23426642/files/manual.pdf?download=1" in readme
    assert "https://doi.org/10.5281/zenodo.20486270/files/" not in readme
    assert "](https://doi.org/10.5281/zenodo.20486270)" in readme
    assert "## Primary display artifact" not in readme
    assert "## Zenodo file assets" not in readme


def test_zenodo_notes_pair_version_pdf_links_with_current_version():
    data = json.loads((ROOT / ".zenodo.json").read_text(encoding="utf-8"))
    notes = data.get("notes", "")
    assert "https://zenodo.org/records/23426642/files/main.pdf?download=1" in notes
    assert "https://zenodo.org/records/23426642/files/manual.pdf?download=1" in notes
    assert "https://doi.org/10.5281/zenodo.20486270/files/" not in notes
    assert 'All versions: <a href="https://doi.org/10.5281/zenodo.20486270">' in notes
    assert "Primary display artifact" not in notes
    assert "Stable release assets" not in notes
    assert "AOD_Temporal_Dynamics_v" not in notes
    assert data["title"] == "Alpha↔Omega Dynamics (AΩD)"
    assert any(t.get("title") == "The Hidden Temporal Dynamics of Stokes" for t in data.get("additional_titles", []))
    assert data["version"] == current_version()
    assert f"Version {current_version()}" in notes


def test_build_docs_name_main_pdf_primary_and_bundle_order():
    build = (ROOT / "BUILD.md").read_text(encoding="utf-8")
    assert "## Artifact order" in build
    assert "use the main note PDF as the primary artifact" in build
    assert "`main.pdf` as the first member" in build
    builder = (ROOT / "scripts" / "build_release_bundle.py").read_text(encoding="utf-8")
    assert 'bundle_order = [' in builder
    assert '"main.pdf"' in builder
    assert builder.index('"main.pdf"') < builder.index('"manual.pdf"') < builder.index('"source.zip"')


def test_canonical_historical_wording_is_version_neutral():
    canon = (ROOT / "CANONICAL_VERSION.txt").read_text(encoding="utf-8")
    metadata = json.loads((ROOT / ".zenodo.json").read_text(encoding="utf-8"))
    assert metadata["version"] == current_version()
    assert f"Canonical version: {current_version()}" in canon
    assert "Older AOD Temporal Dynamics artifacts are historical comparison artifacts only." in canon
    assert "Older r1-r" not in canon


def test_title_page_subtitle_line_order():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    main = (root / "sections" / "00_title.tex").read_text()
    manual = (root / "manual" / "main.tex").read_text()
    for text in [main, manual]:
        assert text.index("The Hidden Temporal Dynamics of Stokes") < text.index("The Art Of The Leprechaun: Fractal Calculus") < text.index("43")

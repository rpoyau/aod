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
    assert "<h2>Abstract and Scope</h2>" in data["description"]
    assert "## Abstract and Scope" not in data["description"]
    assert "<h2>The Application Manual: Reference Implementation Layer</h2>" in data["description"]
    assert "w=(1,1,4,2)" in data["description"] or "w=(1, 1, 4, 2)" in data["description"]
    assert "P<sub>slide</sub>" in data["description"]
    assert "manual.pdf" in data.get("notes", "")
    assert "main.pdf" in data.get("notes", "")
    assert "Axiomatic-Fundamentalism calculus (AFC)" in data["description"]
    assert "Alpha↔Omega Dynamics (AΩD)" in data["description"]
    assert data["upload_type"] == "publication"
    assert data["publication_type"] == "preprint"
    assert data["access_right"] == "open"
    assert data["license"] == "mit"
    assert any(c.get("name") == "Poyau, Reginald" for c in data["creators"])
    assert "references" in data
    assert "Poyau, R. (2025). Axiomatic Fundamentalism Calculus (AFC) (all versions). Zenodo. https://doi.org/10.5281/zenodo.17795590." in data["references"]
    assert "Poyau, R. (2025). Axiomatic Fundamentalism (AF): A Logical Protocol for Traceable Research (all versions). Zenodo. https://doi.org/10.5281/zenodo.17561186." in data["references"]
    assert not any("Alpha–Omega Dynamics Manual" in r or "Alpha--Omega Dynamics Manual" in r for r in data["references"])

    assert data["keywords"] == [
        "axiomatic fundamentalism", "AFC", "AOD", "Stokes", "cut calculus",
        "temporal dynamics", "AΩD", "math-ph", "math-lo"
    ]


def test_afc_af_bib_entries_include_zenodo_dois():
    for rel in ["refs.bib", "manual/refs.bib"]:
        bib = (ROOT / rel).read_text(encoding="utf-8")
        assert "author = {Poyau, Reginald}" in bib
        assert "title = {{Axiomatic Fundamentalism Calculus (AFC) (all versions)}}" in bib
        assert "Version 5.0" not in bib
        assert "version = {5.0}" not in bib
        assert "doi = {10.5281/zenodo.17795590}" in bib
        assert "zenodo_reference = {Poyau, R. (2025). Axiomatic Fundamentalism Calculus (AFC) (all versions). Zenodo. https://doi.org/10.5281/zenodo.17795590}" in bib
        assert "title = {{Axiomatic Fundamentalism (AF): A Logical Protocol for Traceable Research (all versions)}}" in bib
        assert "version = {1.4.0.0}" not in bib
        assert "doi = {10.5281/zenodo.17561186}" in bib
        assert "zenodo_reference = {Poyau, R. (2025). Axiomatic Fundamentalism (AF): A Logical Protocol for Traceable Research (all versions). Zenodo. https://doi.org/10.5281/zenodo.17561186}" in bib
        assert "Axiomatic-Fundamentalism calculus (AFC)" not in bib
        assert "Axiomatic-Fundamentalism (AF)}, 2025" not in bib
        assert "poyau2026aodmanual" not in bib
        assert "AFC Alpha--Omega Dynamics Manual" not in bib


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


def test_root_zenodo_json_is_source_metadata_for_github_sync():
    assert (ROOT / ".zenodo.json").exists()
    build = (ROOT / "BUILD.md").read_text(encoding="utf-8")
    assert "repository root" in build
    assert "GitHub-Zenodo synchronization" in build
    builder = (ROOT / "scripts" / "build_release_bundle.py").read_text(encoding="utf-8")
    assert "def validate_zenodo_metadata" in builder
    assert "repository-root .zenodo.json is required" in builder
    assert '".zenodo.json"' in builder
    data = json.loads((ROOT / ".zenodo.json").read_text(encoding="utf-8"))
    assert data["version"] == current_version()
    assert "references" in data and data["references"]


def test_core_bib_entries_are_structured():
    main_bib = (ROOT / "refs.bib").read_text(encoding="utf-8")
    manual_bib = (ROOT / "manual/refs.bib").read_text(encoding="utf-8")
    for bib in [main_bib, manual_bib]:
        assert "@book{norrisMarkov" in bib
        assert "@book{levinPeresWilmer" in bib
        assert "@book{lawlerLimic" in bib
        assert "key = {norrisMarkov}" not in bib
        assert "key = {levinPeresWilmer}" not in bib
        assert "key = {lawlerLimic}" not in bib
        assert "author = {{Poyau, Reginald}}" not in bib
        assert "author = {Poyau, Reginald}" in bib
    assert "@book{stanleyCatalan" in main_bib
    assert "@book{flajoletSedgewick" in main_bib
    assert "key = {stanleyCatalan}" not in main_bib
    assert "key = {flajoletSedgewick}" not in main_bib



def test_zenodo_related_identifiers_include_parent_dois():
    data = json.loads((ROOT / ".zenodo.json").read_text(encoding="utf-8"))
    related = data.get("related_identifiers", [])
    pairs = {(r.get("identifier"), r.get("relation"), r.get("scheme")) for r in related}
    assert ("10.5281/zenodo.17795590", "references", "doi") in pairs
    assert ("10.5281/zenodo.17561186", "references", "doi") in pairs


def test_manual_references_are_structured_for_key_scientific_sources():
    bib = (ROOT / "manual" / "refs.bib").read_text(encoding="utf-8")
    required = [
        "@article{heisse-proton-mass",
        "doi = {10.1103/PhysRevLett.119.033001}",
        "@article{sturm-electron-mass",
        "doi = {10.1038/nature13026}",
        "@article{meyer-muonium-1s2s",
        "doi = {10.1103/PhysRevLett.84.1136}",
        "@article{lelli-sparc-2016",
        "doi = {10.3847/0004-6256/152/6/157}",
        "@article{atlas-cms-higgs-run1",
        "doi = {10.1103/PhysRevLett.114.191803}",
        "@article{atlas-higgs-mass-combined-2023",
        "doi = {10.1103/PhysRevLett.131.251802}",
        "@article{will-mercury-2018",
        "doi = {10.1103/PhysRevLett.120.191101}",
        "@article{dyson-eddington-davidson-1920",
        "doi = {10.1098/rsta.1920.0009}",
    ]
    for token in required:
        assert token in bib


def test_web_sources_carry_access_dates():
    combined = (ROOT / "refs.bib").read_text(encoding="utf-8") + "\n" + (ROOT / "manual" / "refs.bib").read_text(encoding="utf-8")
    for key in [
        "weissteinHypercubeGraph", "nist-alpha-inverse", "bipm-si-defining-constants",
        "sparc-database", "nasa-moon-by-numbers", "nasa-cassini-division",
    ]:
        m = re.search(r"@\w+\s*\{\s*" + re.escape(key) + r"\s*,(?P<body>.*?)\n\}", combined, re.S)
        assert m, key
        assert "urldate = {2026-06-09}" in m.group("body")

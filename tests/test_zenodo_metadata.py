import json
import re
from html.parser import HTMLParser
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


class DescriptionOutline(HTMLParser):
    def __init__(self):
        super().__init__()
        self.headings = []
        self.ordered_steps = {}
        self.heading_parts = None
        self.section = None
        self.list_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag == "h2":
            self.heading_parts = []
        elif tag == "ol":
            self.list_depth += 1
        elif tag == "li" and self.list_depth == 1:
            self.ordered_steps[self.section] = self.ordered_steps.get(self.section, 0) + 1

    def handle_data(self, data):
        if self.heading_parts is not None:
            self.heading_parts.append(data)

    def handle_endtag(self, tag):
        if tag == "h2":
            self.section = "".join(self.heading_parts)
            self.headings.append(self.section)
            self.heading_parts = None
        elif tag == "ol":
            self.list_depth -= 1


def test_zenodo_metadata_present_and_title_has_no_revision():
    data = json.loads((ROOT / ".zenodo.json").read_text(encoding="utf-8"))
    assert data["title"] == "Alpha↔Omega Dynamics (AΩD)"
    assert not re.search(r"\bv\d", data["title"])
    assert "The Hidden Temporal Dynamics of Stokes" not in data["title"]
    assert any(t.get("title") == "The Hidden Temporal Dynamics of Stokes" and t.get("type", {}).get("id") == "subtitle" for t in data.get("additional_titles", []))
    assert any(t.get("title") == "The Art Of The Leprechaun: Fractal Calculus – 𝔖" and t.get("type", {}).get("id") == "subtitle" for t in data.get("additional_titles", []))
    assert any(t.get("title") == "43◦c" and t.get("type", {}).get("id") == "alternative-title" for t in data.get("additional_titles", []))
    assert data["version"] == current_version()
    assert data["publication_date"] == "2026-06-01"
    assert "<h2>What AΩD is</h2>" in data["description"]
    assert "relational, temporal computational calculus" in data["description"]
    assert not re.search(r"^#{1,6} ", data["description"], re.M)
    assert "main.pdf — The calculus:" in data["description"]
    assert "manual.pdf — Working with the calculus:" in data["description"]
    assert "w=(1,1,4,2)" in data["description"] or "w=(1, 1, 4, 2)" in data["description"]
    assert "P<sub>slide</sub>" in data["description"]
    assert "manual.pdf" in data.get("notes", "")
    assert "main.pdf" in data.get("notes", "")
    assert "Axiomatic Fundamentalism Calculus (AFC)" in data["description"]
    assert "Alpha↔Omega Dynamics (AΩD)" in data["description"]
    assert data["upload_type"] == "publication"
    assert data["publication_type"] == "preprint"
    assert data["access_right"] == "open"
    assert data["license"] == "mit"
    assert data["language"] == "eng"
    assert any(c.get("name") == "Poyau, Reginald" for c in data["creators"])
    assert any(c.get("orcid") == "0009-0007-8303-8627" for c in data["creators"])
    assert data["custom"]["code:codeRepository"] == "https://github.com/rpoyau/aod"
    assert "references" in data
    assert len(data["references"]) == 43
    assert "Poyau, R. (2025). Axiomatic Fundamentalism Calculus (AFC) (all versions). Zenodo. https://doi.org/10.5281/zenodo.17795590." in data["references"]
    assert "Poyau, R. (2025). Axiomatic Fundamentalism (AF): A Logical Protocol for Traceable Research (all versions). Zenodo. https://doi.org/10.5281/zenodo.17561186." in data["references"]
    assert not any("Alpha–Omega Dynamics Manual" in r or "Alpha--Omega Dynamics Manual" in r for r in data["references"])

    assert data["keywords"] == [
        "computational calculus", "axiomatic fundamentalism", "AFC",
        "AOD", "Stokes", "cut calculus", "temporal dynamics", "AΩD",
        "math-ph", "math-lo",
        "discrete Stokes calculus", "graph combinatorics", "certified closure",
        "discrete recurrence", "relational time", "finite Fourier representation",
        "Awareness", "computational intelligence", "persistent learning", "proprioceptive action-return models",
        "physical observable maps", "exact rational simulation", "Declared Edge Computation",
        "Alpha-Omega Dynamics", "temporal wave dynamics", "causal operativity",
        "math.LO", "math.CO", "cs.DM", "cs.AI", "cs.NE"
    ]
    assert data["subjects"] == [
        {"term": "Mathematical Physics", "identifier": "https://arxiv.org/list/math-ph/recent", "scheme": "url"},
        {"term": "Logic", "identifier": "https://arxiv.org/list/math.LO/recent", "scheme": "url"},
        {"term": "Combinatorics", "identifier": "https://arxiv.org/list/math.CO/recent", "scheme": "url"},
        {"term": "Discrete Mathematics", "identifier": "https://arxiv.org/list/cs.DM/recent", "scheme": "url"},
        {"term": "Artificial Intelligence", "identifier": "https://arxiv.org/list/cs.AI/recent", "scheme": "url"},
        {"term": "Neural and Evolutionary Computing", "identifier": "https://arxiv.org/list/cs.NE/recent", "scheme": "url"}
    ]


def test_publication_and_revision_dates_are_distinct_and_paired():
    data = json.loads((ROOT / ".zenodo.json").read_text(encoding="utf-8"))
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert data["publication_date"] == "2026-06-01"
    assert data["dates"] == [{
        "start": "2026-10-17", "end": "2026-10-17", "type": "Other",
        "description": f"Revision date for version {current_version()}",
    }]
    assert "Initial publication: 2026-06-01 · Revision: 2026-10-17" in readme
    assert "revision: 2026-10-17; initial publication: 2026-06-01" in data["notes"]
    assert f"Version {current_version()}" in data["notes"]


def test_readme_and_html_pair_the_engine_and_calculation_spine():
    data = json.loads((ROOT / ".zenodo.json").read_text(encoding="utf-8"))
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    outline = DescriptionOutline()
    outline.feed(data["description"])
    engine = "The engine: how to run it (raw AFC and the D.E.C. ledger)"
    setup = "The setup (The Art of the Leprechaun): how to get specific results"
    assert outline.headings == ["What AΩD is", "Waves, relational time and Fourier", engine, setup]
    assert outline.ordered_steps == {engine: 2, setup: 4}
    readme_headings = re.findall(r"^## (.+)$", readme, re.M)
    normalized_headings = [heading.replace("*", "") for heading in readme_headings]
    positions = [normalized_headings.index(heading) for heading in outline.headings]
    assert positions == sorted(positions)
    for heading, expected_count in [(engine, 2), (setup, 4)]:
        markdown_heading = readme_headings[normalized_headings.index(heading)]
        section = readme.split(f"## {markdown_heading}\n", 1)[1].split("\n## ", 1)[0]
        assert len(re.findall(r"^\d+\. ", section, re.M)) == expected_count
    for phrase in [
        "certified enclosing return", "equal branch support counts", "structural hinge",
        "exact complex characters", "solar native input certificates", "originating tau calculation recipe",
    ]:
        assert phrase in readme
        assert phrase in data["description"]


def test_readme_fixture_fences_and_subject_table_are_complete():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    blocks = re.findall(r"^```(\w*)\n(.*?)^```[ \t]*$", readme, re.M | re.S)
    assert len(re.findall(r"^```", readme, re.M)) == 4
    assert [language for language, _ in blocks] == ["bash", "text"]
    bash = blocks[0][1]
    assert "python3 manual/scripts/aod_native_closure_wave.py --check-data" in bash
    assert "python3 manual/scripts/aod_awareness.py --check-data" in bash
    assert not any(re.search(r"^## ", body, re.M) for _, body in blocks)
    table = [line for line in readme.splitlines() if line.startswith("|")]
    assert len(table) == 8
    assert all(len(line.strip("|").split("|")) == 3 for line in table)
    assert table[0] == "| Scope | Category | Content |"
    assert table[1] == "| --- | --- | --- |"
    assert [re.search(r"`([^`]+)`", row).group(1) for row in table[2:]] == [
        "math.LO", "math.CO", "cs.DM", "math-ph", "cs.AI", "cs.NE",
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
    section = readme.split("## References\n", 1)[1].split("\n## ", 1)[0]
    references = [line[2:] for line in section.splitlines() if line.startswith("- ")]
    assert references == data["references"]


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

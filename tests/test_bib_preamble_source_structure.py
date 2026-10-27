
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text()


def test_main_and_manual_use_refs_bib():
    assert (ROOT / "refs.bib").exists()
    assert (ROOT / "manual" / "refs.bib").exists()


def test_refs_bib_contains_required_keys():
    combined = read("refs.bib") + "\n" + read("manual/refs.bib")
    required = [
        "afc", "reginald2025af", "weissteinHypercubeGraph",
        "sparc-database", "lelli-sparc-2016", "atlas-cms-higgs-run1",
        "cms-hig-21-019", "atlas-higgs-mass-combined-2023",
        "atlas-higgs-diphoton-2023",
    ]
    for key in required:
        assert re.search(r"@\w+\s*\{\s*" + re.escape(key) + r"\s*,", combined)

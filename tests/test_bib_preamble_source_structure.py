
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text()


def test_main_and_manual_use_external_preamble_files():
    main = read("main.tex")
    manual = read("manual/main.tex")
    manual2 = read("manual-2/main.tex")
    assert r"\input{preamble.tex}" in main
    assert r"\input{preamble.tex}" in manual
    assert r"\input{preamble.tex}" in manual2
    assert (ROOT / "preamble.tex").exists()
    assert (ROOT / "manual" / "preamble.tex").exists()
    assert (ROOT / "manual-2" / "preamble.tex").exists()


def test_main_and_manual_use_refs_bib():
    main = read("main.tex")
    manual = read("manual/main.tex")
    manual2 = read("manual-2/main.tex")
    assert r"\bibliography{refs}" in main
    assert r"\bibliography{refs}" in manual
    assert r"\bibliography{refs}" in manual2
    assert (ROOT / "refs.bib").exists()
    assert (ROOT / "manual" / "refs.bib").exists()
    assert (ROOT / "manual-2" / "refs.bib").exists()
    assert r"\begin{thebibliography}" not in main
    assert r"\begin{thebibliography}" not in manual
    assert r"\begin{thebibliography}" not in manual2
    assert r"\bibitem" not in main
    assert r"\bibitem" not in manual
    assert r"\bibitem" not in manual2


def test_refs_bib_contains_required_keys():
    combined = read("refs.bib") + "\n" + read("manual/refs.bib") + "\n" + read("manual-2/refs.bib")
    required = [
        "afc", "reginald2025af", "weissteinHypercubeGraph",
        "sparc-database", "lelli-sparc-2016", "atlas-cms-higgs-run1",
        "cms-hig-21-019", "atlas-higgs-mass-combined-2023",
        "atlas-higgs-diphoton-2023",
    ]
    for key in required:
        assert re.search(r"@\w+\s*\{\s*" + re.escape(key) + r"\s*,", combined)


def test_preamble_files_carry_note_block_macros():
    main_pre = read("preamble.tex")
    manual_pre = read("manual/preamble.tex")
    manual2_pre = read("manual-2/preamble.tex")
    for pre in (main_pre, manual_pre, manual2_pre):
        assert r"\newcommand{\aodnoteblock}" in pre
        assert r"\newcommand{\aodprovenance}" in pre
        assert r"\newcommand{\aodliteraturenote}" in pre
        assert r"\newcommand{\aodremark}" in pre


def test_no_inline_bibliography_in_main_tex_files():
    assert r"\begin{thebibliography}" not in read("main.tex")
    assert r"\begin{thebibliography}" not in read("manual/main.tex")
    assert r"\begin{thebibliography}" not in read("manual-2/main.tex")
    assert r"\bibitem" not in read("main.tex")
    assert r"\bibitem" not in read("manual/main.tex")
    assert r"\bibitem" not in read("manual-2/main.tex")


def test_h6_literature_note_is_single_block():
    text = read("appendices/H_combinatorics_rd_tests.tex")
    assert text.count(r"\aodliteraturenote{Dyck/Catalan path combinatorics") == 1
    assert "Dyck/Catalan path combinatorics" in text
    assert "Markov kernels and random walks" in text
    segment = text.split(r"\aodliteraturenote{Dyck/Catalan path combinatorics", 1)[1].split(r"\aodremark", 1)[0]
    assert r"\aodliteraturenote{Markov kernels and random walks" not in segment

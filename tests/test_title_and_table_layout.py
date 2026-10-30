
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_title_pages_include_author_and_date():
    main_title = (ROOT / "sections" / "00_title.tex").read_text()
    manual_main = (ROOT / "manual" / "main.tex").read_text()
    preamble = (ROOT / "preamble.tex").read_text()
    manual_preamble = (ROOT / "manual" / "preamble.tex").read_text()
    assert "\\AODDocumentAuthor" in main_title
    assert "\\AODDocumentDate" in main_title
    assert "\\AODDocumentAuthor" in manual_main
    assert "\\AODDocumentDate" in manual_main
    assert "\\newcommand{\\AODDocumentAuthor}{Reginald Poyau}" in preamble
    assert "\\newcommand{\\AODDocumentDate}{June 1, 2026}" in preamble
    assert "\\newcommand{\\AODDocumentAuthor}{Reginald Poyau}" in manual_preamble
    assert "\\newcommand{\\AODDocumentDate}{June 1, 2026}" in manual_preamble

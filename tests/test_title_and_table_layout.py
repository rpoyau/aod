from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_title_pages_include_author_and_date():
    main_title = (ROOT / "latex" / "sections" / "00_title.tex").read_text()
    manual_main = (ROOT / "latex" / "manual" / "main.tex").read_text()
    preamble = (ROOT / "latex" / "preamble.tex").read_text()
    manual_preamble = (ROOT / "latex" / "manual" / "preamble.tex").read_text()
    assert "\\AODDocumentAuthor" in main_title
    assert "\\AODDocumentDate" in main_title
    assert "\\AODDocumentAuthor" in manual_main
    assert "\\AODDocumentDate" in manual_main
    assert "\\newcommand{\\AODDocumentAuthor}{Reginald Poyau}" in preamble
    assert "\\newcommand{\\AODDocumentDate}{June 1, 2026}" in preamble
    assert "\\newcommand{\\AODDocumentAuthor}{Reginald Poyau}" in manual_preamble
    assert "\\newcommand{\\AODDocumentDate}{June 1, 2026}" in manual_preamble
    # Canonical Typst title pages and schema carry the same author/date declarations
    typ_schema = (ROOT / "typst" / "lib" / "aod_schema.typ").read_text()
    assert '#let AODDocumentAuthor = "Reginald Poyau"' in typ_schema
    assert '#let AODDocumentDate = "June 1, 2026"' in typ_schema
    assert "#AODDocumentAuthor" in (ROOT / "typst" / "sections" / "00_title.typ").read_text()
    assert "#AODDocumentDate" in (ROOT / "typst" / "sections" / "00_title.typ").read_text()
    assert "#AODDocumentAuthor" in (ROOT / "typst" / "manual" / "main.typ").read_text()
    assert "#AODDocumentDate" in (ROOT / "typst" / "manual" / "main.typ").read_text()

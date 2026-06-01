
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
    assert "\\newcommand{\\AODDocumentDate}{December 2, 2025}" in preamble
    assert "\\newcommand{\\AODDocumentAuthor}{Reginald Poyau}" in manual_preamble
    assert "\\newcommand{\\AODDocumentDate}{December 2, 2025}" in manual_preamble


def test_wide_manual_tables_use_compact_widths():
    field = (ROOT / "manual" / "sections" / "06_field_dynamics_applications.tex").read_text()
    assert "p{0.18\\textwidth}p{0.11\\textwidth}p{0.24\\textwidth}p{0.17\\textwidth}p{0.15\\textwidth}p{0.13\\textwidth}" not in field
    assert "@{}p{0.16\\textwidth}p{0.08\\textwidth}p{0.42\\textwidth}p{0.26\\textwidth}@{}" in field
    assert "@{}p{0.16\\textwidth}p{0.08\\textwidth}p{0.32\\textwidth}p{0.36\\textwidth}@{}" in field
    assert "\\texttt{03\\_Fractal\\_Range\\_Max\\_Field\\_Support}" not in field
    assert "Fractal range / max field support" in field

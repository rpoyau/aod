"""Typed Main references fail closed and use the imported published numbers."""
import importlib.util
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
XELATEX = shutil.which("xelatex")
TARGETS = (
    "manual/sections/00_awareness_fixtures.tex",
    "manual/sections/00_native_closure_wave_temporal_fixtures.tex",
    "manual/sections/00_dec_ledger.tex",
)
SECTION_TARGETS = {
    "subsec:q4-hamming-ternary-kernel": "sections/06_wave_state_relational_time.tex",
    "sec:afc-stokes-seed": "sections/06_field.tex",
    "subsec:q4-four-edge-implementation": "sections/03_afc_basis.tex",
    "subsec:hinge-slide": "sections/06_wave_state_relational_time.tex",
    "subsec:sadar": "sections/06_field.tex",
}


def test_targeted_main_references_bind_to_numbered_equations_or_sections():
    spec = importlib.util.spec_from_file_location(
        "format_reference_audit", ROOT / "scripts/audit_scientific_sources.py"
    )
    audit = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = audit
    spec.loader.exec_module(audit)
    equations = audit.equations(ROOT)
    labels = audit.label_map(ROOT)
    references = []
    for path in TARGETS:
        text = (ROOT / path).read_text()
        for kind, key in re.findall(r"\\(mainequation|mainsection)\{main:([^}]+)\}", text):
            references.append((kind, key))
            assert key in labels, (path, key)
            if kind == "mainequation":
                assert key in equations, (path, key)
            else:
                assert key in SECTION_TARGETS
                assert labels[key]["path"] == SECTION_TARGETS[key]
    assert len(references) == 43
    assert ("mainequation", "eq:awareness-response") in references
    assert ("mainequation", "eq:fourier-transform") in references


def _argument_end(text, opening):
    """Find a note's closing group while retaining its nested source commands."""
    depth = 1
    for index in range(opening + 1, len(text)):
        if text[index] in "{}" and text[index - 1] != "\\":
            depth += 1 if text[index] == "{" else -1
            if depth == 0:
                return index + 1
    raise AssertionError("Unclosed Literature note")


def test_afc_citation_variants_are_confined_to_literature_notes():
    text = (ROOT / "sections/03_afc_basis.tex").read_text()
    notes = [
        (match.start(), _argument_end(text, match.end() - 1))
        for match in re.finditer(r"\\aodliteraturenote\s*\{", text)
    ]
    citations = list(re.finditer(
        r"\\[A-Za-z]*cite[A-Za-z]*\*?\s*(?:\[[^\]]*\]\s*)*\{([^}]+)\}", text
    ))
    afc = [match for match in citations if "afc" in [key.strip() for key in match[1].split(",")]]
    assert afc, "AFC attribution is required, including optional-note cite forms"
    for match in afc:
        assert any(start <= match.start() < match.end() <= end for start, end in notes)
    provenance = text.index(r"\paragraph{Provenance.}")
    literature = text.index(r"\aodliteraturenote", provenance)
    assert not any(provenance < match.start() < literature for match in citations)


def test_historical_role_headings_and_separate_awareness_stages_are_preserved():
    appendix = (ROOT / "appendices/A_fractal_address_bip_biz.tex").read_text()
    assert re.search(
        r"\\subsection\{Setup\}\s*\\label\{app:fractal-address:setup\}", appendix
    )
    assert re.search(
        r"\\subsection\{Statement\(s\)\}\s*\\label\{app:fractal-address:statements\}", appendix
    )
    awareness = (ROOT / "sections/08_awareness_learning_mindfulness.tex").read_text()
    assert r"\paragraph{Falsification and provenance.}" not in awareness
    assert awareness.count(r"\paragraph{Falsification.}") >= 4
    assert awareness.count(r"\paragraph{Provenance.}") >= 4


def _latex(directory):
    return subprocess.run(
        [XELATEX, "-recorder", "-interaction=nonstopmode", "-halt-on-error", "main.tex"],
        cwd=directory, capture_output=True, text=True, timeout=30,
    )


@pytest.fixture
def documents(tmp_path):
    if XELATEX is None:
        pytest.skip("XeLaTeX is required for reference integration tests")
    root = tmp_path / "source"
    manual = root / "manual"
    manual.mkdir(parents=True)
    (root / "main.tex").write_text(
        "\\documentclass{article}\n\\usepackage{amsmath,caption}\n\\usepackage{hyperref}\n"
        "\\begin{document}\n\\section{Source}\\label{sec:source}\n"
        "\\label{eq:prose}\n\\input{proof.tex}\n"
        "\\begin{table}\\caption{Source table}\\label{tab:source}\\end{table}\n"
        "\\appendix\\section{Appendix source}\\label{app:source}\n"
        "\\end{document}\n"
    )
    (root / "proof.tex").write_text(
        "\\setcounter{equation}{7}\n"
        "\\begin{equation}x=x\\label{eq:source}\\end{equation}\n"
        "\\begin{equation*}x=x\\tag{RG4}\\label{eq:tagged}\\end{equation*}\n"
    )
    (root / "refs.bib").write_text("% Declared Main bibliography.\n")
    for _ in range(2):
        result = _latex(root)
        assert result.returncode == 0, result.stdout
    shutil.copyfile(ROOT / "manual/preamble.tex", manual / "preamble.tex")
    return root, manual


def _manual(documents, content):
    _, manual = documents
    (manual / "main.tex").write_text(
        "\\documentclass{article}\n\\input{preamble.tex}\n"
        "\\begin{document}\n" + content + "\n\\end{document}\n"
    )
    return _latex(manual)


def test_imported_main_numbers_are_not_hardcoded(documents):
    result = _manual(documents, r"\mainequation{main:eq:source}; \mainsection{main:sec:source}.")
    assert result.returncode == 0, result.stdout
    _, manual = documents
    pdftotext = shutil.which("pdftotext")
    if pdftotext is not None:
        text = subprocess.run(
            [pdftotext, str(manual / "main.pdf"), "-"], capture_output=True,
            text=True, check=True, timeout=10,
        ).stdout
        assert "Main (8)" in text
        assert "Main §1" in text
    log = (manual / "main.log").read_text()
    assert "Reference `main:" not in log
    # xr-hyper's imported URL is the delivered root sibling, not ../main.pdf.
    probe = _manual(documents, r"\makeatletter\typeout{AOD-URL:\getrefbykeydefault{main:eq:source}{url}{MISSING}}\makeatother")
    assert probe.returncode == 0, probe.stdout
    assert "AOD-URL:main.pdf" in probe.stdout


@pytest.mark.parametrize("filename", ["main.aux", "main.fls"])
def test_missing_main_build_file_is_rejected(documents, filename):
    root, _ = documents
    (root / filename).unlink()
    result = _manual(documents, r"\mainequation{main:eq:source}")
    assert result.returncode != 0
    assert "Missing Main build file" in result.stdout


def test_main_input_newer_than_aux_is_rejected(documents):
    root, _ = documents
    when = (root / "main.aux").stat().st_mtime + 5
    os.utime(root / "proof.tex", (when, when))
    result = _manual(documents, r"\mainequation{main:eq:source}")
    assert result.returncode != 0
    assert "Stale Main AUX" in result.stdout
    assert "proof.tex" in result.stdout


def test_main_bibliography_newer_than_aux_is_rejected(documents):
    root, _ = documents
    when = (root / "main.aux").stat().st_mtime + 5
    os.utime(root / "refs.bib", (when, when))
    result = _manual(documents, r"\mainequation{main:eq:source}")
    assert result.returncode != 0
    assert "Stale Main AUX" in result.stdout
    assert "refs.bib" in result.stdout


def test_missing_recorded_main_input_is_rejected(documents):
    root, _ = documents
    (root / "proof.tex").unlink()
    result = _manual(documents, r"\mainequation{main:eq:source}")
    assert result.returncode != 0
    assert "Missing Main input" in result.stdout


def test_newer_generated_main_bbl_is_not_a_manual_input(documents):
    root, manual = documents
    bbl = root / "main.bbl"
    bbl.write_text("Generated Main bibliography.\n")
    when = (root / "main.aux").stat().st_mtime + 5
    os.utime(bbl, (when, when))
    with (root / "main.fls").open("a") as stream:
        stream.write("INPUT ./main.bbl\n")
    result = _manual(documents, r"\mainequation{main:eq:source}")
    assert result.returncode == 0, result.stdout
    assert "main.bbl" not in (manual / "main.fls").read_text()


def test_main_bibliography_labels_are_not_imported(documents):
    root, _ = documents
    with (root / "main.aux").open("a") as stream:
        stream.write("\\bibcite{samekey}{99}\n")
    result = _manual(documents, (
        r"\makeatletter\@ifundefined{b@main:samekey}"
        r"{\typeout{AOD-BIB:ISOLATED}}{\typeout{AOD-BIB:LEAKED}}\makeatother"
    ))
    assert result.returncode == 0, result.stdout
    assert "AOD-BIB:ISOLATED" in result.stdout


def test_unresolved_main_key_is_rejected(documents):
    result = _manual(documents, r"\mainequation{main:eq:absent}")
    assert result.returncode != 0
    assert "Unresolved Main reference" in result.stdout


def test_imported_tagged_equation_appendix_and_table_render_their_types(documents):
    result = _manual(documents, (
        r"\mainequation{main:eq:tagged}; \mainappendix{main:app:source}; "
        r"\maintable{main:tab:source}."
    ))
    assert result.returncode == 0, result.stdout
    pdftotext = shutil.which("pdftotext")
    if pdftotext is not None:
        text = subprocess.run(
            [pdftotext, str(documents[1] / "main.pdf"), "-"], capture_output=True,
            text=True, check=True, timeout=10,
        ).stdout
        assert "Main (RG4)" in text
        assert "Main App. A" in text
        assert "Main Table 1" in text


def test_non_rg_ams_anchor_is_rejected_as_a_main_equation(documents):
    root, _ = documents
    with (root / "main.aux").open("a") as stream:
        stream.write("\\newlabel{eq:fake}{{Scope}{1}{Prose}{AMS.999}{}}\n")
    result = _manual(documents, r"\mainequation{main:eq:fake}")
    assert result.returncode != 0
    assert "Wrong Main reference type" in result.stdout


@pytest.mark.parametrize("content", [
    r"\mainequation{main:sec:source}",
    r"\mainequation{main:eq:prose}",
    r"\mainsection{main:eq:source}",
    r"\mainsection{main:app:source}",
    r"\mainappendix{main:sec:source}",
    r"\mainappendix{main:tab:source}",
    r"\maintable{main:eq:source}",
    r"\maintable{main:app:source}",
    r"\mainequation{main:tab:source}",
])
def test_wrong_main_reference_type_is_rejected(documents, content):
    result = _manual(documents, content)
    assert result.returncode != 0
    assert "Wrong Main reference type" in result.stdout

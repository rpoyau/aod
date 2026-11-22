from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_all_main_source():
    parts = [ROOT / 'latex/main.tex']
    parts.extend(sorted((ROOT / 'latex/sections').glob('*.tex')))
    parts.extend(sorted((ROOT / 'latex/appendices').glob('*.tex')))
    return '\n'.join(p.read_text() for p in parts)


def test_main_note_container_language_minimalism_replacements_present():
    import importlib.util
    spec = importlib.util.spec_from_file_location("source_audit", ROOT / "scripts/audit_scientific_sources.py")
    audit = importlib.util.module_from_spec(spec); spec.loader.exec_module(audit)
    main_typ = "\n".join(text for _, text in audit.include_graph(ROOT)[1])
    main_tex = "\n".join(text for _, text in audit.latex_include_graph(ROOT)[1])
    assert "<eq:cycle-valued-field-compression>" in main_typ
    assert "<eq:cycle-rd-accessor>" in main_typ
    assert "<app:proto:eq:four-step-load>" in main_typ
    assert "Under the declared single-hinge neutral-reflection" in main_typ
    assert r"\label{eq:cycle-valued-field-compression}" in main_tex
    assert r"\label{eq:cycle-rd-accessor}" in main_tex
    assert r"\label{app:proto:eq:four-step-load}" in main_tex
    assert "Under the declared single-hinge neutral-reflection" in main_tex

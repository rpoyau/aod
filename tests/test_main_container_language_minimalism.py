from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_all_main_source():
    parts = [ROOT / 'main.tex']
    parts.extend(sorted((ROOT / 'sections').glob('*.tex')))
    parts.extend(sorted((ROOT / 'appendices').glob('*.tex')))
    return '\n'.join(p.read_text() for p in parts)


def test_main_note_container_language_minimalism_strings_absent():
    text = read_all_main_source()
    forbidden = [
        'A calculation table may store',
        'Integer fixture rows',
        'declared fixture rows',
        'claimed RD row',
        'walk-support row',
        '4-step closure row',
        'manual uses these values',
        'manual rest-energy calculation entries',
        'The table uses the declared',
    ]
    for term in forbidden:
        assert term not in text


def test_main_note_container_language_minimalism_replacements_present():
    import importlib.util
    spec=importlib.util.spec_from_file_location("source_audit",ROOT/"scripts/audit_scientific_sources.py")
    audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
    main="\n".join(text for path,text in audit.include_graph(ROOT)[1])
    manual="\n".join(text for path,text in audit.include_graph(ROOT,"manual")[1])
    assert "The declared integer reductions are" in main
    assert r"\label{eq:cycle-valued-field-compression}" in main
    assert r"\label{eq:cycle-rd-accessor}" in main
    assert r"\label{app:proto:eq:four-step-load}" in manual
    assert r"\label{tab:ao-field-fractal-properties}" in manual
    assert "Under the declared single-hinge neutral-reflection" in manual

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
    text = read_all_main_source()
    assert 'The scalar accessors \\(RD_{\\AO}\\), \\(\\rho^D_\\omega\\), \\(P^D\\), and \\(Q^D\\) are obtained from \\(C_f[\\Sigma]_{\\AO}\\)' in text
    assert r'\subsection{Integer support reductions}\label{app:rd-tests:support-reductions}' in text
    assert 'The declared integer reductions are' in text
    assert 'This appendix records integer path-complexity reductions and 4-step closure controls' in text
    assert 'A declared 4-step closure reduction is contradicted on a scope' in text
    assert 'This appendix records A\\(\\Omega\\) field-support accessors and field-property invariants.' in text
    assert 'Under the declared single-hinge neutral-reflection field-property reduction' in text

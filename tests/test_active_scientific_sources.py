import importlib.util, json, sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('audit_scientific_sources', ROOT / 'scripts/audit_scientific_sources.py')
a = importlib.util.module_from_spec(spec); sys.modules[spec.name] = a; spec.loader.exec_module(a)


def test_rendered_scientific_authority_and_equations():
    result = a.audit(ROOT)
    assert result['canonical_authority'] == 'typst'
    assert result['equation_contracts'] >= 20


def test_manual_rows_bind_active_main_and_manual_constructs():
    import csv
    main = a.label_map(ROOT); manual = a.label_map(ROOT, 'manual'); rows = []
    for p in (ROOT / 'manual/data/native_closure_wave').glob('*.csv'):
        with p.open() as f:
            rows.extend(csv.DictReader(f))
    assert len({r['fixture_id'] for r in rows}) == len(rows) >= 80
    for row in rows:
        assert row['main_anchor'] in main
        assert row['manual_anchor'] in manual
        assert row['input_trace'] and row['expected_verdict'] in ('PASS', 'REJECT')


def test_conditional_hidden_file_cannot_supply_science(tmp_path):
    (tmp_path / 'main.tex').write_text('\\iffalse\\input{hidden.tex}\\fi')
    (tmp_path / 'hidden.tex').write_text('\\label{eq:closure-phase}\\Delta\\Phi(C)=1_C')
    assert 'eq:closure-phase' not in a.label_map(tmp_path)


@pytest.mark.parametrize('invoked', [True, False], ids=['executed-display', 'uninvoked-macro'])
def test_actual_build_requires_execution_of_scientific_labels(tmp_path, invoked):
    import shutil, subprocess
    xelatex = shutil.which('xelatex')
    if xelatex is None:
        pytest.skip('XeLaTeX is required for executed-source integration controls')
    display = (r'\begin{equation}\operatorname{Close}(C)=1\;\not\Rightarrow\;'
               r'\operatorname{Isotropic}(C).\label{eq:closure-not-isotropy}\end{equation}')
    body = display if invoked else r'\newcommand{\UnusedCanonicalDisplay}{' + display + '}'
    (tmp_path / 'main.tex').write_text(
        r'\documentclass{article}\usepackage{amsmath}\begin{document}'
        + 'Publication control.\n' + body + '\n' + r'\end{document}')
    assert a.equations(tmp_path)['eq:closure-not-isotropy'] == display
    result = subprocess.run(
        [xelatex, '-recorder', '-interaction=nonstopmode', '-halt-on-error', 'main.tex'],
        cwd=tmp_path, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout
    if invoked:
        assert a.actual_build(tmp_path, tmp_path, 'main')['actual_labels'] == 1
    else:
        with pytest.raises(ValueError, match='source label absent from actual aux eq:closure-not-isotropy'):
            a.actual_build(tmp_path, tmp_path, 'main')


def test_unrelated_active_heading_cannot_satisfy_conservation():
    expected = {'source:closure': {'source_content_sha256': 'original-source-equation',
        'destinations': [{'surface': 'main', 'path': 'typst/sections/04_cut_running_fractal_tesseract.typ', 'label': 'eq:closure-phase'}],
        'proof_correspondence': 'one certified closure contributes one complete closure-phase cycle'}}
    good = {'source_id': 'source:closure', 'source_content_sha256': 'original-source-equation',
        'destinations_json': json.dumps(expected['source:closure']['destinations']),
        'proof_correspondence': expected['source:closure']['proof_correspondence']}
    assert a.audit_conservation([good], expected, ROOT) == 1
    bad = dict(good, destinations_json=json.dumps([{'surface': 'main', 'path': 'typst/sections/06_field.typ', 'label': 'eq:fourier-transform'}]))
    with pytest.raises(ValueError, match='unrelated scientific construction'):
        a.audit_conservation([bad], expected, ROOT)


def test_canonical_closure_phase_labels_are_active_and_typed():
    files, _ = a.include_graph(ROOT)
    assert 'typst/sections/04_cut_running_fractal_tesseract.typ' in files
    labels = a.label_map(ROOT)
    assert labels['eq:closure-phase-step-count']['path'] == 'typst/sections/04_cut_running_fractal_tesseract.typ'
    assert labels['eq:minimal-phase-quantum-bound']['path'] == 'typst/sections/04_cut_running_fractal_tesseract.typ'


def test_m2_canonical_science_and_manual_fixture_are_rendered():
    mf = a.include_graph(ROOT)[0]; uf = a.include_graph(ROOT, 'manual')[0]
    assert 'typst/sections/08_awareness_learning_mindfulness.typ' in mf
    fixture = 'typst/manual/sections/00_awareness_fixtures.typ'; assert fixture in uf
    # Verify both canonical Typst authority and generated LaTeX compatibility equations
    typ_main = a.equations(ROOT)
    typ_manual = a.equations(ROOT, 'manual')
    gen_main = a.latex_equations(ROOT)
    gen_manual = a.latex_equations(ROOT, 'manual')
    bindings = {
        'eq:awareness-state-factorization': (r'S_k^+=(X_k,M^C_k,R_k)', r'S_k^(+)=(X_k,M^C_k,R_k)'),
        'eq:awareness-active': (r'\exists t>k', r'existst>k'),
        'eq:awareness-response': (r'J_{k+1}=J_k+\frac{A_k+q_k+g\sum', r'J_(k+1)=J_k+frac(A_k+q_k+gsum'),
        'eq:awareness-causal-difference': (r'\frac{g}{p}', r'frac(g,p)'),
        'eq:operative-source-removal': (r'R_{k,i}&:=\{R_e\in R_k:i_e=i\}', r'R_(k,i)&:=brace.lR_einR_k:i_e=ibrace.r'),
        'eq:operative-self': (r'S_k^{+,-i}', r'S_k^(+,-i)'),
        'eq:action-return-retention': (r'r_a=y-u', r'r_a=y-u'),
        'eq:awareness-carriage': (r'R^{\uparrow}', r'R^(arrow.t)'),
        'eq:mindfulness-stability': (r'J_{k+1}-b=', r'J_(k+1)-b='),
    }
    moved = {'eq:awareness-response', 'eq:awareness-causal-difference',
             'eq:action-return-retention', 'eq:mindfulness-stability'}
    for lab, (tex_form, typ_form) in bindings.items():
        t_owner = typ_manual if lab in moved else typ_main
        t_other = typ_main if lab in moved else typ_manual
        g_owner = gen_manual if lab in moved else gen_main
        assert lab not in t_other
        assert a.normalize_math(typ_form) in a.normalize_math(t_owner[lab])
        assert a.normalize_math(tex_form) in a.normalize_math(g_owner[lab])
    removal = a.normalize_math(gen_main['eq:operative-source-removal'])
    assert a.normalize_math(r'S_k^{+,-i}&:=(X_k,M^C_k,R_k\setminus R_{k,i})') in removal
    operative = a.normalize_math(gen_main['eq:operative-self'])
    assert a.normalize_math(r'\mathcal{U}(S_k^+;E)') in operative
    assert a.normalize_math(r'\mathcal{U}(S_k^{+,-i};E)') in operative
    assert 'manual:m2-awareness-fixtures' in a.label_map(ROOT, 'manual')


def test_m2_data_rows_bind_active_definitions_and_exact_source():
    import hashlib
    rows = [json.loads(t) for t in (ROOT / 'manual/data/awareness/awareness_cases.jsonl').read_text().splitlines()]
    assert len(rows) == 47 and len({x['fixture_id'] for x in rows}) == 47
    maps = {s: a.label_map(ROOT, s) for s in ('main', 'manual')}
    bindings = json.loads((ROOT / 'contracts/scientific/OWNERSHIP_AND_FIXTURES.json').read_text())['fixture_bindings']
    assert a.audit(ROOT)['compaction']['canonical_equations'] == 81
    for x, binding in zip(rows, bindings):
        assert x['fixture_id'] == binding['fixture_id']
        assert x['main_anchor'] == binding['immutable_legacy_main_anchor']
        current = binding['current_construct']
        assert maps[current['surface']][current['label']]['path'] == current['path']
        assert x['manual_anchor'] in maps['manual']
        assert x['source_sha256'] == hashlib.sha256((ROOT / x['source']).read_bytes()).hexdigest()
        assert x['fixture_id'].startswith('R04-NEW-') and x['randomness'] == 'none'
        assert x['record_class'] == 'DECLARED_EXACT_MODEL'


def test_registered_scientific_sources_and_anchors_are_byte_bound():
    records = a.validate_contract_inventory(ROOT)
    assert set(records) == set(a.SCIENTIFIC_CONTRACT_SCHEMAS)
    checked = a.validate_active_specifications(ROOT, records)
    assert checked == ['contracts/scientific/AWARENESS_ACTIVE_CAUSAL_SPEC.json']
    record = records['AWARENESS_ACTIVE_CAUSAL_SPEC.json']
    assert {'eq:awareness-operative-set', 'eq:operative-self', 'eq:awareness-shedding-bridge',
            'eq:awareness-conditioned-shedding'} <= set(record['source_anchors'])


def test_m2_displayed_sum_indices_and_empty_self_match_the_declared_types():
    gen_main = a.latex_equations(ROOT)
    difference = a.normalize_math(a.latex_equations(ROOT, 'manual')['eq:awareness-causal-difference'])
    assert a.normalize_math(r'\sum_{e:\,i_e\in D_k}r_e') in difference
    assert a.normalize_math(r"\sum_{e:\,i_e\in D_k}r'_e") in difference
    empty = a.normalize_math(gen_main['eq:operative-self'])
    assert a.normalize_math(r'\emptyset,&I^{\mathrm{op}}_k=\emptyset') in empty
    typ_empty = a.normalize_math(a.equations(ROOT)['eq:operative-self'])
    assert a.normalize_math(r'emptyset\,&I^(upright("op"))_k=emptyset') in typ_empty

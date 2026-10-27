import importlib.util,json,sys
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('audit_scientific_sources',ROOT/'scripts/audit_scientific_sources.py')
a=importlib.util.module_from_spec(spec);sys.modules[spec.name]=a;spec.loader.exec_module(a)


def test_rendered_scientific_authority_and_equations():
    result=a.audit(ROOT)
    assert result['equation_contracts']>=20


def test_manual_rows_bind_active_main_and_manual_constructs():
    import csv
    main=a.label_map(ROOT);manual=a.label_map(ROOT,'manual');rows=[]
    for p in (ROOT/'manual/data/m1').glob('*.csv'):
        with p.open() as f:rows.extend(csv.DictReader(f))
    assert len({r['fixture_id'] for r in rows})==len(rows)>=80
    for row in rows:
        assert row['main_anchor'] in main
        assert row['manual_anchor'] in manual
        assert row['input_trace'] and row['expected_verdict'] in ('PASS','REJECT')


def test_conditional_hidden_file_cannot_supply_science(tmp_path):
    (tmp_path/'main.tex').write_text('\\iffalse\\input{hidden.tex}\\fi')
    (tmp_path/'hidden.tex').write_text('\\label{eq:closure-phase}\\Delta\\Phi(C)=1_C')
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
    # Both sources satisfy the same static mathematical-body lookup.
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
    expected={'source:closure':{'source_content_sha256':'original-source-equation',
        'destinations':[{'surface':'main','path':'sections/04_cut_running_fractal_tesseract.tex','label':'eq:closure-phase'}],
        'proof_correspondence':'one certified closure contributes one complete closure-phase cycle'}}
    good={'source_id':'source:closure','source_content_sha256':'original-source-equation',
        'destinations_json':json.dumps(expected['source:closure']['destinations']),
        'proof_correspondence':expected['source:closure']['proof_correspondence']}
    assert a.audit_conservation([good],expected,ROOT)==1
    bad=dict(good,destinations_json=json.dumps([{'surface':'main','path':'sections/06_field.tex','label':'eq:fourier-transform'}]))
    with pytest.raises(ValueError,match='unrelated scientific construction'):a.audit_conservation([bad],expected,ROOT)


def test_canonical_closure_phase_language_is_rendered_and_typed():
    files,parts=a.include_graph(ROOT)
    assert 'sections/04_cut_running_fractal_tesseract.tex' in files
    rendered='\n'.join(text for _,text in parts)
    assert 'one complete closure-phase cycle' in rendered
    assert 'phase-bearing step count' in rendered
    assert 'never sufficient closure admission' in rendered
    labels=a.label_map(ROOT)
    assert labels['eq:closure-phase-step-count']['path']=='sections/04_cut_running_fractal_tesseract.tex'
    assert labels['eq:minimal-phase-quantum-bound']['path']=='sections/04_cut_running_fractal_tesseract.tex'


def test_required_scientific_objects_precede_dependent_operations():
    labels=a.label_map(ROOT)
    assert labels['eq:cycle-valued-field-compression']['position']<labels['eq:cycle-rd-accessor']['position']
    assert labels['eq:causal-update']['position']<labels['eq:support-trace-spine']['position']


def test_m2_canonical_science_and_manual_fixture_are_rendered():
    mf=a.include_graph(ROOT)[0];uf=a.include_graph(ROOT,'manual')[0]
    assert 'sections/08_awareness_learning_mindfulness.tex' in mf
    fixture='manual/sections/00_awareness_fixtures.tex';assert fixture in uf
    assert uf.index('manual/sections/00_native_closure_wave_temporal_fixtures.tex')<uf.index(fixture)<uf.index('manual/sections/00_dec_ledger.tex')
    equations=a.equations(ROOT)
    bindings={'eq:awareness-state-factorization':r'S_k^+=(X_k,M^C_k,R_k)',
              'eq:awareness-active':r'\exists t>k',
              'eq:awareness-response':r'J_{k+1}=J_k+\frac{A_k+q_k+g\sum',
              'eq:awareness-causal-difference':r'\frac{g}{p}',
              'eq:operative-source-removal':r'R_{k,i}&:=\{R_e\in R_k:i_e=i\}',
              'eq:operative-self':r'S_k^{+,-i}',
              'eq:action-return-retention':r'r_a=y-u',
              'eq:awareness-carriage':r'R^{\uparrow}',
              'eq:mindfulness-stability':r'J_{k+1}-b='}
    local = a.equations(ROOT, 'manual')
    moved = {'eq:awareness-response', 'eq:awareness-causal-difference',
             'eq:action-return-retention', 'eq:mindfulness-stability'}
    for lab, formula in bindings.items():
        owner = local if lab in moved else equations
        other = equations if lab in moved else local
        assert lab not in other
        assert a.normalize_math(formula) in a.normalize_math(owner[lab])
    removal = a.normalize_math(equations['eq:operative-source-removal'])
    assert a.normalize_math(r'S_k^{+,-i}&:=(X_k,M^C_k,R_k\setminus R_{k,i})') in removal
    operative = a.normalize_math(equations['eq:operative-self'])
    assert a.normalize_math(r'\mathcal U(S_k^+;E)') in operative
    assert a.normalize_math(r'\mathcal U(S_k^{+,-i};E)') in operative
    assert 'manual:m2-awareness-fixtures' in a.label_map(ROOT,'manual')


def test_m2_data_rows_bind_active_definitions_and_exact_source():
    import hashlib
    rows=[json.loads(t) for t in (ROOT/'manual/data/m2/awareness_cases.jsonl').read_text().splitlines()]
    assert len(rows)==47 and len({x['fixture_id'] for x in rows})==47
    maps = {s: a.label_map(ROOT, s) for s in ('main', 'manual')}
    bindings = json.loads((ROOT/'contracts/scientific/OWNERSHIP_AND_FIXTURES.json').read_text())['fixture_bindings']
    assert a.audit(ROOT)['compaction']['canonical_equations'] == 81
    for x, binding in zip(rows, bindings):
        assert x['fixture_id'] == binding['fixture_id']
        assert x['main_anchor'] == binding['immutable_legacy_main_anchor']
        current = binding['current_construct']
        assert maps[current['surface']][current['label']]['path'] == current['path']
        assert x['manual_anchor'] in maps['manual']
        assert x['source_sha256']==hashlib.sha256((ROOT/x['source']).read_bytes()).hexdigest()
        assert x['fixture_id'].startswith('R04-NEW-') and x['randomness']=='none'
        assert x['record_class']=='DECLARED_EXACT_MODEL'


def test_registered_scientific_sources_and_anchors_are_byte_bound():
    records = a.validate_contract_inventory(ROOT)
    assert set(records) == set(a.SCIENTIFIC_CONTRACT_SCHEMAS)
    checked = a.validate_active_specifications(ROOT, records)
    assert checked == ['contracts/scientific/AWARENESS_ACTIVE_CAUSAL_SPEC.json']
    record = records['AWARENESS_ACTIVE_CAUSAL_SPEC.json']
    assert {'eq:awareness-operative-set', 'eq:operative-self', 'eq:awareness-shedding-bridge',
            'eq:awareness-conditioned-shedding'} <= set(record['source_anchors'])


def test_m2_displayed_sum_indices_and_empty_self_match_the_declared_types():
    eq=a.equations(ROOT)
    difference=a.normalize_math(a.equations(ROOT, 'manual')['eq:awareness-causal-difference'])
    assert a.normalize_math(r'\sum_{e:\,i_e\in D_k}r_e') in difference
    assert a.normalize_math(r"\sum_{e:\,i_e\in D_k}r'_e") in difference
    empty=a.normalize_math(eq['eq:operative-self'])
    assert a.normalize_math(r'\varnothing,&I^{\rm op}_k=\varnothing') in empty

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


def test_unrelated_active_heading_cannot_satisfy_conservation():
    expected={'source:closure':{'source_content_sha256':'original-source-equation',
        'destinations':[{'surface':'main','path':'sections/04_closure_phase_wave.tex','label':'eq:closure-phase'}],
        'proof_correspondence':'one certified closure contributes one phase'}}
    good={'source_id':'source:closure','source_content_sha256':'original-source-equation',
        'destinations_json':json.dumps(expected['source:closure']['destinations']),
        'proof_correspondence':expected['source:closure']['proof_correspondence']}
    assert a.audit_conservation([good],expected,ROOT)==1
    bad=dict(good,destinations_json=json.dumps([{'surface':'main','path':'sections/07_stokes_sadar_harmonic_boundary.tex','label':'eq:fourier-transform'}]))
    with pytest.raises(ValueError,match='unrelated scientific construction'):a.audit_conservation([bad],expected,ROOT)


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
    bindings={'eq:awareness-state-factorization':r'S^+_k=(X_k,M^C_k,R_k)',
              'eq:awareness-active':r'\exists t>k',
              'eq:awareness-response':r'J_{k+1}=J_k+\frac{A_k+q_k+g\sum',
              'eq:awareness-causal-difference':r'\frac{g}{p}',
              'eq:operative-self':r'S_k\setminus R_i',
              'eq:action-return-retention':r'r_a=y-u',
              'eq:awareness-carriage':r'R^{\uparrow}',
              'eq:mindfulness-stability':r'J_{k+1}-b='}
    for lab,formula in bindings.items():assert a.normalize_math(formula) in a.normalize_math(equations[lab])
    assert 'manual:m2-awareness-fixtures' in a.label_map(ROOT,'manual')


def test_m2_data_rows_bind_active_definitions_and_exact_source():
    import hashlib
    rows=[json.loads(t) for t in (ROOT/'manual/data/m2/awareness_cases.jsonl').read_text().splitlines()]
    assert len(rows)==47 and len({x['fixture_id'] for x in rows})==47
    main=a.label_map(ROOT);manual=a.label_map(ROOT,'manual')
    for x in rows:
        assert x['main_anchor'] in main and x['manual_anchor'] in manual
        assert x['source_sha256']==hashlib.sha256((ROOT/x['source']).read_bytes()).hexdigest()
        assert x['fixture_id'].startswith('R04-NEW-') and x['randomness']=='none'
        assert x['record_class']=='DECLARED_EXACT_MODEL'


def test_m2_displayed_sum_indices_and_empty_self_match_the_declared_types():
    eq=a.equations(ROOT)
    difference=a.normalize_math(eq['eq:awareness-causal-difference'])
    assert a.normalize_math(r'\sum_{e:\,i_e\in D_k}r_e') in difference
    assert a.normalize_math(r"\sum_{e:\,i_e\in D_k}r'_e") in difference
    empty=a.normalize_math(eq['eq:operative-self'])
    assert a.normalize_math(r'\varnothing,&I^{\rm op}_k=\varnothing') in empty

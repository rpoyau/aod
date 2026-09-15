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

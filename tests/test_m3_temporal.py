"""M3 scoped temporal admission, SI mapping and information separation."""
from copy import deepcopy
from dataclasses import replace
from fractions import Fraction as Q
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'manual/scripts'))
import aod_m3_temporal as t
import aod_native_closure_wave as n
import aod_mapping_error as m


def test_actual_admission_coupling_and_directional_records():
    v=t.adapt(t.example())
    assert v['counts']=={'compared':3,'reference':2}
    assert v['forward']['ratio']=='3/2' and v['reverse']['ratio']=='2/3'
    assert v['forward']['duration']==5 and v['reverse']['duration']==7
    assert v['forward']['lag']=='3/2' and v['reverse']['lag']=='-3/2'
    assert v['complete_input']['left']['certificates']


def test_scheduler_alias_scope_window_and_contact_substitutions_rejected():
    r=t.example()
    bad=[{'left':3,'right':2},replace(r,right=r.left),replace(r,window=(0,10)),
         replace(r,contacts=r.contacts[:1]),replace(r,right=replace(r.right,scope='elsewhere')),
         replace(r,contacts=(replace(r.contacts[0],left_prefix='forged'),r.contacts[1]))]
    for value in bad:
        with pytest.raises((ValueError,n.AdmissionError)):t.adapt(value)


def test_si_epoch_gain_and_typed_contract():
    p=t.predict(t.example(),epoch='13')
    assert Q(p['mapped']['outputs']['elapsed_seconds']['value'])==2/t.CS
    assert Q(p['mapped']['outputs']['average_rate_hz']['value'])==3*t.CS/2
    assert Q(p['end_coordinate_seconds'])==13+2/t.CS
    assert p['derived_reciprocal_period_seconds']!=p['mapped']['outputs']['elapsed_seconds']['value']
    assert p['atomic_prediction'] is None and p['complete_physical_standard_uncertainty'] is None
    f,trusted=t.si_contract(t.example())
    values={x['name']:m.value(x,trusted['native:temporal']['payload'][x['name']],{'native:temporal':trusted['native:temporal']['sha256']},
                            origin={'kind':'source','source_id':'native:temporal','payload_key':x['name']}) for x in f['domain']}
    wrong=deepcopy(values);wrong['reference']['port']['kind']='scheduler_cut'
    with pytest.raises(m.ContractError):m.run_map(f,wrong,trusted)
    for g in ('0','-1'):
        with pytest.raises(ValueError):t.predict(t.example(),reference_gain=g)


def test_target_change_cannot_modify_prediction_bytes_and_gain_is_free():
    p=t.predict(t.example());before=m.canonical(p)
    target={'id':'H','frequency_hz':'1','exposure':'retrospective','prediction_cross_covariance':None}
    a=t.evaluate(p,target);b=t.evaluate(p,{**target,'frequency_hz':'2'})
    assert m.canonical(p)==before and a['prediction_sha256']==b['prediction_sha256']
    assert Q(a['diagnostic_residual_hz'])-Q(b['diagnostic_residual_hz'])==1
    with pytest.raises(ValueError):t.evaluate(p,{**target,'exposure':'blind'})
    q=t.predict(t.example(),compared_gain='2')
    assert q['mapped']['outputs']['elapsed_seconds']==p['mapped']['outputs']['elapsed_seconds'] or Q(q['mapped']['outputs']['elapsed_seconds']['value'])==Q(p['mapped']['outputs']['elapsed_seconds']['value'])
    assert Q(q['mapped']['outputs']['average_rate_hz']['value'])==2*Q(p['mapped']['outputs']['average_rate_hz']['value'])


def test_window_change_recomputes_counts_and_unwrapped_lag():
    r=t.example();v=t.adapt(r)
    short=replace(r,window=(0,23));w=t.adapt(short)
    assert w['counts']['compared']==2 and v['counts']['compared']==3
    assert Q(v['forward']['lag'])-Q(w['forward']['lag'])==1
    assert v['forward']['duration']==w['forward']['duration']


def test_no_evaluation_source_in_conditional_map():
    f,trusted=t.si_contract(t.example())
    f=deepcopy(f);f['sources'][0]['role']='evaluation';trusted=deepcopy(trusted);trusted[f['sources'][0]['id']]=f['sources'][0]
    with pytest.raises(m.ContractError,match='evaluation'):m.validate_map(m.seal(f),trusted)


def test_stored_report_reconstructs():
    import json
    assert json.loads(t.REPORT.read_text())==t.report()


def test_public_contract_rejects_resealed_derived_count_dictionary():
    document=t.adapt(t.example())
    document['counts']['compared']=999
    with pytest.raises(ValueError,match='complete typed temporal record'):
        t.si_contract(document)


@pytest.mark.skipif(not (Path(__file__).resolve().parents[2]/'matter-i').is_dir(),reason='separately bound Matter I checkout absent')
def test_actual_consumer_feedback_intervention_and_mutation():
    evidence=t.consumer_integration(Path(__file__).resolve().parents[2]/'matter-i')
    assert evidence['common_prefix_through_cut']==39
    assert evidence['feedback_disabled_original_validator_rejected']
    cases=evidence['cases']
    assert cases['baseline']['counts']=={'outer_plus':6,'outer_minus':5}
    assert cases['intervention']['counts']=={'outer_plus':2,'outer_minus':5}
    assert cases['feedback_disabled']['finite_window_average_hz']==cases['baseline']['finite_window_average_hz']
    assert cases['baseline']['generic_mapping_execution']['result']['outputs']['average_rate_hz']['value']==cases['baseline']['finite_window_average_hz']
    assert cases['feedback_disabled']['generic_mapping_execution'] is None
    assert evidence['atomic_point_prediction']['frequency_hz'] is None

"""M3 scoped temporal admission, SI mapping and information separation."""
from copy import deepcopy
from dataclasses import replace
from fractions import Fraction as Q
import json
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'manual/scripts'))
import aod_m3_temporal as t
import aod_native_closure_wave as n
import aod_mapping_error as m


def original_context(record=None, **changes):
    return {'original_record':record if record is not None else t.example(),
            'compared_gain':'1', 'reference_gain':'1', 'epoch':'0',
            'coordinate':'stipulated:local', **changes}


def target():
    return {'id':'H','frequency_hz':'1','exposure':'retrospective','prediction_cross_covariance':None}


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
    assert f['version']=='2'
    assert set(f['error'])=={'elapsed_seconds','average_rate_hz'}
    for port in f['codomain']:
        budget=f['error'][port['name']]
        assert {c['unit'] for c in budget.values()}=={port['unit']}
        for component in ('window','calibration','model_discrepancy'):
            assert budget[component]['kind']=='unknown'
            assert 'value' not in budget[component]
    values={x['name']:m.value(x,trusted['native:temporal']['payload'][x['name']],{'native:temporal':trusted['native:temporal']['sha256']},
                            origin={'kind':'source','source_id':'native:temporal','payload_key':x['name']}) for x in f['domain']}
    wrong=deepcopy(values);wrong['reference']['port']['kind']='scheduler_cut'
    with pytest.raises(m.ContractError):m.run_map(f,wrong,trusted)
    for g in ('0','-1'):
        with pytest.raises(ValueError):t.predict(t.example(),reference_gain=g)


def test_target_change_cannot_modify_prediction_bytes_and_gain_is_free():
    context=original_context();p=t.predict(context['original_record']);before=m.canonical(p)
    a=t.evaluate(p,target(),**context);b=t.evaluate(p,{**target(),'frequency_hz':'2'},**context)
    assert m.canonical(p)==before and a['prediction_sha256']==b['prediction_sha256']
    assert a['evaluation_sha256']!=b['evaluation_sha256']
    assert Q(a['diagnostic_residual_hz'])-Q(b['diagnostic_residual_hz'])==1
    with pytest.raises(ValueError):t.evaluate(p,{**target(),'exposure':'blind'},**context)
    q=t.predict(t.example(),compared_gain='2')
    assert q['mapped']['outputs']['elapsed_seconds']==p['mapped']['outputs']['elapsed_seconds'] or Q(q['mapped']['outputs']['elapsed_seconds']['value'])==Q(p['mapped']['outputs']['elapsed_seconds']['value'])
    assert Q(q['mapped']['outputs']['average_rate_hz']['value'])==2*Q(p['mapped']['outputs']['average_rate_hz']['value'])


def test_evaluation_accepts_json_roundtrip_with_complete_original_context():
    context=original_context(compared_gain='3/2',reference_gain='4/3',epoch='13',coordinate='stipulated:alternate')
    p=t.predict(context['original_record'],**{k:v for k,v in context.items() if k!='original_record'})
    restored=json.loads(json.dumps(p))
    result=t.evaluate(restored,target(),**context)
    assert result['prediction_sha256']==m.digest(p)
    assert Q(result['diagnostic_residual_hz'])==Q(p['mapped']['outputs']['average_rate_hz']['value'])-1
    assert result['combined_uncertainty'] is None
    with pytest.raises(TypeError):t.evaluate(restored,target())


@pytest.mark.parametrize(('path','replacement'),[
    (('mapped','outputs','average_rate_hz','value'),'123'),
    (('mapped','outputs','average_rate_hz','sha256'),'forged'),
    (('mapped','outputs','average_rate_hz','origin','execution_sha256'),'forged'),
    (('mapping_contract','spec_sha256'),'forged'),
    (('complete_temporal_record','counts','compared'),999),
    (('complete_temporal_record','endpoints','compared','phase_endpoints'),[0,999]),
    (('complete_temporal_record','complete_input','left','certificates',0,'certificate_digest'),'forged'),
    (('end_coordinate_seconds'),'13'),
    (('classification'),'atomic_prediction'),
])
def test_evaluation_rejects_changed_artifact_fields(path,replacement):
    context=original_context();p=t.predict(context['original_record'])
    path=(path,) if isinstance(path,str) else path
    item=p
    for key in path[:-1]:item=item[key]
    item[path[-1]]=replacement
    with pytest.raises(ValueError,match='prediction differs from replayed original context'):
        t.evaluate(p,target(),**context)


def test_evaluation_rejects_minimal_or_rehashed_false_output():
    context=original_context()
    with pytest.raises(ValueError,match='prediction differs'):
        t.evaluate({'mapped':{'outputs':{'average_rate_hz':{'value':'123'}}}},target(),**context)
    p=t.predict(context['original_record']);out=p['mapped']['outputs']['average_rate_hz']
    out['value']='123'
    out['origin']['execution_sha256']=m.digest({
        'map_spec_sha256':p['mapped']['spec_sha256'],'inputs_sha256':p['mapped']['input_sha256'],
        'output':'average_rate_hz','value':out['value'],'provenance':out['provenance']})
    out['sha256']=m.digest({k:v for k,v in out.items() if k!='sha256'})
    with pytest.raises(ValueError,match='prediction differs'):
        t.evaluate(p,target(),**context)


def test_evaluation_rejects_counts_rebound_to_valid_generic_map():
    context=original_context();p=t.predict(context['original_record'])
    p['complete_temporal_record']['counts']['compared']=999
    f=deepcopy(p['mapping_contract'])
    native=f['sources'][0]
    native['payload']['compared']='999'
    native['payload']['complete_record']=deepcopy(p['complete_temporal_record'])
    native['sha256']=m.digest(native['payload'])
    f=m.seal(f);trusted={s['id']:s for s in f['sources']}
    values={port['name']:m.value(port,native['payload'][port['name']],{native['id']:native['sha256']},
            origin={'kind':'source','source_id':native['id'],'payload_key':port['name']}) for port in f['domain']}
    p['mapping_contract']=f;p['mapped']=m.run_map(f,values,trusted)
    p['derived_reciprocal_period_seconds']=str(1/Q(p['mapped']['outputs']['average_rate_hz']['value']))
    with pytest.raises(ValueError,match='prediction differs'):
        t.evaluate(p,target(),**context)


@pytest.mark.parametrize(('setting','changed'),[
    ('compared_gain','2'),('reference_gain','2'),('epoch','13'),('coordinate','stipulated:other'),
])
def test_evaluation_rejects_changed_original_observation_settings(setting,changed):
    context=original_context();p=t.predict(context['original_record'])
    with pytest.raises(ValueError,match='prediction differs'):
        t.evaluate(p,target(),**{**context,setting:changed})


def test_evaluation_distinguishes_admitted_records_with_equal_counts():
    context=original_context();p=t.predict(context['original_record'])
    a=n.recurrent('other:compared',n=4,spacing=8,scope='m3:comparison')
    b=n.recurrent('other:reference',n=3,spacing=10,scope='m3:comparison')
    other=t.TemporalInput(a,b,n.contacts(a,b),(0,30))
    assert t.adapt(other)['counts']==p['complete_temporal_record']['counts']
    with pytest.raises(ValueError,match='prediction differs'):
        t.evaluate(p,target(),**{**context,'original_record':other})


def test_evaluation_reexecutes_native_admission_of_original_record():
    context=original_context();r=context['original_record'];p=t.predict(r)
    forged=replace(r.left.certificates[0],certificate_digest='forged')
    bad=replace(r,left=replace(r.left,certificates=(forged,)+r.left.certificates[1:]))
    for original in (bad,replace(r,contacts=(replace(r.contacts[0],left_prefix='forged'),r.contacts[1])),
                     p['complete_temporal_record']['complete_input']):
        with pytest.raises((ValueError,n.AdmissionError)):
            t.evaluate(p,target(),**{**context,'original_record':original})


@pytest.mark.parametrize('bad_target',[
    {'frequency_hz':'1'},
    {**target(),'exposure':'blind'},
    {**target(),'frequency_hz':'invalid'},
    {**target(),'extra':'unbound'},
])
def test_evaluation_rejects_invalid_targets(bad_target):
    context=original_context();p=t.predict(context['original_record'])
    with pytest.raises(ValueError):t.evaluate(p,bad_target,**context)


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
    report=t.report()
    assert report['schema_version']==2
    assert json.loads(t.REPORT.read_text())==report


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

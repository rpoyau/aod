"""M3 metrology: exact apparatus reductions and hostile claim-boundary controls."""
from copy import deepcopy
from dataclasses import replace
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'manual/scripts'))
import aod_m3_metrology as a
import aod_m3_temporal as t
import aod_mapping_error as m


def rebind_phase(records,realization):
    source=m.source('fixture:phase','model',{'observations':{r['id']:a.phase_payload(r) for r in records}})
    for r in records:
        r['sources']=[source];r['source_ids']=[source['id']]
    ref=records[1]
    src=m.source('fixture:reference','model',{'reference_id':ref['id'],'coordinate':ref['coordinate'],
        'epoch':ref['epoch'],'window':ref['window'],'defining_integer_hz':a.CS,'physical_correspondence':'declared_fixture'})
    realization['source']=src;realization['trusted_sources']={x['id']:x for x in (source,src)}
    return records[0],records[1],realization


@pytest.mark.parametrize('value',[True,False,0.5,'0.5','2/4','+1','01','1/0','1.0',Q(1,2)])
def test_exact_interface_rejects_ambiguous_values(value):
    with pytest.raises(ValueError):a.exact(value)


def test_exact_phase_split_reversal_and_matched_window_SI():
    x,r,c=a.phase_fixture();result=a.compare_accumulations(x,r,c)
    assert a.phase_advance(x)==Q(7,2) and a.phase_advance(r)==Q(17,2)
    assert result['ratio']=='7/17' and result['duration_seconds']=='17/18385263540'
    assert result['mean_frequency_hz']=='64348422390/17'
    left=deepcopy(x);left.update(window=[10,16],winding=2,phase_end='5/6')
    right=deepcopy(x);right.update(window=[16,22],winding=2,phase_start='5/6')
    assert a.phase_advance(left)==Q(13,6) and a.phase_advance(right)==Q(4,3)
    assert a.phase_advance(left)+a.phase_advance(right)==a.phase_advance(x)
    reverse=deepcopy(x);reverse.update(winding=-4,phase_start=x['phase_end'],phase_end=x['phase_start'],orientation='reverse')
    assert a.phase_advance(reverse)==-a.phase_advance(x)
    assert result['physical_correspondence']=='unestablished' and not result['universal_seconds_per_bip']


@pytest.mark.parametrize(('field','value'),[
    ('coordinate','other'),('epoch','later'),('window',[11,23]),('orientation','reverse')])
def test_equal_duration_different_comparison_scope_rejected(field,value):
    x,r,c=a.phase_fixture();x[field]=value;x,r,c=rebind_phase([x,r],c)
    with pytest.raises(ValueError,match='matched'):a.compare_accumulations(x,r,c)


@pytest.mark.parametrize(('field','value'),[('phase_start','1'),('phase_end','-1/2'),('winding',True),('winding','4'),('kind','shed_packet_event')])
def test_phase_domain_and_observable_confusion_rejected(field,value):
    x,_,_=a.phase_fixture();x[field]=value
    with pytest.raises(ValueError):a.phase_advance(x)


def test_phase_source_payload_not_just_a_matching_label():
    x,r,c=a.phase_fixture();x['winding']=40
    with pytest.raises(ValueError,match='extractor'):a.compare_accumulations(x,r,c)
    x,r,c=a.phase_fixture();x['sources'][0]['payload']['observations']['compared']['winding']=40
    with pytest.raises(ValueError,match='hash'):a.compare_accumulations(x,r,c)


@pytest.mark.parametrize('winding',[0,-8])
def test_nonpositive_reference_cannot_define_elapsed_time(winding):
    x,r,c=a.phase_fixture();r.update(winding=winding,phase_start='0',phase_end='0');x,r,c=rebind_phase([x,r],c)
    with pytest.raises(ValueError,match='positive'):a.compare_accumulations(x,r,c)


def test_reference_scope_and_realization_cannot_be_assumed():
    x,r,c=a.phase_fixture();c['source']['payload']['window']=[11,23]
    with pytest.raises(ValueError):a.compare_accumulations(x,r,c)
    x,r,c=a.phase_fixture();c['physical_correspondence']='experimentally_validated'
    with pytest.raises(ValueError):a.compare_accumulations(x,r,c)
    x,r,c=a.phase_fixture();r['corrections']=[{'id':'offset','source_id':'fixture:phase','value_turns':'0','already_applied':True}]
    with pytest.raises(ValueError,match='correction'):a.compare_accumulations(x,r,c)


def test_whole_native_artifact_replay_uses_original_context():
    context=t.example_context();prediction=t.predict(context);before=m.canonical(prediction)
    result=a.bind_native_prediction(prediction,context)
    assert result['prediction_sha256']==m.digest(prediction) and result['native_schema_version']==3
    for key in ('classification','exposure'):
        mutant=deepcopy(prediction);mutant[key]='forged'
        with pytest.raises(ValueError,match='replayed'):a.bind_native_prediction(mutant,context)
    with pytest.raises(ValueError):a.bind_native_prediction(prediction,t.example_context(compared_gain='2'))
    first=a.reduce_hydrogen(a.load_profile('hydrogen'),'table_iv')
    target={'id':'H','frequency_hz':first['corrected_frequency_hz'],'exposure':'retrospective','prediction_cross_covariance':None}
    t.evaluate(prediction,target,original_context=context)
    t.evaluate(prediction,{**target,'frequency_hz':'1'},original_context=context)
    assert m.canonical(prediction)==before


def test_native_count_replay_cannot_change_count_or_channel():
    x,_,c=a.phase_fixture();context=t.example_context();prediction=t.predict(context)
    x.update(kind='native_reclosure_count',count=3,channel='compared',prediction=prediction,original_context=context)
    with pytest.raises(ValueError):a.validate_observation(x,c['trusted_sources'])
    x.update(window=prediction['complete_temporal_record']['window'],scope=prediction['complete_temporal_record']['native_scope'],
             coordinate=prediction['coordinate'],epoch=prediction['epoch_seconds'],preparation=deepcopy(context.preparation))
    with pytest.raises(ValueError,match='extractor/type'):a.validate_observation(x,c['trusted_sources'])
    binding=a.bind_native_prediction(prediction,context)
    payload={k:deepcopy(x[k]) for k in ('kind','coordinate','epoch','window','scope','preparation','count','channel')}
    payload.update(prediction_sha256=binding['prediction_sha256'],original_context_sha256=binding['original_context_sha256'])
    src=m.source('native:declared','model',{'observations':{x['id']:payload}})
    x['sources']=[src];trusted={src['id']:src}
    a.validate_observation(x,trusted)
    x['count']=4
    with pytest.raises(ValueError,match='count differs'):a.validate_observation(x,trusted)
    x['count']=3;x['window']=[10,22];payload['window']=[10,22]
    src=m.source('native:declared','model',{'observations':{x['id']:payload}})
    x['sources']=[src]
    with pytest.raises(ValueError,match='window/scope'):a.validate_observation(x,{src['id']:src})


def ledger():
    return {'window':[0,5],'packets':[{'id':'old','emitted':-1,'arrived':2},
        {'id':'new','emitted':3,'arrived':None}],'pending_start':1,'pending_end':1}


def test_passive_transport_ledger_keeps_pending_ancestry():
    record=ledger();before=deepcopy(record);out=a.validate_transport_ledger(record)
    assert record==before and out['emitted']-out['arrived']==out['pending_end']-out['pending_start']==0
    assert out['emitted']==1 and out['arrived']==1
    # Arrival separation equals emission separation plus the difference of delays.
    e1,e2,d1,d2=2,6,3,5
    assert (e2+d2)-(e1+d1)==(e2-e1)+(d2-d1)


@pytest.mark.parametrize('mutation',['duplicate','future_emission','future_arrival','negative_delay','erase_pending'])
def test_transport_hostile_controls(mutation):
    r=ledger()
    if mutation=='duplicate':r['packets'].append(deepcopy(r['packets'][0]))
    if mutation=='future_emission':r['packets'][1]['emitted']=6
    if mutation=='future_arrival':r['packets'][1]['arrived']=6
    if mutation=='negative_delay':r['packets'][1]['arrived']=1
    if mutation=='erase_pending':r['pending_end']=0
    with pytest.raises(ValueError):a.validate_transport_ledger(r)


def test_hydrogen_actual_continuous_maser_tables_mean_and_uncertainty():
    p=a.load_profile('hydrogen');before=m.canonical(p)
    iv=a.reduce_hydrogen(p,'table_iv');vi=a.reduce_hydrogen(p,'table_vi');mean=a.reduce_hydrogen(p,'published_mean')
    assert iv['corrected_frequency_hz']=='14204057517691/10000'
    assert vi['corrected_frequency_hz']=='14204057517667/10000'
    assert mean['corrected_frequency_hz']=='14204057517679/10000'
    assert mean['published_rounded_frequency_hz']=='1420405751.768'
    assert iv['source_reported_uncertainty']['component_square_sum_hz2']=='14651/2500000000'
    assert vi['source_reported_uncertainty']['component_square_sum_hz2']=='7851/2500000000'
    assert mean['source_reported_uncertainty']['reported_value_or_bound']=='0.002'
    assert vi['correction_ownership']['already_in_input']==['NP3','wall']
    assert vi['source_reported_uncertainty']['components_hz']['reference_offset']=='0.0013'
    assert iv['method']=='continuous_active_maser_heterodyne' and not iv['raw_phase_stream_available']
    assert iv['missing_raw_inputs'] and not iv['source_reported_uncertainty']['finite_distribution_inferred']
    assert not iv['independent_atomic_prediction'] and m.canonical(p)==before


@pytest.mark.parametrize('mutation',['Ramsey','duplicate_wall','duplicate_NP3','frequency','missing_tuning','source_alias'])
def test_hydrogen_source_and_correction_ownership_guards(mutation):
    p=a.load_profile('hydrogen')
    if mutation=='Ramsey':p['observation_contracts']['experiment_1']['method']='Ramsey'
    if mutation=='duplicate_wall':p['observation_contracts']['experiment_2']['added_corrections'].append('wall')
    if mutation=='duplicate_NP3':p['observation_contracts']['experiment_2']['added_corrections'].append('NP3')
    if mutation=='frequency':p['table_term_provenance']['Table_IV']['beat']['value_hz']='-0.1194'
    if mutation=='missing_tuning':p['observation_contracts']['experiment_1']['tuning_evidence']=None
    if mutation=='source_alias':p['source_id']='arbitrary_label'
    with pytest.raises(ValueError,match='source protocol'):a.reduce_hydrogen(p,'table_iv')


def test_cesium_campaigns_are_distinct_and_nominal_synthesis_is_not_measurement():
    p=a.load_profile('cesium');aug=a.reduce_cesium(p,'August2013');typ=a.reduce_cesium(p,'typical_Table1')
    assert aug['source_reported_uncertainty']['TypeA']['reported_value_or_bound']=='10111894947/2500000000000000'
    assert aug['source_reported_uncertainty']['TypeB']['reported_value_or_bound']=='919263177/625000000000000'
    assert typ['source_reported_uncertainty']['TypeB']['reported_value_or_bound']=='10111894947/10000000000000000'
    assert aug['spin_exchange_statistics_already_in_TypeA']
    assert not aug['raw_population_and_servo_replay'] and not aug['nominal_synthesis_is_exact_carrier']
    assert any('standard_uncertainty_bound' in x for x in typ['reported_entries'])
    p['uncertainty_budgets']['August2013']['TypeB_standard_uncertainty']='0.11'
    with pytest.raises(ValueError):a.reduce_cesium(p,'August2013')


def test_population_estimates_are_calibrated_noninteger_observables():
    p={'N3':'1/2','N4':'3/2','calibration_3':'detector:A','calibration_4':'detector:A','estimator':'normalized_fluorescence'}
    assert a.population_fraction(p)==Q(3,4)
    for changes in ({'N3':'0','N4':'0'},{'N3':'-1/2'},{'calibration_4':'detector:B'},{'N4':1.5}):
        with pytest.raises(ValueError):a.population_fraction({**p,**changes})


def test_shared_input_dependency_and_aliases():
    fixture=a.finite_dependency_fixture();result=a.validate_error_dependencies(fixture)
    assert result['output_variance']=='1' and result['jacobian']==['2']
    r=deepcopy(fixture);r['inputs']['alias']=deepcopy(r['inputs']['X'])
    with pytest.raises(ValueError,match='aliases'):a.validate_error_dependencies(r)
    r=deepcopy(fixture);src=deepcopy(r['sources'][0]);src['id']='different_label'
    r['sources'].append(src);r['trusted_sources'][src['id']]=src
    r['inputs']['alias']={**r['inputs']['X'],'source_id':src['id']}
    with pytest.raises(ValueError,match='aliases'):a.validate_error_dependencies(r)


def test_dependency_units_aggregates_and_unknowns_are_not_silently_dropped():
    r=a.finite_dependency_fixture();r['output_dimension']=[0,1,0]
    with pytest.raises(ValueError,match='dimension'):a.validate_error_dependencies(r)
    r=a.finite_dependency_fixture();r['inputs']['X']['components']=['X']
    with pytest.raises(ValueError,match='aggregate'):a.validate_error_dependencies(r)
    for kind in ('unknown','source_reported_uncertainty','bound'):
        r=a.finite_dependency_fixture();r['inputs']['X']['kind']=kind
        with pytest.raises(ValueError,match='fabricated'):a.validate_error_dependencies(r)
        r['support']=None
        result=a.validate_error_dependencies(r)
        assert result['output_variance'] is None and result['status']=='source_metadata_only'
    r=a.finite_dependency_fixture();r['support'][0][0]='1/4'
    with pytest.raises(ValueError,match='source'):a.validate_error_dependencies(r)


def test_shared_covariance_singular_cancellation_and_total_variance():
    f=a.ensemble_fixtures()
    assert f['total_variance']=={'within':'1','between':'1','total':'2'}
    assert f['correlated_window_mean_variance']=='1/4'
    assert f['shared_source_residual_variance']=='0'
    assert f['opposite_source_residual_variance']=='1'
    assert f['threshold']['exact_variance']=='1/4' and f['threshold']['local_linearized_variance']=='0'
    assert not f['threshold']['local_approximation_adequate'] and not f['atomic_transition_model']
    with pytest.raises(ValueError):m.validate_psd([['1','2'],['2','1']])
    with pytest.raises(ValueError):m.joint_moments([['1/3',{'X':'0'}],['1/3',{'X':'1'}]],['X'])


def event():
    r={'origin':'implantation','timestamp_origin':'implantation','timestamp':'3/2','timestamp_unit':'s',
        'detector_timebase':{'id':'campaign-clock:A','unit':'s','calibration':{'kind':'unknown','reason':'not provided'}},
        'resolution':'1/1000','uncertainty':deepcopy(a.UNKNOWN),
        'status':'censored','conditioning':'survived transport','transport':'flight retained',
        'selection':'campaign-specific detection; not model-independent acceptance'}
    src=m.source('declared:event','model',{'event_timing':deepcopy(r)})
    return {**r,'source':src,'trusted_sources':{src['id']:src}}


def test_nuclear_origin_resolution_censoring_interface_adds_no_kernel():
    e=event();r=a.validate_event_timing(e)
    assert r['origin']=='implantation' and r['selection_status']=='censored' and r['lifetime_prediction'] is None
    e['origin']='formation'
    with pytest.raises(ValueError,match='origin'):a.validate_event_timing(e)
    e=event();e['uncertainty']={'kind':'unknown','value':'0','reason':'sampling is fast'}
    with pytest.raises(ValueError):a.validate_event_timing(e)
    e=event();e['uncertainty']={'kind':'bound','value':'1/1000'}
    with pytest.raises(ValueError,match='evidence'):a.validate_event_timing(e)


def test_claims_cannot_be_promoted_by_a_passing_contract():
    x,r,c=a.phase_fixture();x['evidence_class']='independent_prediction'
    with pytest.raises(ValueError,match='independent physical'):a.validate_observation(x,c['trusted_sources'])
    report=a.build_report()
    assert report['claim_status']['independent_atomic_prediction']=='not_established'
    assert report['claim_status']['nuclear_dynamics']=='not_implemented'
    assert report['native_binding']['physical_correspondence']=='unestablished'


def test_report_replays_and_check_is_read_only():
    assert a.REPORT.read_bytes()==a.report_bytes()
    before={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in a.DATA.rglob('*') if p.is_file()}
    result=subprocess.run([sys.executable,str(Path(a.__file__)),'--check'],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    assert before=={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in before}
    assert all(not Path(key).is_absolute() for key in a.build_report()['inputs_sha256'])


def test_corrections_bind_value_ownership_and_window_to_source_payload():
    x,r,c=a.phase_fixture()
    payload={'corrections':{'offset':{'value_turns':'1/2','already_applied':False,
        'observation_id':x['id'],
        'coordinate':x['coordinate'],'epoch':x['epoch'],'window':x['window']}}}
    src=m.source('correction:A','calibration',payload)
    x['sources'].append(src);c['trusted_sources'][src['id']]=src
    x['corrections']=[{'id':'offset','source_id':src['id'],'value_turns':'1/2','already_applied':False}]
    assert a.compare_accumulations(x,r,c)['ratio']=='8/17'
    x['corrections'][0]['value_turns']='100'
    with pytest.raises(ValueError,match='correction value'):a.compare_accumulations(x,r,c)
    x['corrections'][0]['value_turns']='1/2';x['corrections'].append(deepcopy(x['corrections'][0]))
    with pytest.raises(ValueError,match='duplicate correction'):a.compare_accumulations(x,r,c)


@pytest.mark.parametrize('uncertainty',[
    {'kind':'source_reported_uncertainty','value':'0'},
    {'kind':'declared_finite_law'},
    {'kind':'unknown','reason':'none','value':'0'}])
def test_observation_uncertainty_cannot_be_empty_or_relabelled_zero(uncertainty):
    x,_,c=a.phase_fixture();x['uncertainty']=uncertainty
    with pytest.raises(ValueError):a.validate_observation(x,c['trusted_sources'])


def test_source_reported_uncertainty_is_checked_without_inventing_joint_law():
    x,_,c=a.phase_fixture()
    u={'kind':'source_reported_uncertainty','source':'paper:A','campaign_or_measurement':'printed fixture',
       'unit':'turn','reported_value_or_bound':'0.02','category_or_coverage_status':'standard uncertainty',
       'reporting_precision':'two decimal places'}
    src=m.source('paper:A','evaluation',{'reported_uncertainty':{x['id']:deepcopy(u)}})
    x['sources'].append(src);x['uncertainty']=u;c['trusted_sources'][src['id']]=src
    assert a.validate_observation(x,c['trusted_sources'])['uncertainty']==u
    x['uncertainty']['reported_value_or_bound']='0'
    with pytest.raises(ValueError,match='differs'):a.validate_observation(x,c['trusted_sources'])


def test_dependency_transitive_aggregates_and_evaluation_laws_rejected():
    r=a.finite_dependency_fixture()
    for name,components in [('B',['X']),('A',['B'])]:
        r['inputs'][name]={**r['inputs']['X'],'quantity_id':name,'components':components}
    r['active']=['A','X'];r['expression']=['add',['input','A'],['input','X']]
    with pytest.raises(ValueError,match='aggregate'):a.validate_error_dependencies(r)
    r=a.finite_dependency_fixture()
    src=m.source('fixture:joint','evaluation',deepcopy(r['sources'][0]['payload']))
    r['sources']=[src];r['trusted_sources']={src['id']:src}
    with pytest.raises(ValueError,match='role'):a.validate_error_dependencies(r)


def test_dependency_parameters_require_canonical_values_and_bound_source():
    r=a.finite_dependency_fixture();r['expression']=['mul',['input','X'],['parameter','gain']]
    parameter={'value':'1/2','unit':'1','dimension':[0,0,0]}
    src=m.source('gain:fixture','model',{'parameters':{'gain':deepcopy(parameter)}})
    r['sources'].append(src);r['trusted_sources'][src['id']]=src
    r['parameters']={'gain':{**parameter,'source_id':src['id'],'quantity_id':'gain'}}
    assert a.validate_error_dependencies(r)['output_variance']=='1/16'
    r['parameters']['gain']['value']='0.5'
    with pytest.raises(ValueError,match='noncanonical'):a.validate_error_dependencies(r)
    r['parameters']['gain']['value']='1/4'
    with pytest.raises(ValueError,match='parameter differs'):a.validate_error_dependencies(r)
    r['parameters']['gain']=parameter
    with pytest.raises(ValueError,match='source-bound'):a.validate_error_dependencies(r)


def test_event_origin_change_cannot_relabel_a_bound_timestamp():
    e=event();e['origin']=e['timestamp_origin']='formation'
    with pytest.raises(ValueError,match='trusted origin'):a.validate_event_timing(e)
    e=event();e['timestamp_unit']='detector_tick'
    with pytest.raises(ValueError,match='evidence'):a.validate_event_timing(e)


@pytest.mark.parametrize('kind',['shed_packet_event','fluorescence_population_estimate'])
def test_each_observable_extractor_needs_its_own_source_payload(kind):
    x,_,c=a.phase_fixture();x['kind']=kind
    fields=['kind','coordinate','epoch','window']
    if kind=='shed_packet_event':
        x.update(packet_id='packet:1',cut=15);fields+=['packet_id','cut']
    else:
        x['populations']={'N3':'1/2','N4':'3/2','calibration_3':'A','calibration_4':'A','estimator':'normalized_fluorescence'}
        fields+=['populations']
    with pytest.raises(ValueError,match='extractor/type'):a.validate_observation(x,c['trusted_sources'])
    src=m.source('observable:actual','model',{'observations':{x['id']:{k:deepcopy(x[k]) for k in fields}}})
    x['sources']=[src];a.validate_observation(x,{src['id']:src})
    if kind=='shed_packet_event':x['packet_id']='packet:2'
    else:x['populations']['N4']='5/2'
    with pytest.raises(ValueError,match='extractor/type'):a.validate_observation(x,{src['id']:src})


def test_nuclear_observation_cannot_install_its_own_untrusted_nested_registry():
    x,_,c=a.phase_fixture();x['kind']='nuclear_event_timestamp';x['event_timing']=event()
    with pytest.raises(ValueError,match='outer observation'):a.validate_observation(x,c['trusted_sources'])
    src=x['event_timing']['source'];x['sources'].append(src);c['trusted_sources'][src['id']]=src
    with pytest.raises(ValueError,match='extractor/type'):a.validate_observation(x,c['trusted_sources'])
    payload={k:deepcopy(x[k]) for k in ('kind','scope','coordinate','epoch','window','preparation')}
    payload.update(event_source_id=src['id'],event_source_sha256=src['sha256'])
    outer=m.source('declared:event-observation','model',{'observations':{x['id']:payload}})
    x['sources'].append(outer);c['trusted_sources'][outer['id']]=outer
    assert a.validate_observation(x,c['trusted_sources'])['kind']=='nuclear_event_timestamp'

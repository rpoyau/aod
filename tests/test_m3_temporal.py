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
    return {'original_context':t.example_context(record,**changes)}


def target():
    return {'id':'H','frequency_hz':'1','exposure':'retrospective','prediction_cross_covariance':None}


def test_actual_admission_coupling_and_directional_records():
    v=t.adapt(t.example())
    assert v['counts']=={'compared':3,'reference':2}
    assert v['forward']['ratio']=='3/2' and v['reverse']['ratio']=='2/3'
    assert v['forward']['duration']==5 and v['reverse']['duration']==7
    assert v['forward']['lag']=='3/2' and v['reverse']['lag']=='-3/2'
    assert v['complete_input']['left']['certificates']


def readout_definitions():
    return [{'id':'returns','quantity':'compared_reclosures'},
            {'id':'rate','quantity':'average_rate_hz'}]


def test_readouts_share_one_original_context_and_conditional_operator():
    context=t.example_context();definitions=readout_definitions()
    product=t.readouts(context,definitions)
    assert product['outputs']['returns']['value']=='3'
    assert Q(product['outputs']['rate']['value'])==3*t.CS/2
    assert product['dependence']['context_sha256']==product['original_context_sha256']
    assert product['dependence']['stochastic_cross_covariance'] is None
    assert t.replay_readouts(product,original_context=context,definitions=definitions)==product
    with pytest.raises(ValueError):t.readouts({'counts':{'compared':3,'reference':2}},definitions)


@pytest.mark.parametrize('changed', ['preparation','pending','coordinate','gain','readout','value','trace'])
def test_readout_replay_rejects_changed_context_or_view(changed):
    context=t.example_context();definitions=readout_definitions();product=t.readouts(context,definitions)
    original=context
    if changed=='preparation':
        preparation={'id':'other','parameters':{'compared_spacing':8,'reference_spacing':10}}
        domain=t.domain_for(context.population,context.couplings,preparation,context.record.window)
        original=replace(context,preparation=preparation,observation=t.observation_law([domain]))
    elif changed=='pending':
        pending={'wave_identity':context.record.left.identity,'kind':'incomplete_return',
                 'committed_cut':context.record.window[1],
                 'prefix_sha256':n.wave_prefix(context.record.left,context.record.window[1]),
                 'payload':{'stage':'declared incomplete fixture'}}
        original=replace(context,pending=(pending,))
    elif changed=='coordinate':original=t.example_context(coordinate='stipulated:other')
    elif changed=='gain':original=t.example_context(compared_gain='2')
    elif changed=='readout':definitions[0]['quantity']='reference_reclosures'
    elif changed=='value':product['outputs']['returns']['value']='999'
    else:
        a=n.recurrent('other:compared',n=4,spacing=8,scope='m3:comparison')
        b=n.recurrent('other:reference',n=3,spacing=10,scope='m3:comparison')
        original=t.example_context(t.TemporalInput(a,b,n.contacts(a,b),(0,30)))
        product['original_context_sha256']=m.digest(t.plain(t.asdict(original)))
    with pytest.raises(ValueError,match='readouts differ'):
        t.replay_readouts(product,original_context=original,definitions=definitions)


@pytest.mark.parametrize('definitions',[
    [],[{'id':'x','quantity':'nuclear_rate'}],
    [{'id':'x','quantity':'forward_lag','dynamics':'other'}],
    [{'id':'x','quantity':'forward_lag'},{'id':'x','quantity':'forward_drift'}],
])
def test_readouts_reject_unbound_laws_and_ambiguous_names(definitions):
    with pytest.raises(ValueError):t.readouts(t.example_context(),definitions)


def test_window_reduction_retains_lineage_counts_and_scoped_evidence():
    context=t.example_context();product=t.window_reduction(context,(0,23))
    assert product['projection']['counts']=={'compared':2,'reference':2}
    assert {k:len(v) for k,v in product['selected_returns'].items()}==product['projection']['counts']
    assert product['future_response_preservation']=='not_claimed'
    assert product['evidence']['kind']=='exhaustive_finite'
    assert t.replay_window_reduction(product,original_context=context,window=(0,23))==product
    with pytest.raises(ValueError,match='reduction differs'):
        t.replay_window_reduction(product,original_context=context,window=(0,30))
    with pytest.raises(ValueError):t.window_reduction(context,(0,31))
    product['future_response_preservation']='all dynamics'
    with pytest.raises(ValueError,match='reduction differs'):
        t.replay_window_reduction(product,original_context=context,window=(0,23))


def response_states(context):
    first=n.initial_state(context.record.left)
    return (first,replace(first,pressure=Q(2)),n.initial_state(context.record.right))


def test_existing_response_operator_falsifies_current_only_coarse_state():
    context=t.example_context();states=response_states(context);cut=min(s.committed for s in states)
    poor=t.finite_response_reduction(context,states,['current'],attention='1',input_index=cut)
    assert poor['sufficient_on_checked_states'] is False
    assert poor['counterexamples'][0]['next_currents']==['1','1/2','1']
    rich=t.finite_response_reduction(context,states,['current','pressure'],attention='1',input_index=cut)
    assert rich['sufficient_on_checked_states'] is True and rich['counterexamples']==[]
    assert rich['rows'][0]['coarse_state']==rich['rows'][2]['coarse_state']
    assert rich['evidence']['scope'].startswith('only the listed states')


@pytest.mark.parametrize('changed',['current','pressure','population','window','boundary','attention','fields'])
def test_response_cache_requires_original_state_and_domain(changed):
    context=t.example_context();states=response_states(context);cut=min(s.committed for s in states)
    fields=['current','pressure'];attention='1'
    product=t.finite_response_reduction(context,states,fields,attention=attention,input_index=cut)
    assert t.replay_response_reduction(product,original_context=context,states=states,
        retained_fields=fields,attention=attention,input_index=cut)==product
    if changed in ('current','pressure','boundary'):
        states=(replace(states[0],**{changed:'other' if changed=='boundary' else Q(3)}),)+states[1:]
    elif changed=='population':
        extra=n.recurrent('extra',n=3,spacing=10,scope='m3:comparison')
        population=context.population+(extra,)
        domain=t.domain_for(population,context.couplings,context.preparation,context.record.window)
        context=replace(context,population=population,observation=t.observation_law([domain]))
    elif changed=='window':
        context=replace(context,record=replace(context.record,window=(1,30)))
    elif changed=='attention':attention='2'
    else:fields=['current']
    with pytest.raises(ValueError):
        t.replay_response_reduction(product,original_context=context,states=states,
            retained_fields=fields,attention=attention,input_index=cut)


def test_fold_control_does_not_promote_boundary_commutation_to_area_or_response():
    controls=t.reduction_fixtures();fold=controls['fold']
    assert fold['original']['chain_map'] is True
    assert fold['original']['input_occupancy_area']=='2'
    assert fold['original']['image_support_area']=='1'
    assert fold['source_occurrences']==fold['image_occurrences']==2
    assert fold['area_preserved'] is False and fold['future_response_preservation']=='not_claimed'


def test_scheduler_alias_scope_window_and_contact_substitutions_rejected():
    r=t.example()
    bad=[{'left':3,'right':2},replace(r,right=r.left),replace(r,window=(0,10)),
         replace(r,contacts=r.contacts[:1]),replace(r,right=replace(r.right,scope='elsewhere')),
         replace(r,contacts=(replace(r.contacts[0],left_prefix='forged'),r.contacts[1]))]
    for value in bad:
        with pytest.raises((ValueError,n.AdmissionError)):t.adapt(value)


def test_si_epoch_gain_and_typed_contract():
    p=t.predict(t.example_context(epoch='13'))
    assert Q(p['mapped']['outputs']['elapsed_seconds']['value'])==2/t.CS
    assert Q(p['mapped']['outputs']['average_rate_hz']['value'])==3*t.CS/2
    assert Q(p['end_coordinate_seconds'])==13+2/t.CS
    assert p['derived_reciprocal_period_seconds']!=p['mapped']['outputs']['elapsed_seconds']['value']
    assert p['atomic_prediction'] is None and p['complete_physical_standard_uncertainty'] is None
    f,trusted=t.si_contract(t.example_context())
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
        with pytest.raises(ValueError):t.predict(t.example_context(reference_gain=g))


def test_target_change_cannot_modify_prediction_bytes_and_gain_is_free():
    context=original_context();p=t.predict(context['original_context']);before=m.canonical(p)
    a=t.evaluate(p,target(),**context);b=t.evaluate(p,{**target(),'frequency_hz':'2'},**context)
    assert m.canonical(p)==before and a['prediction_sha256']==b['prediction_sha256']
    assert a['evaluation_sha256']!=b['evaluation_sha256']
    assert Q(a['diagnostic_residual_hz'])-Q(b['diagnostic_residual_hz'])==1
    with pytest.raises(ValueError):t.evaluate(p,{**target(),'exposure':'blind'},**context)
    q=t.predict(t.example_context(compared_gain='2'))
    assert q['mapped']['outputs']['elapsed_seconds']==p['mapped']['outputs']['elapsed_seconds'] or Q(q['mapped']['outputs']['elapsed_seconds']['value'])==Q(p['mapped']['outputs']['elapsed_seconds']['value'])
    assert Q(q['mapped']['outputs']['average_rate_hz']['value'])==2*Q(p['mapped']['outputs']['average_rate_hz']['value'])


def test_evaluation_accepts_json_roundtrip_with_complete_original_context():
    context=original_context(compared_gain='3/2',reference_gain='4/3',epoch='13',coordinate='stipulated:alternate')
    p=t.predict(context['original_context'])
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
    context=original_context();p=t.predict(context['original_context'])
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
    p=t.predict(context['original_context']);out=p['mapped']['outputs']['average_rate_hz']
    out['value']='123'
    out['origin']['execution_sha256']=m.digest({
        'map_spec_sha256':p['mapped']['spec_sha256'],'inputs_sha256':p['mapped']['input_sha256'],
        'output':'average_rate_hz','value':out['value'],'provenance':out['provenance']})
    out['sha256']=m.digest({k:v for k,v in out.items() if k!='sha256'})
    with pytest.raises(ValueError,match='prediction differs'):
        t.evaluate(p,target(),**context)


def test_evaluation_rejects_counts_rebound_to_valid_generic_map():
    context=original_context();p=t.predict(context['original_context'])
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
    context=original_context();p=t.predict(context['original_context'])
    with pytest.raises(ValueError,match='prediction differs'):
        t.evaluate(p,target(),**original_context(**{setting:changed}))


def test_evaluation_distinguishes_admitted_records_with_equal_counts():
    context=original_context();p=t.predict(context['original_context'])
    a=n.recurrent('other:compared',n=4,spacing=8,scope='m3:comparison')
    b=n.recurrent('other:reference',n=3,spacing=10,scope='m3:comparison')
    other=t.TemporalInput(a,b,n.contacts(a,b),(0,30))
    assert t.adapt(other)['counts']==p['complete_temporal_record']['counts']
    with pytest.raises(ValueError,match='prediction differs'):
        t.evaluate(p,target(),**original_context(other))


def test_evaluation_reexecutes_native_admission_of_original_record():
    context=original_context();r=context['original_context'].record;p=t.predict(context['original_context'])
    forged=replace(r.left.certificates[0],certificate_digest='forged')
    bad=replace(r,left=replace(r.left,certificates=(forged,)+r.left.certificates[1:]))
    for original in (bad,replace(r,contacts=(replace(r.contacts[0],left_prefix='forged'),r.contacts[1])),
                     p['complete_temporal_record']['complete_input']):
        with pytest.raises((ValueError,n.AdmissionError)):
            t.evaluate(p,target(),**original_context(original))


@pytest.mark.parametrize('bad_target',[
    {'frequency_hz':'1'},
    {**target(),'exposure':'blind'},
    {**target(),'frequency_hz':'invalid'},
    {**target(),'extra':'unbound'},
])
def test_evaluation_rejects_invalid_targets(bad_target):
    context=original_context();p=t.predict(context['original_context'])
    with pytest.raises(ValueError):t.evaluate(p,bad_target,**context)


def test_window_change_recomputes_counts_and_unwrapped_lag():
    r=t.example();v=t.adapt(r)
    short=replace(r,window=(0,23));w=t.adapt(short)
    assert w['counts']['compared']==2 and v['counts']['compared']==3
    assert Q(v['forward']['lag'])-Q(w['forward']['lag'])==1
    assert v['forward']['duration']==w['forward']['duration']


def test_no_evaluation_source_in_conditional_map():
    f,trusted=t.si_contract(t.example_context())
    f=deepcopy(f);f['sources'][0]['role']='evaluation';trusted=deepcopy(trusted);trusted[f['sources'][0]['id']]=f['sources'][0]
    with pytest.raises(m.ContractError,match='evaluation'):m.validate_map(m.seal(f),trusted)


def test_stored_report_reconstructs():
    report=t.report()
    assert report['schema_version']==3
    assert json.loads(t.REPORT.read_text())==report


def test_public_contract_rejects_resealed_derived_count_dictionary():
    document=t.adapt(t.example())
    document['counts']['compared']=999
    with pytest.raises(ValueError,match='complete typed observation context'):
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


def test_context_binds_population_preparation_prefixes_and_directional_operands():
    c=t.example_context();p=t.predict(c);v=p['complete_temporal_record']['observation_context']
    assert v['contract_sha256']==t.TEMPORAL_CONTRACT_SHA256
    assert v['input_sha256']==m.digest(t.plain(t.asdict(c)))
    assert {x['identity'] for x in v['population']}=={c.record.left.identity,c.record.right.identity}
    assert v['duration_participation']['status']=='unknown'
    assert v['duration_participation']['value'] is None
    assert p['reference_corrected_cycle_prediction']=='2'
    assert v['applicability']=='declared_domain_only_physical_unknown'


@pytest.mark.parametrize('mutation', ['preparation','population','graph','window','law','epoch','source','pending'])
def test_whole_context_replay_rejects_resealed_context_or_artifact_mutations(mutation):
    c=t.example_context();p=t.predict(c);altered=deepcopy(p)
    v=altered['complete_temporal_record']['observation_context']
    if mutation=='preparation':v['preparation']['parameters']['compared_spacing']=99
    elif mutation=='population':v['population'][0]['lineage']='forged'
    elif mutation=='graph':v['directed_graph']=[]
    elif mutation=='window':altered['complete_temporal_record']['window']=[0,29]
    elif mutation=='law':v['observation_law']['reference_gain']='2'
    elif mutation=='epoch':altered['epoch_seconds']='1'
    elif mutation=='source':v['source_dependencies']=[m.source('fake','model',{'data':1})]
    else:v['pending']=[{'forged':True}]
    v['input_sha256']=m.digest(v)
    v['observation_law']['law_sha256']=m.digest({k:x for k,x in v['observation_law'].items() if k!='law_sha256'})
    with pytest.raises(ValueError,match='prediction differs'):t.evaluate(altered,target(),original_context=c)


@pytest.mark.parametrize('mutation',['preparation','population','graph','cut_bounds'])
def test_context_outside_frozen_calibration_domain_is_rejected(mutation):
    c=t.example_context()
    if mutation=='preparation':c=replace(c,preparation={'id':'other','parameters':{}})
    elif mutation=='population':c=replace(c,population=c.population+(n.recurrent('third',n=3,spacing=10,scope='m3:comparison'),))
    else:
        o=deepcopy(c.observation)
        if mutation=='graph':o['domains'][0]['directed_graph']=[]
        else:o['domains'][0]['cut_bounds']=[0,29]
        o['law_sha256']=m.digest({k:v for k,v in o.items() if k!='law_sha256'});c=replace(c,observation=o)
    with pytest.raises(ValueError,match='outside frozen domain'):t.predict(c)


def test_future_population_prefix_and_aliased_wave_inventory_rejected():
    c=t.example_context()
    with pytest.raises(ValueError,match='duplicate wave'):t.predict(replace(c,population=c.population+(c.record.left,)))
    late=n.recurrent('future',n=4,spacing=20,scope='m3:comparison')
    with pytest.raises(ValueError,match='future return'):t.predict(replace(c,population=c.population+(late,)))
    with pytest.raises(ValueError,match='evaluation source'):t.predict(replace(c,source_dependencies=(m.source('target','evaluation',{'x':1}),)))


def test_pending_payload_retains_prefix_and_never_supplies_closure():
    c=t.example_context()
    pending={'wave_identity':c.record.left.identity,'kind':'incomplete_return','committed_cut':30,
             'prefix_sha256':n.wave_prefix(c.record.left,30),'payload':{'event_ids':['pending:31'],'completed':False}}
    with_pending=replace(c,pending=(pending,))
    a,b=t.predict(c),t.predict(with_pending)
    assert a['complete_temporal_record']['counts']==b['complete_temporal_record']['counts']
    assert a['reference_corrected_cycle_prediction']==b['reference_corrected_cycle_prediction']
    assert m.digest(a)!=m.digest(b)
    for field,value in [('prefix_sha256','forged'),('committed_cut',31),('wave_identity','other')]:
        with pytest.raises(ValueError):t.predict(replace(c,pending=({**pending,field:value},)))


def test_short_count_projection_cannot_claim_rcd_and_original_context_replay_preserves_target_separation():
    c=t.example_context();short=t.project_counts(c,(20,23))
    assert short['counts']=={'compared':0,'reference':1}
    assert short['directional_rcd_status']=='not_admitted_by_count_projection'
    with pytest.raises(ValueError):t.predict(short)
    with pytest.raises((ValueError,n.AdmissionError)):t.adapt(replace(c.record,window=(20,23),contacts=(c.record.contacts[1],)))


def test_duplicate_synchronized_references_and_shared_calibration_sources_do_not_prove_independence():
    c=t.example_context()
    result=t.reference_independence([c,deepcopy(c)])
    assert result['status']=='dependent' and result['duplicate_reference']
    assert result['independent_evidence_count'] is None
    a=m.source('calibration:a','calibration',{'shared_measurement':'same'})
    b=m.source('calibration:b','calibration',{'shared_measurement':'same'})
    result=t.reference_independence([replace(c,source_dependencies=(a,)),replace(c,source_dependencies=(b,))])
    assert result['shared_calibration_payloads']==[a['sha256']]


def calibrated_context():
    c=t.example_context()
    calibration=m.source('calibration:original','calibration',{'reference_reclosures':'2','corrected_cycles':'6',
        'window':[-20,0],'context_sha256':m.digest({'separate':'original calibration context'})})
    tolerance=m.source('tolerance:algebraic','model',{'kind':'algebraic_exact','cycles':'0','reason':'synthetic exact identity test'})
    law=t.observation_law(c.observation['domains'],reference_gain='3',calibration_source_id=calibration['id'],tolerance_source_id=tolerance['id'])
    return replace(c,source_dependencies=(calibration,tolerance),observation=law)


def test_frozen_calibration_operands_and_output_specific_unknown_units_are_preserved():
    c=calibrated_context();p=t.predict(c)
    assert p['reference_corrected_cycle_prediction']=='6'
    f=p['mapping_contract'];assert f['parameters']['reference_gain']['origin']=='fitted'
    for port in f['codomain']:
        budget=f['error'][port['name']]
        assert set(budget)==set(m.ERROR_COMPONENTS)
        assert {item['unit'] for item in budget.values()}=={port['unit']}
        assert budget['calibration']['kind']=='unknown'
        assert budget['calibration']['included_sources']
        assert budget['model_discrepancy']['kind']=='unknown'
    bad=deepcopy(c.observation);bad['reference_gain']='4';bad['law_sha256']=m.digest({k:v for k,v in bad.items() if k!='law_sha256'})
    with pytest.raises(ValueError,match='calibration operands'):t.predict(replace(c,observation=bad))


def test_cycle_validation_replays_whole_artifact_before_independent_evaluation():
    c=calibrated_context();p=t.predict(c);before=m.canonical(p)
    a=m.source('observed','evaluation',{'corrected_cycles':'6','window':[0,30]})
    b=m.source('observed','evaluation',{'corrected_cycles':'7','window':[0,30]})
    one=t.compare_cycles(p,a,original_context=c);two=t.compare_cycles(p,b,original_context=c)
    assert one['compatible'] is True and two['compatible'] is False
    assert one['residual_cycles']=='0' and two['residual_cycles']=='-1'
    assert m.canonical(p)==before and one['prediction_sha256']==two['prediction_sha256']
    assert one['combined_standard_uncertainty'] is None
    forged=deepcopy(p);forged['reference_corrected_cycle_prediction']='7'
    with pytest.raises(ValueError,match='prediction differs'):t.compare_cycles(forged,b,original_context=c)
    with pytest.raises(ValueError,match='observed window'):t.compare_cycles(p,m.source('other','evaluation',{'corrected_cycles':'6','window':[1,30]}),original_context=c)


def test_calibration_validation_overlap_and_physical_zero_tolerance_rejected():
    c=calibrated_context();sources=list(c.source_dependencies)
    sources[0]=m.source(sources[0]['id'],'calibration',{**sources[0]['payload'],'window':[0,10]})
    overlapping=replace(c,source_dependencies=tuple(sources));p=t.predict(overlapping)
    with pytest.raises(ValueError,match='overlap'):t.compare_cycles(p,m.source('observed','evaluation',{'corrected_cycles':'6','window':[0,30]}),original_context=overlapping)
    sources=list(c.source_dependencies);sources[1]=m.source(sources[1]['id'],'model',{**sources[1]['payload'],'kind':'physical'})
    with pytest.raises(ValueError,match='physical tolerance remains unknown'):t.predict(replace(c,source_dependencies=tuple(sources)))


def test_prior_drift_requires_replayed_native_comparison_and_exact_lag():
    a=n.recurrent('a',n=8,spacing=8,scope='drift');b=n.recurrent('b',n=6,spacing=10,scope='drift')
    def contact(k):
        support=n.trace(f'{a.identity}|{b.identity}',k,scope='drift',start_index=k-2)
        return n.Contact(f'c:{k}',a.identity,b.identity,'drift',k,n.wave_prefix(a,k),n.wave_prefix(b,k),(1,2),support,n.certify(support))
    events=tuple(contact(k) for k in (12,18,22,42))
    old=t.TemporalInput(a,b,events[:2],(0,18),biases=(Q(0),Q(0)),prior_lag=Q(0))
    now=t.TemporalInput(a,b,events[2:],(18,58),biases=(Q(2),Q(1)),prior_lag=Q(1))
    prep={'id':'drift','parameters':{}}
    c=t.ObservationContext(now,(a,b),events,prep,(),(),t.observation_law([t.domain_for((a,b),events,prep,(0,58))]),old)
    v=t.validate_observation_context(c)
    assert v['forward']['lag']=='2' and v['forward']['drift']=='1'
    assert v['reverse']['lag']=='-2' and v['reverse']['drift']=='-1'
    with pytest.raises(ValueError,match='requires committed comparison'):t.predict(replace(c,previous_comparison=None))
    with pytest.raises(ValueError,match='predecessor lag'):t.predict(replace(c,record=replace(now,prior_lag=Q(2))))


@pytest.mark.parametrize('bad',[True,0.5,'1/1'])
def test_observation_parameter_strict_type_and_canonical_format(bad):
    c=t.example_context();o=deepcopy(c.observation);o['reference_gain']=bad
    o['law_sha256']=m.digest({k:v for k,v in o.items() if k!='law_sha256'})
    with pytest.raises(ValueError):t.predict(replace(c,observation=o))


def test_contract_content_cannot_be_replaced_by_self_hash(monkeypatch,tmp_path):
    changed=json.loads(t.TEMPORAL_CONTRACT.read_text());changed['version']=99
    path=tmp_path/'forged-contract.json';path.write_text(json.dumps(changed))
    monkeypatch.setattr(t,'TEMPORAL_CONTRACT',path)
    with pytest.raises(ValueError,match='independently bound'):t.predict(t.example_context())


def test_prediction_mutation_cannot_mutate_independent_original_context_by_alias():
    c=calibrated_context();before=m.canonical(t.plain(t.asdict(c)));p=t.predict(c)
    p['complete_temporal_record']['observation_context']['preparation']['parameters']['forged']=True
    p['complete_temporal_record']['observation_context']['observation_law']['reference_gain']='99'
    p['mapping_contract']['sources'][1]['payload']['frozen_law']['reference_gain']='99'
    p['mapping_contract']['sources'][3]['payload']['corrected_cycles']='99'
    assert m.canonical(t.plain(t.asdict(c)))==before
    with pytest.raises(ValueError,match='prediction differs'):t.evaluate(p,target(),original_context=c)


def test_predictive_fingerprint_separates_source_evidence_from_actual_inputs():
    c=t.example_context();extra=m.source('uncertain:source','calibration',{'uncertainty':'unknown'})
    a=t.predict(c);b=t.predict(replace(c,source_dependencies=(extra,)))
    av=a['complete_temporal_record']['observation_context'];bv=b['complete_temporal_record']['observation_context']
    assert av['predictive_model_sha256']==bv['predictive_model_sha256']
    assert av['evidence_sha256']!=bv['evidence_sha256']
    changed=t.predict(t.example_context(reference_gain='2'))['complete_temporal_record']['observation_context']
    assert changed['predictive_model_sha256']!=av['predictive_model_sha256']


def test_extra_population_contact_cannot_relabel_a_cross_return():
    c=t.example_context();alias=replace(c.couplings[0],identity='relabeled')
    with pytest.raises(ValueError,match='distinct ordered commitments'):
        t.predict(replace(c,couplings=c.couplings+(alias,)))
    alias=replace(alias,committed=23,left_prefix=n.wave_prefix(c.record.left,23),
                  right_prefix=n.wave_prefix(c.record.right,23))
    with pytest.raises(ValueError,match='relabelled cross-return'):
        t.predict(replace(c,couplings=c.couplings+(alias,)))


def test_distinct_directed_pairs_can_share_a_commitment_cut():
    c=t.example_context();a,b=c.population
    reverse=n.contacts(b,a);couplings=c.couplings+reverse
    law=t.observation_law([t.domain_for(c.population,couplings,c.preparation,c.record.window)])
    p=t.predict(replace(c,couplings=couplings,observation=law))
    assert p['complete_temporal_record']['counts']=={'compared':3,'reference':2}


@pytest.mark.parametrize('window',[[0.0,30.0],[False,30],[0,True],(0,30),[0]])
def test_observed_cycle_window_requires_exact_integer_endpoints(window):
    c=t.example_context();p=t.predict(c)
    observed=m.source('observed','evaluation',{'corrected_cycles':'2','window':window})
    with pytest.raises(ValueError,match='observed window requires exact integer endpoints'):
        t.compare_cycles(p,observed,original_context=c)

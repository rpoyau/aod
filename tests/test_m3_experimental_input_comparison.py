"""Complete prediction freeze and authenticated, joint endpoint comparisons."""
from copy import deepcopy
from dataclasses import replace
from fractions import Fraction as Q
import json
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'manual/scripts'))
import aod_m3_experimental as e
import aod_mapping_error as m
import aod_m3_metrology as mt
import aod_m3_temporal as t


def materialized(*,joint=False,cross='0'):
    plan,sources,context=e.prediction_fixture()
    product=e.predict(plan,sources,original_context=context)
    target,extra=e.evaluation_fixture(product,joint=joint,cross_covariance=cross)
    return plan,{**sources,**extra},context,product,target


def reseal_plan(plan,sources):
    owner=m.source(plan['source_id'],'model',{'prediction_plans':{plan['id']:deepcopy(plan['plan'])}})
    sources[owner['id']]=owner;plan['source_sha256']=owner['sha256']


def test_complete_prediction_replay_precedes_target_join_and_records_exposure():
    plan,sources,context,product,target=materialized()
    original=m.canonical(product)
    first=e.evaluate(product,target,original_plan=plan,trusted_sources=sources,original_context=context)
    other,extra=e.evaluation_fixture(product,str(Q(product['output']['value'])+1))
    second=e.evaluate(product,other,original_plan=plan,trusted_sources={**sources,**extra},original_context=context)
    assert first['prediction_sha256']==second['prediction_sha256']
    assert first['evaluation_sha256']!=second['evaluation_sha256']
    assert (first['residual'],second['residual'])==('0','-1')
    assert m.canonical(product)==original
    assert first['uncertainty']['status']=='partial' and first['uncertainty']['variance'] is None
    assert first['independent_validation'] is False and first['corrections_applied'] is False
    assert product['exposure']=='retrospective'


@pytest.mark.parametrize('changed',['uncertainty','window','candidate','stopping','readout','criterion','exposure'])
def test_mutated_plan_rejects_against_independent_source(changed):
    plan,sources,context,product,target=materialized()
    p=plan['plan']
    if changed=='uncertainty':p['uncertainty_request']['model']['covariance']=[['0']]
    elif changed=='window':p['reduction_window']=[0,23]
    elif changed=='candidate':p['selection']['candidate_id']='target-selected'
    elif changed=='stopping':p['stopping']['rule']='stop-on-good-residual'
    elif changed=='readout':p['readout_definitions'][0]['quantity']='reference_reclosures'
    elif changed=='criterion':p['comparison_criterion']['kind']='anything-passes'
    else:p['exposure']='blind'
    with pytest.raises(ValueError,match='plan differs'):
        e.evaluate(product,target,original_plan=plan,trusted_sources=sources,original_context=context)


@pytest.mark.parametrize('changed',['window','stopping','exposure','readout_link','code'])
def test_resealed_unsupported_plan_still_rejects(changed):
    plan,sources,context=e.prediction_fixture();p=plan['plan']
    if changed=='window':p['reduction_window']=[0,23]
    elif changed=='stopping':p['stopping']['rule']='stop-on-good-residual'
    elif changed=='exposure':p['exposure']='blind'
    elif changed=='readout_link':p['readout_parameter_links']['rate']='returns'
    else:p['code_bindings'][next(iter(p['code_bindings']))]='0'*64
    reseal_plan(plan,sources)
    with pytest.raises(ValueError):e.predict(plan,sources,original_context=context)


def test_input_perturbation_runs_map_and_uncertainty_budget():
    plan,sources,context=e.prediction_fixture();first=e.predict(plan,sources,original_context=context)
    other,inputs,original=e.prediction_fixture(gain='3/2',variance='1/25')
    second=e.predict(other,inputs,original_context=original)
    assert Q(second['output']['value'])==Q(first['output']['value'])*Q(3,2)
    assert Q(second['output']['variance'])==Q(first['output']['variance'])*4
    assert second['propagation']['outputs']['rate']['budget']['propagation']['variance']==second['output']['variance']
    assert first['readouts']['prediction_sha256']==second['readouts']['prediction_sha256']


def test_prediction_cannot_consume_known_evaluation_payload_alias():
    plan,sources,context=e.prediction_fixture()
    identity=plan['plan']['uncertainty_request']['inputs']['gain']['source_id']
    sources['evaluation:alias']=m.source('evaluation:alias','evaluation',deepcopy(sources[identity]['payload']))
    with pytest.raises(ValueError,match='evaluation source or payload alias'):
        e.predict(plan,sources,original_context=context)


def test_nested_evaluation_source_in_model_plan_is_rejected():
    plan,sources,context=e.prediction_fixture()
    sources['evaluation:target']=m.source('evaluation:target','evaluation',{'target':'1'})
    plan['plan']['selection']['source_ids']=['evaluation:target'];reseal_plan(plan,sources)
    with pytest.raises(ValueError,match='evaluation'):
        e.predict(plan,sources,original_context=context)


@pytest.mark.parametrize('key',['source_ids','dependency_ids','included_sources'])
def test_nested_dependency_vectors_cannot_hide_target_exposure(key):
    plan,sources,context=e.prediction_fixture()
    target=m.source('evaluation:hidden','evaluation',{'target':'1'});sources[target['id']]=target
    identity=plan['plan']['uncertainty_request']['model_source_id'];payload=deepcopy(sources[identity]['payload'])
    payload['provenance']={key:({target['id']:target['sha256']} if key=='included_sources' else [target['id']])}
    sources[identity]=m.source(identity,'model',payload)
    with pytest.raises(ValueError,match='evaluation'):
        e.predict(plan,sources,original_context=context)


def test_calibration_exposure_inventory_covers_actual_dependency_closure():
    plan,sources,context=e.prediction_fixture()
    calibration=m.source('calibration:selection','calibration',{'meaning':'previously exposed candidate selection'})
    sources[calibration['id']]=calibration
    plan['plan']['selection']['source_ids']=[calibration['id']];reseal_plan(plan,sources)
    with pytest.raises(ValueError,match='calibration exposure inventory'):
        e.predict(plan,sources,original_context=context)
    plan['plan']['calibration_source_ids']=[calibration['id']];reseal_plan(plan,sources)
    product=e.predict(plan,sources,original_context=context)
    assert calibration['id'] in product['source_dependencies'] and product['exposure']=='retrospective'


def test_rehashed_product_cannot_replace_original_context_execution():
    plan,sources,context,product,target=materialized()
    product['propagation']['outputs']['rate']['result']['output_variance']='0'
    product['output']['variance']='0'
    with pytest.raises(ValueError,match='complete prediction differs'):
        e.evaluate(product,target,original_plan=plan,trusted_sources=sources,original_context=context)
    with pytest.raises(ValueError,match='original setup differs'):
        e.predict(plan,sources,original_context=t.example_context(compared_gain='2'))


@pytest.mark.parametrize('changed',['unit','kind','dimension','window','missing_value','source_role','correction_owner'])
def test_target_quality_and_typing_guards(changed):
    plan,sources,context,product,target=materialized()
    binding=target['quantity_binding'];q=binding['quantity']
    if changed=='unit':q['unit']='s';q['dimension']=[0,1,0]
    elif changed=='kind':q['kind']='different_physical_quantity'
    elif changed=='dimension':q['dimension']=[True,-1,0]
    elif changed=='window':q['window']={'coordinate':'other','epoch':'0','bounds':[0,30]}
    elif changed=='missing_value':q['value']=None
    elif changed=='source_role':q['role']='model'
    else:q['corrections']={'field':{'owner_quantity_id':'other','status':'included_in_input','value':'0','unit':'Hz'}}
    source=m.source(binding['source_id'],q['role'],{'quantities':{binding['quantity_id']:deepcopy(q)}})
    sources[source['id']]=source;binding['source_sha256']=source['sha256']
    with pytest.raises(ValueError):
        e.evaluate(product,target,original_plan=plan,trusted_sources=sources,original_context=context)


def test_joint_endpoint_uncertainty_keeps_cross_covariance():
    plan,sources,context,product,target=materialized(joint=True,cross='1')
    result=e.evaluate(product,target,original_plan=plan,trusted_sources=sources,original_context=context)
    assert result['uncertainty']['status']=='conditional_joint_moments'
    assert Q(result['uncertainty']['variance'])==Q(product['output']['variance'])+1-2
    assert result['uncertainty']['cross_covariance']=='1'
    assert result['uncertainty']['standard_deviation']['representation']=='symbolic_square_root'


@pytest.mark.parametrize('changed',['prediction_identity','target_identity','prediction_variance','cross_covariance','expression'])
def test_joint_evidence_cannot_substitute_endpoints_or_unsupported_variance(changed):
    plan,sources,context,product,target=materialized(joint=True)
    evidence_source=sources[target['joint_evidence']['source_id']]
    evidence=deepcopy(evidence_source['payload']['comparisons']['worked'])
    request=evidence['request']
    if changed=='prediction_identity':evidence['prediction_sha256']='0'*64
    elif changed=='target_identity':evidence['target_binding_sha256']='0'*64
    elif changed=='prediction_variance':request['model']['covariance'][0][0]='0'
    elif changed=='cross_covariance':request['model']['covariance'][0][1]='100000000000000000000'
    else:request['model']['outputs']['residual']['expression']=['add',['input','prediction'],['input','target']]
    model_source=m.source(request['model_source_id'],'model',{'uncertainty_models':{'residual':request['model']}})
    sources[model_source['id']]=model_source
    new=m.source(evidence_source['id'],'model',{'comparisons':{'worked':evidence}});sources[new['id']]=new
    with pytest.raises(ValueError):
        e.evaluate(product,target,original_plan=plan,trusted_sources=sources,original_context=context)


def test_all_worked_routes_and_freeze_controls_reproduce():
    report=e.build_report();routes=report['quantity_routes']
    assert len(routes)==10
    assert routes['nonlinear_moments']['result']['status']=='partial'
    assert routes['metadata']['result']['status']=='partial'
    assert routes['bounds']['result']['outputs']['Y']['result']['output_bounds']==['1/3','1']
    assert routes['shared_cancel']['result']['outputs']['residual']['result']['output_variance']=='0'
    assert routes['shared_reinforce']['result']['outputs']['residual']['result']['output_variance']=='8'
    published=routes['published_moments']['result']['outputs']['Y']['result']
    assert published['output_mean']=='177550718971/125'
    assert published['output_variance']=='1/250000'
    assert report['freeze']['comparison']['prediction_sha256']==report['freeze']['target_only_change']['prediction_sha256']
    assert report['reduction_controls']['insufficient_current_only']['sufficient_on_checked_states'] is False


def test_stored_experimental_report_reconstructs():
    assert e.REPORT.read_bytes()==e.report_bytes()

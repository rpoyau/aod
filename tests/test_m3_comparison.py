"""Source-bound comparison metadata and the claims it cannot establish."""
from copy import deepcopy
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'manual/scripts'))
import aod_m3_metrology as a
import aod_mapping_error as m


def rebind(record, trusted):
    """Declare a changed fixture so semantic guards, not stale hashes, are tested."""
    declaration={k:deepcopy(v) for k,v in record.items() if k not in ('source_id','sources')}
    source=m.source(record['source_id'],'model',{'comparison_assessment':declaration})
    trusted[source['id']]=source
    record['sources']=[source if s['id']==source['id'] else s for s in record['sources']]
    return record,trusted


def add_evidence(record, trusted, payload):
    source=m.source('fixture:independent-evidence','calibration',payload)
    trusted[source['id']]=source;record['sources'].append(source)
    record['influences'][0]['source_ids'].append(source['id'])
    return source['id']


def test_assessment_is_passive_and_keeps_correction_uncertainty_separate():
    record,trusted=a.comparison_fixture();before=m.canonical(record)
    result=a.assess_comparison(record,trusted)
    assert result['residual']=='1'  # The -2 correction already in the input is not applied again.
    assert result['correction_ownership']=={'internal-field':'included_in_input'}
    assert result['unresolved_influences']==['internal-field']
    assert result['interpretation']=='reference_dependent_comparison'
    assert result['shared_source_payload_sha256']
    assert not result['corrections_applied_by_assessment']
    assert not result['independent_physical_validation']
    assert result['complete_physical_uncertainty']['kind']=='unknown'
    assert m.canonical(record)==before


def test_assessment_and_endpoint_values_need_separate_trusted_bindings():
    record,trusted=a.comparison_fixture();record['comparison']['value']='1'
    with pytest.raises(ValueError,match='trusted declaration'):a.assess_comparison(record,trusted)
    rebind(record,trusted)
    with pytest.raises(ValueError,match='trusted quantity'):a.assess_comparison(record,trusted)


def test_unknown_correction_remains_unresolved_when_residual_uncertainty_is_supplied():
    record,trusted=a.comparison_fixture();item=record['influences'][0]
    item['correction']={'kind':'unknown','reason':'Correction estimate unavailable'}
    item['residual_uncertainty']={'kind':'source_reported_uncertainty','value':'1/100',
        'unit':'Hz','category_or_coverage_status':'declared standard uncertainty'}
    rebind(record,trusted);result=a.assess_comparison(record,trusted)
    assert result['unresolved_influences']==['internal-field']
    assert result['reflection_to_observation_map_status']=='unknown'


def test_evaluation_source_cannot_enter_prediction_through_dependency_list():
    record,trusted=a.comparison_fixture()
    source=m.source('fixture:evaluation-input','evaluation',{'target':'held out'})
    record['sources'].append(source);trusted[source['id']]=source
    record['prediction']['dependency_ids']=[source['id']]
    rebind(record,trusted)
    with pytest.raises(ValueError,match='evaluation source'):a.assess_comparison(record,trusted)


@pytest.mark.parametrize('target',['correction','residual_uncertainty'])
def test_unknown_influence_cannot_acquire_zero_value(target):
    record,trusted=a.comparison_fixture()
    record['influences'][0][target]={'kind':'unknown','reason':'Missing evidence','value':'0'}
    rebind(record,trusted)
    with pytest.raises(ValueError):a.assess_comparison(record,trusted)


@pytest.mark.parametrize('method',['random','systematic','Type_A_error'])
def test_evaluation_methods_are_not_error_types(method):
    record,trusted=a.comparison_fixture();record['influences'][0]['evaluation_method']=method
    rebind(record,trusted)
    with pytest.raises(ValueError,match='Type A/B'):a.assess_comparison(record,trusted)


def test_external_field_is_not_internal_field_without_transfer_evidence():
    record,trusted=a.comparison_fixture();condition=record['influences'][0]['conditions']
    condition['input_location']='external_environment'
    condition['transfer']={'kind':'unknown','reason':'Shield response and bias field not supplied'}
    rebind(record,trusted)
    with pytest.raises(ValueError,match='transfer evidence'):a.assess_comparison(record,trusted)
    record['influences'][0]['correction']={'kind':'unknown','reason':'No applicable internal-field input'}
    rebind(record,trusted)
    assert a.assess_comparison(record,trusted)['unresolved_influences']==['internal-field']


def test_external_to_internal_transfer_is_bound_to_the_actual_window():
    record,trusted=a.comparison_fixture();condition=record['influences'][0]['conditions']
    condition['input_location']='external_environment'
    payload={'input_location':'external_environment','effect_location':'internal_apparatus',
             'coordinate':record['coordinate'],'epoch':record['epoch'],'window':record['window']}
    source_id=add_evidence(record,trusted,{'transfer':payload})
    condition['transfer']={'kind':'source_bound','source_id':source_id,'payload_key':'transfer'}
    rebind(record,trusted)
    assert a.assess_comparison(record,trusted)['residual']=='1'
    record['window']=[1,13];rebind(record,trusted)
    with pytest.raises(ValueError,match='transfer differs'):a.assess_comparison(record,trusted)


def test_reflection_duration_does_not_become_observation_duration_by_renaming():
    record,trusted=a.comparison_fixture()
    record['reflection_duration']['observation_map']={'kind':'identity','reason':'Equal labels'}
    rebind(record,trusted)
    with pytest.raises(ValueError,match='does not equate'):a.assess_comparison(record,trusted)
    record['reflection_duration']={'kind':'unknown','reason':'Directional duration absent'}
    rebind(record,trusted)
    assert a.assess_comparison(record,trusted)['residual']=='1'


def test_anchor_equality_is_calibration_and_not_independent_validation():
    record,trusted=a.comparison_fixture();record['reference_role']='calibration_anchor'
    record['prediction']=deepcopy(record['comparison'])
    rebind(record,trusted)
    result=a.assess_comparison(record,trusted)
    assert result['residual']=='0' and result['anchor_equality']
    assert result['interpretation']=='calibration_anchor_check'
    assert not result['independent_physical_validation']


def test_same_payload_under_source_aliases_remains_shared():
    record,trusted=a.comparison_fixture()
    source=m.source('fixture:aliased-values','evaluation',deepcopy(record['sources'][0]['payload']))
    record['sources'].append(source);trusted[source['id']]=source
    record['comparison']['source_id']=source['id'];record['reference_role']='evaluation'
    rebind(record,trusted)
    assert a.assess_comparison(record,trusted)['interpretation']=='reference_dependent_comparison'


def test_materiality_requires_scoped_evidence_and_does_not_resolve_unknown_budget():
    record,trusted=a.comparison_fixture()
    evidence={'influence_id':'internal-field','bound':'1/100','tolerance':'1/10','unit':'Hz',
              'coordinate':record['coordinate'],'epoch':record['epoch'],'window':record['window']}
    source_id=add_evidence(record,trusted,{'materiality':evidence})
    record['influences'][0]['materiality']={'kind':'bounded_below_tolerance','bound':'1/100',
        'tolerance':'1/10','unit':'Hz','source_id':source_id,'payload_key':'materiality'}
    rebind(record,trusted);result=a.assess_comparison(record,trusted)
    assert result['bounded_influences']==['internal-field']
    assert result['complete_physical_uncertainty']['kind']=='unknown'
    record['influences'][0]['materiality']['bound']='1/1000';rebind(record,trusted)
    with pytest.raises(ValueError,match='materiality bound differs'):a.assess_comparison(record,trusted)


@pytest.mark.parametrize(('bound','tolerance','unit'),[
    ('-1','1','Hz'),('0','0','Hz'),('1','1','Hz'),('2','1','Hz'),('0','1','s')])
def test_invalid_materiality_bound_tolerance_or_unit_rejected(bound,tolerance,unit):
    record,trusted=a.comparison_fixture()
    record['influences'][0]['materiality']={'kind':'bounded_below_tolerance','bound':bound,
        'tolerance':tolerance,'unit':unit,'source_id':record['sources'][0]['id'],'payload_key':'unused'}
    rebind(record,trusted)
    with pytest.raises(ValueError,match='materiality'):a.assess_comparison(record,trusted)


@pytest.mark.parametrize('mutation',['duplicate','event_unit','fraction','evaluation_input'])
def test_remaining_claim_boundaries(mutation):
    record,trusted=a.comparison_fixture()
    if mutation=='duplicate':record['influences'].append(deepcopy(record['influences'][0]))
    elif mutation=='event_unit':record['kind']='nuclear_event_timestamp'
    elif mutation=='fraction':record['reflection_duration']['value']='0.5'
    else:
        source=m.source('fixture:evaluation-only','evaluation',deepcopy(record['sources'][0]['payload']))
        record['sources'].append(source);trusted[source['id']]=source;record['prediction']['source_id']=source['id']
    rebind(record,trusted)
    with pytest.raises(ValueError):a.assess_comparison(record,trusted)

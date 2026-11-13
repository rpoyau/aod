"""Authenticated quantities and conditional uncertainty routes, with hostile controls."""
from copy import deepcopy
from fractions import Fraction as Q
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'manual/scripts'))
import aod_mapping_error as m
import aod_m3_metrology as a


def reseal_model(record, trusted):
    old=trusted[record['model_source_id']]
    trusted[old['id']]=m.source(old['id'],old['role'],{'uncertainty_models':{record['model_id']:deepcopy(record['model'])}})


def rebind_quantity(record, trusted, name='X', parameter=False):
    bindings=record['parameters'] if parameter else record['inputs']
    binding=bindings[name];old=trusted[binding['source_id']];payload=deepcopy(old['payload'])
    payload['quantities'][binding['quantity_id']]=deepcopy(binding['quantity'])
    source=m.source(old['id'],old['role'],payload);trusted[source['id']]=source
    for collection,field in ((record['inputs'],'input_bindings'),(record['parameters'],'parameter_bindings')):
        for n,b in collection.items():
            if b['source_id']==source['id']:
                b['source_sha256']=source['sha256']
                record['model'][field][n]=a._input_identity(b)
    reseal_model(record,trusted)


@pytest.mark.parametrize('route', ['finite_joint_law','moments','nonlinear_moments','bounds','metadata','conversion','shared_cancel','shared_reinforce','published','multi_output','published_moments'])
def test_routes_are_passive_and_preserve_physical_unknowns(route):
    record,trusted=a.quantity_input_fixture(route);before=m.canonical([record,trusted])
    result=a.propagate_quantities(record,trusted)
    assert m.canonical([record,trusted])==before
    assert result['physical_model_discrepancy']['kind']=='unknown'
    for output in result['outputs'].values():
        assert set(output['budget'])=={'arithmetic','resolution','window','model_discrepancy','calibration','propagation','solver','comparison'}
        assert output['budget']['model_discrepancy']['kind']=='unknown'
        assert all(c['unit']==output['unit'] for c in output['budget'].values())


@pytest.mark.parametrize(('field','value'),[
    ('unit','Hz'),('dimension',[0,-1,0]),('kind','frequency'),('role','evaluation'),
    ('domain',['-200','200']),('locator','elsewhere'),('meaning','other meaning'),
    ('uncertainty',{'category':'unknown'}),('components',['other']),
    ('window',{'coordinate':'bip','epoch':'0','bounds':['0','3']})])
def test_trusted_quantity_semantic_mutations_reject(field,value):
    r,t=a.quantity_input_fixture();r['inputs']['X']['quantity'][field]=value
    with pytest.raises(ValueError,match='trusted quantity'): a.propagate_quantities(r,t)


@pytest.mark.parametrize('field,value',[('quantity_id','Y'),('source_sha256','0'*64),('schema','old')])
def test_binding_identity_mutations_reject(field,value):
    r,t=a.quantity_input_fixture();r['inputs']['X'][field]=value
    with pytest.raises(ValueError): a.propagate_quantities(r,t)


def test_legacy_declared_fixture_compatibility_and_reviewed_unit_witness():
    r=a.finite_dependency_fixture();assert a.validate_error_dependencies(r)['output_variance']=='1'
    src=m.source('fixture:joint','model',{'joint_law':{'order':['X'],'support':r['support']},
        'quantities':{'X':{'unit':'1','dimension':[0,0,0],'kind':'finite_law'}}})
    r['sources']=[src];r['trusted_sources']={src['id']:src}
    assert a.validate_error_dependencies(r)['output_variance']=='1'
    r['inputs']['X'].update(unit='Hz',dimension=[0,-1,0]);r['output_dimension']=[0,-1,0]
    with pytest.raises(ValueError,match='trusted quantity'): a.validate_error_dependencies(r)


def test_exact_affine_moments_and_symbolic_standard_deviation():
    r,t=a.quantity_input_fixture('moments');out=a.propagate_quantities(r,t)['outputs']['Y']
    assert out['result']['output_variance']=='2'
    assert out['result']['uncertainty_status']=='exact_for_declared_affine_model'
    assert out['budget']['propagation']['standard_deviation']=={'representation':'symbolic_square_root','radicand':'2','unit':'1'}
    assert out['budget']['propagation']['variance_unit']=={'base_unit':'1','power':2}


@pytest.mark.parametrize('covariance', [[['-1']],[[True]],[[None]], [['1','1']], [], [['2/4']]])
def test_bad_or_incomplete_covariance_rejects(covariance):
    r,t=a.quantity_input_fixture('moments');r['model']['covariance']=covariance;reseal_model(r,t)
    with pytest.raises((ValueError,TypeError)):a.propagate_quantities(r,t)


def test_nonlinear_equal_moments_do_not_determine_output_variance():
    r,t=a.quantity_input_fixture();one=a.propagate_quantities(r,t)
    assert one['outputs']['Y']['result']['output_mean']=='1'
    assert one['outputs']['Y']['result']['output_variance']=='0'
    r['model']['support']=[['1/8',{'X':'-2'}],['3/4',{'X':'0'}],['1/8',{'X':'2'}]];reseal_model(r,t)
    two=a.propagate_quantities(r,t)
    assert two['outputs']['Y']['result']['input_mean']==one['outputs']['Y']['result']['input_mean']
    assert two['outputs']['Y']['result']['input_covariance']==one['outputs']['Y']['result']['input_covariance']
    assert two['outputs']['Y']['result']['output_mean']=='1'
    assert two['outputs']['Y']['result']['output_variance']=='3'
    r,t=a.quantity_input_fixture('nonlinear_moments');partial=a.propagate_quantities(r,t)
    assert partial['outputs']['Y']['result']['linearized_variance_diagnostic']=='0'
    assert partial['outputs']['Y']['result']['output_variance'] is None
    assert partial['output_covariance'] is None


def test_finite_model_numbers_cannot_change_under_unchanged_trust():
    r,t=a.quantity_input_fixture();r['model']['support'][0][1]['X']='-2'
    with pytest.raises(ValueError,match='trusted source'):a.propagate_quantities(r,t)


def test_source_bound_conversion_scales_value_and_variance():
    r,t=a.quantity_input_fixture('conversion');out=a.propagate_quantities(r,t)['outputs']['Y']
    assert out['result']['output_mean']=='200' and out['result']['output_variance']=='2500'
    assert out['unit']=='cm' and out['budget']['propagation']['variance_dimension']==[2,0,0]
    r['model']['outputs']['Y']['expression']=['input','X'];reseal_model(r,t)
    with pytest.raises(ValueError):a.propagate_quantities(r,t)


@pytest.mark.parametrize('mutation',['remove_conversion','wrong_scale','uncertain_scale'])
def test_conversion_relabelling_or_omitted_parameter_uncertainty_rejects(mutation):
    r,t=a.quantity_input_fixture('conversion')
    if mutation=='remove_conversion':r['model']['outputs']['Y']['conversion']=None;reseal_model(r,t)
    elif mutation=='wrong_scale':
        r['parameters']['scale']['quantity']['value']='10';rebind_quantity(r,t,'scale',True)
    else:
        r['parameters']['scale']['quantity']['uncertainty']={'category':'moments'};rebind_quantity(r,t,'scale',True)
    with pytest.raises(ValueError):a.propagate_quantities(r,t)


def test_declared_bounds_are_not_standard_deviations_and_zero_denominator_rejects():
    r,t=a.quantity_input_fixture('bounds');out=a.propagate_quantities(r,t)['outputs']['Y']
    assert out['result']['output_bounds']==['1/3','1'] and out['result']['output_variance'] is None
    assert out['budget']['propagation']['kind']=='bound'
    r['inputs']['X']['quantity']['uncertainty']['interval']=['-1','1'];r['inputs']['X']['quantity']['value']='0';rebind_quantity(r,t)
    r['model']['bounds']['X']=['-1','1'];reseal_model(r,t)
    with pytest.raises(ValueError,match='denominator'):a.propagate_quantities(r,t)


def test_expanded_metadata_without_coverage_remains_partial():
    r,t=a.quantity_input_fixture('metadata');result=a.propagate_quantities(r,t)
    assert result['outputs']['Y']['result']['nominal']=='2'
    assert result['outputs']['Y']['result']['output_variance'] is None
    r['model'].update(method='moments',means={'X':'2'},covariance=[['1']]);reseal_model(r,t)
    with pytest.raises(ValueError,match='coverage'):a.propagate_quantities(r,t)


def test_supplied_expanded_coverage_uses_only_that_factor():
    r,t=a.quantity_input_fixture('metadata');r['inputs']['X']['quantity']['uncertainty']['coverage_factor']='2'
    r['inputs']['X']['quantity']['uncertainty']['coverage_information']='factor supplied by declared fixture'
    rebind_quantity(r,t);r['model'].update(method='moments',means={'X':'2'},covariance=[['1/4']]);reseal_model(r,t)
    assert a.propagate_quantities(r,t)['outputs']['Y']['result']['output_variance']=='1/4'
    r['model']['covariance']=[['1']];reseal_model(r,t)
    with pytest.raises(ValueError,match='expanded uncertainty'):a.propagate_quantities(r,t)


def test_same_source_cancels_and_reinforces_with_joint_covariance():
    for route,covariance,residual in [('shared_cancel','2','0'),('shared_reinforce','-2','8')]:
        r,t=a.quantity_input_fixture(route);out=a.propagate_quantities(r,t)
        assert out['output_covariance'][0][1]==covariance
        assert out['outputs']['residual']['result']['output_variance']==residual


def test_payload_alias_cannot_make_an_independent_copy():
    r,t=a.quantity_input_fixture('moments');alias=deepcopy(r['inputs']['X']);old=t[alias['source_id']]
    copy=m.source('different-label',old['role'],old['payload']);t[copy['id']]=copy;alias['source_id']=copy['id']
    r['inputs']['copy']=alias;r['model']['input_order'].append('copy');r['model']['input_bindings']['copy']=a._input_identity(alias)
    reseal_model(r,t)
    with pytest.raises(ValueError,match='aliases'):a.propagate_quantities(r,t)


def test_prediction_rejects_evaluation_source_but_comparison_keeps_role():
    r,t=a.quantity_input_fixture('moments');binding=r['inputs']['X'];binding['quantity']['role']='evaluation'
    old=t[binding['source_id']];payload=deepcopy(old['payload']);payload['quantities']['X']=deepcopy(binding['quantity'])
    source=m.source(old['id'],'evaluation',payload);t[source['id']]=source;binding['source_sha256']=source['sha256']
    r['model']['input_bindings']['X']=a._input_identity(binding);reseal_model(r,t)
    with pytest.raises(ValueError,match='evaluation quantity'):a.propagate_quantities(r,t)
    r['stage']='comparison';assert a.propagate_quantities(r,t)['inputs']['X']['role']=='evaluation'


def test_published_measurement_survives_without_raw_stream_or_invented_covariance():
    r,t=a.quantity_input_fixture('published');out=a.propagate_quantities(r,t)
    q=out['inputs']['X'];assert q['uncertainty']['category']=='standard_uncertainty'
    assert q['uncertainty']['printed_token']=='0.0018'
    assert set(q['corrections'])=={'NP3','wall'}
    assert all(c['status']=='included_in_input' for c in q['corrections'].values())
    assert out['outputs']['Y']['result']['nominal']=='14204057517667/10000'
    assert out['outputs']['Y']['result']['output_variance'] is None


def test_source_dimension_boolean_cannot_match_integer():
    r,t=a.quantity_input_fixture();r['inputs']['X']['quantity']['dimension']=[False,0,0]
    with pytest.raises(ValueError,match='trusted quantity'):a.propagate_quantities(r,t)


def test_source_disagreed_joint_law_moments_reject():
    r,t=a.quantity_input_fixture();r['model']['means']={'X':'7'};reseal_model(r,t)
    with pytest.raises(ValueError,match='means disagree'):a.propagate_quantities(r,t)


def test_two_output_units_keep_distinct_budgets_and_common_uncertain_input():
    r,t=a.quantity_input_fixture('multi_output');out=a.propagate_quantities(r,t)
    assert out['output_covariance']==[['8','12'],['12','18']]
    f,d=(out['outputs'][n] for n in ('frequency','duration'))
    assert (f['unit'],d['unit'])==('Hz','s')
    assert f['budget']['propagation']['included_sources']==d['budget']['propagation']['included_sources']
    assert f['parameter_bindings'] and d['parameter_bindings']
    r['inputs']['X']['quantity']['value']='1';rebind_quantity(r,t)
    r['model']['means']['X']='1';r['model']['covariance']=[['3']];reseal_model(r,t)
    changed=a.propagate_quantities(r,t)
    assert changed['outputs']['frequency']['result']['output_mean']=='2'
    assert changed['output_covariance']==[['12','18'],['18','27']]


@pytest.mark.parametrize('components', [['X'],['missing']])
def test_source_aggregate_cycle_or_unknown_component_rejects(components):
    r,t=a.quantity_input_fixture();r['inputs']['X']['quantity']['components']=components;rebind_quantity(r,t)
    with pytest.raises(ValueError,match='aggregate'):a.propagate_quantities(r,t)


def test_exact_definition_cannot_acquire_spread_in_finite_law():
    r,t=a.quantity_input_fixture();r['inputs']['X']['quantity']['uncertainty']={'category':'exact_definition'};rebind_quantity(r,t)
    with pytest.raises(ValueError,match='exact definition'):a.propagate_quantities(r,t)


@pytest.mark.parametrize('route', ['finite_joint_law','bounds','conversion'])
def test_output_domain_must_contain_propagated_image(route):
    r,t=a.quantity_input_fixture(route);r['model']['outputs']['Y']['domain']=['-1/10','1/10'];reseal_model(r,t)
    with pytest.raises(ValueError,match='output image'):a.propagate_quantities(r,t)


def test_moments_cannot_have_impossible_variance_on_bounded_domain():
    r,t=a.quantity_input_fixture('moments');r['model']['covariance']=[['10001']];reseal_model(r,t)
    with pytest.raises(ValueError,match='bounded input domain'):a.propagate_quantities(r,t)


def test_conversion_carries_a_source_bound_interval_without_probability_law():
    r,t=a.quantity_input_fixture('conversion');r['inputs']['X']['quantity']['uncertainty']={'category':'bound','interval':['3/2','5/2']}
    rebind_quantity(r,t);r['model'].update(method='bounds',means=None,covariance=None,bounds={'X':['3/2','5/2']});reseal_model(r,t)
    result=a.propagate_quantities(r,t)['outputs']['Y']['result']
    assert result['output_bounds']==['150','250'] and result['output_variance'] is None


@pytest.mark.parametrize('uncertainty', [
    {'category':'unknown'}, {'category':'unknown','reason':'not supplied','value':'0'},
    {'category':'unknown','reason':'not supplied','interval':['0','0']},
    {'category':'exact_definition','value':'1'}])
def test_unknown_and_exact_categories_cannot_hide_quantified_uncertainty(uncertainty):
    r,t=a.quantity_input_fixture();r['inputs']['X']['quantity']['uncertainty']=uncertainty;rebind_quantity(r,t)
    with pytest.raises(ValueError):a.propagate_quantities(r,t)


def test_partial_calibration_uncertainty_is_not_reported_as_quantified():
    r,t=a.quantity_input_fixture('published');result=a.propagate_quantities(r,t)
    assert result['outputs']['Y']['budget']['calibration']['kind']=='unknown'
    assert result['outputs']['Y']['budget']['calibration']['included_sources']


def test_aggregate_cannot_count_a_grandchild_as_an_independent_contribution():
    r,t=a.quantity_input_fixture('moments');old=t[r['inputs']['X']['source_id']]
    payload=deepcopy(old['payload']);payload['quantities']['middle']=deepcopy(payload['quantities']['X'])
    payload['quantities']['leaf']=deepcopy(payload['quantities']['X'])
    payload['quantities']['X']['components']=['middle'];payload['quantities']['middle']['components']=['leaf']
    source=m.source(old['id'],old['role'],payload);t[source['id']]=source
    def binding(name):
        return {'schema':a.QUANTITY_SCHEMA,'source_id':source['id'],'source_sha256':source['sha256'],
                'quantity_id':name,'quantity':deepcopy(payload['quantities'][name])}
    r['inputs']={'X':binding('X'),'leaf':binding('leaf')}
    r['model'].update(input_order=['X','leaf'],input_bindings={n:a._input_identity(b) for n,b in r['inputs'].items()},
                      means={'X':'0','leaf':'0'},covariance=[['2','0'],['0','2']])
    r['model']['outputs']['Y']['expression']=['add',['input','X'],['input','leaf']];reseal_model(r,t)
    with pytest.raises(ValueError,match='aggregate and own components'):a.propagate_quantities(r,t)


@pytest.mark.parametrize('name',['hydrogen','cesium'])
@pytest.mark.parametrize('mutation',['receipt','raw_bytes'])
def test_primary_receipt_and_archived_bytes_are_independently_bound(tmp_path,monkeypatch,mutation,name):
    import json
    old=a.DATA/name/'source';new=tmp_path/name/'source';new.mkdir(parents=True)
    receipt=json.loads((old/'source_receipt.json').read_text())
    raw=(old/receipt['file']).read_bytes()
    if mutation=='receipt':receipt['method']='changed transcription review'
    else:raw+=b'changed'
    (new/'source_receipt.json').write_text(json.dumps(receipt));(new/receipt['file']).write_bytes(raw)
    monkeypatch.setattr(a,'DATA',tmp_path)
    with pytest.raises(ValueError,match='primary'):a.load_primary_receipt(name)


def test_constant_readout_does_not_acquire_unrelated_input_uncertainty():
    r,t=a.quantity_input_fixture('multi_output')
    r['model']['outputs']['constant']={**deepcopy(r['model']['outputs']['frequency']), 'expression':['parameter','frequency']}
    reseal_model(r,t);result=a.propagate_quantities(r,t)
    assert result['outputs']['constant']['result']['output_variance']=='0'
    assert result['outputs']['constant']['budget']['propagation']['included_sources']=={}
    assert result['output_covariance'][-1]==['0','0','0']


def test_published_aggregate_standard_uncertainty_reaches_affine_output():
    r,t=a.quantity_input_fixture('published_moments');result=a.propagate_quantities(r,t)
    output=result['outputs']['Y']
    assert output['result']['output_mean']=='177550718971/125'
    assert output['result']['output_variance']=='1/250000'
    assert output['result']['uncertainty_status']=='exact_for_declared_affine_model'
    assert output['budget']['propagation']['variance_unit']=={'base_unit':'Hz','power':2}
    assert result['inputs']['X']['uncertainty']['printed_token']=='0.002'
    assert 'NBS-III' in result['inputs']['X']['uncertainty']['shared_reference']
    assert r['model']['support'] is None and result['physical_model_discrepancy']['kind']=='unknown'


def test_primary_cesium_receipt_preserves_table_and_campaign_distinction():
    receipt=a.load_primary_receipt('cesium');profile=a.load_profile('cesium')
    table=receipt['transcription']['p179_Table1'];august=receipt['transcription']['p181_section5']
    assert table['entries']==profile['uncertainty_budgets']['typical_Table1']['entries']
    assert table['total_TypeB_standard_uncertainty']=='0.11'
    assert table['low_density_spin_exchange_included_in_TypeB_total'] is False
    assert august['TypeA_standard_uncertainty']=='0.44e-15'
    assert august['TypeB_standard_uncertainty']=='0.16e-15'
    assert august['spin_exchange_statistical_uncertainty_included_in_TypeA'] is True

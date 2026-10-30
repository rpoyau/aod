"""Scientific positive and hostile controls for typed maps and exact joint laws."""
from copy import deepcopy
from fractions import Fraction as Q
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import pytest
ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('m3_mapping_error',ROOT/'manual/scripts/aod_mapping_error.py')
m = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(m)


def setup_map():
    record=m.example_map()
    registry={s['id']:s for s in record['sources']}
    values={'x':m.value(record['domain'][0],3,{s['id']:s['sha256'] for s in record['sources']},
                       {'kind':'source','source_id':'model:scale','payload_key':'input'})}
    return record,registry,values


@pytest.mark.parametrize('field',m.FIELDS)
def test_map_rejects_missing_contract_field(field):
    record,registry,_=setup_map();del record[field]
    with pytest.raises(m.ContractError): m.validate_map(record,registry)


def test_map_executes_bound_rational_law_and_detects_changed_input():
    record,registry,values=setup_map()
    result=m.run_map(record,values,registry)
    assert result['outputs']['y']['value']=='6'
    values['x']['value']='4'
    with pytest.raises(m.ContractError,match='hash'):m.run_map(record,values,registry)


@pytest.mark.parametrize('mutation',['source','parameter','code','domain','unit','dimension','origin','version'])
def test_independently_bound_map_negative_controls(mutation):
    record,registry,values=setup_map()
    if mutation=='source': record['sources'][0]=m.source('unbound','model',{'factor':'2'})
    if mutation=='parameter':record['parameters']['factor']['value']='3'
    if mutation=='code':record['code_sha256']='0'*64
    if mutation=='domain':record['domain'][0]['bounds']=['4','5']
    if mutation=='unit':record['domain'][0]['unit']='m'
    if mutation=='dimension':record['codomain'][0]['dimension']=[3,0,0]
    if mutation=='origin':del record['parameters']['factor']['origin']
    if mutation=='version':record['version']=''
    if mutation!='code':record=m.seal(record)
    with pytest.raises(m.ContractError):m.run_map(record,values,registry)


def test_source_payload_tamper_and_spec_tamper_are_separate_guards():
    record,registry,_=setup_map();record['sources'][0]['payload']['factor']='3';record=m.seal(record)
    with pytest.raises(m.ContractError,match='hash'):m.validate_map(record,registry)
    record,registry,_=setup_map();record['law']['y'][0]='add'
    with pytest.raises(m.ContractError,match='specification'):m.validate_map(record,registry)


def test_fitted_parameter_needs_calibration_exposure():
    record,registry,_=setup_map();record['parameters']['factor']['origin']='fitted';record=m.seal(record)
    with pytest.raises(m.ContractError,match='fitted'):m.validate_map(record,registry)


def test_composition_preserves_shared_source_once_and_checks_full_domain():
    a,registry,values=setup_map();b=deepcopy(a);b['id']='second'
    b['domain'][0]['bounds']=['-20','20'];b['codomain'][0]['bounds']=['-40','40'];b=m.seal(b)
    chain=m.compose(a,b,values,registry)
    assert chain['stages'][-1]['outputs']['y']['value']=='12'
    assert chain['shared_sources']==['model:scale'] and len(chain['provenance'])==1
    b['domain'][0]['bounds']=['-10','10'];b=m.seal(b)
    with pytest.raises(m.ContractError,match='image'):m.compose(a,b,values,registry)
    b['domain'][0]['dimension']=[2,0,0];b=m.seal(b)
    with pytest.raises(m.ContractError,match='incompatible'):m.compose(a,b,values,registry)


def test_evaluation_sources_cannot_leak_directly_or_through_input():
    record,registry,values=setup_map();evaluation=m.source('target','evaluation',{'target':'3'});registry['target']=evaluation
    record['sources'].append(evaluation);record=m.seal(record)
    with pytest.raises(m.ContractError,match='evaluation'):m.run_map(record,values,registry)
    record,registry,values=setup_map();registry['target']=evaluation
    values['x']=m.value(record['domain'][0],3,{'target':evaluation['sha256']},{'kind':'source','source_id':'target','payload_key':'target'})
    with pytest.raises(m.ContractError,match='evaluation'):m.run_map(record,values,registry)


def test_exact_projection_loses_reconstruction_without_numerical_error():
    result=m.report()['exact_lossy_projection']
    assert result['witnesses'][0]['input_sha256']!=result['witnesses'][1]['input_sha256']
    assert result['witnesses'][0]['outputs']['y']['value']==result['witnesses'][1]['outputs']['y']['value']
    assert result['witnesses'][0]['outputs']['y']['port']==result['witnesses'][1]['outputs']['y']['port']
    assert result['arithmetic_error']=='0'
    record=m.report()['maps'][2];registry={s['id']:s for s in record['sources']}
    record['information_loss']['reconstruction']='unique';record=m.seal(record)
    with pytest.raises(m.ContractError,match='reconstruction'):m.validate_map(record,registry)


@pytest.mark.parametrize('component',m.ERROR_COMPONENTS)
def test_missing_budget_component_and_unknown_to_zero_fail(component):
    budget=m.default_budget();del budget[component]
    with pytest.raises(m.ContractError,match='components'):m.validate_budget(budget)
    budget=m.default_budget();budget['model_discrepancy']['value']='0'
    with pytest.raises(m.ContractError,match='unknown'):m.validate_budget(budget)


def test_bound_is_not_sigma_and_sources_cannot_be_counted_twice():
    budget=m.default_budget();budget['calibration'].update(kind='standard_uncertainty',value='1')
    with pytest.raises(m.ContractError,match='joint law'):m.validate_budget(budget)
    budget=m.default_budget();budget['calibration']['included_sources']=['clock'];budget['window']['included_sources']=['clock']
    with pytest.raises(m.ContractError,match='twice'):m.validate_budget(budget)
    assert m.validate_budget(m.default_budget())['status']=='partial'


@pytest.mark.parametrize('matrix',[[[1,2],[2,1]],[[0,1],[1,1]],[[1,0],[1,1]],[[1,None],[None,1]]])
def test_invalid_or_unknown_covariance_is_not_silently_accepted(matrix):
    with pytest.raises(m.ContractError):m.validate_psd(matrix)


def test_valid_singular_covariance_and_common_offset_exact_cancellation():
    assert m.quadratic([1,-1],[[4,4],[4,4]])==0
    result=m.report()['legitimate_common_offset_cancellation']
    assert result['output_mean']=='5' and result['output_variance']=='0'
    assert result['uncertainty_status']=='exact_for_declared_affine_model'
    assert m.report()['constant_on_declared_support']['output_variance']=='0'


def test_new_interval_zero_jacobian_oracle_independently_by_two_output_values():
    result=m.report()['interval_zero_linear_control']
    # delta=+-1/100 gives 10000/9999, delta=0 gives 1, each output mass 1/2.
    mean=(Q(10000,9999)+1)/2
    variance=(Q(10000,9999)-1)**2/4
    assert Q(result['output_mean'])==mean and Q(result['output_variance'])==variance>0
    assert result['linearized_variance_diagnostic']=='0'
    assert result['uncertainty_status']=='exact_for_declared_joint_law'


def test_new_near_cancelled_product_includes_quadratic_variance_and_mean_shift():
    result=m.report()['near_cancelled_product_control']
    # E[d^2]=1/20000, Var(d^2)=1/400000000, and Cov(d,d^2)=0.
    expected_linear=Q(1,1000)**2/Q(20000)
    expected_nonlinear=Q(999,1000)**2/Q(400000000)
    assert Q(result['linearized_variance_diagnostic'])==expected_linear
    assert Q(result['output_variance'])==expected_linear+expected_nonlinear
    assert Q(result['output_variance'])>40*expected_linear
    assert Q(result['mean_shift'])==-Q(999,1000)/20000


def test_recovered_separate_historical_product_regression():
    result=m.report()['historical_product_regression']
    assert result['output_mean']=='7/8' and result['output_variance']=='1/64'
    assert result['linearized_variance_diagnostic']=='0'
    assert 'partial' in m.report()['historical_probe_status']['fidelity']


def test_covariance_alone_does_not_certify_nonlinear_adequacy():
    result=m.report()['covariance_only_nonlinear']
    assert result['uncertainty_status']=='partial'
    assert result['output_variance'] is None and result['linearized_variance_diagnostic']=='0'
    expr=['mul',['input','a'],['input','b']]
    nonzero=m.propagate(expr,['a','b'],{},means={'a':'1','b':'1'},covariance=[['1/1000000','0'],['0','1/1000000']])
    assert Q(nonzero['linearized_variance_diagnostic'])>0 and nonzero['output_variance'] is None


def test_joint_law_prevents_silently_zeroing_covariance_and_unspecified_independence():
    expr=['mul',['input','a'],['input','b']]
    support=[('1/2',{'a':'1','b':'1'}),('1/2',{'a':'2','b':'2'})]
    with pytest.raises(m.ContractError,match='disagrees'):m.propagate(expr,['a','b'],{},support=support,covariance=[['1/4','0'],['0','1/4']])
    with pytest.raises(m.ContractError,match='sum'):m.propagate(expr,['a','b'],{},support=[('1/3',{'a':'1','b':'1'})])
    with pytest.raises(m.ContractError,match='identities'):m.propagate(expr,['a','a'],{},support=support)


def test_equal_input_means_and_covariance_do_not_determine_nonlinear_output():
    square=['mul',['input','x'],['input','x']]
    first=m.propagate(square,['x'],{},support=[('1/2',{'x':'-1'}),('1/2',{'x':'1'})])
    second=m.propagate(square,['x'],{},support=[('1/8',{'x':'-2'}),('3/4',{'x':'0'}),('1/8',{'x':'2'})])
    assert first['input_mean']==second['input_mean'] and first['input_covariance']==second['input_covariance']
    assert first['output_variance']=='0' and second['output_variance']=='3'


def test_ratio_zero_domains_and_conditional_composed_bound():
    assert m.ratio_bounds(('1','2'),('-1','1'))['bounds'] is None
    assert m.ratio_bounds(('1','2'),('2','3'))['bounds']==['1/3','1']
    result=m.composed_bound('1/100','1/1000',('1','2'),('1/2','3'),'reciprocal')
    assert result['L']=='4' and result['bound']=='41/1000'
    with pytest.raises(m.ContractError,match='images'):m.composed_bound('1/10','0',('1','2'),('1','2'),'affine')
    with pytest.raises(m.ContractError,match='zero'):m.composed_bound('0','0',('-1','1'),('-2','2'),'reciprocal')


def test_rounding_interpretation_is_separate_from_source_hash():
    assert m.parse_printed('0.0E-34','Hz^2','unknown')['bound'] is None
    assert m.parse_printed('0.0E-34','Hz^2','documented_exact_zero')['bound']=='0'
    assert Q(m.parse_printed('1.234E-4','Hz^2','unknown')['bound'])==Q(1,20000000)
    raw=m.source('raw','model',{'token':'1.234E-4','unit':'Hz^2'})
    assert m.validate_sources([raw],{'raw':raw})
    wrong=m.parse_printed(raw['payload']['token'],raw['payload']['unit'],'unknown');wrong['bound']='0'
    assert wrong!=m.parse_printed(raw['payload']['token'],raw['payload']['unit'],'unknown')
    # An intact raw hash does not certify the altered numerical interpretation.
    assert m.validate_sources([raw],{'raw':raw})


def test_stored_report_reproduces_and_read_only_check_rejects_mutation(tmp_path):
    expected=m.report();assert json.loads(m.REPORT.read_text())==expected
    script=str(ROOT/'manual/scripts/aod_mapping_error.py')
    destination=tmp_path/'report.json'
    subprocess.run([sys.executable,script,'--write','--output',str(destination)],check=True,capture_output=True)
    original=destination.read_bytes()
    subprocess.run([sys.executable,script,'--check','--output',str(destination)],check=True,capture_output=True)
    assert destination.read_bytes()==original
    changed=json.loads(original);changed['interval_zero_linear_control']['output_variance']='0';destination.write_text(json.dumps(changed))
    result=subprocess.run([sys.executable,script,'--check','--output',str(destination)],capture_output=True)
    assert result.returncode!=0


def test_projection_cannot_promote_injectivity_by_flipping_boolean():
    record=m.report()['maps'][2];registry={s['id']:s for s in record['sources']}
    record['structure']['injective']=True;record['information_loss']['reconstruction']='unique';record=m.seal(record)
    with pytest.raises(m.ContractError,match='rank'):m.validate_map(record,registry)


def test_standard_uncertainty_requires_actual_law_and_matches_variance():
    budget=m.default_budget();budget['calibration'].update(kind='standard_uncertainty',value='1',joint_law=[('1/2',{'error':'-1'}),('1/2',{'error':'1'})])
    assert m.validate_budget(budget)['status']=='partial'
    budget['calibration']['value']='2'
    with pytest.raises(m.ContractError,match='disagrees'):m.validate_budget(budget)
    budget['calibration']['joint_law']='assume Gaussian silently'
    with pytest.raises(m.ContractError,match='joint law'):m.validate_budget(budget)


def test_exact_definition_and_unknown_realization_are_distinct():
    assert m.reference_uncertainty('defining_constant','0')['variance']=='0'
    with pytest.raises(m.ContractError,match='exactly zero'):m.reference_uncertainty('defining_constant','1/1000')
    result=m.reference_uncertainty('realized_reference')
    assert result['variance'] is None and 'partial' in result['status']
    assert m.reference_uncertainty('realized_reference','1/1000')['variance']=='1/1000'


def test_dimensionally_wrong_port_cannot_be_fixed_by_matching_only_operands():
    p=m.port('x',dimension=(3,0,0),unit='m^2')
    with pytest.raises(m.ContractError,match='unit/dimension'):m.validate_port(p)


def test_resealed_raw_input_cannot_change_trusted_source_value():
    record,registry,values=setup_map()
    values['x']=m.value(record['domain'][0],4,values['x']['provenance'],values['x']['origin'])
    with pytest.raises(m.ContractError,match='bound source'):m.run_map(record,values,registry)


def test_resealed_upstream_output_requires_actual_execution():
    a,registry,values=setup_map();b=deepcopy(a);b['id']='second'
    b['domain'][0]['bounds']=['-20','20'];b['codomain'][0]['bounds']=['-40','40'];b=m.seal(b)
    output=m.run_map(a,values,registry)['outputs']['y']
    forged=m.value(output['port'],7,output['provenance'],output['origin'])
    with pytest.raises(m.ContractError,match='upstream execution'):m.run_map(b,{'x':forged},registry)
    output['origin']['execution_sha256']='0'*64
    output=m.value(output['port'],output['value'],output['provenance'],output['origin'])
    with pytest.raises(m.ContractError,match='upstream execution'):m.run_map(b,{'x':output},registry)


def test_free_status_string_cannot_promote_physical_applicability():
    record,registry,_=setup_map();record['status']['physical_applicability']='complete';record=m.seal(record)
    with pytest.raises(m.ContractError,match='physical applicability'):m.validate_map(record,registry)
    record,registry,_=setup_map();record['error']['model_discrepancy'].update(kind='exact',value='0');record=m.seal(record)
    with pytest.raises(m.ContractError,match='discrepancy'):m.validate_map(record,registry)


def test_full_discrete_law_can_exist_when_linearization_point_is_outside_domain():
    expr=['div',['parameter','one'],['input','x']]
    result=m.propagate(expr,['x'],{'one':{'value':'1'}},support=[('1/2',{'x':'-1'}),('1/2',{'x':'1'})])
    assert result['output_variance']=='1' and result['output_mean']=='0'
    assert result['linearized_variance_diagnostic'] is None and result['mean_shift'] is None


@pytest.mark.parametrize('support',[None,[('1',{'x':'1'})]])
def test_duplicate_source_order_rejected_in_both_propagation_paths(support):
    with pytest.raises(m.ContractError,match='distinct input source'):
        m.propagate(['input','x'],['x','x'],{},means={'x':'1'},covariance=[['1','0'],['0','1']],support=support)


def test_printed_rounding_bound_explicitly_depends_on_rounding_policy():
    result=m.parse_printed('1.234E-4','Hz^2','unknown')
    assert result['status']=='conditional_deterministic_rounding_bound'
    assert result['rounding_policy']=='nearest_to_printed_last_place'
    with pytest.raises(m.ContractError,match='rounding policy'):m.parse_printed('1.234E-4','Hz^2','unknown','unknown')


def test_calibration_source_cannot_hide_behind_declared_parameter_origin():
    s=m.source('cal:measured','calibration',{'factor':'2','input':'3'})
    record=m.example_map(source_record=s)
    with pytest.raises(m.ContractError,match='calibration applicable'):m.validate_map(record,{s['id']:s})
    record['calibration']={'status':'unknown','reason':'realization not characterized'}
    record['error']['calibration']={'kind':'unknown','reason':'realization unknown','unit':'1','scope':'parameter','provenance':s['id']}
    m.validate_map(m.seal(record),{s['id']:s})
    record['error']['calibration'].update(kind='exact',value='0')
    with pytest.raises(m.ContractError,match='real calibration'):m.validate_map(m.seal(record),{s['id']:s})


def test_calibration_provenance_and_raw_source_hash_are_checked_even_outside_map_sources():
    record,registry,values=setup_map()
    s=m.source('cal:input','calibration',{'x':'3'});registry[s['id']]=s
    values['x']=m.value(record['domain'][0],3,{s['id']:s['sha256']},{'kind':'source','source_id':s['id'],'payload_key':'x'})
    with pytest.raises(m.ContractError,match='calibration applicable'):m.run_map(record,values,registry)
    s=m.source('raw:input','model',{'x':'3'});registry[s['id']]=s;s['payload']['x']='4'
    values['x']=m.value(record['domain'][0],4,{s['id']:s['sha256']},{'kind':'source','source_id':s['id'],'payload_key':'x'})
    with pytest.raises(m.ContractError,match='source content hash'):m.run_map(record,values,registry)

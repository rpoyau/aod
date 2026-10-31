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


def budget_fixture():
    record,registry,_=setup_map()
    output=record['codomain'][0]
    return record['error']['y'],output,registry,m.model_sha256(record)


def quantify(budget, output, registry, fingerprint, *, component='calibration',
             kind='bound', amount='1', included=None, law=None, role='model', identity='evidence:error'):
    """An independent trusted fixture binds an output-error claim before validation."""
    included={} if included is None else included
    payload={'model_sha256':fingerprint,'output':output['name'],'component':component,
             'kind':kind,'unit':output['unit'],'value':amount,'included_sources':included}
    if kind=='standard_uncertainty':payload['joint_law']=law
    evidence=m.source(identity,role,{'result':payload});registry[identity]=evidence
    budget[component]={'kind':kind,'unit':output['unit'],'reason':'declared output-error evidence',
        'value':amount,'included_sources':included,
        'evidence':{'source_id':identity,'payload_key':'result','sha256':evidence['sha256']}}
    return evidence


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
    budget,output,registry,fingerprint=budget_fixture();del budget[component]
    with pytest.raises(m.ContractError,match='components'):m.validate_budget(budget,output,registry,model_sha256=fingerprint)
    budget=m.default_budget(output);budget['model_discrepancy']['value']='0'
    with pytest.raises(m.ContractError,match='unknown'):m.validate_budget(budget,output,registry,model_sha256=fingerprint)


def test_bound_is_not_sigma_and_sources_cannot_be_counted_twice():
    budget,output,registry,fingerprint=budget_fixture()
    quantify(budget,output,registry,fingerprint,kind='standard_uncertainty')
    with pytest.raises(m.ContractError,match='joint law'):m.validate_budget(budget,output,registry,model_sha256=fingerprint)
    budget=m.default_budget(output)
    for name in ('calibration','window'):
        budget[name].update(kind='unknown',included_sources={'model:scale':registry['model:scale']['sha256']})
    with pytest.raises(m.ContractError,match='twice'):m.validate_budget(budget,output,registry,model_sha256=fingerprint)
    assert m.validate_budget(m.default_budget(output),output,registry,model_sha256=fingerprint)['status']=='partial'


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
    budget,output,registry,fingerprint=budget_fixture()
    law=[('1/2',{'error':'-1'}),('1/2',{'error':'1'})]
    quantify(budget,output,registry,fingerprint,kind='standard_uncertainty',law=law)
    assert m.validate_budget(budget,output,registry,model_sha256=fingerprint)['status']=='partial'
    quantify(budget,output,registry,fingerprint,kind='standard_uncertainty',amount='2',law=law)
    with pytest.raises(m.ContractError,match='disagrees'):m.validate_budget(budget,output,registry,model_sha256=fingerprint)
    quantify(budget,output,registry,fingerprint,kind='standard_uncertainty',law='assume Gaussian silently')
    with pytest.raises(m.ContractError,match='joint law'):m.validate_budget(budget,output,registry,model_sha256=fingerprint)


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
    record,registry,_=setup_map();record['error']['y']['model_discrepancy'].update(kind='exact',value='0');record=m.seal(record)
    with pytest.raises(m.ContractError,match='computational'):m.validate_map(record,registry)


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
    record['error']['y']['calibration']={'kind':'unknown','reason':'realization unknown','unit':'1','included_sources':{s['id']:s['sha256']}}
    m.validate_map(m.seal(record),{s['id']:s})
    record['error']['y']['calibration'].update(kind='exact',value='0',included_sources={})
    with pytest.raises(m.ContractError,match='computational'):m.validate_map(m.seal(record),{s['id']:s})


def test_calibration_provenance_and_raw_source_hash_are_checked_even_outside_map_sources():
    record,registry,values=setup_map()
    s=m.source('cal:input','calibration',{'x':'3'});registry[s['id']]=s
    values['x']=m.value(record['domain'][0],3,{s['id']:s['sha256']},{'kind':'source','source_id':s['id'],'payload_key':'x'})
    with pytest.raises(m.ContractError,match='calibration applicable'):m.run_map(record,values,registry)
    s=m.source('raw:input','model',{'x':'3'});registry[s['id']]=s;s['payload']['x']='4'
    values['x']=m.value(record['domain'][0],4,{s['id']:s['sha256']},{'kind':'source','source_id':s['id'],'payload_key':'x'})
    with pytest.raises(m.ContractError,match='source content hash'):m.run_map(record,values,registry)


@pytest.mark.parametrize('injective',['unknown',1,0,1.0,0.0,'true',None])
def test_unique_reconstruction_requires_strict_boolean_and_rank_proof(injective):
    record=m.report()['maps'][2];registry={s['id']:s for s in record['sources']}
    record['structure']['injective']=injective
    record['information_loss']['reconstruction']='unique'
    with pytest.raises(m.ContractError,match='injectivity'):
        m.validate_map(m.seal(record),registry)


def test_unknown_injectivity_remains_valid_without_unique_reconstruction():
    record=m.report()['maps'][2];registry={s['id']:s for s in record['sources']}
    record['structure']['injective']='unknown'
    m.validate_map(m.seal(record),registry)


@pytest.mark.parametrize('mutation',['flat','missing','extra'])
def test_error_budgets_match_the_output_set(mutation):
    record,registry,_=setup_map()
    if mutation=='flat':record['error']=record['error']['y']
    if mutation=='missing':record['error']={}
    if mutation=='extra':record['error']['other']=deepcopy(record['error']['y'])
    with pytest.raises(m.ContractError):m.validate_map(m.seal(record),registry)


@pytest.mark.parametrize('mutation',['unit','free_provenance','missing_evidence','unknown_evidence',
                                    'reference_hash','source_content','payload_key','evaluation'])
def test_quantified_errors_require_output_units_and_trusted_evidence(mutation):
    budget,output,registry,fingerprint=budget_fixture()
    evidence=quantify(budget,output,registry,fingerprint,component='propagation')
    component=budget['propagation']
    if mutation=='unit':component['unit']='s'
    if mutation=='free_provenance':component['provenance']='does-not-exist'
    if mutation=='missing_evidence':del component['evidence']
    if mutation=='unknown_evidence':component['evidence']['source_id']='does-not-exist'
    if mutation=='reference_hash':component['evidence']['sha256']='0'*64
    if mutation=='source_content':evidence['payload']['result']['value']='2'
    if mutation=='payload_key':component['evidence']['payload_key']='does-not-exist'
    if mutation=='evaluation':evidence['role']='evaluation'
    with pytest.raises(m.ContractError):m.validate_budget(budget,output,registry,model_sha256=fingerprint)


@pytest.mark.parametrize('field',['model_sha256','output','component','kind','unit','value','included_sources'])
def test_evidence_cannot_be_reused_for_a_different_claim(field):
    budget,output,registry,fingerprint=budget_fixture()
    evidence=quantify(budget,output,registry,fingerprint)
    changed=deepcopy(evidence['payload'])
    changed['result'][field]={'ghost':'0'*64} if field=='included_sources' else 'different'
    changed=m.source(evidence['id'],evidence['role'],changed)
    registry[changed['id']]=changed
    budget['calibration']['evidence']['sha256']=changed['sha256']
    with pytest.raises(m.ContractError,match='evidence disagrees'):
        m.validate_budget(budget,output,registry,model_sha256=fingerprint)


@pytest.mark.parametrize('field',['code_sha256','id','version','domain','codomain','law','parameters'])
def test_model_fingerprint_binds_every_computational_field(field):
    record,_,_=setup_map();original=m.model_sha256(record)
    record[field]={'changed':record[field]}
    assert m.model_sha256(record)!=original


@pytest.mark.parametrize('change',['id','version','domain','codomain','law','parameter'])
def test_retained_bound_evidence_rejects_an_otherwise_valid_changed_model(change):
    record,registry,_=setup_map()
    evidence=quantify(record['error']['y'],record['codomain'][0],registry,m.model_sha256(record))
    record['sources'].append(evidence)
    m.validate_map(m.seal(record),registry)
    if change=='id':record['id']='map:renamed'
    if change=='version':record['version']='3'
    if change=='domain':record['domain'][0]['bounds']=['-9','9']
    if change=='codomain':record['codomain'][0]['bounds']=['-30','30']
    if change=='law':record['law']['y']=['mul',['parameter','factor'],['input','x']]
    if change=='parameter':
        record['parameters']['factor']['value']='3'
        revised=m.source('model:scale','model',{'factor':'3','input':'3'})
        registry[revised['id']]=revised;record['sources'][0]=revised
    changed=m.seal(record)
    with pytest.raises(m.ContractError,match='evidence disagrees'):m.validate_map(changed,registry)
    # Replacing only the obsolete error claim restores an admissible map.
    changed['error']['y']=m.default_budget(changed['codomain'][0])
    m.validate_map(m.seal(changed),registry)


def test_evidence_and_full_specification_are_outside_computational_fingerprint():
    record,registry,_=setup_map();original=m.model_sha256(record)
    evidence=quantify(record['error']['y'],record['codomain'][0],registry,original)
    record['sources'].append(evidence)
    revised=m.seal(record)
    assert m.model_sha256(revised)==original and revised['spec_sha256']!=record['spec_sha256']
    m.validate_map(revised,registry)


@pytest.mark.parametrize('kind',['unknown','not_applicable'])
def test_unresolved_or_inapplicable_error_has_no_hidden_numeric_claim(kind):
    budget,output,registry,fingerprint=budget_fixture()
    budget['window'].update(kind=kind,value='0')
    with pytest.raises(m.ContractError,match='unknown/inapplicable'):
        m.validate_budget(budget,output,registry,model_sha256=fingerprint)


@pytest.mark.parametrize('component',['resolution','window','calibration','comparison'])
def test_unproved_exact_zero_is_not_an_observation_error_certificate(component):
    budget,output,registry,fingerprint=budget_fixture()
    budget[component].update(kind='exact',value='0')
    with pytest.raises(m.ContractError,match='computational'):
        m.validate_budget(budget,output,registry,model_sha256=fingerprint)


def test_zero_standard_uncertainty_can_follow_from_a_trusted_constant_law():
    budget,output,registry,fingerprint=budget_fixture()
    quantify(budget,output,registry,fingerprint,kind='standard_uncertainty',amount='0',law=[('1',{'error':'0'})])
    assert m.validate_budget(budget,output,registry,model_sha256=fingerprint)['status']=='partial'


def test_joint_law_must_be_inside_the_evidence_and_is_hashed():
    budget,output,registry,fingerprint=budget_fixture()
    evidence=quantify(budget,output,registry,fingerprint,kind='standard_uncertainty',
        law=[('1/2',{'error':'-1'}),('1/2',{'error':'1'})])
    budget['calibration']['joint_law']=[('1',{'error':'0'})]
    with pytest.raises(m.ContractError,match='fields'):m.validate_budget(budget,output,registry,model_sha256=fingerprint)
    del budget['calibration']['joint_law']
    evidence['payload']['result']['joint_law']=[('1',{'error':'0'})]
    with pytest.raises(m.ContractError,match='hash'):m.validate_budget(budget,output,registry,model_sha256=fingerprint)


def test_evidence_sources_are_retained_but_do_not_become_calibration_operands():
    record,registry,values=setup_map()
    evidence=quantify(record['error']['y'],record['codomain'][0],registry,m.model_sha256(record),
        component='propagation',role='calibration',included={'model:scale':registry['model:scale']['sha256']})
    record['sources'].append(evidence);record=m.seal(record)
    result=m.run_map(record,values,registry)
    assert result['outputs']['y']['value']=='6'
    assert result['operand_sources']=={'y':{'model:scale':registry['model:scale']['sha256']}}
    assert result['provenance'][evidence['id']]==evidence['sha256']
    assert record['calibration']['status']=='not_applicable'
    second,_,_=setup_map();second['id']='downstream'
    second['domain'][0]['bounds']=['-20','20'];second['codomain'][0]['bounds']=['-40','40']
    downstream=m.run_map(m.seal(second),{'x':result['outputs']['y']},registry)
    assert downstream['outputs']['y']['value']=='12'
    assert downstream['operand_sources']==result['operand_sources']
    assert evidence['id'] in downstream['provenance']


def test_evidence_must_be_in_map_sources_and_included_sources_must_be_operands():
    record,registry,values=setup_map()
    evidence=quantify(record['error']['y'],record['codomain'][0],registry,m.model_sha256(record))
    with pytest.raises(m.ContractError,match='retained'):m.validate_map(m.seal(record),registry)
    unused=m.source('unused','model',{'reading':'1'});registry[unused['id']]=unused
    evidence=quantify(record['error']['y'],record['codomain'][0],registry,m.model_sha256(record),
        included={unused['id']:unused['sha256']})
    record['sources'].append(evidence)
    with pytest.raises(m.ContractError,match='not an output operand'):m.run_map(m.seal(record),values,registry)


def test_evidence_cannot_double_as_a_raw_operand_source():
    record,registry,values=setup_map()
    evidence=quantify(record['error']['y'],record['codomain'][0],registry,m.model_sha256(record))
    payload=deepcopy(evidence['payload']);payload['input']='3'
    evidence=m.source(evidence['id'],evidence['role'],payload);registry[evidence['id']]=evidence
    record['error']['y']['calibration']['evidence']['sha256']=evidence['sha256']
    record['sources'].append(evidence)
    values['x']=m.value(record['domain'][0],3,{evidence['id']:evidence['sha256']},
        {'kind':'source','source_id':evidence['id'],'payload_key':'input'})
    with pytest.raises(m.ContractError,match='also be an operand'):m.run_map(m.seal(record),values,registry)


def test_calibration_operand_bindings_are_required_through_upstream_replay():
    record,registry,values=setup_map()
    calibration=m.source('cal:input','calibration',{'reading':'3'});registry[calibration['id']]=calibration
    values['x']=m.value(record['domain'][0],3,{calibration['id']:calibration['sha256']},
        {'kind':'source','source_id':calibration['id'],'payload_key':'reading'})
    record['calibration']={'status':'unknown','reason':'uncharacterized instrument'}
    record['error']['y']['calibration'].update(kind='unknown')
    with pytest.raises(m.ContractError,match='inclusion'):m.run_map(m.seal(record),values,registry)
    record['error']['y']['calibration']['included_sources']={calibration['id']:calibration['sha256']}
    result=m.run_map(m.seal(record),values,registry)
    second,_,_=setup_map();second['id']='downstream'
    second['domain'][0]['bounds']=['-20','20'];second['codomain'][0]['bounds']=['-40','40']
    with pytest.raises(m.ContractError,match='calibration applicable'):
        m.run_map(m.seal(second),{'x':result['outputs']['y']},registry)
    second['calibration']=deepcopy(record['calibration'])
    second['error']['y']['calibration']=deepcopy(record['error']['y']['calibration'])
    replay=m.run_map(m.seal(second),{'x':result['outputs']['y']},registry)
    assert replay['operand_sources']['y'][calibration['id']]==calibration['sha256']


def test_reused_uncertainty_source_is_valid_for_distinct_outputs():
    record,registry,values=setup_map()
    record['codomain'].append(m.port('z',bounds=('-20','20')))
    record['law']['z']=['input','x'];record['error']['z']=m.default_budget(record['codomain'][1])
    record=m.seal(record)
    included={'model:scale':registry['model:scale']['sha256']}
    for output in record['codomain']:
        evidence=quantify(record['error'][output['name']],output,registry,m.model_sha256(record),
            included=included,identity='evidence:'+output['name'])
        record['sources'].append(evidence)
    result=m.run_map(m.seal(record),values,registry)
    assert result['outputs']['y']['value']=='6' and result['outputs']['z']['value']=='3'


def test_quantified_calibration_binds_actual_operands_without_evidence_self_reference():
    calibration=m.source('cal:scale','calibration',{'factor':'2','input':'3'})
    registry={calibration['id']:calibration}
    record=m.example_map(source_record=calibration)
    record['calibration']={'status':'specified','reason':'declared finite calibration model'}
    evidence=quantify(record['error']['y'],record['codomain'][0],registry,m.model_sha256(record),
        role='calibration',included={calibration['id']:calibration['sha256']})
    record['sources'].append(evidence);record=m.seal(record)
    values={'x':m.value(record['domain'][0],3,{calibration['id']:calibration['sha256']},
        {'kind':'source','source_id':calibration['id'],'payload_key':'input'})}
    result=m.run_map(record,values,registry)
    assert result['outputs']['y']['value']=='6'
    assert set(result['provenance'])=={calibration['id'],evidence['id']}
    assert result['operand_sources']['y']=={calibration['id']:calibration['sha256']}
    # Reissued, internally consistent evidence still cannot omit a real operand.
    omitted=quantify(record['error']['y'],record['codomain'][0],registry,m.model_sha256(record),role='calibration')
    record['sources'][-1]=omitted
    with pytest.raises(m.ContractError,match='inclusion'):m.run_map(m.seal(record),values,registry)


@pytest.mark.parametrize('included',[['model:scale'],{'missing':'0'*64},{'model:scale':'0'*64}])
def test_included_uncertainty_sources_require_trusted_identity_hash_bindings(included):
    budget,output,registry,fingerprint=budget_fixture()
    budget['window'].update(kind='unknown',included_sources=included)
    with pytest.raises(m.ContractError):m.validate_budget(budget,output,registry,model_sha256=fingerprint)


def test_unused_input_provenance_does_not_create_a_calibration_operand():
    record=m.report()['maps'][2];registry={s['id']:s for s in record['sources']}
    calibration=m.source('cal:unused','calibration',{'hidden':'1'});registry[calibration['id']]=calibration
    model=record['sources'][0]
    values={p['name']:m.value(p,3 if p['name']=='x' else 1,
        {model['id']:model['sha256']} if p['name']=='x' else {calibration['id']:calibration['sha256']},
        {'kind':'source','source_id':model['id'] if p['name']=='x' else calibration['id'],
         'payload_key':'input' if p['name']=='x' else 'hidden'}) for p in record['domain']}
    result=m.run_map(record,values,registry)
    assert calibration['id'] in result['provenance']
    assert calibration['id'] not in result['operand_sources']['y']

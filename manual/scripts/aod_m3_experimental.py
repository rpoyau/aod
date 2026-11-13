"""Frozen, source-bound worked comparisons using existing M3 operators."""
from copy import deepcopy
from dataclasses import asdict
from fractions import Fraction as Q
import argparse
import hashlib
import json
from pathlib import Path
import aod_mapping_error as m
import aod_m3_temporal as t
import aod_m3_metrology as mt

ROOT=Path(__file__).resolve().parents[2]
REPORT=ROOT/'manual/data/m3/experimental_input_comparison.json'
PLAN_SCHEMA='aod.m3.prediction-plan.v1'


def require(condition,message):
    if not condition: raise ValueError(message)


def code_bindings():
    paths=[Path(__file__),Path(m.__file__),Path(t.__file__),Path(mt.__file__),Path(t.n.__file__)]
    paths += [ROOT/'contracts/scientific'/name for name in
              ('MAP_CONTRACT.json','ERROR_BUDGET.json','TEMPORAL_OBSERVATION.json','TEMPORAL_METROLOGY.json')]
    return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def _prediction_sources(identities,trusted):
    """Check the declared dependency closure, including nested source references."""
    checked=set();evaluation_hashes={s['sha256'] for s in trusted.values() if s['role']=='evaluation'}
    def source(identity):
        require(type(identity) is str and identity,'source dependency identity required')
        if identity in checked:return
        require(identity in trusted,'prediction source absent from independent trust registry')
        s=trusted[identity];m.validate_sources([s],trusted)
        require(s['role'] in ('model','calibration','definition') and s['sha256'] not in evaluation_hashes,
                'evaluation source or payload alias in prediction')
        checked.add(identity);walk(s['payload'])
    def walk(value):
        if isinstance(value,dict):
            require(value.get('role')!='evaluation','nested evaluation source in prediction')
            if 'source_id' in value:source(value['source_id'])
            for key in ('source_ids','dependency_ids','calibration_source_ids'):
                if key in value:
                    require(isinstance(value[key],list),'source dependency vector required')
                    for identity in value[key]:source(identity)
            if 'included_sources' in value:
                require(isinstance(value['included_sources'],dict),'included source identities required')
                for identity,digest in value['included_sources'].items():
                    source(identity)
                    require(trusted[identity]['sha256']==digest,'included source payload hash differs')
            for item in value.values():walk(item)
        elif isinstance(value,list):
            for item in value:walk(item)
    for identity in identities:source(identity)
    return {i:trusted[i]['sha256'] for i in sorted(checked)}


def predict(binding,trusted_sources,*,original_context):
    require(isinstance(binding,dict) and set(binding)=={'schema','id','source_id','source_sha256','plan'},
            'prediction plan binding fields')
    require(binding['schema']==PLAN_SCHEMA and type(binding['id']) is str and binding['id'], 'prediction plan identity')
    mt.no_floats(binding)
    require(binding['source_id'] in trusted_sources,'prediction plan source not trusted')
    owner=trusted_sources[binding['source_id']];m.validate_sources([owner],trusted_sources)
    require(owner['role']=='model' and owner['sha256']==binding['source_sha256'],'prediction plan source role/hash')
    plan=binding['plan']
    require(m.canonical(owner['payload'].get('prediction_plans',{}).get(binding['id']))==m.canonical(plan),
            'prediction plan differs from trusted source')
    fields={'original_context_sha256','code_bindings','uncertainty_request','readout_definitions',
            'readout_parameter_links','reduction_window','selection','stopping','output_definition',
            'comparison_criterion','calibration_source_ids','exposure'}
    require(isinstance(plan,dict) and set(plan)==fields,'complete prediction plan fields')
    require(plan['code_bindings']==code_bindings(),'prediction executable or contract binding changed')
    require(plan['original_context_sha256']==m.digest(t.plain(asdict(original_context))),
            'original setup differs from frozen prediction plan')
    require(plan['exposure'] in ('retrospective','declared_fixture'),'artifact freeze cannot establish blind chronology')
    selection=plan['selection'];stopping=plan['stopping']
    require(isinstance(selection,dict) and set(selection)=={'candidate_id','rule','source_ids'}
            and type(selection['candidate_id']) is str and selection['candidate_id']
            and selection['rule']=='single_declared_candidate','only a single declared candidate is implemented')
    require(isinstance(stopping,dict) and set(stopping)=={'rule','source_ids'}
            and stopping['rule']=='fixed_context_window','only fixed context-window stopping is implemented')
    require(plan['comparison_criterion']=={'kind':'signed_residual','uncertainty':'joint_if_supplied_else_partial'},
            'unsupported comparison criterion')
    request=plan['uncertainty_request']
    require(request['stage']=='prediction','freeze requires a prediction-stage uncertainty request')
    source_ids=[binding['source_id'],request['model_source_id']]
    source_ids += [q['source_id'] for q in [*request['inputs'].values(),*request['parameters'].values()]]
    for ids in (selection['source_ids'],stopping['source_ids'],plan['calibration_source_ids']):
        require(isinstance(ids,list) and len(ids)==len(set(ids)),'explicit unique prediction dependency ids required')
        source_ids+=ids
    for identity in plan['calibration_source_ids']:
        require(identity in trusted_sources and trusted_sources[identity]['role']=='calibration','calibration exposure source role')
    source_ids += [s['id'] for s in original_context.source_dependencies]
    for s in original_context.source_dependencies:m.validate_sources([s],trusted_sources)
    dependencies=_prediction_sources(source_ids,trusted_sources)
    require(set(plan['calibration_source_ids'])=={i for i in dependencies if trusted_sources[i]['role']=='calibration'},
            'calibration exposure inventory omits a prediction dependency')
    views=t.readouts(original_context,plan['readout_definitions'])
    require(plan['reduction_window']==list(original_context.record.window),
            'prediction reduction must use the executed context window')
    reduction=t.window_reduction(original_context,plan['reduction_window'])
    links=plan['readout_parameter_links']
    require(isinstance(links,dict) and bool(links),'native readout parameter links required')
    for parameter,readout in links.items():
        require(parameter in request['parameters'] and readout in views['outputs'],'readout parameter link absent')
        quantity=mt.validate_quantity(request['parameters'][parameter],trusted_sources);value=views['outputs'][readout]
        require(quantity['uncertainty']['category']=='exact_definition'
                and Q(quantity['value'])==Q(value['value']) and quantity['unit']==value['unit'],
                'propagation parameter differs from replayed native readout')
    propagated=mt.propagate_quantities(request,trusted_sources)
    definition=plan['output_definition']
    require(isinstance(definition,dict) and set(definition)=={'name','estimator'}
            and definition['name'] in propagated['outputs']
            and definition['estimator'] in ('nominal','propagated_mean'),'frozen output definition')
    name=definition['name'];output=propagated['outputs'][name];result=output['result']
    require(set(links)<=m.expression_refs(request['model']['outputs'][name]['expression'],'parameter'),
            'selected output omits the linked native readout')
    if definition['estimator']=='propagated_mean':
        value=result.get('output_mean');require(value is not None,'propagated mean unresolved for selected output')
    else:
        quantities=propagated['inputs']
        require(all(q['value'] is not None for q in quantities.values()),'nominal inputs not supplied')
        parameters={p:mt.validate_quantity(q,trusted_sources) for p,q in request['parameters'].items()}
        value=str(m.evaluate(request['model']['outputs'][name]['expression'],
                             {n:q['value'] for n,q in quantities.items()},parameters))
    return {'schema':'aod.m3.frozen-prediction.v1','plan_binding':deepcopy(binding),
        'source_dependencies':dependencies,'readouts':views,'reduction':reduction,'propagation':propagated,
        'output':{'name':name,'estimator':definition['estimator'],'value':value,'kind':output['kind'],
                  'unit':output['unit'],'dimension':output['dimension'],'variance':result.get('output_variance')},
        'exposure':plan['exposure'],'chronology':'declared plan and replay; no independent time-of-freeze proof',
        'physical_applicability':'unresolved'}


def evaluate(product,target,*,original_plan,trusted_sources,original_context):
    """Replay the complete prediction, then authenticate the separate target."""
    replayed=predict(original_plan,trusted_sources,original_context=original_context)
    require(m.canonical(product)==m.canonical(replayed),'complete prediction differs from original-plan replay')
    require(isinstance(target,dict) and set(target)=={'quantity_binding','joint_evidence'},'evaluation target fields')
    quantity=mt.validate_quantity(target['quantity_binding'],trusted_sources)
    require(quantity['role'] in ('evaluation','calibration'),'target must have an evaluation or calibration role')
    output=replayed['output']
    require(all(quantity[k]==output[k] for k in ('kind','unit','dimension')),'target quantity kind/unit/dimension differs')
    require(quantity['value'] is not None,'target numerical value is missing')
    target_window=quantity['window']
    if target_window is not None:
        views=replayed['readouts']
        require(target_window=={'coordinate':views['coordinate'],'epoch':views['epoch_seconds'],
                                'bounds':views['window']},'target window/coordinate differs from prediction')
    residual=Q(output['value'])-Q(quantity['value'])
    uncertainty={'status':'partial','variance':None,'reason':'No joint prediction/target uncertainty evidence supplied'}
    joint=target['joint_evidence']
    if joint is not None:
        require(isinstance(joint,dict) and set(joint)=={'source_id','evidence_id'},'joint evidence locator fields')
        require(joint['source_id'] in trusted_sources,'joint evidence source not trusted')
        evidence_source=trusted_sources[joint['source_id']];m.validate_sources([evidence_source],trusted_sources)
        require(evidence_source['role'] in ('model','calibration'),'joint evidence source role')
        evidence=evidence_source['payload'].get('comparisons',{}).get(joint['evidence_id'])
        require(isinstance(evidence,dict) and set(evidence)=={'prediction_sha256','target_binding_sha256','request'},
                'joint comparison evidence fields')
        require(evidence['prediction_sha256']==m.digest(product)
                and evidence['target_binding_sha256']==m.digest(target['quantity_binding']),
                'joint evidence belongs to another prediction or target')
        request=evidence['request']
        require(request['stage']=='comparison' and set(request['inputs'])=={'prediction','target'}
                and request['parameters']=={},'joint residual must use both endpoints without extra parameters')
        require(m.canonical(request['inputs']['target'])==m.canonical(target['quantity_binding']),
                'joint model target binding differs')
        prediction_quantity=mt.validate_quantity(request['inputs']['prediction'],trusted_sources)
        require(all(prediction_quantity[k]==output[k] for k in ('kind','unit','dimension','value'))
                and prediction_quantity['role']!='evaluation','joint model prediction endpoint differs')
        model=request['model']
        require(model['method']=='moments' and model['input_order']==['prediction','target']
                and set(model['outputs'])=={'residual'},'joint residual requires supplied endpoint moments')
        require(model['outputs']['residual']=={'kind':output['kind'],'unit':output['unit'],
            'dimension':output['dimension'],'expression':['sub',['input','prediction'],['input','target']],
            'conversion':None,'domain':None},'joint residual output definition differs')
        require(output['variance'] is not None and model['covariance'] is not None
                and Q(model['covariance'][0][0])==Q(output['variance']),
                'joint evidence changes frozen prediction variance')
        propagated=mt.propagate_quantities(request,trusted_sources)
        r=propagated['outputs']['residual']['result']
        require(Q(r['output_mean'])==residual,'joint model residual differs from endpoint comparison')
        uncertainty={'status':'conditional_joint_moments','variance':r['output_variance'],
            'standard_deviation':{'representation':'symbolic_square_root','radicand':r['output_variance'],'unit':output['unit']},
            'cross_covariance':model['covariance'][0][1],'evidence_source_sha256':evidence_source['sha256'],
            'propagation':propagated}
    target_source=trusted_sources[target['quantity_binding']['source_id']]
    shared=sorted(set(replayed['source_dependencies'].values()) & {target_source['sha256']})
    return {'schema':'aod.m3.frozen-comparison.v1','prediction_sha256':m.digest(product),
        'evaluation_sha256':m.digest(target),'residual':str(residual),'unit':output['unit'],
        'uncertainty':uncertainty,'shared_source_payloads':shared,'exposure':replayed['exposure'],
        'interpretation':'calibration_anchor' if quantity['role']=='calibration' else 'retrospective_comparison',
        'independent_validation':False,'corrections_applied':False,'physical_discrepancy':'unresolved'}


def _binding(source,identity):
    return {'schema':mt.QUANTITY_SCHEMA,'source_id':source['id'],'source_sha256':source['sha256'],
            'quantity_id':identity,'quantity':deepcopy(source['payload']['quantities'][identity])}


def prediction_fixture(gain='1',variance='1/100'):
    context=t.example_context();native=t.predict(context)
    rate=native['mapped']['outputs']['average_rate_hz']['value']
    base={'kind':'reported_scalar','unit':'1','dimension':[0,0,0],'domain':['0','2'],'window':None,
          'locator':'declared setup gain','role':'model','meaning':'Synthetic uncertain readout scale',
          'value':gain,'uncertainty':{'category':'moments'},'components':[],'corrections':{}}
    rate_quantity={**deepcopy(base),'unit':'Hz','dimension':[0,-1,0],'domain':['0','100000000000'],
        'locator':'original native-context conditional rate','meaning':'Exact conditional temporal output',
        'value':rate,'uncertainty':{'category':'exact_definition'}}
    quantities=m.source('fixture:freeze-inputs','model',{'quantities':{'gain':base,'rate':rate_quantity}})
    inputs={'gain':_binding(quantities,'gain')};parameters={'rate':_binding(quantities,'rate')}
    model={'method':'moments','input_order':['gain'],
        'input_bindings':{'gain':{'source_sha256':quantities['sha256'],'quantity_id':'gain'}},
        'parameter_bindings':{'rate':{'source_sha256':quantities['sha256'],'quantity_id':'rate'}},
        'outputs':{'rate':{'kind':'reported_scalar','unit':'Hz','dimension':[0,-1,0],
            'expression':['mul',['input','gain'],['parameter','rate']],'conversion':None,'domain':None}},
        'support':None,'means':{'gain':gain},'covariance':[[variance]],'bounds':None,
        'interpretation':'Declared uncertain scale of an existing conditional readout; no physical atomic law'}
    law=m.source('fixture:freeze-moments','model',{'uncertainty_models':{'gain':deepcopy(model)}})
    request={'schema':mt.PROPAGATION_SCHEMA,'stage':'prediction','inputs':inputs,'parameters':parameters,
        'model_source_id':law['id'],'model_id':'gain','model':model}
    plan={'original_context_sha256':m.digest(t.plain(asdict(context))),'code_bindings':code_bindings(),
        'uncertainty_request':request,'readout_definitions':[{'id':'rate','quantity':'average_rate_hz'},
                                                          {'id':'returns','quantity':'compared_reclosures'}],
        'readout_parameter_links':{'rate':'rate'},'reduction_window':list(context.record.window),
        'selection':{'candidate_id':'declared-coupled-pair','rule':'single_declared_candidate','source_ids':[]},
        'stopping':{'rule':'fixed_context_window','source_ids':[]},
        'output_definition':{'name':'rate','estimator':'propagated_mean'},
        'comparison_criterion':{'kind':'signed_residual','uncertainty':'joint_if_supplied_else_partial'},
        'calibration_source_ids':[],'exposure':'retrospective'}
    owner=m.source('fixture:freeze-plan','model',{'prediction_plans':{'worked':deepcopy(plan)}})
    binding={'schema':PLAN_SCHEMA,'id':'worked','source_id':owner['id'],'source_sha256':owner['sha256'],'plan':plan}
    return binding,{s['id']:s for s in (quantities,law,owner)},context


def evaluation_fixture(product,value=None,*,cross_covariance='0',joint=False):
    output=product['output'];value=output['value'] if value is None else value
    q={'kind':output['kind'],'unit':output['unit'],'dimension':output['dimension'],
       'domain':['0','100000000000'],'window':None,'locator':'declared comparison endpoint',
       'role':'evaluation','meaning':'Synthetic target, historically exposed','value':value,
       'uncertainty':{'category':'standard_uncertainty','value':'1','printed_token':'1'},
       'components':[],'corrections':{}}
    source=m.source('fixture:freeze-target','evaluation',{'quantities':{'target':q}})
    target={'quantity_binding':_binding(source,'target'),'joint_evidence':None};trusted={source['id']:source}
    if joint:
        pq={**deepcopy(q),'role':'model','locator':'frozen prediction moments','meaning':'Executed conditional prediction',
            'value':output['value'],'uncertainty':{'category':'moments'}}
        ps=m.source('fixture:prediction-endpoint','model',{'quantities':{'prediction':pq}})
        inputs={'prediction':_binding(ps,'prediction'),'target':target['quantity_binding']}
        model={'method':'moments','input_order':['prediction','target'],
            'input_bindings':{n:{'source_sha256':b['source_sha256'],'quantity_id':b['quantity_id']} for n,b in inputs.items()},
            'parameter_bindings':{},'outputs':{'residual':{'kind':q['kind'],'unit':q['unit'],
                'dimension':q['dimension'],'expression':['sub',['input','prediction'],['input','target']],'conversion':None,'domain':None}},
            'support':None,'means':{'prediction':output['value'],'target':value},
            'covariance':[[output['variance'],cross_covariance],[cross_covariance,'1']],
            'bounds':None,'interpretation':'Supplied joint endpoint moments; zero covariance is a fixture choice'}
        ms=m.source('fixture:comparison-moments','model',{'uncertainty_models':{'residual':deepcopy(model)}})
        request={'schema':mt.PROPAGATION_SCHEMA,'stage':'comparison','inputs':inputs,'parameters':{},
            'model_source_id':ms['id'],'model_id':'residual','model':model}
        es=m.source('fixture:comparison-evidence','model',{'comparisons':{'worked':{
            'prediction_sha256':m.digest(product),'target_binding_sha256':m.digest(target['quantity_binding']),'request':deepcopy(request)}}})
        target['joint_evidence']={'source_id':es['id'],'evidence_id':'worked'}
        trusted.update({s['id']:s for s in (ps,ms,es)})
    return target,trusted


def build_report():
    routes=('finite_joint_law','nonlinear_moments','bounds','metadata','conversion',
            'shared_cancel','shared_reinforce','multi_output','published','published_moments')
    quantities={}
    for route in routes:
        request,sources=mt.quantity_input_fixture(route)
        quantities[route]={'request':request,'trusted_sources':sources,
                           'result':mt.propagate_quantities(request,sources)}
    plan,sources,context=prediction_fixture();product=predict(plan,sources,original_context=context)
    target,extra=evaluation_fixture(product,joint=True);trusted={**sources,**extra}
    first=evaluate(product,target,original_plan=plan,trusted_sources=trusted,original_context=context)
    changed,changed_sources=evaluation_fixture(product,str(Q(product['output']['value'])+1),joint=True)
    second=evaluate(product,changed,original_plan=plan,trusted_sources={**sources,**changed_sources},original_context=context)
    require(first['prediction_sha256']==second['prediction_sha256'],'target affected frozen prediction')
    changed_plan,changed_inputs,changed_context=prediction_fixture(gain='3/2')
    perturbed=predict(changed_plan,changed_inputs,original_context=changed_context)
    return {'schema':'aod.m3.experimental-input-comparison.v1','code_bindings':code_bindings(),
        'quantity_routes':quantities,'reduction_controls':t.reduction_fixtures(),
        'freeze':{'prediction':product,'target':target,'comparison':first,'target_only_change':second,
                  'input_only_change':perturbed,'target_changes_prediction':False},
        'scope':'Declared exact/moment/bound examples and printed-input replay; physical discrepancy remains unresolved'}


def report_bytes():
    return (json.dumps(build_report(),sort_keys=True,indent=2)+'\n').encode()


def main():
    parser=argparse.ArgumentParser(description=__doc__);mode=parser.add_mutually_exclusive_group()
    mode.add_argument('--write',action='store_true');mode.add_argument('--check',action='store_true')
    args=parser.parse_args();payload=report_bytes()
    if args.write:REPORT.write_bytes(payload);print('experimental input comparison report written')
    elif args.check:
        require(REPORT.is_file() and REPORT.read_bytes()==payload,'experimental input comparison report differs')
        print('experimental input comparison report verified')
    else:print(payload.decode(),end='')


if __name__=='__main__':main()

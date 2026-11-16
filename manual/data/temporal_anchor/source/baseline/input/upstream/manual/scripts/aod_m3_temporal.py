"""M3 complete native temporal adapter and explicitly conditional SI report.

Accepted native witnesses are consumed before scalar counts are exposed. SI cycle
observation gains are declared model parameters; no atomic law is inferred.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass, replace
from fractions import Fraction as Q
import argparse
import hashlib
import json
from pathlib import Path
import sys
import aod_native_closure_wave as n
import aod_mapping_error as m

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / 'manual/data/m3/temporal.json'
CS = Q(9192631770)


def require(test, message):
    if not test:
        raise ValueError(message)


def plain(value):
    return json.loads(json.dumps(value, default=str))


@dataclass(frozen=True)
class TemporalInput:
    left: n.Wave
    right: n.Wave
    contacts: tuple[n.Contact, ...]
    window: tuple[int, int]
    biases: tuple[Q, Q] = (Q(1, 4), Q(-1, 4))
    prior_lag: Q = Q(0)


def example():
    a = n.recurrent('m3:compared', n=4, spacing=8, scope='m3:comparison')
    b = n.recurrent('m3:reference', n=3, spacing=10, scope='m3:comparison')
    return TemporalInput(a, b, n.contacts(a, b), (0, 30))


def adapt(record):
    require(isinstance(record, TemporalInput), 'complete typed temporal record required, not scheduler counts')
    require(isinstance(record.left, n.Wave) and isinstance(record.right, n.Wave), 'admitted wave records required')
    require(all(isinstance(c, n.Contact) for c in record.contacts), 'bound directional coupling records required')
    forward = n.compare(record.left, record.right, record.contacts, record.window,
                        bias=record.biases, prior_lag=record.prior_lag)
    backward = n.compare(record.left, record.right, record.contacts, record.window,
                         reverse=True, bias=record.biases, prior_lag=record.prior_lag)
    endpoints = {}
    counts = {}
    for role, wave in (('compared', record.left), ('reference', record.right)):
        phase = [sum(t.indices[-1] <= k for t in wave.returns[1:]) for k in record.window]
        endpoints[role] = {'identity':wave.identity, 'lineage':wave.lineage, 'phase_endpoints':phase,
                           'prefix_sha256':[n.wave_prefix(wave, k) for k in record.window]}
        counts[role] = phase[1]-phase[0]
    require(Q(counts['compared'], counts['reference']) == forward['ratio'], 'endpoint count agreement')
    return {'record_type':'admitted_native_recurrent_coupled_pair', 'native_scope':record.left.scope,
            'window':list(record.window), 'window_domain':'integer_native_cuts_not_seconds',
            'complete_input':plain(asdict(record)), 'endpoints':endpoints, 'counts':counts,
            'forward':plain({**forward, 'rcd':asdict(forward['rcd'])}),
            'reverse':plain({**backward, 'rcd':asdict(backward['rcd'])}),
            'window_meaning':'finite_window_reclosure_comparison_not_stationary_frequency',
            'physical_observation_status':'not_identified'}


def si_contract(record, compared_gain='1', reference_gain='1', epoch='0', coordinate='stipulated:local'):
    """Public entry: derive counts from complete admitted objects on every call."""
    return _si_contract_for_validated_record(adapt(record), compared_gain, reference_gain, epoch, coordinate)


def _si_contract_for_validated_record(adapted, compared_gain='1', reference_gain='1', epoch='0', coordinate='stipulated:local'):
    """Internal construction after native admission or complete consumer replay.

    Raw dictionaries are never a public admitted-input interface. Callers must
    execute the appropriate typed native or declared-consumer validator first.
    """
    require(Q(compared_gain)>0 and Q(reference_gain)>0, 'positive observation gains required')
    require(isinstance(coordinate, str) and coordinate, 'time coordinate required')
    Q(epoch)
    native = m.source('native:temporal', 'model', {
        'compared':str(adapted['counts']['compared']), 'reference':str(adapted['counts']['reference']),
        'complete_record':adapted})
    observation = m.source('observation:declared', 'model', {
        'compared_gain':str(Q(compared_gain)), 'reference_gain':str(Q(reference_gain)),
        'origin':'stipulated_cycle_equivalents_per_return_not_physical_calibration',
        'coordinate':coordinate, 'epoch_seconds':str(Q(epoch)),
        'window':adapted['window'], 'scope':adapted['native_scope']})
    reference = m.source('si:second', 'definition', {
        'frequency':str(CS), 'url':'https://www.bipm.org/en/si-base-units/second',
        'role':'exact_defining_reference_not_realized_clock'})
    f = m.example_map('map:m3:conditional-cycle-time')
    f['sources'] = [native, observation, reference]
    f['domain'] = [m.port(name, 'native_reclosure_count', (0,0,1), 'count', ('1','1000000'))
                   for name in ('compared', 'reference')]
    f['codomain'] = [m.port('elapsed_seconds', 'elapsed_interval', (0,1,0), 's', ('0','1000000')),
                     m.port('average_rate_hz', 'finite_window_cycle_average', (0,-1,0), 'Hz', ('0','1000000000000000000'))]
    for p in f['domain'] + f['codomain']:
        p['scope'] = adapted['native_scope']
        p['lineage'] = adapted['endpoints']['compared']['identity']+'|'+adapted['endpoints']['reference']['identity']
    f['parameters'] = {
        'compared_gain':{'value':str(Q(compared_gain)), 'dimension':[0,0,-1], 'source_id':observation['id'], 'origin':'declared', 'payload_key':'compared_gain'},
        'reference_gain':{'value':str(Q(reference_gain)), 'dimension':[0,0,-1], 'source_id':observation['id'], 'origin':'declared', 'payload_key':'reference_gain'},
        'frequency':{'value':str(CS), 'dimension':[0,-1,0], 'source_id':reference['id'], 'origin':'definition', 'payload_key':'frequency'}}
    elapsed = ['div',['mul',['input','reference'],['parameter','reference_gain']],['parameter','frequency']]
    f['law'] = {'elapsed_seconds':elapsed,
                'average_rate_hz':['div',['mul',['input','compared'],['parameter','compared_gain']],elapsed]}
    f['structure'] = {'injective':'unknown', 'invariance':'nonlinear scalar injectivity not certified by generic adapter; upstream history-to-count projection ignores event ordering and retains provenance'}
    f['information_loss'] = {'task':'reconstruct committed history from two report scalars', 'reconstruction':'nonunique',
                             'equivalence':'admitted histories with identical endpoint increments under the fixed gains'}
    f['resolution'] = {'status':'specified','reason':'fixed native cut window with committed endpoint phases and all contact records; no stationarity inference'}
    f['calibration'] = {'status':'not_applicable', 'reason':'declared exact observation gains and defining second only; no instrument realization', 'fitted_parameters':[]}
    f['error'] = {p['name']:m.default_budget(p) for p in f['codomain']}
    for p in f['codomain']:
        budget = f['error'][p['name']]
        for key in ('window','calibration'):
            budget[key] = {'kind':'unknown', 'unit':p['unit'], 'included_sources':{},
                           'reason':'physical endpoint phase, missed cycles, slips, drift, realization and temporal covariance not supplied'}
        budget['propagation']['reason'] = 'exact rational evaluation of deterministic declared operands; no physical probability law'
    f['status'] = {'arithmetic':'exact within declared domain', 'physical_applicability':'unknown'}
    return m.seal(f), {s['id']:s for s in f['sources']}


def predict(record, compared_gain='1', reference_gain='1', epoch='0', coordinate='stipulated:local'):
    adapted = adapt(record)
    f, trusted = si_contract(record, compared_gain, reference_gain, epoch, coordinate)
    native = trusted['native:temporal']
    values = {p['name']:m.value(p, adapted['counts'][p['name']], {native['id']:native['sha256']},
        origin={'kind':'source','source_id':native['id'],'payload_key':p['name']}) for p in f['domain']}
    mapped = m.run_map(f, values, trusted)
    dt = Q(mapped['outputs']['elapsed_seconds']['value'])
    rate = Q(mapped['outputs']['average_rate_hz']['value'])
    return {'classification':'conditional_model_prediction_not_atomic_prediction',
            'complete_temporal_record':adapted, 'mapping_contract':f, 'mapped':mapped,
            'coordinate':coordinate, 'epoch_seconds':str(Q(epoch)),
            'end_coordinate_seconds':str(Q(epoch)+dt),
            'derived_reciprocal_period_seconds':str(1/rate),
            'period_role':'derived_transform_not_elapsed_interval_or_second_validation',
            'complete_physical_standard_uncertainty':None,
            'atomic_prediction':None, 'exposure':'known_H_previously_exposed; no_blind_claim'}


def evaluate(prediction, target, *, original_record, compared_gain, reference_gain, epoch, coordinate):
    """Compare only an artifact replayed from caller-supplied original context."""
    require(set(target)=={'id','frequency_hz','exposure','prediction_cross_covariance'}, 'evaluation target fields')
    require(target['exposure']=='retrospective', 'known hydrogen cannot become blind by freezing a later artifact')
    replayed = predict(original_record, compared_gain, reference_gain, epoch, coordinate)
    require(m.canonical(prediction)==m.canonical(replayed), 'prediction differs from replayed original context')
    rate = Q(replayed['mapped']['outputs']['average_rate_hz']['value'])
    return {'prediction_sha256':m.digest(prediction), 'evaluation_sha256':m.digest(target),
            'diagnostic_residual_hz':str(rate-Q(target['frequency_hz'])),
            'combined_uncertainty':None, 'status':'diagnostic_only_missing_atomic_law_and_cross_covariance'}


def consumer_integration(root):
    """Replay actual frozen v2 dynamics and test a real feedback intervention."""
    root = Path(root).resolve()
    sys.path.insert(0,str(root/'manual2/scripts'))
    import matter1_stateful as s
    import matter1_temporal as t
    import matter1_atomic as a
    fixture = t.read_json(root/s.GEOMETRY)
    s.verify(root)
    bundle=s.prepare(root)
    left,right=bundle['baseline_trace'],bundle['early_loss_trace']
    # Hostile executable mutation: keep the intervention and calibration fixed,
    # but prevent its queued loss response from reaching the next state.
    # The mutation is never persisted or admitted as a valid model execution.
    from unittest.mock import patch
    original_response=t.response
    def disconnected_response(*args, **kwargs):
        result=original_response(*args, **kwargs)
        if result['outer_retention']=='lost_by_declared_capacity_rule':
            result['outer_retention']='retained_feedback_disconnected_mutation'
        return result
    with patch.object(t,'response',disconnected_response):
        disabled=s.simulate(bundle['early_loss_scenario'],fixture,root)
    rejected=False
    try:s.validate_simulation(disabled,bundle['early_loss_scenario'],fixture,root)
    except ValueError:rejected=True
    require(rejected,'disconnected feedback trace must fail original replay validation')
    prefix=lambda tr:[row for row in tr['cut_records'] if row['cut']<40]
    require(prefix(left)==prefix(right)==prefix(disabled),'committed prefix altered')
    results={}
    # Calibration is fixed before any case: one stipulated cycle per return.
    for name,tr in [('baseline',left),('intervention',right),('feedback_disabled',disabled)]:
        if name!='feedback_disabled':
            s.validate_simulation(tr, bundle['baseline_scenario'] if name=='baseline' else bundle['early_loss_scenario'],fixture,root)
        counts=tr['summary']['observed_reclosure_counts']
        dt=Q(counts['outer_minus'])/CS
        contract_result=None
        if name!='feedback_disabled':
            adapted={'record_type':'declared_finite_recurrent_coupled_pair',
                     'native_scope':'matter-i:v2:finite-comparison', 'window':tr['summary']['window'],
                     'complete_input':tr, 'source_scenario':bundle['baseline_scenario'] if name=='baseline' else bundle['early_loss_scenario'],
                     'native_admission_status':'pending_not_promoted',
                     'endpoints':{'compared':{'identity':tr['outer_waves'][0]['identity']},
                                  'reference':{'identity':tr['outer_waves'][1]['identity']}},
                     'counts':{'compared':counts['outer_plus'],'reference':counts['outer_minus']}}
            f,trusted=_si_contract_for_validated_record(adapted)
            native=trusted['native:temporal']
            values={p['name']:m.value(p,adapted['counts'][p['name']],{native['id']:native['sha256']},
                    origin={'kind':'source','source_id':native['id'],'payload_key':p['name']}) for p in f['domain']}
            contract_result={'contract':f,'result':m.run_map(f,values,trusted)}
        results[name]={'trace_sha256':t.sha(tr),'counts':counts,'elapsed_seconds':str(dt),
                       'finite_window_average_hz':str(Q(counts['outer_plus'])/dt),
                       'contacts_sha256':t.sha(tr['contacts']), 'directional_comparisons_sha256':t.sha(tr['comparisons']),
                       'record_class':tr['statuses'], 'native_admission':'pending',
                       'validation':'rejected_hostile_feedback_mutation' if name=='feedback_disabled' else 'validated_declared_model',
                       'generic_mapping_execution':contract_result}
    require(results['intervention']['finite_window_average_hz']!=results['baseline']['finite_window_average_hz'],'intervention failed to affect observable')
    require(results['feedback_disabled']['finite_window_average_hz']==results['baseline']['finite_window_average_hz'],'broken feedback not detected')
    prediction=a.predict(root)
    return {'classification':'actual_matter_i_v2_declared_finite_dynamics',
            'common_prefix_through_cut':39,'fixed_cycle_equivalents_per_return':'1', 'cases':results,
            'feedback_disabled_original_validator_rejected':rejected,
            'atomic_countermodels':prediction['countermodels'], 'atomic_point_prediction':prediction['atomic_prediction'],
            'atomic_objective':'incomplete', 'claim':'conditional finite-model causal observable; not native atomic admission'}


def report():
    r=example(); p=predict(r)
    context={'original_record':r,'compared_gain':'1','reference_gain':'1','epoch':'0','coordinate':'stipulated:local'}
    target={'id':'known-H','frequency_hz':'1420405751.768','exposure':'retrospective','prediction_cross_covariance':None}
    changed={**target,'frequency_hz':'1420405752.768'}
    c1,c2=evaluate(p,target,**context),evaluate(p,changed,**context)
    require(c1['prediction_sha256']==c2['prediction_sha256'] and c1['diagnostic_residual_hz']!=c2['diagnostic_residual_hz'],'target separation')
    witnesses=[]
    for lam in (Q(0),Q(1)):
        w=predict(r,compared_gain=str(1+lam))
        witnesses.append({'lambda':str(lam),'Cs_gain':'1','H_gain':str(1+lam),
                          'conditional_rate_hz':w['mapped']['outputs']['average_rate_hz']['value']})
    return {'schema_version':2,'prediction':p,'comparison':c1,'evaluation_only_mutation':c2,
            'gain_countermodels':witnesses,
            'gain_family':'g_lambda(Z)=1+lambda*(55-Z)/54; lambda>-1; Cs fixed and H free',
            'countermodel_scope':'hypothetical species assignment only; no member selected or fitted',
            'atomic_objective':'incomplete: state construction and target-independent relative gain law missing',
            'source_code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    mode=p.add_mutually_exclusive_group(); mode.add_argument('--write',action='store_true');mode.add_argument('--check',action='store_true')
    p.add_argument('--output',type=Path,default=REPORT);p.add_argument('--consumer-root',type=Path)
    args=p.parse_args()
    result=consumer_integration(args.consumer_root) if args.consumer_root else report()
    data=json.dumps(result,indent=2,sort_keys=True)+'\n'
    if args.write:args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(data)
    elif args.check:require(args.output.read_text()==data,'stored temporal evidence differs')
    else:print(data,end='')
    if args.write or args.check:print(json.dumps({'status':'reconstructed','output':str(args.output),'atomic_prediction':'incomplete'}))

if __name__=='__main__':main()

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
TEMPORAL_CONTRACT = ROOT / 'contracts/scientific/TEMPORAL_OBSERVATION.json'
TEMPORAL_CONTRACT_SHA256 = '6a984523fe2d01ba8d1045965d7b3014b07e4d0494e8110b10c7507736582f90'


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


@dataclass(frozen=True)
class ObservationContext:
    record: TemporalInput
    population: tuple[n.Wave, ...]
    couplings: tuple[n.Contact, ...]
    preparation: dict
    pending: tuple[dict, ...]
    source_dependencies: tuple[dict, ...]
    observation: dict
    previous_comparison: TemporalInput | None = None


def _exact_json(value):
    if value is None or type(value) in (str, int, bool):
        return
    if isinstance(value, (tuple, list)):
        for item in value: _exact_json(item)
        return
    require(isinstance(value, dict) and all(type(k) is str for k in value), 'exact JSON context required')
    for item in value.values(): _exact_json(item)


def _population_identity(population):
    return sorted([{'identity':w.identity, 'scope':w.scope, 'scale':w.scale,
                    'lineage':w.lineage, 'motif':w.motif} for w in population], key=lambda x:x['identity'])


def domain_for(population, couplings, preparation, cut_bounds):
    """Explicit validation envelope; prefix lengths are not a population identity."""
    require(len(cut_bounds)==2 and all(type(k) is int for k in cut_bounds)
            and cut_bounds[0]<cut_bounds[1], 'domain cut bounds')
    _exact_json(preparation)
    return {'population':_population_identity(population),
            'directed_graph':[list(edge) for edge in sorted({(e.left,e.right) for e in couplings})],
            'preparation_sha256':m.digest(preparation), 'cut_bounds':list(cut_bounds)}


def observation_law(domains, *, law_id='observation:m3:fixed-gain:v1', compared_gain='1',
                    reference_gain='1', epoch='0', coordinate='stipulated:local',
                    calibration_source_id=None, tolerance_source_id=None):
    result={'schema':'aod_temporal_observation_v1', 'id':law_id,
            'compared_gain':str(m.rational(compared_gain)), 'reference_gain':str(m.rational(reference_gain)),
            'epoch_seconds':str(m.rational(epoch)), 'coordinate':coordinate,
            'domains':plain(domains), 'calibration_source_id':calibration_source_id,
            'tolerance_source_id':tolerance_source_id,
            'physical_applicability':'unknown', 'frozen_before_validation':True}
    result['law_sha256']=m.digest(result)
    return result


def example_context(record=None, **settings):
    record=example() if record is None else record
    require(isinstance(record,TemporalInput),'complete typed temporal record required')
    population=(record.left,record.right)
    preparation={'id':'m3:declared-recurrence-preparation',
                 'parameters':{'compared_spacing':8,'reference_spacing':10}}
    domain=domain_for(population,record.contacts,preparation,record.window)
    return ObservationContext(record,population,record.contacts,preparation,(),(),
                              observation_law([domain],**settings))


def _contract_binding():
    raw=TEMPORAL_CONTRACT.read_bytes()
    require(hashlib.sha256(raw).hexdigest()==TEMPORAL_CONTRACT_SHA256,
            'temporal observation contract differs from independently bound contract')
    return TEMPORAL_CONTRACT_SHA256


def _predictive_fingerprint(context):
    # Error/evidence payloads stay outside predictive identity; actual gains,
    # native inputs, applicability and executable identity remain inside it.
    inputs=plain(asdict(context));inputs.pop('source_dependencies')
    observation=inputs['observation']
    for key in ('calibration_source_id','tolerance_source_id','law_sha256',
                'physical_applicability','frozen_before_validation'):
        observation.pop(key)
    return m.digest({'context':inputs,'context_contract_sha256':_contract_binding(),
        'code':{Path(module.__file__).name:hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()
                for module in (sys.modules[__name__],n,m)}})


def validate_observation_context(context):
    """Validate actual native witnesses and the frozen observation applicability.

    Preparation and pending payloads are declared model inputs, not newly admitted
    nuclear dynamics. Their producer must replay them from original engine inputs.
    """
    require(isinstance(context,ObservationContext), 'complete typed observation context required')
    _contract_binding()
    r=context.record
    require(isinstance(r,TemporalInput), 'complete typed temporal record required')
    adapted=adapt(r)
    require(isinstance(context.population,tuple) and len(context.population)>=2, 'actual population required')
    require(all(isinstance(w,n.Wave) for w in context.population), 'population contains non-wave record')
    waves={w.identity:w for w in context.population}
    require(len(waves)==len(context.population),'duplicate wave identity in population')
    require(waves.get(r.left.identity)==r.left and waves.get(r.right.identity)==r.right,
            'comparison waves differ from population prefixes')
    for w in context.population:
        n.validate_wave(w)
        require(all(t.indices[-1]<=r.window[1] for t in w.returns),'future return in committed population prefix')
    require(isinstance(context.couplings,tuple) and all(isinstance(e,n.Contact) for e in context.couplings),
            'actual directed coupling records required')
    keys=[(e.left,e.right,e.identity) for e in context.couplings]
    require(len(set(keys))==len(keys),'duplicate directed contact')
    for edge in {(e.left,e.right) for e in context.couplings}:
        history=[e for e in context.couplings if (e.left,e.right)==edge]
        require(len({e.committed for e in history})==len(history)
                and all(a.committed<b.committed for a,b in zip(history,history[1:])),
                'directed contact history must use distinct ordered commitments')
        require(len({e.support_trace.return_id for e in history})==len(history),
                'relabelled cross-return in population coupling history')
    for e in context.couplings:
        require(e.left in waves and e.right in waves and e.left!=e.right,'coupling outside population')
        a,b=waves[e.left],waves[e.right]
        require(type(e.committed) is int and e.committed<=r.window[1],'future or noninteger contact')
        require((a.scope,a.scale)==(b.scope,b.scale) and e.scope==a.scope,'coupling scope mismatch')
        require((e.left_prefix,e.right_prefix)==(n.wave_prefix(a,e.committed),n.wave_prefix(b,e.committed)),
                'population coupling prefix mismatch')
        require(all(sum(t.indices[-1]<=e.committed for t in w.returns)>=2 for w in (a,b)),
                'population contact precedes recurrence')
        require(len(e.reflection)==2 and all(type(x) is int and x>=0 for x in e.reflection),
                'invalid directional reflection counts')
        n.admitted(e.support_trace,e.support_certificate,{e.support_certificate.certificate_digest:e.support_certificate})
        require(e.support_trace.lineage==f'{a.identity}|{b.identity}' and e.support_trace.scope==e.scope
                and e.support_trace.scale==a.scale and e.support_trace.indices[-1]<=e.committed,
                'unbound population cross-return')
    require(all(e in context.couplings for e in r.contacts),'comparison contacts absent from actual coupling history')
    _exact_json(context.preparation)
    require(isinstance(context.preparation,dict) and context.preparation.get('id')
            and isinstance(context.preparation.get('parameters'),dict),'explicit preparation required')
    require(isinstance(context.pending,tuple),'typed pending inventory required')
    for item in context.pending:
        require(isinstance(item,dict) and set(item)=={'wave_identity','kind','committed_cut','prefix_sha256','payload'},
                'pending record fields')
        require(item['wave_identity'] in waves and item['kind'] in ('in_flight_contact','incomplete_return'),
                'pending wave/kind')
        require(type(item['committed_cut']) is int and item['committed_cut']<=r.window[1],'pending commitment cut')
        require(item['prefix_sha256']==n.wave_prefix(waves[item['wave_identity']],r.window[1]),'pending prefix mismatch')
        require(isinstance(item['payload'],dict) and bool(item['payload']),'pending event payload required')
        _exact_json(item['payload'])
    require(isinstance(context.source_dependencies,tuple),'source dependencies must be explicit')
    sources=list(context.source_dependencies);trusted={s['id']:s for s in sources}
    if sources:m.validate_sources(sources,trusted)
    require(all(s['role']!='evaluation' for s in sources),'evaluation source in prediction context')
    for s in sources:_exact_json(s['payload'])
    if context.previous_comparison is None:
        require(m.rational(r.prior_lag)==0,'nonzero drift predecessor requires committed comparison')
        previous=None
    else:
        p=context.previous_comparison
        require(isinstance(p,TemporalInput) and p.window[1]==r.window[0], 'previous comparison must end at window start')
        require(p.left==r.left and p.right==r.right,'previous comparison changed population histories')
        require(all(e in context.couplings for e in p.contacts),'previous contacts absent from actual history')
        previous=adapt(p)
        require(m.rational(r.prior_lag)==m.rational(previous['forward']['lag']),'drift predecessor lag mismatch')
    o=context.observation
    fields={'schema','id','compared_gain','reference_gain','epoch_seconds','coordinate','domains',
            'calibration_source_id','tolerance_source_id','physical_applicability','frozen_before_validation','law_sha256'}
    require(isinstance(o,dict) and set(o)==fields,'observation law fields')
    require(o['schema']=='aod_temporal_observation_v1' and o['physical_applicability']=='unknown'
            and o['frozen_before_validation'] is True,'observation schema/status')
    require(o['law_sha256']==m.digest({k:v for k,v in o.items() if k!='law_sha256'}),'observation law fingerprint mismatch')
    require(all(isinstance(o[k],str) and o[k] for k in ('id','coordinate')),'observation identity and coordinate')
    for key in ('compared_gain','reference_gain','epoch_seconds'):
        require(type(o[key]) is str and str(m.rational(o[key]))==o[key], 'canonical exact observation parameter required')
    require(m.rational(o['compared_gain'])>0 and m.rational(o['reference_gain'])>0,'positive observation gains required')
    require(isinstance(o['domains'],list) and bool(o['domains']),'frozen observation domain required')
    current=domain_for(context.population,context.couplings,context.preparation,r.window)
    matched=False
    for d in o['domains']:
        require(isinstance(d,dict) and set(d)==set(current),'observation domain fields')
        bounds=d['cut_bounds']
        require(isinstance(bounds,list) and len(bounds)==2 and all(type(k) is int for k in bounds)
                and bounds[0]<bounds[1],'observation domain cut bounds')
        matched |= all(d[k]==current[k] for k in ('population','directed_graph','preparation_sha256')) and bounds[0]<=r.window[0]<r.window[1]<=bounds[1]
    require(matched,'observation applicability rejected: context outside frozen domain')
    calibration=o['calibration_source_id']
    if calibration is not None:
        require(calibration in trusted and trusted[calibration]['role']=='calibration','calibration source binding')
        payload=trusted[calibration]['payload']
        require(set(payload)=={'reference_reclosures','corrected_cycles','window','context_sha256'},'calibration payload fields')
        require(m.rational(payload['reference_reclosures'])>0 and m.rational(payload['corrected_cycles'])>0,'calibration positive operands')
        require(m.rational(o['reference_gain'])==m.rational(payload['corrected_cycles'])/m.rational(payload['reference_reclosures']),
                'frozen reference gain differs from calibration operands')
        require(isinstance(payload['context_sha256'],str) and len(payload['context_sha256'])==64,'calibration context identity')
        require(isinstance(payload['window'],list) and len(payload['window'])==2
                and all(type(k) is int for k in payload['window']) and payload['window'][0]<payload['window'][1], 'calibration window')
    tolerance=o['tolerance_source_id']
    if tolerance is not None:
        require(tolerance in trusted and trusted[tolerance]['role'] in ('model','calibration'),'tolerance source binding')
        payload=trusted[tolerance]['payload']
        require(set(payload)=={'kind','cycles','reason'} and payload['kind']=='algebraic_exact'
                and m.rational(payload['cycles'])==0 and isinstance(payload['reason'],str) and payload['reason'],
                'only justified algebraic-zero tolerance is implemented; physical tolerance remains unknown')
    prefixes=[]
    for w in context.population:
        prefixes.append({'identity':w.identity,'scope':w.scope,'lineage':w.lineage,
            'committed_prefix_sha256':n.wave_prefix(w,r.window[1]),'returns':len(w.returns)})
    adapted['observation_context']={'schema':'aod_temporal_observation_v1','contract_sha256':_contract_binding(),
        'input_sha256':m.digest(plain(asdict(context))),
        'predictive_model_sha256':_predictive_fingerprint(context),
        'evidence_sha256':m.digest({'sources':plain(context.source_dependencies),
            'calibration_source_id':o['calibration_source_id'],'tolerance_source_id':o['tolerance_source_id']}),
        'population':prefixes,
        'preparation':plain(context.preparation),'directed_graph':current['directed_graph'],
        'coupling_history_sha256':m.digest(plain([asdict(e) for e in context.couplings])),
        'pending':plain(context.pending),'source_dependencies':plain(sources),'observation_law':plain(o),
        'previous_comparison':previous,
        'counting_convention':'(lo,hi]; initial admitted closure anchors lineage; only later completed returns count',
        'duration_participation':{'status':'unknown','value':None,
                                  'reason':'no observation-window map into the directional native duration domain supplied'},
        'applicability':'declared_domain_only_physical_unknown'}
    return adapted


def reference_independence(contexts):
    """Reject duplicate evidence; absence of a collision does not prove independence."""
    require(len(contexts)>=2,'multiple reference contexts required')
    for c in contexts:validate_observation_context(c)
    references=[m.digest(plain(asdict(c.record.right))) for c in contexts]
    dependency_sets=[{s['sha256'] for s in c.source_dependencies if s['role']=='calibration'} for c in contexts]
    shared=set().union(*(dependency_sets[i]&dependency_sets[j] for i in range(len(contexts)) for j in range(i)))
    duplicate=len(set(references))!=len(references)
    return {'status':'dependent' if duplicate or shared else 'independence_not_established',
            'duplicate_reference':duplicate,'shared_calibration_payloads':sorted(shared),
            'independent_evidence_count':None}


def project_counts(context, window):
    """A short count projection supplies no new cross-return admission."""
    validate_observation_context(context)
    require(isinstance(window,(tuple,list)) and len(window)==2 and all(type(k) is int for k in window)
            and context.record.window[0]<=window[0]<window[1]<=context.record.window[1],'projection window')
    return {'window':list(window),'counts':{role:sum(window[0]<t.indices[-1]<=window[1] for t in w.returns[1:])
            for role,w in [('compared',context.record.left),('reference',context.record.right)]},
            'directional_rcd_status':'not_admitted_by_count_projection','source_context_sha256':m.digest(plain(asdict(context)))}


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


def si_contract(context):
    """Public entry: admit complete context and frozen applicability on every call."""
    adapted=validate_observation_context(context)
    return _si_contract_for_validated_record(adapted, context.observation, context.source_dependencies)


def _si_contract_for_validated_record(adapted, observation_law, source_dependencies=()):
    """Internal construction after native admission or complete consumer replay.

    Raw dictionaries are never a public admitted-input interface. Callers must
    execute the appropriate typed native or declared-consumer validator first.
    """
    observation_law=plain(observation_law)
    source_dependencies=plain(source_dependencies)
    compared_gain=observation_law['compared_gain']; reference_gain=observation_law['reference_gain']
    epoch=observation_law['epoch_seconds']; coordinate=observation_law['coordinate']
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
        'window':adapted['window'], 'scope':adapted['native_scope'],
        'frozen_law':observation_law, 'context_contract_sha256':_contract_binding()})
    reference = m.source('si:second', 'definition', {
        'frequency':str(CS), 'url':'https://www.bipm.org/en/si-base-units/second',
        'role':'exact_defining_reference_not_realized_clock'})
    f = m.example_map('map:m3:conditional-cycle-time')
    f['sources'] = [native, observation, reference] + list(source_dependencies)
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
    if observation_law['calibration_source_id'] is not None:
        calibration=observation_law['calibration_source_id']
        source_by_id={s['id']:s for s in f['sources']}
        f['parameters']['reference_gain'].update({'source_id':calibration,'origin':'fitted','payload_key':'reference_gain'})
        # Keep the original independent calibration source intact; the derived gain
        # is a separate calibration record whose payload retains that source.
        fitted=m.source('calibration:frozen-gain','calibration',{'reference_gain':reference_gain,'original':source_by_id[calibration]})
        f['sources'].append(fitted)
        f['parameters']['reference_gain']['source_id']=fitted['id']
        f['calibration']={'status':'specified','reason':'synthetic frozen calibration; physical realization unknown','fitted_parameters':['reference_gain']}
        for budget in f['error'].values():
            budget['calibration']['included_sources']={fitted['id']:fitted['sha256']}
    f['status'] = {'arithmetic':'exact within declared domain', 'physical_applicability':'unknown'}
    return m.seal(f), {s['id']:s for s in f['sources']}


def predict(context):
    adapted=validate_observation_context(context)
    o=context.observation
    f,trusted=_si_contract_for_validated_record(adapted,o,context.source_dependencies)
    native=trusted['native:temporal']
    values={p['name']:m.value(p,adapted['counts'][p['name']],{native['id']:native['sha256']},
        origin={'kind':'source','source_id':native['id'],'payload_key':p['name']}) for p in f['domain']}
    mapped=m.run_map(f,values,trusted)
    dt=Q(mapped['outputs']['elapsed_seconds']['value']);rate=Q(mapped['outputs']['average_rate_hz']['value'])
    return {'schema_version':3,'classification':'conditional_model_prediction_not_atomic_prediction',
            'complete_temporal_record':adapted,'mapping_contract':f,'mapped':mapped,
            'coordinate':o['coordinate'],'epoch_seconds':o['epoch_seconds'],
            'end_coordinate_seconds':str(Q(o['epoch_seconds'])+dt),
            'reference_corrected_cycle_prediction':str(Q(adapted['counts']['reference'])*Q(o['reference_gain'])),
            'derived_reciprocal_period_seconds':str(1/rate),
            'period_role':'derived_transform_not_elapsed_interval_or_second_validation',
            'complete_physical_standard_uncertainty':None,'atomic_prediction':None,
            'exposure':'known_H_previously_exposed; no_blind_claim'}


def replay_prediction(prediction, original_context):
    replayed=predict(original_context)
    require(m.canonical(prediction)==m.canonical(replayed),'prediction differs from replayed original context')
    return replayed


def evaluate(prediction,target,*,original_context):
    require(set(target)=={'id','frequency_hz','exposure','prediction_cross_covariance'},'evaluation target fields')
    require(target['exposure']=='retrospective','known hydrogen cannot become blind by freezing a later artifact')
    replayed=replay_prediction(prediction,original_context)
    rate=Q(replayed['mapped']['outputs']['average_rate_hz']['value'])
    return {'prediction_sha256':m.digest(prediction),'evaluation_sha256':m.digest(target),
            'diagnostic_residual_hz':str(rate-m.rational(target['frequency_hz'])),
            'combined_uncertainty':None,'status':'diagnostic_only_missing_atomic_law_and_cross_covariance'}


def compare_cycles(prediction,observed_source,*,original_context):
    replayed=replay_prediction(prediction,original_context)
    m.validate_sources([observed_source],{observed_source['id']:observed_source})
    require(observed_source['role']=='evaluation','separate evaluation source required')
    payload=observed_source['payload']
    require(set(payload)=={'corrected_cycles','window'},'observed corrected-cycle fields')
    require(isinstance(payload['window'],list) and len(payload['window'])==2
            and all(type(k) is int for k in payload['window']), 'observed window requires exact integer endpoints')
    require(payload['window']==list(original_context.record.window),'observed window differs')
    o=original_context.observation;sources={s['id']:s for s in original_context.source_dependencies}
    if o['calibration_source_id'] is not None:
        calibration=sources[o['calibration_source_id']]['payload']
        require(calibration['window'][1]<=payload['window'][0],'calibration/evaluation windows overlap')
    delta=Q(replayed['reference_corrected_cycle_prediction'])-m.rational(payload['corrected_cycles'])
    tolerance=None if o['tolerance_source_id'] is None else m.rational(sources[o['tolerance_source_id']]['payload']['cycles'])
    return {'prediction_sha256':m.digest(prediction),'evaluation_sha256':observed_source['sha256'],
            'residual_cycles':str(delta),'tolerance_cycles':None if tolerance is None else str(tolerance),
            'compatible':None if tolerance is None else abs(delta)<=tolerance,
            'status':'diagnostic_tolerance_unknown' if tolerance is None else 'synthetic_algebraic_transfer_check',
            'physical_applicability':'unknown','combined_standard_uncertainty':None}


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
            declared=observation_law([],law_id='observation:matter-i:declared-v2')
            adapted['original_context_sha256']=t.sha({'scenario':adapted['source_scenario'],'fixture':fixture,'complete_simulation':tr})
            f,trusted=_si_contract_for_validated_record(adapted,declared)
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
    r=example_context(); p=predict(r)
    context={'original_context':r}
    target={'id':'known-H','frequency_hz':'1420405751.768','exposure':'retrospective','prediction_cross_covariance':None}
    changed={**target,'frequency_hz':'1420405752.768'}
    c1,c2=evaluate(p,target,**context),evaluate(p,changed,**context)
    require(c1['prediction_sha256']==c2['prediction_sha256'] and c1['diagnostic_residual_hz']!=c2['diagnostic_residual_hz'],'target separation')
    witnesses=[]
    for lam in (Q(0),Q(1)):
        w=predict(example_context(compared_gain=str(1+lam)))
        witnesses.append({'lambda':str(lam),'Cs_gain':'1','H_gain':str(1+lam),
                          'conditional_rate_hz':w['mapped']['outputs']['average_rate_hz']['value']})
    return {'schema_version':3,'context_contract_sha256':_contract_binding(),'prediction':p,'comparison':c1,'evaluation_only_mutation':c2,
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

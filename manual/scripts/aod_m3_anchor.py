"""Frozen anchor evidence and explicitly declared population/exposure controls."""
from __future__ import annotations

import argparse
from bisect import bisect_left, bisect_right
from contextlib import contextmanager
from dataclasses import asdict, replace
from fractions import Fraction as Q
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

import aod_native_closure_wave as n
import aod_mapping_error as m
import aod_m3_temporal as t

ROOT = Path(__file__).resolve().parents[2]
DATA = Path('manual/data/m3/temporal_anchor')
ARCHIVE_SHA256 = '2b26210cf0f7f2fa5e510560d5156aebddaa6a7039e1eab4e9a8209500bead25'
NATIVE_SHA256 = '3ba98c7097bc104aeb6218265b8531f94f2ca5a35239d0df097aba096675dfdf'
CASES = ('baseline', 'second_support_pair', 'compared_population', 'reference_exposure')
HORIZON = 3316192
INTERVENTION = 300000
SPLIT = 1808096


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), default=str).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def plain(value):
    return json.loads(canonical(value))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_archive(root=ROOT):
    path = Path(root)/DATA/'original_anchor_r02.zip'
    require(sha(path) == ARCHIVE_SHA256, 'original anchor archive changed')
    with zipfile.ZipFile(path) as archive:
        require(archive.testzip() is None, 'original archive CRC failure')
        manifest = dict((name, checksum) for checksum, name in
                        (line.split('  ', 1) for line in archive.read('MANIFEST_SHA256.txt').decode().splitlines()))
        require(set(archive.namelist()) == set(manifest)|{'MANIFEST_SHA256.txt'}, 'original archive inventory changed')
        for name, checksum in manifest.items():
            require(hashlib.sha256(archive.read(name)).hexdigest() == checksum, 'original member changed: '+name)
        binding = json.loads(archive.read('INPUT_BINDING.json'))
        for name, checksum in binding['files'].items():
            require(hashlib.sha256(archive.read(name)).hexdigest() == checksum, 'original input binding changed: '+name)
    require(sha(Path(n.__file__)) == NATIVE_SHA256, 'native admission source differs from bound engine')
    return {'archive_sha256':ARCHIVE_SHA256, 'manifest_members':len(manifest),
            'input_bindings':len(binding['files']), 'original_source_commit':binding['source_commit']}


@contextmanager
def source_modules(root=ROOT):
    """Load authenticated engine/decoder; keep legacy files outside active source."""
    verify_archive(root)
    with tempfile.TemporaryDirectory(prefix='aod-anchor-source-') as directory:
        folder = Path(directory)
        with zipfile.ZipFile(Path(root)/DATA/'original_anchor_r02.zip') as archive:
            for name in archive.namelist():
                require(not Path(name).is_absolute() and '..' not in Path(name).parts, 'unsafe archive member')
            archive.extractall(folder)
        saved_path = list(sys.path)
        saved = {key:sys.modules.get(key) for key in ('population', 'pair_trial', 'common_reference')}
        modules = {}
        try:
            for key, filename in (('population','population.py'), ('pair_trial','pair_trial.py'),
                                  ('common_reference','common_reference.py')):
                spec = importlib.util.spec_from_file_location(key, folder/'baseline/input'/filename)
                module = importlib.util.module_from_spec(spec)
                sys.modules[key] = module
                spec.loader.exec_module(module)
                modules[key] = module
            modules['population'].check_sources()
            yield modules, folder
        finally:
            sys.path[:] = saved_path
            for key, previous in saved.items():
                if previous is None:
                    sys.modules.pop(key, None)
                else:
                    sys.modules[key] = previous


def original_replay(root=ROOT):
    """Execute the unmodified historical audit and compare every original output."""
    with source_modules(root) as (_, folder):
        out = folder/'replayed'
        optimization = ['-O'] if sys.flags.optimize else []
        result = subprocess.run([sys.executable, '-B', *optimization, str(folder/'audit_anchor.py'), '--output', str(out)],
                                capture_output=True, text=True)
        require(result.returncode == 0, 'historical anchor replay failed: '+result.stderr)
        files = sorted(p.name for p in (folder/'results').iterdir())
        require(sorted(p.name for p in out.iterdir()) == files, 'historical replay inventory differs')
        for name in files:
            require((out/name).read_bytes() == (folder/'results'/name).read_bytes(), 'historical replay differs: '+name)
        rows = json.loads((out/'admitted_validation.json').read_text())
        report = json.loads((out/'report.json').read_text())
        return {'classification':'unchanged_retrospective_original_experiment',
                'checks':report['check_count'], 'output_sha256':{name:sha(out/name) for name in files},
                'direct_pair_residuals':{key:rows['direct_pair']['transfers'][key]['comparison']['relative_residual']
                                         for key in ('A','B')},
                'independent_reference_evidence':False, 'physical_anchor':'not_established'}


def default_inputs(root=ROOT):
    return {'schema':'aod.m3.anchor-input.v1', 'model_id':'m3:anchor-context-controls:v1',
            'archive_sha256':ARCHIVE_SHA256, 'code_sha256':sha(Path(__file__)),
            'native_sha256':NATIVE_SHA256, 'temporal_sha256':sha(Path(t.__file__)),
            'mapping_sha256':sha(Path(m.__file__)), 'horizon':HORIZON, 'intervention':INTERVENTION,
            'calibration_window':[INTERVENTION,SPLIT], 'validation_window':[SPLIT,HORIZON],
            'preparation':{'initial_returns':'two authenticated support returns per prepared node',
                           'base_first_action':2000, 'initial_contact_starts':[700,1200],
                           'dormant_local':'L0 is prepared in every case; only the intervention activates its recurrence',
                           'counting':'later reclosures in (u,v]; initial closure excluded',
                           'source_law':'unchanged original population.py; explicit population/topology initialization'},
            'cases':{name:{'support_pair':[[3,2],[3,3]] if name=='second_support_pair' else [[3,3],[1,2]],
                           'backgrounds':[['F0',3,4],['F1',3,4]], 'prepared_local':['L0',3,4],
                           'local_target':{'compared_population':'A','reference_exposure':'F0'}.get(name),
                           'direct_pair_at_intervention':True}
                     for name in CASES},
            'physical_cycle_observation':None, 'physical_tolerance':None,
            'isotope_capacity_or_ttl_parameters':None}


def validate_inputs(inputs, root=ROOT):
    require(canonical(inputs) == canonical(default_inputs(root)), 'anchor original inputs differ from frozen construction')


def run_engine(spec, modules, end=HORIZON):
    p, pair = modules['population'], modules['pair_trial']

    class ContextEngine(pair.PairEngine):
        def __init__(self):
            self.scenario, self.intervention = 'direct_pair', INTERVENTION
            self.nodes = {name:p.Node(name, exponent, count) for name,exponent,count in
                          [('A',*spec['support_pair'][0]), ('B',*spec['support_pair'][1]),
                           *spec['backgrounds'], spec['prepared_local']]}
            self.base = ('A','B','F0','F1')
            self.channels, self.active, self.heap = {}, set(), []
            self.serial = self.record_count = self.trace_count = 0
            self.pending, self.returned_packets = {}, []
            self.steps = {name:[] for name in self.nodes}
            self.pressure_changes, self.last_pressure = [], {}
            self.common_prefix_hash, self.observable_hash = hashlib.sha256(), hashlib.sha256()
            self.first_operational_local_contact = None
            self.feedback_disabled = False
            self.trace_path = self.writer = self.raw_writer = None
            self.trace = False
            self.events = []
            for receiver in self.base:
                for sender in self.base:
                    if receiver != sender and (receiver,sender) not in pair.PAIR:
                        self.activate(receiver,sender)
                        for start in (700,1200):
                            self.seed_contact(receiver,sender,start)
            for name in self.base:
                self.push(self.nodes[name].due,'node',name)
            self.push(INTERVENTION,'intervention',None)

        def log(self, row):
            self.trace_count += 1
            self.events.append(plain(row))

        def intervene(self, cut):
            for receiver,sender in sorted(pair.PAIR):
                self.activate(receiver,sender)
            target = spec['local_target']
            if target is not None:
                self.nodes['L0'].due = cut+1
                self.push(cut+1,'node','L0')
                self.activate(target,'L0')
                self.activate('L0',target)
            self.log([cut,'declared_context_intervention',{'local_target':target,
                      'direct_pair':sorted(pair.PAIR), 'recurring_backgrounds':['F0','F1']}])

    engine = ContextEngine().run(end)
    engine.validate(end)
    return engine


def engine_payload(engine, spec, end):
    return plain({'model_specification':spec, 'horizon':end,
                  'waves':{name:asdict(node.wave()) for name,node in engine.nodes.items()},
                  'channels':{'|'.join(key):{'contacts':[asdict(c) for c in channel.contacts],
                                           'evidence':channel.evidence}
                              for key,channel in sorted(engine.channels.items())},
                  'pending':engine.pending, 'returned_packets':engine.returned_packets,
                  'events':engine.events, 'pressure_changes':engine.pressure_changes,
                  'steps':engine.steps, 'next_scheduled':{name:node.due for name,node in engine.nodes.items()},
                  'common_prefix_sha256':engine.common_prefix_hash.hexdigest(),
                  'execution_sha256':engine.observable_hash.hexdigest()})


def counts(engine, window):
    return {name:node.count(*window) for name,node in engine.nodes.items()}


def native_input(engine, compared, reference, window, *, previous=False):
    a,b = (wave_at(engine.nodes[name],window[1]) for name in (compared,reference))
    contacts = tuple(c for c in engine.channels[(compared,reference)].contacts if window[0]<=c.committed<=window[1])
    biases = (Q(0),Q(0)) if previous else tuple(Q(engine.nodes[name].count(-1,window[0])) for name in (compared,reference))
    return t.TemporalInput(a,b,contacts,tuple(window),biases,biases[0]-biases[1])


def wave_at(node, cut):
    indices = [index for index,(trace,_,_) in enumerate(node.records) if trace.indices[-1]<=cut]
    return n.wave([node.records[index] for index in indices], tuple(node.motifs[index] for index in indices))


def observation_context(engine, inputs, case, window, *, compared='A', reference='F0'):
    """Only committed native prefixes enter the shared observation interface."""
    hi = window[1]
    population = tuple(wave_at(node,hi) for node in engine.nodes.values())
    couplings = tuple(contact for key in sorted(engine.channels)
                      for contact in engine.channels[key].contacts if contact.committed<=hi)
    preparation = {'id':'m3:anchor:prepared-population:v1',
                   'parameters':{'protocol':inputs['preparation'], 'construction':inputs['cases'][case],
                                 'intervention_cut':inputs['intervention'], 'model_id':inputs['model_id']}}
    pending=[]
    packets=[*engine.returned_packets,*engine.pending.values()]
    for packet in sorted(packets,key=lambda row:row['id']):
        if packet['emitted']<=hi<packet['arrives']:
            wave=next(w for w in population if w.lineage==engine.nodes[packet['sender']].lineage)
            pending.append({'wave_identity':wave.identity, 'kind':'in_flight_contact',
                            'committed_cut':packet['emitted'], 'prefix_sha256':n.wave_prefix(wave,hi),
                            'payload':packet})
    for name,node in engine.nodes.items():
        actions=[event for event in engine.events if len(event)>2 and event[1] in ('start','edge','hinge')
                 and event[2]==name and event[0]<=hi]
        if actions and actions[-1][0]>max(trace.indices[-1] for trace,_,_ in node.records if trace.indices[-1]<=hi):
            last_start=max(index for index,row in enumerate(actions) if row[1]=='start')
            wave=next(w for w in population if w.identity==node.identity)
            pending.append({'wave_identity':node.identity, 'kind':'incomplete_return',
                            'committed_cut':actions[-1][0], 'prefix_sha256':n.wave_prefix(wave,hi),
                            'payload':{'actions_since_start':actions[last_start:]}})
    # The permitted graph comes from the declared intervention, not the observed
    # validation contacts. Identity comes from each retained formation witness.
    domain=t.domain_for(population,(),preparation,[INTERVENTION,HORIZON])
    edges={(receiver,sender) for receiver in engine.base for sender in engine.base if receiver!=sender}
    target=inputs['cases'][case]['local_target']
    if target is not None:
        edges.update({(target,'L0'),('L0',target)})
    domain['directed_graph']=[list(edge) for edge in sorted((engine.nodes[a].identity,engine.nodes[b].identity) for a,b in edges)]
    law=t.observation_law([domain], law_id='m3:anchor:stipulated-cycle-equivalents:v1',
                          compared_gain='1',reference_gain='1',epoch='0',coordinate='stipulated:anchor')
    sources=(m.source('anchor:archive','model',{'sha256':ARCHIVE_SHA256,'native_sha256':NATIVE_SHA256}),
             m.source('anchor:construction','model',{'input_sha256':digest(inputs),'case':case}),
             m.source('anchor:shared-observation','model',{'law_id':law['id'] if 'id' in law else 'm3:anchor:stipulated-cycle-equivalents:v1',
                                                          'physical_cycle_observation':None}))
    record=native_input(engine,compared,reference,window)
    previous=replace(native_input(engine,compared,reference,(0,window[0]),previous=True),
                     left=record.left,right=record.right)
    return t.ObservationContext(record,population,couplings,
                                preparation,tuple(pending),sources,law,
                                previous)


def count_projection(engine, compared, reference, window):
    selected = counts(engine,window)
    events = [c for c in engine.channels[(compared,reference)].contacts if window[0]<=c.committed<=window[1]]
    return {'window':list(window), 'counts':selected, 'returned_contacts':len(events),
            'count_projection_only':True, 'RCD_admitted':False, 'physical_seconds':None}


def diagnostics(engine):
    pair = ('A','F0')
    lo,hi = INTERVENTION,HORIZON
    ref = [k for k in engine.nodes['F0'].returns[1:] if lo<k<=hi]
    rolling=[]
    for width in (4,8):
        for index in (0,len(ref)//2):
            if index+width<len(ref):
                rolling.append(count_projection(engine,*pair,(ref[index],ref[index+width])))
    endpoints=[]
    u,v=ref[0],ref[4]
    times={name:node.returns[1:] for name,node in engine.nodes.items()}
    baseline=counts(engine,(u,v))
    bounds={name:bisect_right(ts,u+1)-bisect_left(ts,u-1)+bisect_right(ts,v+1)-bisect_left(ts,v-1)
            for name,ts in times.items()}
    for du in (-1,0,1):
        for dv in (-1,0,1):
            row=count_projection(engine,*pair,(u+du,v+dv))
            require(all(abs(row['counts'][name]-baseline[name])<=bounds[name] for name in times), 'endpoint count bound')
            endpoints.append({'offsets':[du,dv],**row})
    short=None
    for u,v in zip(ref,ref[1:]):
        row=count_projection(engine,*pair,(u,v))
        if row['counts']['A']>0 and row['returned_contacts']<2:
            short=row
            break
    # A one-cut count projection can be requested even without enough returns.
    if short is None:
        short=count_projection(engine,*pair,(ref[0]-1,ref[0]))
    packet=next(packet for packet in engine.returned_packets if packet['reflection'][0]>0)
    pending_cut=packet['starts']
    require(packet['emitted']<pending_cut<packet['arrives'], 'pending return ordering')
    channel=engine.channels[(packet['receiver'],packet['sender'])]
    require(packet['id'] not in {c.identity for c in channel.contacts if c.committed<=pending_cut}, 'pending packet counted as return')
    return {'rolling':rolling, 'overlapping_projections_are_independent':False,
            'endpoint_base_counts':baseline, 'endpoint_event_bounds':bounds, 'endpoint_variants':endpoints,
            'unsupported_short_projection':short,
            'reflection_and_pending':{'packet':packet, 'cut':pending_cut,
                                      'admitted_at_cut':False, 'later_contact_sha256':digest(asdict(next(c for c in channel.contacts if c.identity==packet['id'])))}}


def predict_engine(engine, inputs, case):
    train, validation = inputs['calibration_window'], inputs['validation_window']
    contexts={name:observation_context(engine,inputs,case,window)
              for name,window in (('calibration',train),('validation',validation))}
    require(contexts['calibration'].observation==contexts['validation'].observation, 'observation law changed at validation')
    temporal={name:t.predict(context) for name,context in contexts.items()}
    training_counts,validation_counts=counts(engine,train),counts(engine,validation)
    frozen={name:{'field':name, 'training_window':train, 'training_context_sha256':digest(plain(asdict(contexts['calibration']))),
                  'reference_bips_per_closure':str(Q(training_counts['F0'],training_counts[name]))}
            for name in ('A','B','F1')}
    predictions={name:{'frozen_sha256':digest(frozen[name]), 'validation_window':validation,
                       'operand_count':validation_counts[name],
                       'predicted_reference_bips':str(Q(frozen[name]['reference_bips_per_closure'])*validation_counts[name])}
                 for name in frozen}
    directions={}
    for receiver,sender in (('A','F0'),('F0','A'),('A','B'),('B','A')):
        record=native_input(engine,receiver,sender,validation)
        directions[receiver+'|'+sender]=plain(t.adapt(record))
    return {'classification':'declared_synthetic_context_experiment', 'case':case,
            'original_inputs_sha256':digest(inputs), 'complete_execution':engine_payload(engine,inputs['cases'][case],HORIZON),
            'temporal_predictions':temporal, 'training_counts':training_counts,
            'validation_counts':validation_counts, 'frozen_count_transfer':frozen,
            'count_transfer_predictions':predictions, 'directional_comparisons':directions,
            'diagnostics':diagnostics(engine), 'physical_anchor':'not_established',
            'physical_tolerance':None, 'complete_physical_standard_uncertainty':None}


def predict_case(inputs, case, root=ROOT):
    validate_inputs(inputs,root)
    require(case in CASES, 'unknown declared anchor case')
    with source_modules(root) as (modules,_):
        return predict_engine(run_engine(inputs['cases'][case],modules),inputs,case)


def evaluate_transfer(prediction, target):
    require(type(target) is int and target>0, 'positive exact reference count required')
    require(set(prediction)=={'frozen_sha256','validation_window','operand_count','predicted_reference_bips'}, 'transfer prediction fields')
    residual=Q(prediction['predicted_reference_bips'])-target
    return {'observed_reference_bips':target, 'residual':str(residual), 'relative_residual':str(residual/target),
            'classification':'retrospective_count_diagnostic_not_Cs_validation'}


def evaluate_case(supplied, target, *, original_inputs, case, root=ROOT):
    replayed=predict_case(original_inputs,case,root)
    require(canonical(supplied)==canonical(replayed), 'anchor artifact differs from independent original-context replay')
    return {'prediction_sha256':digest(replayed),
            'comparison':evaluate_transfer(replayed['count_transfer_predictions']['A'],target)}


def reference_independence(left_times, right_times, left_sources, right_sources):
    """Distinct names do not establish independent evidence or remove covariance."""
    return {'identical_endpoint_histories':left_times==right_times,
            'shared_source_ids':sorted(set(left_sources)&set(right_sources)),
            'independent_evidence':False,
            'reason':'independence is not certified by distinct lineage labels or different endpoint histories'}


def summarize(cases, historical, inputs):
    result={}
    for name,case in cases.items():
        waves=case['complete_execution']['waves']
        times={key:[trace['indices'][-1] for trace in wave['returns'][1:]] for key,wave in waves.items()}
        duration_provenance={}
        for key,comparison in case['directional_comparisons'].items():
            contacts=[event for event in case['complete_execution']['channels'][key]['contacts']
                      if SPLIT<=event['committed']<=HORIZON]
            support=comparison['forward']['rcd']['support']
            reflection=sum(event['reflection'][0] for event in contacts)
            elapsed=sum(event['support_trace']['indices'][-1]-event['support_trace']['indices'][0] for event in contacts)
            require(int(comparison['forward']['duration'])==support+reflection, 'directional RCD operand reconstruction')
            require(elapsed==len(contacts)*support+reflection, 'actual cross-return elapsed cuts differ from recorded support/reflection')
            duration_provenance[key]={'structural_support':support,'returned_contacts':len(contacts),
                                      'reflection_contribution':reflection,'compressed_RCD_duration':support+reflection,
                                      'sum_actual_cross_return_elapsed_cuts':elapsed,
                                      'contact_ids_sha256':digest([event['identity'] for event in contacts]),
                                      'duration_participation':'not_inferred_from_reference_bip_count'}
        transferred={}
        for field in ('A','B'):
            frozen=cases['baseline']['frozen_count_transfer'][field]
            prediction={'frozen_sha256':digest(frozen), 'validation_window':inputs['validation_window'],
                        'operand_count':case['validation_counts'][field],
                        'predicted_reference_bips':str(Q(frozen['reference_bips_per_closure'])*case['validation_counts'][field])}
            transferred[field]={'prediction':prediction,
                                'comparison':evaluate_transfer(prediction,case['validation_counts']['F0']),
                                'applicability':'same declared preparation' if name=='baseline' else
                                                'changed population/preparation; transfer not certified'}
        result[name]={'support_pair':inputs['cases'][name]['support_pair'],
                      'support_RD':{key:n.rd(*map(int,wave['motif'].split(':'))) for key,wave in waves.items()},
                      'training_counts':case['training_counts'], 'validation_counts':case['validation_counts'],
                      'heldout_count_transfer':{key:evaluate_transfer(value,case['validation_counts']['F0'])
                                               for key,value in case['count_transfer_predictions'].items()},
                      'reference_independence':reference_independence(times['F0'],times['F1'],
                          ['anchor:archive','anchor:shared-observation'],['anchor:archive','anchor:shared-observation']),
                      'directional_durations':{key:value['forward']['duration'] for key,value in case['directional_comparisons'].items()},
                      'duration_provenance':duration_provenance,
                      'baseline_frozen_gain_diagnostic':transferred,
                      'common_prefix_sha256':case['complete_execution']['common_prefix_sha256'],
                      'execution_sha256':case['complete_execution']['execution_sha256'],
                      'case_sha256':digest(case)}
    matched=[cases[name]['complete_execution']['common_prefix_sha256']
             for name in ('baseline','compared_population','reference_exposure')]
    require(len(set(matched))==1, 'intervention changed common committed base prefix')
    for name in ('compared_population','reference_exposure'):
        require(result[name]['execution_sha256']!=result['baseline']['execution_sha256'], 'intervention failed to alter execution')
    def return_times(case,name):
        return [tr['indices'][-1] for tr in cases[case]['complete_execution']['waves'][name]['returns']]
    require(return_times('reference_exposure','F0')!=return_times('baseline','F0'), 'reference exposure did not change reference history')
    require(return_times('compared_population','A')!=return_times('baseline','A'), 'compared population did not change compared history')
    return {'schema':'aod.m3.anchor-report.v1', 'acceptance_namespace':'M3-TA',
            'model_id':inputs['model_id'], 'original_inputs_sha256':digest(inputs),
            'historical_replay':historical, 'cases':result,
            'frozen_baseline_count_transfer':cases['baseline']['frozen_count_transfer'],
            'matched_prefix_preserved':True, 'separate_intervention_targets':{'compared_population':'A','reference_exposure':'F0'},
            'physical_Cs_observation_law':None, 'physical_tolerance':None, 'physical_SI_prediction':None,
            'scope':'Exact finite-model contexts and retrospective count-transfer controls; no physical calibration, independence, or stationarity claim.'}


def products(root=ROOT):
    inputs=default_inputs(root)
    historical=original_replay(root)
    require(historical['direct_pair_residuals']=={'A':'-5/29','B':'-49/151'}, 'original transfer rejection changed')
    cases={}
    with source_modules(root) as (modules,_):
        for name,spec in inputs['cases'].items():
            cases[name]=predict_engine(run_engine(spec,modules),inputs,name)
    report=summarize(cases,historical,inputs)
    output={'inputs.json':canonical(inputs)+b'\n','report.json':json.dumps(report,sort_keys=True,indent=2).encode()+b'\n'}
    output.update({f'cases/{name}.json.gz':gzip.compress(canonical(case)+b'\n',mtime=0) for name,case in cases.items()})
    return output


def verify(root=ROOT):
    folder=Path(root)/DATA
    bound_files=[path for path in folder.rglob('*') if path.is_file()]
    bound_files.extend(Path(module.__file__) for module in (n,m,t))
    bound_files.append(Path(__file__))
    before={str(path):sha(path) for path in bound_files}
    expected=products(root)
    actual={path.relative_to(folder).as_posix() for path in folder.rglob('*') if path.is_file()}
    require(actual==set(expected)|{'original_anchor_r02.zip'}, 'anchor artifact inventory differs')
    for name,value in expected.items():
        require((folder/name).read_bytes()==value, 'persisted anchor artifact differs: '+name)
    require({str(path):sha(path) for path in bound_files}==before, 'anchor replay changed bound source or data')
    return {'status':'PASS_ANCHOR_REPLAY','generated_outputs':len(expected),'original_archive_preserved':True,
            'original_controls':{'A':'-5/29','B':'-49/151'},'source_unchanged':True}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--write-data',action='store_true')
    group.add_argument('--check-data',action='store_true')
    args=parser.parse_args()
    if args.write_data:
        for name,value in products(args.root).items():
            path=args.root/DATA/name
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(value)
        print(json.dumps({'status':'generated','outputs':6}))
    else:
        print(json.dumps(verify(args.root),sort_keys=True))


if __name__=='__main__':
    main()

#!/usr/bin/env python3
"""A direct 3:3:6 <-> 1:2:6 closure comparison in a retained 3:4:6 background."""
import argparse
from dataclasses import asdict, replace
from fractions import Fraction as Q
import gzip
import hashlib
import io
import json
from pathlib import Path
import time

import population as p

PAIR = {('A', 'B'), ('B', 'A')}


def write_json(path, value):
    path.write_text(json.dumps(p.plain(value), indent=2, sort_keys=True)+'\n')


def write_gzip(path, value):
    path.write_bytes(gzip.compress(p.canonical(value)+b'\n', mtime=0))


class PairEngine(p.Engine):
    """Reuse the sealed dynamics; specialize population, graph and intervention."""
    def __init__(self, scenario, intervention, output=None):
        p.require(scenario in ('background_only', 'direct_pair', 'recorded_only'), 'unknown intervention')
        self.scenario, self.intervention = scenario, intervention
        self.nodes = {name:p.Node(name, exponent, count) for name,exponent,count in
                      (('A',3,3), ('B',1,2), ('F0',3,4), ('F1',3,4))}
        self.base = tuple(self.nodes)
        self.channels, self.active, self.heap = {}, set(), []
        self.serial, self.record_count, self.trace_count = 0, 0, 0
        self.pending, self.returned_packets = {}, []
        self.steps = {name:[] for name in self.nodes}
        self.pressure_changes, self.last_pressure = [], {}
        self.common_prefix_hash, self.observable_hash = hashlib.sha256(), hashlib.sha256()
        self.first_operational_local_contact = None
        self.feedback_disabled = False
        self.trace_path, self.trace = output, bool(output)
        self.raw_writer = open(output,'wb') if output else None
        self.writer = (io.TextIOWrapper(gzip.GzipFile(filename='',mode='wb',fileobj=self.raw_writer,mtime=0),encoding='utf-8')
                       if self.raw_writer else None)
        for receiver in self.base:
            for sender in self.base:
                if receiver != sender and (receiver,sender) not in PAIR:
                    self.activate(receiver,sender)
                    for start in (700,1200):
                        self.seed_contact(receiver,sender,start)
        for node in self.nodes.values():
            self.push(node.due,'node',node.name)
        self.push(intervention,'intervention',None)

    def intervene(self, cut):
        if self.scenario != 'background_only':
            for receiver,sender in sorted(PAIR):
                self.activate(receiver,sender)
        self.log([cut,'direct_pair_intervention',self.scenario,
                  {'population_unchanged':list(self.nodes),'new_channels':sorted(PAIR) if self.scenario!='background_only' else []}])

    def pressure(self, receiver):
        total, terms = super().pressure(receiver)
        if self.scenario == 'recorded_only':
            terms = tuple(term for term in terms if tuple(term.get('channel',())) not in PAIR)
            total = sum(term['rho'] for term in terms)
        return total, terms


def signature(engine):
    return p.digest({'returns':{name:[tr.trace_digest for tr,_,_ in node.records]
                                for name,node in engine.nodes.items()},
                     'execution':engine.observable_hash.hexdigest()})


def rcd_for(engine, receiver, sender, contacts):
    if len(contacts)<2:
        return None
    r = p.n.RCD(engine.nodes[receiver].identity,engine.nodes[sender].identity,p.SCOPE,
                tuple(c.identity for c in contacts),engine.nodes[sender].rd,
                tuple(c.reflection[0] for c in contacts))
    return {'record':asdict(r),'duration':r.duration()}


def bip_rows(engine, reference, compared, lo, hi):
    ref, target = engine.nodes[reference], engine.nodes[compared]
    channel = engine.channels.get((reference,compared))
    contacts = [] if channel is None else channel.contacts
    rows = []
    for index in range(1,len(ref.records)):
        previous, current = ref.records[index-1][0],ref.records[index][0]
        u,v = previous.indices[-1],current.indices[-1]
        if not lo<=u<v<=hi:
            continue
        returned = [c for c in contacts if u<=c.committed<=v]
        carry = [c for c in contacts if c.committed<=v][-2:]
        target_returns = [tr for tr,_,_ in target.records[1:] if u<tr.indices[-1]<=v]
        row = {'reference':reference,'compared':compared,'window':[u,v],
               'reference_return_ids':[previous.return_id,current.return_id],
               'reference_bip_increment':ref.count(u,v),
               'compared_closures':len(target_returns),
               'compared_return_ids':[tr.return_id for tr in target_returns],
               'lag_at_start':target.count(-1,u)-ref.count(-1,u),
               'lag_at_end':target.count(-1,v)-ref.count(-1,v),
               'window_contact_count':len(returned),
               'within_bip_RCD':rcd_for(engine,reference,compared,returned),
               'endpoint_RCD_with_carry':rcd_for(engine,reference,compared,carry),
               'temporal_comparison_admitted':len(returned)>=2 and len(target_returns)>0}
        p.require(row['reference_bip_increment']==1,'one reference bip must be one distinct reclosure')
        p.require(len(set(row['compared_return_ids']))==row['compared_closures'],'reclosure counted twice')
        p.require(row['lag_at_end']-row['lag_at_start']==row['compared_closures']-1,'unwrapped lag increment differs')
        rows.append(row)
    p.require(bool(rows),'no complete reference bip windows')
    partition_counts = sum(row['compared_closures'] for row in rows)
    p.require(partition_counts == target.count(rows[0]['window'][0], rows[-1]['window'][1]),'bip partition lost closures')
    counts = [row['compared_closures'] for row in rows]
    histogram = {str(v):counts.count(v) for v in sorted(set(counts))}
    return {'reference':reference,'compared':compared,'rows':rows,
            'complete_reference_bips':len(rows),'compared_closures_in_complete_bips':partition_counts,
            'mean_closures_per_reference_bip':str(Q(partition_counts,len(rows))),
            'histogram':histogram,
            'partial_boundary_counts':{'leading':target.count(lo,rows[0]['window'][0]),
                                       'trailing':target.count(rows[-1]['window'][1],hi)},
            'admitted_bip_windows':sum(row['temporal_comparison_admitted'] for row in rows),
            'carry_present_but_window_RCD_absent':sum(row['endpoint_RCD_with_carry'] is not None and row['within_bip_RCD'] is None for row in rows)}


def feedback_example(engine, receiver, sender):
    changes = [row for row in engine.pressure_changes if row['field']==receiver]
    index = next(i for i,row in enumerate(changes)
                 if any(term.get('channel')==[receiver,sender] for term in row['terms']))
    after = changes[index]
    previous = changes[index-1] if index else None
    term = next(t for t in after['terms'] if t.get('channel')==[receiver,sender])
    steps = engine.steps[receiver]
    step = next(i for i,row in enumerate(steps) if row[0]==after['cut'])
    current,next_step = steps[step:step+2]
    # A completed return schedules a start marker one cut later. A start
    # marker then schedules a traversal using the committed pressure.
    expected_delay = 1 if next_step[1]=='start' else after['pressure']
    p.require(next_step[0]-current[0]==expected_delay,'committed pressure did not control next event')
    contact_ids=set(term['rcd']['contact_ids'])
    packets=[x for x in engine.channels[(receiver,sender)].evidence if x['id'] in contact_ids]
    p.require(len(packets)==2 and all(x['arrives']<=after['cut'] for x in packets),'unreturned coupling used')
    return {'receiver':receiver,'sender':sender,'packets':packets,'previous_pressure':previous,
            'new_pressure':after,'direct_channel_duration':term['rho'],
            'current_step':current,'next_step':next_step}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=p.HERE/'results')
    parser.add_argument('--background-returns',type=int,default=64)
    args=parser.parse_args()
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    source=p.check_sources()
    predecessor=json.loads((p.HERE/'PREDECESSOR_BINDING.json').read_text())
    for name,sha in predecessor['sha256'].items():
        p.require(hashlib.sha256((p.HERE/name).read_bytes()).hexdigest()==sha,'predecessor changed: '+name)
    model=json.loads((p.HERE/'MODEL.json').read_text())
    frozen={'model_sha256':p.digest(model),
            'code_sha256':{name:hashlib.sha256((p.HERE/name).read_bytes()).hexdigest() for name in ('pair_trial.py','population.py')},
            'source_commit':source['commit']}
    write_json(out/'frozen_contract.json',frozen)
    lo=model['intervention_cut']
    skeleton=PairEngine('background_only',lo)
    duration=args.background_returns*skeleton.nodes['F0'].rd*sum(n.rd for n in skeleton.nodes.values())
    hi=lo+duration
    engines,results,checks={},{},[]

    def check(name,ok):
        p.require(ok,'check failed: '+name)
        checks.append({'name':name,'status':'pass'})

    for scenario in model['scenarios']:
        started=time.monotonic()
        engine=PairEngine(scenario,lo,out/(scenario+'.events.jsonl.gz')).run(hi)
        waves=engine.validate(hi)
        counts={name:node.count(lo,hi) for name,node in engine.nodes.items()}
        check(scenario+': persistent admitted 3:4:6 background',all(waves[name].motif=='3:4' and counts[name]>=args.background_returns-1 for name in ('F0','F1')))
        check(scenario+': A and B retain actual 3:3:6 and 1:2:6 witnesses',waves['A'].motif=='3:3' and waves['B'].motif=='1:2' and all(m.enclosure==6 for w in waves.values() for m in w.motif_witnesses))
        bips={r+'|'+c:bip_rows(engine,r,c,lo,hi) for r,c in [('A','B'),('B','A'),('F0','A'),('F0','B')]}
        check(scenario+': distinct closure counts and complete-bip partitions validated',True)
        windows=[]
        for divisor in (4,2,1):
            stop=lo+duration//divisor
            wc={name:node.count(lo,stop) for name,node in engine.nodes.items()}
            item={'window':[lo,stop],'counts':wc,'B_closures_per_A_bip':str(Q(wc['B'],wc['A'])),'comparisons':{}}
            if scenario!='background_only':
                for receiver,sender in sorted(PAIR):
                    contacts=tuple(c for c in engine.channels[(receiver,sender)].contacts if lo<=c.committed<=stop)
                    biases=(Q(engine.nodes[receiver].count(-1,lo)),Q(engine.nodes[sender].count(-1,lo)))
                    result=p.n.compare(waves[receiver],waves[sender],contacts,(lo,stop),bias=biases,prior_lag=biases[0]-biases[1])
                    item['comparisons'][sender+'->'+receiver]=p.plain({k:asdict(v) if k=='rcd' else v for k,v in result.items()})
            windows.append(item)
        summary={'scenario':scenario,'window':[lo,hi],'counts':counts,
                 'B_closures_per_A_bip':str(Q(counts['B'],counts['A'])),
                 'A_closures_per_B_bip':str(Q(counts['A'],counts['B'])),
                 'base_prefix_sha256':engine.common_prefix_hash.hexdigest(),
                 'history_signature':signature(engine),'last_pressure':{name:engine.pressure(name)[0] for name in engine.nodes},
                 'support_RD':{name:node.rd for name,node in engine.nodes.items()},
                 'window_checks':windows,
                 'bip_statistics':{k:{field:value for field,value in rows.items() if field!='rows'} for k,rows in bips.items()},
                 'next_scheduled':{name:node.due for name,node in engine.nodes.items()},
                 'pending_return_count':len(engine.pending),'trace_rows':engine.trace_count}
        write_gzip(out/(scenario+'.histories.json.gz'),{name:asdict(w) for name,w in waves.items()})
        write_gzip(out/(scenario+'.couplings.json.gz'),{'|'.join(k):{'contacts':[asdict(c) for c in v.contacts],'evidence':v.evidence} for k,v in sorted(engine.channels.items())})
        write_gzip(out/(scenario+'.pressure.json.gz'),engine.pressure_changes)
        write_gzip(out/(scenario+'.bip-windows.json.gz'),bips)
        write_json(out/(scenario+'.pending.json'),engine.pending)
        write_json(out/(scenario+'.summary.json'),summary)
        engines[scenario],results[scenario]=engine,summary
        print(json.dumps({'scenario':scenario,'counts':counts,'B_per_A_bip':summary['B_closures_per_A_bip'],'runtime_seconds':round(time.monotonic()-started,2)}),flush=True)

    baseline,coupled,control=(engines[x] for x in model['scenarios'])
    check('common execution before direct coupling',len({x['base_prefix_sha256'] for x in results.values()})==1)
    check('direct coupling changes both generated closure counts',all(results['direct_pair']['counts'][name]!=results['background_only']['counts'][name] for name in ('A','B')))
    check('recording contacts without pressure feedback preserves baseline histories',signature(control)==signature(baseline))
    check('both pair directions contain repeated actual returns',all(len(coupled.channels[key].contacts)>=2 for key in PAIR))
    examples={}
    for receiver,sender in sorted(PAIR):
        a,b=baseline.steps[receiver],coupled.steps[receiver]
        difference=next(i for i,(x,y) in enumerate(zip(a,b)) if x!=y)
        second_return=coupled.channels[(receiver,sender)].contacts[1].committed
        check(receiver+': first changed traversal follows its second incoming pair return',min(a[difference][0],b[difference][0])>second_return)
        examples[sender+'->'+receiver]=feedback_example(coupled,receiver,sender)
        check(receiver+': returned RCD enters pressure and next-event scheduling',True)
    check('bip windows expose carry-in separately from within-window RCD',results['direct_pair']['bip_statistics']['B|A']['carry_present_but_window_RCD_absent']>0)
    channel=coupled.channels[('A','B')]
    bad=replace(channel.contacts[-1],left_prefix='0'*64)
    try:
        p.n.compare(coupled.nodes['A'].wave(),coupled.nodes['B'].wave(),(*channel.contacts[-2:-1],bad),(lo,hi))
    except (ValueError,TypeError) as exc:
        checks.append({'name':'substituted direct-coupling history rejected','status':'pass','rejection':str(exc)})
    else:
        raise ValueError('substituted history was accepted')
    check('model and code remain frozen',frozen['model_sha256']==p.digest(json.loads((p.HERE/'MODEL.json').read_text())) and all(hashlib.sha256((p.HERE/name).read_bytes()).hexdigest()==sha for name,sha in frozen['code_sha256'].items()))
    report={'status':'pass','source_commit':source['commit'],'contract':frozen,
            'window':[lo,hi],'background_return_target':args.background_returns,
            'results':results,'feedback_examples':examples,'checks':checks,'check_count':len(checks),
            'counting_statement':'One field-own reclosure is one bip; cross-field closures per bip are measured from committed event intervals.',
            'evidence_scope':'Declared finite dynamics, with unchanged response/reflection choices. No Cs gain, seconds, photon detection, shedding or core transformation is claimed.'}
    write_json(out/'report.json',report)
    print(json.dumps({'status':'pass','checks':len(checks)}),flush=True)


if __name__=='__main__':
    main()

#!/usr/bin/env python3
"""Replay both fields' comparisons with the retained background F0."""
import argparse
from dataclasses import asdict
from fractions import Fraction as Q
import gzip
import json
from pathlib import Path
import population as p


def trace(raw):
    r=dict(raw)
    for key in ('event_ids','vertices','indices','roles'):
        r[key]=tuple(r[key])
    w=dict(r['reflection'])
    for key in ('outbound_ids','return_ids'):
        w[key]=tuple(w[key])
    r['reflection']=p.n.ReflectionWitness(**w)
    t=p.n.Trace(**r)
    p.n.validate_trace(t)
    return t


def certificate(raw,tr):
    p.require(raw['motif']=='Monon' and not raw['inner_waves'],'unexpected folded certificate')
    c=p.n.certify(tr)
    p.require(p.canonical(asdict(c))==p.canonical(raw),'certificate replay mismatch')
    return c


def wave(raw):
    records=[]
    for r,c in zip(raw['returns'],raw['certificates']):
        tr=trace(r);cert=certificate(c,tr)
        records.append((tr,cert,{cert.certificate_digest:cert}))
    motifs=[]
    for r in raw['motif_witnesses']:
        support=trace(r['support_trace'])
        components=[]
        for tr_raw,c_raw in zip(r['component_traces'],r['component_certificates']):
            tr=trace(tr_raw);components.append((tr,certificate(c_raw,tr)))
        closure=certificate(r['closure'],support)
        registry={c.certificate_digest:c for _,c in components};registry[closure.certificate_digest]=closure
        construction=(tuple(tuple(b) for b in r['construction'][0]),tuple(r['construction'][1]))
        m=p.n.motif_witness(r['core'],support,construction,components,registry,r['enclosure'],r['chirality'])
        p.require(p.canonical(asdict(m))==p.canonical(r),'motif replay mismatch')
        motifs.append(m)
    w=p.n.wave(records,tuple(motifs))
    p.require(p.canonical(asdict(w))==p.canonical(raw),'complete serialized wave differs')
    return w


def contact(raw):
    r=dict(raw);r['reflection']=tuple(r['reflection'])
    r['support_trace']=trace(r['support_trace'])
    r['support_certificate']=certificate(r['support_certificate'],r['support_trace'])
    return p.n.Contact(**r)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results',type=Path,default=p.HERE/'results')
    parser.add_argument('--output',type=Path,default=p.HERE/'common-reference.json')
    args=parser.parse_args()
    p.check_sources()
    rows=[]
    for scenario in ('background_only','direct_pair','recorded_only'):
        raw=json.loads(gzip.decompress((args.results/(scenario+'.histories.json.gz')).read_bytes()))
        channels=json.loads(gzip.decompress((args.results/(scenario+'.couplings.json.gz')).read_bytes()))
        summary=json.loads((args.results/(scenario+'.summary.json')).read_text())
        lo,hi=summary['window']
        waves={name:wave(raw[name]) for name in ('A','B','F0')}
        comparisons={}
        for name in ('A','B'):
            events=tuple(contact(c) for c in channels[name+'|F0']['contacts'] if lo<=c['committed']<=hi)
            biases=tuple(Q(sum(t.indices[-1]<=lo for t in waves[k].returns[1:])) for k in (name,'F0'))
            result=p.n.compare(waves[name],waves['F0'],events,(lo,hi),bias=biases,prior_lag=biases[0]-biases[1])
            comparisons[name+'|F0']={key:asdict(value) if key=='rcd' else value for key,value in result.items()}
        ratio=comparisons['B|F0']['ratio']/comparisons['A|F0']['ratio']
        p.require(ratio==Q(summary['B_closures_per_A_bip']),'common-reference cadence composition differs')
        lag=comparisons['B|F0']['lag']-comparisons['A|F0']['lag']
        expected=sum(t.indices[-1]<=hi for t in waves['B'].returns[1:])-sum(t.indices[-1]<=hi for t in waves['A'].returns[1:])
        p.require(lag==expected,'common-reference phase difference differs')
        rows.append({'scenario':scenario,'window':[lo,hi],'comparisons':comparisons,
                     'composed_B_per_A':ratio,'composed_B_minus_A_lag':lag,'status':'pass',
                     'scope':'Cadence ratios and unwrapped count lag share a committed window. Directional RCD objects remain specific to their actual channels; no RCD composition equality is asserted.'})
    args.output.write_text(json.dumps(p.plain(rows),indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':'pass','common_reference_cases':len(rows)}))


if __name__=='__main__':
    main()

#!/usr/bin/env python3
"""Conditional, source-bound closure/Cs-cycle/second mapping with explicit scale."""
from dataclasses import asdict
from fractions import Fraction as Q
import gzip
import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'input'))
import population as p
import common_reference as codec

CS=Q(9192631770)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_inputs():
    binding=json.loads((HERE/'INPUT_BINDING.json').read_text())
    for name,value in binding['sha256'].items():
        p.require(sha(HERE/'input'/name)==value,'sealed input changed: '+name)
    p.check_sources()
    return binding


def load_scenario(name):
    root=HERE/'input/results'
    paths={key:root/(name+'.'+suffix+'.json.gz') for key,suffix in [('histories','histories'),('couplings','couplings')]}
    raw=json.loads(gzip.decompress(paths['histories'].read_bytes()))
    couplings=json.loads(gzip.decompress(paths['couplings'].read_bytes()))
    waves={name:codec.wave(raw[name]) for name in ('A','B','F0','F1')}
    channels={key:tuple(codec.contact(c) for c in val['contacts']) for key,val in couplings.items()}
    return {'scenario':name,'waves':waves,'channels':channels,'raw_sha256':{k:sha(v) for k,v in paths.items()},
            'summary':json.loads((root/(name+'.summary.json')).read_text())}


def comparison(data,receiver,sender,window):
    u,v=window
    a,b=data['waves'][receiver],data['waves'][sender]
    events=tuple(c for c in data['channels'][receiver+'|'+sender] if u<=c.committed<=v)
    biases=tuple(Q(sum(t.indices[-1]<=u for t in w.returns[1:])) for w in (a,b))
    result=p.n.compare(a,b,events,window,bias=biases,prior_lag=biases[0]-biases[1])
    return {key:asdict(value) if key=='rcd' else value for key,value in result.items()}


def context(data,window):
    u,v=window
    p.require(type(u) is int and type(v) is int and u<v,'invalid comparison window')
    counts={name:sum(u<t.indices[-1]<=v for t in wave.returns[1:]) for name,wave in data['waves'].items()}
    p.require(all(counts[k]>0 for k in ('A','B','F0')),'positive recurrence required')
    comparisons={name+'|F0':comparison(data,name,'F0',window) for name in ('A','B')}
    if data['scenario']!='background_only':
        comparisons['A|B']=comparison(data,'A','B',window)
        comparisons['B|A']=comparison(data,'B','A',window)
    prefixes={name:[p.n.wave_prefix(wave,k) for k in window] for name,wave in data['waves'].items()}
    population={name:{'identity':wave.identity,'core':wave.motif,
                      'enclosures':sorted({m.enclosure for m in wave.motif_witnesses})}
                for name,wave in data['waves'].items()}
    base={'scenario':data['scenario'],'window':list(window),'counts':counts,'population':population,
          'input_sha256':data['raw_sha256'],'endpoint_prefixes':prefixes,'comparisons':comparisons,
          'input_binding_sha256':sha(HERE/'INPUT_BINDING.json'),
          'bridge_code_sha256':sha(Path(__file__)),
          'decoder_code_sha256':sha(HERE/'input/common_reference.py'),
          'observation_contract_sha256':p.digest(json.loads((HERE/'OBSERVATION_CONTRACT.json').read_text()))}
    # A context digest binds the entire admitted comparison, not just scalar counts.
    base=p.plain(base)
    return {'record':base,'sha256':p.digest(base)}


def _symbolic_for_validated_context(ctx):
    record=ctx['record']
    p.require(ctx['sha256']==p.digest(record),'context digest mismatch')
    nr=record['counts']['F0']
    gains={name:Q(nr,record['counts'][name]) for name in ('A','B','F0')}
    routes={name:gains[name]*record['counts'][name]/CS for name in gains}
    p.require(len(set(routes.values()))==1,'reference-transfer elapsed coefficients differ')
    rates={name:CS*Q(record['counts'][name],nr) for name in ('A','B')}
    return p.plain({'classification':'conditional_symbolic_SI_map','context_sha256':ctx['sha256'],
                    'gain_coefficient_multiplying_kappa':gains,
                    'elapsed_seconds_coefficient_multiplying_kappa':Q(nr)/CS,
                    'elapsed_coefficients_by_reference_route':routes,
                    'rate_hz_coefficient_divided_by_kappa':rates,
                    'physical_elapsed_seconds':None,'physical_rate_hz':None,
                    'complete_physical_standard_uncertainty':None,
                    'reason':'External kappa and its source-bound realization law are not established.'})


def predict(data,window):
    """Public prediction always reconstructs the admitted comparison first."""
    ctx=context(data,window)
    return {'context':ctx,'mapped':_symbolic_for_validated_context(ctx)}


def hypothetical_scale(mapped,kappa,*,classification):
    p.require(classification=='hypothetical_countermodel','numerical scale requires explicit hypothetical classification')
    p.require(type(kappa) in (str,int,Q) and type(kappa) is not bool,'exact positive scale required')
    kappa=Q(kappa);p.require(kappa>0,'scale must be positive')
    return {'classification':classification,'kappa':str(kappa),
            'elapsed_seconds':str(kappa*Q(mapped['elapsed_seconds_coefficient_multiplying_kappa'])),
            'rates_hz':{name:str(Q(value)/kappa) for name,value in mapped['rate_hz_coefficient_divided_by_kappa'].items()},
            'physical_calibration':False}


def evaluate_supplied(supplied,*,original_data,original_window):
    expected=predict(original_data,original_window)
    p.require(p.canonical(supplied)==p.canonical(expected),'artifact differs from original histories/window replay')
    return expected

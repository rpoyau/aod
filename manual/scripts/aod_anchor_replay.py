#!/usr/bin/env python3
"""Scientific replay of retained count histories, with explicit source admission.

Derived from the preserved historical audit; this adapter replaces task-archive
admission and provenance only. It is not the unmodified historical archive audit.
"""
import argparse
from bisect import bisect_left, bisect_right
from copy import deepcopy
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path
import sys

import aod_temporal_anchor as anchor
def configure(root):
    global HERE, s, ROOT
    ROOT=Path(root).resolve()
    anchor.verify_sources(ROOT)
    HERE=ROOT/anchor.DATA/'source'
    sys.path.insert(0,str(HERE/'baseline'))
    import si_bridge
    s=si_bridge


def write(path,value):
    path.write_text(json.dumps(s.p.plain(value),sort_keys=True,indent=2)+'\n')


def verify_inputs():
    return anchor.verify_sources(ROOT)


def count(times,u,v):
    s.p.require(type(u) is int and type(v) is int and u<v,'invalid window')
    return bisect_right(times,v)-bisect_right(times,u)


def fit_transfer(training,field):
    """Only the admitted training record enters this coefficient."""
    c=training['counts']
    s.p.require(c[field]>0 and c['F0']>0,'positive calibration counts required')
    return {'classification':'retrospective_count_transfer_not_Cs_calibration',
            'field':field,'training_window':training['window'],
            'training_sha256':s.p.digest(training),
            'F0_bips_per_field_closure':str(Q(c['F0'],c[field]))}


def predict_reference(frozen,operand_count,window):
    """The validation reference count is deliberately not an input."""
    s.p.require(type(operand_count) is int and operand_count>0,'positive exact operand count required')
    s.p.require(frozen['training_window'][1]<=window[0]<window[1],'training and validation must be disjoint')
    return {'frozen_transfer_sha256':s.p.digest(frozen),'operand_count':operand_count,
            'validation_window':list(window),
            'predicted_F0_bips':str(Q(frozen['F0_bips_per_field_closure'])*operand_count)}


def evaluate(prediction,reference_count):
    s.p.require(type(reference_count) is int and reference_count>0,'positive exact reference count required')
    residual=Q(prediction['predicted_F0_bips'])-reference_count
    return {'observed_F0_bips':reference_count,'residual_F0_bips':str(residual),
            'relative_residual':str(residual/reference_count)}


def floor_affine_test(xs,ys):
    """Exact feasibility of y_j=floor(alpha*x_j+beta), alpha>0.

    Each pair i<j requires (dy-1)/dx < alpha < (dy+1)/dx.
    Intersecting all pairs is equivalent to a nonempty common beta interval.
    This is a declared count-rounding null, not a continuous AOD phase law.
    """
    s.p.require(len(xs)==len(ys)>=2,'at least two paired samples required')
    s.p.require(all(type(v) is int for v in (*xs,*ys)),'integer count samples required')
    s.p.require(all(a<b for a,b in zip(xs,xs[1:])),'strictly increasing reference counts required')
    lower=Q(0);upper=None;low_pair=None;high_pair=None
    for i in range(len(xs)):
        for j in range(i+1,len(xs)):
            dx=xs[j]-xs[i];dy=ys[j]-ys[i]
            a,b=Q(dy-1,dx),Q(dy+1,dx)
            witness={'indices':[i,j],'reference_counts':[xs[i],xs[j]],
                     'field_counts':[ys[i],ys[j]]}
            if a>lower:lower=a;low_pair=witness
            if upper is None or b<upper:upper=b;high_pair=witness
    compatible=lower<upper
    result={'hypothesis':'one fixed positive cadence plus an unknown count origin and whole-count rounding',
            'compatible':compatible,'strict_lower':str(lower),'strict_upper':str(upper),
            'lower_witness':low_pair,'upper_witness':high_pair,'sample_count':len(xs)}
    if compatible:
        alpha=(lower+upper)/2
        beta_lo=max(Q(y)-alpha*x for x,y in zip(xs,ys))
        beta_hi=min(Q(y+1)-alpha*x for x,y in zip(xs,ys))
        s.p.require(beta_lo<beta_hi,'pairwise feasibility lost common intercept')
        beta=(beta_lo+beta_hi)/2
        s.p.require(all((alpha*x+beta).__floor__()==y for x,y in zip(xs,ys)),'feasibility witness does not reproduce counts')
        result['diagnostic_witness']={'alpha':str(alpha),'beta':str(beta)}
    return result


def admitted_window(data,window):
    times={name:[t.indices[-1] for t in w.returns[1:]] for name,w in data['waves'].items()}
    comparisons={name+'|F0':s.comparison(data,name,'F0',window) for name in ('A','B','F1')}
    return s.p.plain({'window':list(window),'counts':{k:count(v,*window) for k,v in times.items()},
                     'comparisons':comparisons,'input_sha256':data['raw_sha256'],
                     'endpoint_prefixes':{k:[s.p.n.wave_prefix(w,t) for t in window] for k,w in data['waves'].items()}})


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=anchor.ROOT)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();configure(args.root);args.output.mkdir(parents=True,exist_ok=True)
    verify_inputs()
    frozen={'adapter_code_sha256':s.sha(Path(__file__)),
            'scientific_members_sha256':anchor.SOURCE_MEMBERS_SHA256,
            'original_archive_sha256':anchor.ARCHIVE_SHA256,
            'classification':'scientific_subset_replay_adapter'}
    write(args.output/'frozen.json',frozen)
    checks=[]
    def check(name,condition):
        s.p.require(condition,'check failed: '+name)
        checks.append({'name':name,'status':'pass'})
    def reject(name,fn):
        try:fn()
        except (ValueError,TypeError) as e:checks.append({'name':name,'status':'pass','rejection':str(e)})
        else:raise ValueError('invalid case accepted: '+name)

    xs=list(range(40));ys=[(Q(3,2)*x+Q(1,3)).__floor__() for x in xs]
    check('constant rational cadence with rounding is admitted',floor_affine_test(xs,ys)['compatible'])
    check('nonconstant quadratic count control is rejected',not floor_affine_test(xs,[x*x for x in xs])['compatible'])
    # A strict endpoint matters: bounds meeting at one value do not admit a floor law.
    check('empty strict slope intersection is rejected',not floor_affine_test([0,1,2],[0,2,2])['compatible'])
    reject('Boolean count sample is rejected',lambda:floor_affine_test([0,1],[0,True]))

    records={};rolling=[];boundary=[];retained_data={}
    for scenario in ('background_only','direct_pair','recorded_only'):
        data=s.load_scenario(scenario);retained_data[scenario]=data
        times={name:[t.indices[-1] for t in w.returns[1:]] for name,w in data['waves'].items()}
        lo,hi=data['summary']['window'];mid=(lo+hi)//2
        check(scenario+': all closure endpoints strictly ordered',
              all(all(a<b for a,b in zip(ts,ts[1:])) for ts in times.values()))
        training=admitted_window(data,[lo,mid])
        validation=admitted_window(data,[mid,hi])
        transfers={}
        for field in ('A','B','F1'):
            fit=fit_transfer(training,field)
            pred=predict_reference(fit,validation['counts'][field],[mid,hi])
            transfers[field]={'frozen':fit,'prediction':pred,'comparison':evaluate(pred,validation['counts']['F0'])}
        check(scenario+': split counts recover complete window',
              all(training['counts'][k]+validation['counts'][k]==count(times[k],lo,hi) for k in times))
        check(scenario+': A and B fixed-gain validation has nonzero residual',
              all(Q(transfers[k]['comparison']['residual_F0_bips'])!=0 for k in ('A','B')))
        same=times['F0']==times['F1']
        check(scenario+': F0 and F1 have distinct identities but identical endpoint sequences',
              data['waves']['F0'].identity!=data['waves']['F1'].identity and same)
        check(scenario+': matching F1 validation is explained by identical count histories',
              same and transfers['F1']['comparison']['relative_residual']=='0')
        cuts=[t for t in times['F0'] if lo<=t<=hi]
        x=[bisect_right(times['F0'],t) for t in cuts]
        series={k:[bisect_right(times[k],t) for t in cuts] for k in ('A','B','F1')}
        tests={k:floor_affine_test(x,y) for k,y in series.items()}
        check(scenario+': A and B fail the constant-cadence plus count-rounding null',
              not tests['A']['compatible'] and not tests['B']['compatible'])
        check(scenario+': identical F1 passes the rounding null',tests['F1']['compatible'])
        # Rolling rows are descriptive count projections from admitted full histories.
        # They are NOT labelled standalone RCD comparisons or SI measurements.
        for width in (4,8,16,32):
            for start in range(len(cuts)-width):
                u,v=cuts[start],cuts[start+width]
                row={'scenario':scenario,'reference_bips':width,'start_reference_index':start,'window':[u,v],
                     'count_projection_only':True,'physical_seconds':None,'fields':{}}
                for field in ('A','B','F1'):
                    n=count(times[field],u,v)
                    s.p.require(n>0,'rolling field count is zero')
                    row['fields'][field]={'closures':n,'closures_per_F0_bip':str(Q(n,width)),
                                          'F0_bips_per_closure':str(Q(width,n))}
                rolling.append(row)
        # Move endpoints by one ordering cut at selected reference closures.
        # No ordering-cut duration is introduced and no fractional phase is invented.
        for start in (0,16,32):
            for width in (8,16,32):
                if start+width>=len(cuts):continue
                u,v=cuts[start],cuts[start+width]
                base={k:count(ts,u,v) for k,ts in times.items()}
                bands={k:bisect_right(ts,u+1)-bisect_left(ts,u-1)+bisect_right(ts,v+1)-bisect_left(ts,v-1) for k,ts in times.items()}
                variants=[]
                for du in (-1,0,1):
                    for dv in (-1,0,1):
                        c={k:count(ts,u+du,v+dv) for k,ts in times.items()}
                        s.p.require(all(abs(c[k]-base[k])<=bands[k] for k in times),'endpoint event bound failed')
                        variants.append({'offsets':[du,dv],'counts':c})
                boundary.append({'scenario':scenario,'window':[u,v],'reference_bips':width,
                                 'base_counts':base,'endpoint_event_bounds':bands,'variants':variants,
                                 'scope':'count projection; one ordering cut is not a time unit'})
        records[scenario]={'training':training,'validation':validation,'transfers':transfers,
                           'reference_endpoint_identity':same,'reference_cuts':cuts,
                           'reference_cumulative_counts':x,'field_cumulative_counts':series,
                           'constant_cadence_rounding_tests':tests,
                           'independent_reference_validation':False}
        print(json.dumps({'scenario':scenario,'status':'pass','heldout_relative_residuals':{k:v['comparison']['relative_residual'] for k,v in transfers.items()},'reference_samples':len(cuts)}),flush=True)

    ref=records['direct_pair'];pred=ref['transfers']['A']['prediction']
    before=s.p.canonical(pred)
    altered_target=evaluate(pred,ref['validation']['counts']['F0']+1)
    check('target-only changes preserve prediction bytes and alter comparison',
          s.p.canonical(pred)==before and altered_target!=ref['transfers']['A']['comparison'])
    reject('overlapping training and validation is rejected',
           lambda:predict_reference(ref['transfers']['A']['frozen'],48,ref['training']['window']))
    reject('Boolean prediction operand is rejected',
           lambda:predict_reference(ref['transfers']['A']['frozen'],True,ref['validation']['window']))
    check('one-cut endpoint perturbations obey exact event-count bounds',bool(boundary))
    old=json.loads((HERE/'baseline/results/window_records.json').read_text())
    check('all inherited physical SI outputs remain unidentified',
          all(r['mapped']['physical_elapsed_seconds'] is None and r['mapped']['physical_rate_hz'] is None for rows in old.values() for r in rows.values()))
    check('background reference timings unchanged across retained coupling scenarios',
          all(records[k]['reference_cuts']==records['background_only']['reference_cuts'] for k in records))
    # Recalculate the earlier percentages from independent endpoint counts.
    oldbase=old['background_only']['prefix_4']['context']['record']['counts']
    oldcoupled=old['direct_pair']['prefix_4']['context']['record']['counts']
    quarter=old['direct_pair']['prefix_1']['context']['record']['counts']
    previous={'stale_baseline_gain':str(Q(oldbase['F0'],oldbase['A'])*oldcoupled['A']/oldcoupled['F0']-1),
              'stale_quarter_gain':str(Q(quarter['F0'],quarter['A'])*oldcoupled['A']/oldcoupled['F0']-1),
              'classification':'exact transfer discrepancies, not measured Cs accuracy or standard uncertainties'}
    check('prior transfer percentages reproduce exactly',previous['stale_baseline_gain']=='-1/54' and previous['stale_quarter_gain']=='-9/62')
    verify_inputs()
    check('scientific sources and replay adapter remain frozen',s.sha(Path(__file__))==frozen['adapter_code_sha256'])
    summaries={}
    for scenario in records:
        summaries[scenario]={}
        for width in (4,8,16,32):
            subset=[r for r in rolling if r['scenario']==scenario and r['reference_bips']==width]
            summaries[scenario][str(width)]={k:{'minimum':str(min(Q(r['fields'][k]['closures_per_F0_bip']) for r in subset)),
                                                   'maximum':str(max(Q(r['fields'][k]['closures_per_F0_bip']) for r in subset)),
                                                   'windows':len(subset)} for k in ('A','B','F1')}
    report={'software_validation':'pass','checks':checks,'check_count':len(checks),
            'admitted_split_windows':2*len(records),'admitted_directional_comparisons':6*len(records),
            'rolling_count_windows':len(rolling),'endpoint_perturbation_cases':sum(len(r['variants']) for r in boundary),
            'previous_discrepancies':previous,'rolling_summary':summaries,
            'fixed_transfer_claim':'fails held-out count validation for A and B in every retained scenario',
            'constant_cadence_count_rounding_claim':'rejected for A and B on complete reference-closure sample series',
            'independent_reference_evidence':False,'physical_Cs_calibration':False,
            'absolute_SI_anchor_status':'not established','physical_uncertainty':None,
            'scope':'retrospective exact diagnostics of the existing finite run; no future prediction or laboratory validation claimed',
            'frozen':frozen}
    write(args.output/'admitted_validation.json',records)
    write(args.output/'rolling_count_windows.json',rolling)
    write(args.output/'endpoint_perturbations.json',boundary)
    write(args.output/'report.json',report)
    print(json.dumps({'status':'pass','checks':len(checks),'anchor':'not established'}),flush=True)


if __name__=='__main__':main()

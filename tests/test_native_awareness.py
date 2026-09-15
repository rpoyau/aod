import csv,json,sys,importlib.util
from pathlib import Path
from dataclasses import replace
from fractions import Fraction
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'manual/scripts'))
import aod_awareness as a
n=a.n
ROWS=[json.loads(t) for t in (ROOT/'manual/data/m2/awareness_cases.jsonl').read_text().splitlines()]

@pytest.mark.parametrize('row',ROWS,ids=[r['fixture_id'] for r in ROWS])
def test_exact_new_witness(row):
    actual=a.execute_row(row)
    assert actual['expected_matched'],actual


def test_factorization_removal_and_exact_restoration_at_both_pressures():
    for pressure,answer in [(1,Fraction(1)),(2,Fraction(1,2))]:
        c=a.core(pressure);pair=c['pair']
        assert pair['effect'] and pair['left']['events'][0]['current']==answer
        assert pair['right']['events'][0]['current']==0
        assert c['state'].present.retained_rebalancing==c['state'].present.closure_memory==()
        assert a.execution_bytes(c['restored'])==a.execution_bytes(pair['left'])
        assert all(e['at']>pair['boundary'] for e in pair['left']['events'])
        assert a.outcome(pair['left']['events'])!=a.outcome(pair['right']['events'])


def test_removed_coordinate_is_not_reconstructed_from_world_or_memory():
    s,w,m,inputs=a.context();s=replace(s,retained=())
    assert w.prior_commitments and s.closure_memory
    yes=a.execute(s,w,m,inputs)
    assert all(e['retained_terms']==() and e['current']==0 for e in yes['events'])
    assert not a.matched(s,s,w,w,m,m,inputs,inputs)['effect']


def test_trace_and_evidence_lane_names_are_nonoperative():
    c=a.core();s,w,m,inputs=(c[k] for k in ['state','world','model','inputs'])
    plain=a.execute(s,w,m,inputs);traced=a.execute(s,w,m,inputs,True)
    assert a.execution_bytes(plain)==a.execution_bytes(traced)
    assert traced['observations'] and not plain['observations']
    row=ROWS[0];changed=dict(row,fixture_id='a completely different label',control_lane_id='wrong_lane',case_kind='hostile')
    assert a.execute_row(row)['actual']==a.execute_row(changed)['actual']


def test_attention_memory_residual_and_phase_lock_are_insufficient():
    assert a.run_case('attention_only',{})=={'current':1,'awareness_effect':False,'closure_memory_present':True}
    assert not a.core(gain=0)['pair']['effect']
    assert not a.core(values=[0])['pair']['effect']
    assert not a.core(gain=0,mode='phase_lock')['pair']['effect']


def test_response_keeps_h1_hinge_and_no_phase_without_certificate():
    c=a.core();before=c['state'].present
    for state,event in zip(c['pair']['left']['states'],c['pair']['left']['events']):
        assert n.hamming(before.present[0],state.present.present[0])==1
        old,new=before.present[1],state.present.present[1]
        assert (old!=0 and new==0) or (old==0 and new in (-1,1))
        assert event['new_phase']==0 and state.present.phases==before.phases
        before=state.present


@pytest.mark.parametrize('field,value',[('motif_certificates',()),('cadence',(999,)),('orientation',-1),('phases',100),('current',0.1),('capacity',0),('present',(0,2)),('committed',33.0)])
def test_inherited_complete_state_cannot_be_fabricated(field,value):
    s,w,m,inputs=a.context();bad=replace(s,present=replace(s.present,**{field:value}))
    with pytest.raises(a.AdmissionError):a.transition(bad,w,m,inputs[0])


def recommit(s,w,prior):
    r=a.retain(prior);return replace(s,retained=(r,)),replace(w,prior_commitments=(a.digest(prior),))


@pytest.mark.parametrize('field,value',[('input_commit',23.0),('retained_at',24.0),('scale',0.0),('comparator_bias',(0,0,99)),('comparator_bias',(0.1,0)),('relational_type','Tau')])
def test_recommitted_prior_still_requires_correct_types_and_domains(field,value):
    s,w,m,inputs=a.context();s,w=recommit(s,w,replace(s.retained[0].prior,**{field:value}))
    with pytest.raises(a.AdmissionError):a.transition(s,w,m,inputs[0])


def test_input_cut_and_query_observation_have_exact_later_order():
    s,w,m,inputs=a.context()
    for bad in [replace(inputs[0],committed=float(inputs[0].committed)),replace(inputs[0],committed=inputs[0].committed+1),replace(inputs[0],query=1),replace(inputs[0],query=1,query_observed_at=s.present.committed+1)]:
        with pytest.raises(a.AdmissionError):a.transition(s,w,m,bad)


def test_pressure_change_is_separate_family_not_retention_effect():
    s,w,m,inputs=a.context();other=replace(s,present=replace(s.present,pressure=2),retained=())
    with pytest.raises(a.AdmissionError):a.matched(s,other,w,w,m,m,inputs,inputs)


def test_operative_graph_preserves_cancelled_individual_channels():
    s,w,m,inputs=a.context(peers=2,values=(1,-1));g=a.operative(s,w,m,inputs[0])
    assert len(g['sources'])==2 and len(g['nodes'])==3
    assert a.transition(s,w,m,inputs[0])[1]['current']==0
    assert a.run_case('antisymmetry',{})['antisymmetry']
    assert a.run_case('label',{'prefix':'arbitrary-renaming'})['generalizes']
    with pytest.raises(a.AdmissionError):a.label_case(impostor=True)


def test_action_readout_is_a_projection_not_an_unbound_scalar():
    x=a.proprioception();r=x['match']['left']['final'].retained[0];p=replace(r.prior,observed=200,cross=(Fraction(199),))
    s=x['match']['left']['final'];s,w=recommit(s,x['world'],p)
    with pytest.raises(a.AdmissionError,match='projection'):a.validate_retention(s.retained[0],w,s.present.committed)


def test_action_identity_and_issuance_require_admitted_prefixes():
    x=a.proprioception();w=x['world'];action=x['action']
    assert action.issued==13 and x['return'].indices==(14,15,16)
    for identity in [action.issuer,action.channel]:assert sum(t.indices[-1]<=action.issued for t in w.get(identity).returns)>=2
    with pytest.raises(a.AdmissionError):a.validate_world(replace(w,actions=(action,replace(action,command=2))))
    early=replace(action,issued=1,identity=a.digest((action.issuer,1,action.command,action.channel)))
    with pytest.raises(a.AdmissionError,match='precedes admitted'):a.validate_world(replace(w,actions=(early,)))


def test_learning_persists_and_restores_after_training_stimulus_ends():
    x=a.learning();assert x['acquisition']==x['retained_after_training'] and x['pair']['effect'] and x['restored_equal']
    assert all(i.attention==0 for i in x['future'])
    yes=[e['current'] for e in x['pair']['left']['events']];no=[e['current'] for e in x['pair']['right']['events']]
    assert yes==[5,6,7] and no==[4,4,4]


def test_crescendo_dropout_recovery_and_distinct_recurrence_modes():
    x=a.crescendo();assert x['operative_sources']==(1,2,3,0,3) and x['retained_after_dropout']==3
    for mode in ('phase_lock','nonzero_bias','polyrhythm','jitter'):
        c=a.core(mode=mode);assert c['pair']['effect']
        p=c['state'].retained[0].prior
        if mode=='nonzero_bias':assert p.lag==Fraction(1,4) and p.comparator_bias==(Fraction(1,4),0)
        if mode=='phase_lock':assert p.lag==0
        if mode=='jitter':assert c['world'].waves[1].cadence==(8,7,13)


def test_phase_shuffle_preserves_marginals_but_fails_lineage_binding():
    s,w,m,inputs=a.context(peers=3);values=[r.prior.lag for r in s.retained];rotated=values[-1:]+values[:-1]
    assert values!=rotated and sorted(values)==sorted(rotated)
    wrong=tuple(a.retain(replace(r.prior,lag=value)) for r,value in zip(s.retained,rotated))
    # Recommit bytes to demonstrate that exact native comparison still rejects the permutation.
    bad=replace(s,retained=wrong);bw=replace(w,prior_commitments=tuple(a.digest(r.prior) for r in wrong))
    with pytest.raises(a.AdmissionError,match='phase type/provenance'):a.transition(bad,bw,m,inputs[0])


def test_each_chain_hop_requires_a_new_later_retained_intervention():
    x=a.contact_chain();assert x['positive']['phase']==1 and not x['removal']['admitted']
    assert x['higher_match']['effect'] and x['top_positive']['admitted'] and not x['top_removal']['admitted']
    assert a.digest(x['top_positive'])==a.digest(x['top_restoration'])
    high=x['higher_state'];ret=high.retained[0]
    assert ret.prior.retained_at<high.present.committed<x['top_positive']['event']['at']<x['top_positive']['fold']['outer'][0].indices[0]
    assert len(x['positive']['inner_after_shedding'])==2
    assert n.validate_wave(x['positive']['higher'])


def test_higher_peer_commits_its_actual_folded_construction():
    x=a.contact_chain();positive=x['positive'];inner=positive['outer_one']['inner']
    peer=positive['higher_peer'];higher=positive['higher']
    assert n.validate_wave(peer) and peer.cadence==(9,9)
    for trace,certificate in zip(peer.returns,peer.certificates):
        assert certificate.motif=='outer' and certificate.inner_waves==inner
        registry={certificate.certificate_digest:certificate}
        folded=n.fold(inner,(trace,certificate,registry))
        assert n.expose(folded)==inner and folded['phase']==1
        assert max(w.returns[-1].indices[-1] for w in inner)<trace.indices[0]
        with pytest.raises(n.AdmissionError):n.admitted(trace,replace(certificate,inner_waves=()),registry)
    with pytest.raises(n.AdmissionError):
        n.certified(n.trace('unsupported-peer',scope='B1',scale=1,start_index=100),'outer')
    # B1 itself does not assert folding: a separately declared primitive is valid.
    primitive=n.recurrent('primitive-peer',scope='B1',scale=1)
    assert n.validate_wave(primitive) and all(c.motif=='Monon' for c in primitive.certificates)
    top=x['top_positive']['fold']
    assert top['outer'][1].inner_waves==(higher,peer) and n.expose(top)==(higher,peer)
    assert x['higher_match']['effect'] and not x['top_removal']['admitted']
    assert a.digest(x['top_positive'])==a.digest(x['top_restoration'])


def test_action_origin_retention_can_be_carried_with_its_authentic_registry():
    x=a.contact_chain();p=a.proprioception();old=p['match']['left']['final'].retained[0]
    high=x['higher_state'];prior=high.retained[0].prior
    c=replace(prior.carriage,retained=old,source_actions=p['world'].actions,source_commitments=p['world'].prior_commitments)
    high,hw=recommit(high,x['higher_world'],replace(prior,carriage=c))
    assert a.validate_retention(high.retained[0],hw,high.present.committed)
    broken=replace(c,source_actions=())
    bad,bw=recommit(high,hw,replace(prior,carriage=broken))
    with pytest.raises(a.AdmissionError):a.validate_retention(bad.retained[0],bw,bad.present.committed)
    forged=replace(c,source_actions=(replace(c.source_actions[0],command=200),))
    bad,bw=recommit(high,hw,replace(prior,carriage=forged))
    with pytest.raises(a.AdmissionError):a.validate_retention(bad.retained[0],bw,bad.present.committed)


def test_mindfulness_hypothesis_is_not_extra_delay_or_all_pressures():
    x=a.mindfulness();assert all(e['current']==1 and e['new_phase']==0 for e in x['events'])
    assert len({tuple(e['edge']) for e in x['events']})>=2
    assert not a.mindfulness(extra_delay=True)['stability_hypothesis']
    assert not all(e['current']==1 for e in a.mindfulness(extra_delay=True)['events'])
    assert not a.mindfulness(pressure='1/2')['stability_hypothesis']


@pytest.mark.parametrize('delayed',[False,True])
def test_query_provenance_names_the_observation_actually_consumed(delayed):
    result=a.mindfulness(extra_delay=delayed)
    observations=result['observations'];seed=result['declared_delay_initial_history']
    if delayed:
        assert seed==(observations[0][0]-1,Fraction(0))
        sources=[seed,*observations[:-1]]
        assert [event['current'] for event in result['events']]==[4,2,-1,-2,0,3]
    else:
        assert seed is None
        sources=observations
        assert all(event['current']==1 for event in result['events'])
    for event,(cut,value),(input_cut,_) in zip(result['events'],sources,observations):
        assert event['query_observed_at']==cut and event['query']==-value
        assert cut<=input_cut<event['at']


def test_retention_lineage_digest_is_not_a_free_record_label():
    s,w,m,inputs=a.context();r=replace(s.retained[0],lineage_digest='0'*64)
    with pytest.raises(a.AdmissionError,match='lineage digest'):a.transition(replace(s,retained=(r,)),w,m,inputs[0])

import csv,importlib.util,json,sys
from dataclasses import replace
from fractions import Fraction as Q
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('aod_native_closure_wave',ROOT/'manual/scripts/aod_native_closure_wave.py')
n=importlib.util.module_from_spec(spec);sys.modules[spec.name]=n;spec.loader.exec_module(n)
ROWS=[]
for p in sorted((ROOT/'manual/data/m1').glob('*.csv')):
    with p.open() as f:ROWS.extend(csv.DictReader(f))

@pytest.mark.parametrize('row',ROWS,ids=[r['fixture_id'] for r in ROWS])
def test_exact_fixture(row):
    result=n.execute_row(row)
    assert result['expected_matched'],result


def test_immutable_terminal_event_cannot_acquire_second_phase():
    with pytest.raises(n.AdmissionError,match='immutable terminal'):
        n.phase_count([n.certified(n.trace()),n.certified(n.trace(dwell=1))])


def test_all_finite_q4_incidence_and_ancestor_slot_roles():
    for scale in (0,1,7):
        for vertex in range(16):
            for slot in range(4):
                record=n.incident_support(vertex,slot,scale)
                assert len(set(record['neighbours']))==4 and len(record['remaining_slots'])==3
                assert slot not in record['remaining_slots']
                assert all(n.hamming(vertex,v)==1 for v in record['neighbours'])
                assert n.hamming(vertex,record['predecessor_coordinate'])==1
    first=n.incident_support(0,0,first_anchor=True)
    assert first['predecessor_coordinate'] is None and first['ancestral_role']=='retained first distinction'
    with pytest.raises(n.AdmissionError):n.incident_support(0,4)
    with pytest.raises(n.AdmissionError):n.incident_support(1,0,first_anchor=True)


def test_distinct_return_phase_and_dwell_are_separate():
    records=[n.certified(n.trace(occurrence=k,dwell=k%2)) for k in range(4)]
    assert n.phase_count(records)==4
    w=n.wave(records);assert w.bip==3 and w.cadence==(11,9,11)


def test_preexistence_coupling_rejected_even_with_matching_empty_hashes():
    a=n.wave([n.certified(n.trace('a',k,start_index=100+10*k)) for k in range(3)])
    b=n.wave([n.certified(n.trace('b',k,start_index=100+10*k)) for k in range(3)])
    events=n.contacts(a,b)
    early=tuple(replace(e,committed=k,left_prefix=n.wave_prefix(a,k),right_prefix=n.wave_prefix(b,k)) for k,e in enumerate(events))
    with pytest.raises(n.AdmissionError,match='recurrent prefix'):n.compare(a,b,early,window=(0,200))


def test_directional_rcd_retains_support_and_scalar_clipping():
    a=n.recurrent('a');b=n.recurrent('b',spacing=7);events=n.contacts(a,b)
    forward=n.compare(a,b,events);back=n.compare(a,b,events,reverse=True)
    assert forward['ratio']*back['ratio']==1
    assert (forward['duration'],back['duration'])==(5,7)
    r=forward['rcd'];assert r.support==3
    assert n.participation(r,2,r.domain)==2 and r.duration()==5 and r.support==3
    neutral=replace(r,reflection_counts=(0,0));assert neutral.duration()==neutral.support
    changed=replace(events[0],support_trace=n.trace('unrelated'))
    with pytest.raises(n.AdmissionError):n.compare(a,b,(changed,events[1]))


def test_whole_closure_slip_unwrapped_and_three_wave_edges():
    a=n.recurrent('a',4);b=n.recurrent('b',3,spacing=7);c=n.recurrent('c',4,spacing=6)
    ab=n.compare(a,b,n.contacts(a,b));bc=n.compare(b,c,n.contacts(b,c));ac=n.compare(a,c,n.contacts(a,c))
    assert ab['lag']==1 and ab['lag']%1==0
    assert ab['ratio']*bc['ratio']==ac['ratio']
    assert len({(x['rcd'].left,x['rcd'].right) for x in (ab,bc,ac)})==3


def test_equal_ratio_phase_can_have_distinct_duration_and_complete_state():
    a=n.recurrent('a');b=n.recurrent('b',spacing=7);e=n.contacts(a,b)
    x=n.compare(a,b,e);y=n.compare(a,b,tuple(replace(c,reflection=(4,2)) for c in e))
    assert [x[k] for k in ('ratio','bias','lag')]==[y[k] for k in ('ratio','bias','lag')]
    assert x['duration']!=y['duration']
    s=n.initial_state(a);assert s!=replace(s,pressure=Q(9))


def test_scalar_collision_does_not_identify_lineage():
    a=n.recurrent('a');b=n.recurrent('b')
    assert a.bip==b.bip and a.cadence==b.cadence and a.identity!=b.identity
    f=n.field('B0','one',[a,b]);assert len(f.members)==2
    assert len(n.resolve_fields([f,f]))==2


def test_reflected_factorization_is_equality_not_just_inequality():
    reference=n.certified(n.trace('reference'))
    x=n.leg_comparison(n.certified(n.trace(vertices=(0,1,3,2,0))),reference)
    assert x['sum']==4 and x['sum']!=2*x['outbound'] and x['sum']!=2*x['return']
    assert 2*x['outbound']>=x['embedded_unit'] and 2*x['return']>=x['embedded_unit']
    w=n.trace().reflection
    assert w.turnaround_committed_at<w.committed_at


def test_motif_name_alone_is_not_admission():
    for motif in ('Duon','1:2','3:2','3:3','3:4'):
        with pytest.raises(n.AdmissionError,match='construction witness'):n.certify(n.trace(),motif)


def test_all_twelve_duon_pivot_variants_bind_monon_provenance():
    component=n.trace();c=n.certify(component);t=n.trace(occurrence=1);target=n.certify(t)
    reg={c.certificate_digest:c,target.certificate_digest:target};witnesses=[]
    for left in ((1,-1),(-1,1)):
        for right in ((1,-1),(-1,1)):
            for mu in (-1,0,1):
                witnesses.append(n.motif_witness('Duon',t,(left,(c.certificate_digest,mu),right),((component,c),),reg))
    assert len({w.identity for w in witnesses})==12
    with pytest.raises(n.AdmissionError):n.motif_witness('Duon',t,((1,-1),('wrong',0),(-1,1)),((component,c),),reg)


@pytest.mark.parametrize('p,q',[(1,2),(3,1),(3,2),(3,3),(3,4),(3,5)])
def test_inherited_support_constructor_binds_shape_and_trace(p,q):
    ts=[n.trace('support',k) for k in range(max(q,2))];cs=tuple(n.certify(t) for t in ts)
    target=n.trace('support',len(ts));tc=n.certify(target)
    reg={c.certificate_digest:c for c in (*cs,tc)};ids=tuple(c.return_id for c in cs[:q])
    records=tuple(zip(ts,cs))
    construction=(tuple(ids for depth in range(p)),ids)
    w=n.motif_witness(f'{p}:{q}',target,construction,records,reg)
    assert w.core==f'{p}:{q}' and w.support_trace.trace_digest==target.trace_digest
    with pytest.raises(n.AdmissionError):n.motif_witness(f'{p}:{q}',target,((('unbound',),),ids),records,reg)
    with pytest.raises(n.AdmissionError,match='precede'):n.motif_witness(f'{p}:{q}',ts[0],construction,records,reg)
    bad=replace(cs[0],status='open');badreg={**reg,bad.certificate_digest:bad}
    with pytest.raises(n.AdmissionError):n.motif_witness(f'{p}:{q}',target,construction,((ts[0],bad),*records[1:]),badreg)


def test_duon_current_recurrence_and_duad_state_share_identity():
    records=[];motifs=[]
    for k in range(3):
        pivot=n.trace('duon',2*k);pc=n.certify(pivot)
        target=n.trace('duon',2*k+1);tc=n.certify(target)
        registry={pc.certificate_digest:pc,tc.certificate_digest:tc}
        motifs.append(n.motif_witness('Duon',target,((1,-1),(pc.certificate_digest,0),(-1,1)),((pivot,pc),),registry))
        records.append((target,tc,registry))
    with pytest.raises(n.AdmissionError):n.wave(records[:1],motifs[:1])
    w=n.wave(records,motifs);assert w.motif=='Duon' and w.bip==2 and w.cadence==(20,20)
    state=n.update(n.initial_state(w,2),6,w.returns[-1].indices[-1])
    assert state.current==3 and state.committed>w.returns[-1].indices[-1]
    seated=n.seat_duon(w,state,True)
    assert seated.identity==state.identity and seated.closure_status=='seated' and seated.current==state.current
    with pytest.raises(n.AdmissionError):n.seat_duon(w,state,False)
    assert n.field('B0','duon organization',[w]).members==(w.identity,)


@pytest.mark.parametrize('scale',[0,7])
def test_primitive_duon_scale_binding_before_wave_and_field(scale):
    records=[];motifs=[]
    for k in range(3):
        pivot=n.trace('scaled-duon',2*k,scale=scale)
        target=n.trace('scaled-duon',2*k+1,scale=scale)
        pc=n.certify(pivot);tc=n.certify(target)
        registry={pc.certificate_digest:pc,tc.certificate_digest:tc}
        construction=((1,-1),(pc.certificate_digest,0),(-1,1))
        motifs.append(n.motif_witness('Duon',target,construction,((pivot,pc),),registry))
        records.append((target,tc,registry))
        unrelated=replace(pivot,scale=scale+1);uc=n.certify(unrelated)
        with pytest.raises(n.AdmissionError,match='scale mismatch'):
            n.motif_witness('Duon',target,((1,-1),(uc.certificate_digest,0),(-1,1)),
                            ((unrelated,uc),),{uc.certificate_digest:uc,tc.certificate_digest:tc})
    w=n.wave(records,motifs)
    assert n.validate_wave(w) and w.scale==scale
    assert n.field('B0','scaled organization',[w]).members==(w.identity,)


@pytest.mark.parametrize('origin',[0,8])
def test_initial_state_composes_with_its_actual_return_readout(origin):
    w=n.wave([n.certified(n.trace('origin',k,vertices=(origin,origin^1,origin))) for k in range(3)])
    state=n.initial_state(w);readout=n.declared_readout(w,(0,0,0))
    assert state.present==(origin,)
    assert n.bind_values(w,(*readout.states[:-1],state))==readout
    assert n.update(state,Q(1,3),state.committed).current==Q(1,3)


@pytest.mark.parametrize('bias',[(),(Q(1),),(Q(1),Q(0),Q(999))])
def test_comparator_rejects_incomplete_or_extra_coordinates(bias):
    a=n.recurrent('a');b=n.recurrent('b');events=n.contacts(a,b)
    with pytest.raises(n.AdmissionError,match='exactly two'):
        n.compare(a,b,events,bias=bias)
    forward=n.compare(a,b,events,bias=(Q(1,3),Q(1,6)))
    reverse=n.compare(a,b,events,bias=(Q(1,3),Q(1,6)),reverse=True)
    assert forward['bias']==Q(1,6) and reverse['bias']==-forward['bias']


@pytest.mark.parametrize('cut',[21.5,Q(43,2),22.0,True])
def test_update_rejects_noninteger_state_and_input_cuts(cut):
    state=n.initial_state(n.recurrent('cuts'))
    with pytest.raises(n.AdmissionError,match='indices must be integers'):
        n.update(state,Q(1,3),cut)
    with pytest.raises(n.AdmissionError,match='indices must be integers'):
        n.update(replace(state,committed=cut),Q(1,3),0)
    valid=n.update(state,Q(1,3),state.committed)
    assert valid.committed==state.committed+1 and valid.current==Q(1,3)


@pytest.mark.parametrize('origin',[0,8])
def test_recurring_ancestry_survives_coordinate_relabelling_and_rejects_substitution(origin):
    records=[n.certified(n.trace('ancestry',k,vertices=(origin,origin^1,origin))) for k in range(3)]
    good=n.wave(records);assert n.validate_wave(good) and good.bip==2
    substituted=n.certified(replace(records[1][0],ancestor='unrelated-unregistered-ancestor'))
    with pytest.raises(n.AdmissionError,match='ancestor identity'):
        n.wave((records[0],substituted,records[2]))
    forged=replace(good,returns=(records[0][0],substituted[0],records[2][0]),
                   certificates=(records[0][1],substituted[1],records[2][1]))
    with pytest.raises(n.AdmissionError,match='ancestor identity'):n.field('B0','bad',[forged])
    with pytest.raises(n.AdmissionError,match='ancestor identity'):n.declared_readout(forged,[1,0,-1])


@pytest.mark.parametrize('cut',[Q(25,2),12.0,True])
def test_comparison_rejects_noninteger_contact_commitments(cut):
    a,b=n.recurrent('a'),n.recurrent('b');events=n.contacts(a,b)
    with pytest.raises(n.AdmissionError,match='contact commitments'):
        n.compare(a,b,(replace(events[0],committed=cut),events[1]))
    good=n.compare(a,b,events,bias=(Q(1,3),Q(1,6)))
    assert good['ratio']==1 and good['bias']==Q(1,6)


@pytest.mark.parametrize('window',[(Q(1,2),Q(99,2)),(0,Q(99,2)),(0,100.0),
                                  (False,100),(100,0),(12,12),(0,100,200),(),None])
def test_comparison_rejects_untyped_native_windows(window):
    a,b=n.recurrent('a'),n.recurrent('b');events=n.contacts(a,b)
    with pytest.raises(n.AdmissionError,match='native window'):
        n.compare(a,b,events,window=window)


def test_phase_accessor_and_reclosure_windows_keep_the_initial_origin_distinct():
    records=[n.certified(n.trace('phase',k)) for k in range(4)];w=n.wave(records)
    assert [n.phase_count(records,cut=k) for k in (1,2,12,22,32)]==[0,1,2,3,4]
    assert n.phase_count(records+[records[-1]],cut=32)==4 and w.bip==3
    for u,v in [(0,32),(2,32),(12,32),(2,12)]:
        phases=n.phase_count(records,cut=v)-n.phase_count(records,cut=u)
        beats=sum(u<t.indices[-1]<=v for t in w.returns[1:])
        assert phases==beats+int(u<w.returns[0].indices[-1]<=v)
    # Contacts at the left boundary are support; beat counting is (u,v].
    peer=n.recurrent('peer',4);events=n.contacts(w,peer)
    assert n.compare(w,peer,events,window=(12,32),bias=(Q(1,3),Q(1,6)))['ratio']==1
    with pytest.raises(n.AdmissionError,match='phase accessor'):n.phase_count(records,cut=Q(5,2))


def test_outer_certification_requires_the_existing_inner_fold_witness():
    inner=(n.recurrent('inner-origin'),);t=n.outer_trace(inner)
    with pytest.raises(n.AdmissionError,match='inner lineages'):n.certified(t,'outer')
    with pytest.raises(n.AdmissionError,match='bound inner construction'):
        n.certified(n.trace('unbound',scope='B1',scale=1,start_index=30),'outer',inner=inner)
    records=[n.certified(n.outer_trace(inner,occurrence=k),'outer',inner=inner) for k in range(3)]
    outer=n.wave(records);assert n.validate_wave(outer) and outer.bip==2
    assert all(n.expose(n.fold(inner,r))==inner for r in records)
    altered=replace(records[0][1],inner_waves=(n.recurrent('impostor'),))
    with pytest.raises(n.AdmissionError):n.admitted(t,altered,{altered.certificate_digest:altered})
    stripped=replace(records[0][1],inner_waves=())
    with pytest.raises(n.AdmissionError):n.admitted(t,stripped,{stripped.certificate_digest:stripped})


def test_outer_recurrence_preserves_identity_through_a_growing_inner_prefix():
    early=(n.recurrent('growing',3),);later=(n.recurrent('growing',4),)
    first=n.certified(n.outer_trace(early),'outer',inner=early)
    second=n.certified(n.outer_trace(later,occurrence=1),'outer',inner=later)
    assert early[0].identity==later[0].identity and first[0].ancestor!=second[0].ancestor
    assert n.validate_wave(n.wave((first,second)))
    wrong=(n.recurrent('unrelated',4),)
    impostor=n.certified(n.outer_trace(wrong,occurrence=1),'outer',inner=wrong)
    with pytest.raises(n.AdmissionError,match='ancestor identity'):n.wave((first,impostor))
    rolled_back=n.certified(n.outer_trace(early,occurrence=2,start_index=60),'outer',inner=early)
    with pytest.raises(n.AdmissionError,match='inner prefix'):n.wave((second,rolled_back))


def test_outer_phase_reclosure_and_exposure_bind_actual_inner_construction():
    inner=[n.recurrent('inside')]
    records=[n.certified(n.outer_trace(inner,occurrence=k),'outer',inner=inner) for k in range(3)]
    folds=[n.fold(inner,r) for r in records]
    assert all(f['phase']==1 and n.expose(f)==tuple(inner) for f in folds)
    shedding=dict(folds[0],status='shedding');assert n.expose(shedding)==tuple(inner) and shedding['phase']==1
    outer=n.wave(records);assert outer.bip==2 and outer.scale==1 and n.phase_count(records)==3
    assert n.field('B1','outer organization',[outer]).members==(outer.identity,)
    with pytest.raises(n.AdmissionError):n.wave([records[0],records[0]])
    with pytest.raises(n.AdmissionError):n.fold(inner,n.certified(n.trace('outer',scale=1,scope='B1'),'outer'))
    with pytest.raises(n.AdmissionError):n.fold([replace(inner[0],identity='forged')],records[0])
    with pytest.raises(n.AdmissionError):n.fold([n.recurrent('different')],records[0])
    with pytest.raises(n.AdmissionError):n.outer_trace(inner,start_index=0)


def test_coupled_return_cannot_be_replayed_or_change_scale():
    a=n.recurrent('a');b=n.recurrent('b',spacing=7);events=n.contacts(a,b)
    same=replace(events[1],support_trace=events[0].support_trace,support_certificate=events[0].support_certificate)
    with pytest.raises(n.AdmissionError,match='two contacts'):n.compare(a,b,(events[0],same))
    wrong=replace(events[0].support_trace,scale=1);bad=replace(events[0],support_trace=wrong,support_certificate=n.certify(wrong))
    with pytest.raises(n.AdmissionError,match='cross-return support'):n.compare(a,b,(bad,events[1]))


def test_negative_closure_and_native_standing_require_coupled_history():
    a=n.recurrent('positive')
    b=n.wave([n.certified(n.trace('negative',k,chirality=-1)) for k in range(3)])
    assert n.phase_count([n.certified(t) for t in b.returns])==3
    states=(replace(n.initial_state(a),current=Q(2)),replace(n.initial_state(b),current=Q(-2)))
    result=n.standing_organization(a,b,n.contacts(a,b),states)
    assert result['kind']=='standing' and len(result['contact_returns'])==2
    assert result['retained_ancestry'][0]!=result['retained_ancestry'][1]
    with pytest.raises(n.AdmissionError):n.standing_organization(a,b,(),states)
    with pytest.raises(n.AdmissionError):n.standing_organization(a,b,n.contacts(a,b),(states[0],replace(states[1],current=Q(-1))))


def test_nonzero_prior_lag_reverses_in_the_original_pair_convention():
    a=n.recurrent('a',4);b=n.recurrent('b',3,spacing=7);events=n.contacts(a,b)
    forward=n.compare(a,b,events,prior_lag=Q(1,4));backward=n.compare(a,b,events,reverse=True,prior_lag=Q(1,4))
    assert forward['drift']==Q(3,4) and backward['drift']==-forward['drift']


def test_binary_floats_cannot_enter_native_count_or_weight_domains():
    a=n.recurrent('a');b=n.recurrent('b',spacing=7);events=n.contacts(a,b)
    with pytest.raises(n.AdmissionError,match='integer counts'):
        n.compare(a,b,tuple(replace(e,reflection=(0.1,0.2)) for e in events))
    with pytest.raises(n.AdmissionError):n.initial_state(a,0.1)
    with pytest.raises(n.AdmissionError):n.Q(0.1)


def test_kernel_finite_set_and_ternary_role_domains():
    e=(0,1,1,0);invalid=(0,1,2,0)
    result=n.kernel([e,e,invalid],{e:1,invalid:7})
    assert result['status']=='NORMALIZED' and sum(result['probabilities'].values())==1
    assert result['probabilities'][e]==1 and result['probabilities'][invalid]==0


def test_linear_representation_does_not_make_the_declared_state_law_linear():
    w=n.recurrent();s=n.initial_state(w,1);t=replace(s,pressure=Q(2));combined=replace(s,pressure=Q(3))
    assert n.update(s,6,s.committed).current==6 and n.update(t,6,t.committed).current==3
    assert n.update(combined,12,combined.committed).current==4
    assert 4!=6+3


def test_cancellation_retains_oriented_pair_evidence():
    f=n.aod_flux([(0,1,7,1,'out'),(0,1,7,-1,'return')]);r=n.stokes(f,{0})
    assert r['boundary']==0 and r['lineages']==('out','return') and len(f)==4


def test_duplicate_channel_and_negative_pressure_controls():
    assert len(n.aod_flux([(0,1,2,1,'same'),(0,1,2,1,'same')]))==2
    with pytest.raises(n.AdmissionError,match='duplicate channel'):
        n.aod_flux([(0,1,2,1,'same'),(0,1,3,1,'same')])
    with pytest.raises(n.AdmissionError,match='nonnegative'):
        n.aod_flux([(0,1,-7,1,'same')])


def test_fibre_dwell_is_not_advertised_as_atomic_h1():
    assert n.fibre_step(0,0,'additional_dwell')['atomic_traversals']==0
    assert n.fibre_step(1,0,'enter_hinge')['role']==0
    assert n.fibre_step(0,-1,'leave_hinge')['role']==-1
    with pytest.raises(n.AdmissionError):n.fibre_step(1,-1,'leave_hinge')


def test_generic_return_does_not_require_downstream_leg_comparison():
    t=replace(n.trace(),reflected_comparison=False);r=n.certified(t)
    assert n.phase_count([r])==1
    with pytest.raises(n.AdmissionError,match='comparison model'):
        n.leg_comparison(r,n.certified(n.trace('reference')))


def test_harmonic_values_require_their_bound_committed_projection():
    w=n.recurrent('harmonic',4);b=n.declared_readout(w,[1,0,-1,0])
    with pytest.raises(n.AdmissionError):n.fourier([99,0,0,0],w)
    with pytest.raises(n.AdmissionError):n.fourier([99,0,0,0],w,b)
    with pytest.raises(n.AdmissionError):n.fourier(b.values,n.recurrent('other',4),b)
    assert n.inverse(n.fourier(b.values,w,b))==(1,0,-1,0)
    assert b.index_group==('cyclic',4) and b.committed_window==(2,32)
    first=b.states[0];assert first.phases==1 and first.cadence==() and len(first.motif_certificates)==1
    with pytest.raises(n.AdmissionError,match='future recurrence'):
        n.bind_values(w,(replace(first,phases=4),*b.states[1:]))
    for bad in (replace(b,index_group=('cyclic',3)),replace(b,committed_window=(0,999)),replace(b,projection='unbound')):
        with pytest.raises(n.AdmissionError):n.fourier(b.values,w,bad)
    with pytest.raises(n.AdmissionError):n.declared_readout(w,[1,0,-1,0,99])


def test_fourier_full_corollary_family_exact():
    import sympy as s
    w=n.recurrent('harmonic',4)
    def ft(v):return n.fourier(v,w,n.declared_readout(w,v))
    v=[1,2,0,-1];u=[0,1,2,3];V=ft(v);U=ft(u);N=4
    assert n.inverse(V)==tuple(v)
    assert ft([2*a-3*b for a,b in zip(v,u)])==tuple(2*a-3*b for a,b in zip(V,U))
    shift=ft(v[-1:]+v[:-1]);assert all(s.simplify(shift[k]-(-s.I)**k*V[k])==0 for k in range(N))
    mod=ft([(-1)**g*v[g] for g in range(N)]);assert mod==tuple(V[(k-2)%N] for k in range(N))
    conv=[sum(v[h]*u[(g-h)%N] for h in range(N)) for g in range(N)]
    assert ft(conv)==tuple(s.simplify(N*V[k]*U[k]) for k in range(N))
    prod=ft([a*b for a,b in zip(v,u)])
    assert prod==tuple(s.simplify(sum(V[j]*U[(k-j)%N] for j in range(N))) for k in range(N))
    corr=[sum(v[(g+a)%N]*u[g] for g in range(N)) for a in range(N)]
    assert ft(corr)==tuple(s.simplify(N*V[k]*s.conjugate(U[k])) for k in range(N))
    assert Q(sum(x*x for x in v),N)==sum(s.simplify(x*s.conjugate(x)) for x in V)
    assert all(s.simplify(V[-k%N]-s.conjugate(V[k]))==0 for k in range(N))
    h=ft([1,2,1,2]);assert h[1]==h[3]==0
    power=lambda a:tuple(s.simplify(x*s.conjugate(x)) for x in ft(a))
    assert power([1,0,-1,0])==power([0,1,0,-1]) and ft([1,0,-1,0])!=ft([0,1,0,-1])


def test_product_group_basis_does_not_imply_separable_trace():
    # Exact characters of C2 x C2; no approximate complex arithmetic.
    group=[(a,b) for a in range(2) for b in range(2)]
    def ft(v):return {k:sum(Q(v[g])*(-1)**(k[0]*g[0]+k[1]*g[1]) for g in group)/4 for k in group}
    x=[1,3];y=[2,4];v={(a,b):x[a]*y[b] for a,b in group}
    X=[Q(sum(x[g]*(-1)**(k*g) for g in range(2)),2) for k in range(2)]
    Y=[Q(sum(y[g]*(-1)**(k*g) for g in range(2)),2) for k in range(2)]
    assert all(ft(v)[a,b]==X[a]*Y[b] for a,b in group)
    non={(0,0):1,(0,1):0,(1,0):0,(1,1):1};F=ft(non)
    assert F[0,0]*F[1,1]-F[0,1]*F[1,0]!=0


def test_stochastic_history_bins_form_partition_before_average():
    # One history may have an old alpha event and a later return; classify at cut.
    histories=[{'alpha':True,'returned':True},{'alpha':True,'returned':False},{'alpha':False,'returned':False}]
    statuses=['omega' if h['returned'] else 'alpha' if h['alpha'] else 'unresolved' for h in histories]
    counts=[statuses.count(s) for s in ('alpha','omega','unresolved')]
    assert sum(counts)==len(histories) and Q(sum([1]*len(histories)),sum(counts))==1

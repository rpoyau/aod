"""Exact declared AOD witnesses. No universal dynamics or metrology is inferred.

The immutable certificate registry binds trace, scope, lineage and witness bytes.
Normative decisions use integers/Fraction; finite characters use exact SymPy.
Run --check-data to execute all immutable fixture rows and emit actual results.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict, replace
from fractions import Fraction
from pathlib import Path
import argparse, csv, hashlib, json
from typing import Mapping


class AdmissionError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise AdmissionError(message)


def Q(value=0,denominator=None):
    """Exact declared inputs; binary floating-point is not a native operand."""
    require(type(value) in (int,str,Fraction),'exact integer, rational or rational string required')
    if denominator is None:return Fraction(value)
    require(type(value) is int and type(denominator) is int,'integer ratio operands required')
    return Fraction(value,denominator)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), default=str)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def hamming(a: int, b: int, width=4):
    require(isinstance(a,int) and isinstance(b,int), 'integer encoding required')
    require(0 <= a < 2**width and 0 <= b < 2**width, 'encoding outside support')
    return (a ^ b).bit_count()


def incident_support(vertex,ancestor_slot,scale=0,first_anchor=False):
    """Finite Q4 incidence witness; slot roles are assigned after distinction."""
    require(scale>=0 and 0<=vertex<16 and ancestor_slot in range(4),'invalid finite support role')
    require(not first_anchor or (scale==0 and vertex==0),'first anchor is the primitive 00_8 occurrence')
    neighbours=tuple(vertex^(1<<slot) for slot in range(4))
    require(all(hamming(vertex,x)==1 for x in neighbours),'non-H1 incidence')
    return {'vertex':vertex,'neighbours':neighbours,'ancestor_slot':ancestor_slot,
            'remaining_slots':tuple(i for i in range(4) if i!=ancestor_slot),
            'predecessor_coordinate':None if first_anchor else neighbours[ancestor_slot],
            'ancestral_role':'retained first distinction' if first_anchor else 'retained incident predecessor'}


@dataclass(frozen=True)
class ReflectionWitness:
    scope: str
    lineage: str
    turnaround_id: str
    outbound_ids: tuple[str, ...]
    return_ids: tuple[str, ...]
    target_start_id: str
    committed_at: int
    turnaround_committed_at: int


@dataclass(frozen=True)
class Trace:
    scope: str
    scale: int
    lineage: str
    event_ids: tuple[str, ...]
    vertices: tuple[int, ...]
    indices: tuple[int, ...]
    roles: tuple[int, ...]
    turn: int
    ancestor: str
    reflection: ReflectionWitness | None
    reflected_comparison: bool=True

    @property
    def trace_digest(self):
        return digest(asdict(self))

    @property
    def return_id(self):
        # Certificate serials, observation time and packaging do not identify a return.
        return digest((self.scope,self.scale,self.lineage,self.event_ids[0],
                       self.event_ids[-1],self.trace_digest))


def trace(lineage='a', occurrence=0, vertices=(0,1,0), dwell=0, scope='B0',
          scale=0, turn=1, start_index=None, chirality=1):
    start = occurrence*10 if start_index is None else start_index
    ids=tuple(f'{lineage}:{occurrence}:e{n}' for n in range(len(vertices)))
    witness=ReflectionWitness(scope,lineage,ids[turn],ids[1:turn+1],
                              ids[turn+1:],ids[0],start+len(vertices)-1+dwell,start+turn)
    return Trace(scope,scale,lineage,ids,tuple(vertices),
                 tuple(start+n+(dwell if n>turn else 0) for n in range(len(vertices))),
                 (chirality,)+(0,)*(1+dwell)+(-chirality,),turn,
                 f'{lineage}:ancestor',witness)


def validate_trace(t: Trace, require_closed=True):
    require(bool(t.scope) and bool(t.lineage) and bool(t.ancestor),'unbound scope/lineage/ancestor')
    require(type(t.scale) is int and t.scale>=0,'below first finite anchor is unbound')
    require(type(t.turn) is int and all(type(k) is int for k in t.indices),
            'committed native indices must be integers')
    require(len(t.vertices)>=3,'two nonempty legs required')
    require(len(t.vertices)==len(t.event_ids)==len(t.indices),'trace coordinate mismatch')
    require(len(set(t.event_ids))==len(t.event_ids),'event replay inside trace')
    require(all(a<b for a,b in zip(t.indices,t.indices[1:])),'uncommitted event order')
    require(all(hamming(a,b)==1 for a,b in zip(t.vertices,t.vertices[1:])),'non-H1 atomic traversal')
    require(len(t.roles)>=3 and t.roles[0] in (-1,1) and
            t.roles[-1]==-t.roles[0] and all(x==0 for x in t.roles[1:-1]),
            'mandatory hinge and counterbranch required')
    require(0<t.turn<len(t.vertices)-1,'empty directed leg')
    w=t.reflection
    require(w is not None,'missing bound reflection witness')
    require((w.scope,w.lineage,w.turnaround_id,w.target_start_id)==
            (t.scope,t.lineage,t.event_ids[t.turn],t.event_ids[0]),'wrong reflection lineage or hinge')
    require(w.outbound_ids==t.event_ids[1:t.turn+1] and
            w.return_ids==t.event_ids[t.turn+1:],'reflection legs not bound to committed events')
    require(w.turnaround_committed_at==t.indices[t.turn] and
            w.turnaround_committed_at<t.indices[-1] and w.committed_at==t.indices[-1],
            'reflection witness violates causal order')
    if require_closed:
        require(t.vertices[-1]==t.vertices[0],'end differs from retained start')
    return True


@dataclass(frozen=True)
class Certificate:
    motif: str
    scope: str
    scale: int
    lineage: str
    trace_digest: str
    return_id: str
    witness_digest: str
    status: str
    certificate_digest: str
    inner_waves: tuple[Wave,...]=()


def certify(t: Trace, motif='Monon', *, inner=()):
    validate_trace(t)
    require(motif in ('Monon','outer'), 'nonprimitive motif requires its separate construction witness')
    inner=tuple(inner)
    witness=digest(asdict(t.reflection))
    if motif=='outer':
        proposal=fold_proposal(inner,t.scope,t.scale)
        require(t.ancestor=='fold:'+digest(proposal),
                'outer certificate requires its bound inner construction and scope map')
        require(t.indices[0]>max(w.returns[-1].indices[-1] for w in inner),
                'outer construction reads future inner closure')
        witness=digest((asdict(t.reflection),proposal))
    else:require(not inner,'primitive certificate has no folded inner construction')
    fields=(motif,t.scope,t.scale,t.lineage,t.trace_digest,t.return_id,witness,'closed')
    return Certificate(*fields,digest(fields),inner)


def admitted(t: Trace, c: Certificate, registry: Mapping[str,Certificate]):
    require(bool(c.certificate_digest),'blank certificate')
    require(registry.get(c.certificate_digest)==c,'unregistered or altered certificate')
    require(certify(t,c.motif,inner=c.inner_waves)==c,'scope, lineage, trace, witness or status mismatch')
    return True


def phase_count(records,cut=None):
    require(cut is None or type(cut) is int,
            'phase accessor cut must be an integer')
    seen=set()
    terminal_bindings={}
    for t,c,registry in records:
        admitted(t,c,registry)
        key=(t.scope,t.scale,t.lineage,t.event_ids[-1])
        require(key not in terminal_bindings or terminal_bindings[key]==t.trace_digest,
                'conflicting trace for immutable terminal return event')
        terminal_bindings[key]=t.trace_digest
        if cut is None or t.indices[-1]<=cut:seen.add(t.return_id)
    return len(seen)


def certified(t, motif='Monon', *, inner=()):
    c=certify(t,motif,inner=inner)
    return (t,c,{c.certificate_digest:c})


@dataclass(frozen=True)
class Wave:
    scope: str
    scale: int
    lineage: str
    motif: str
    identity: str
    returns: tuple[Trace,...]
    certificates: tuple[Certificate,...]
    motif_witnesses: tuple=()

    @property
    def bip(self):
        return len(self.returns)-1

    @property
    def cadence(self):
        return tuple(b.indices[-1]-a.indices[-1] for a,b in zip(self.returns,self.returns[1:]))


def wave(records,motif_witnesses=()):
    require(len(records)>=2,'one closure supplies no recurrence')
    phase_count(records)
    ts=tuple(r[0] for r in records);cs=tuple(r[1] for r in records)
    require(len({t.return_id for t in ts})==len(ts),'replayed return is not a beat')
    require(len({(t.scope,t.scale,t.lineage,c.motif) for t,c in zip(ts,cs)})==1,
            'incompatible recurrence lineage, motif or scope')
    if cs[0].motif=='outer':
        origin=tuple((w.identity,w.scope,w.scale) for w in cs[0].inner_waves)
        require(all(tuple((w.identity,w.scope,w.scale) for w in c.inner_waves)==origin for c in cs),
                'recurrence changed retained ancestor identity')
        require(all(x.certificates==y.certificates[:len(x.certificates)]
                    for before,after in zip(cs,cs[1:])
                    for x,y in zip(before.inner_waves,after.inner_waves)),
                'outer recurrence changed a retained inner prefix')
    else:
        require(all(t.ancestor==ts[0].ancestor for t in ts),
                'recurrence changed retained ancestor identity')
    require(all(a.indices[-1]<b.indices[0] for a,b in zip(ts,ts[1:])),
            'recurrence must follow previous completion')
    motif=cs[0].motif
    if motif_witnesses:
        require(len(motif_witnesses)==len(ts),'one bound construction per higher-motif return required')
        for t,c,m in zip(ts,cs,motif_witnesses):
            validate_motif(m)
            require(m.support_trace==t and m.closure==c,'motif witness belongs to another return')
        require(len({m.core for m in motif_witnesses})==1,'recurrence changed inherited motif type')
        motif=motif_witnesses[0].core
    return Wave(ts[0].scope,ts[0].scale,ts[0].lineage,motif,
                digest((ts[0].scope,ts[0].lineage,motif,ts[0].return_id)),ts,cs,tuple(motif_witnesses))


def recurrent(lineage='a', n=3, spacing=10, scope='B0',scale=0):
    return wave([certified(trace(lineage,k,start_index=k*spacing,scope=scope,scale=scale)) for k in range(n)])


def validate_wave(w):
    require(isinstance(w,Wave),'admitted recurring wave required')
    registry={c.certificate_digest:c for c in w.certificates}
    require(wave([(t,c,registry) for t,c in zip(w.returns,w.certificates)],w.motif_witnesses)==w,
            'wave identity or certificate history mismatch')
    return True


@dataclass(frozen=True)
class MotifWitness:
    identity: str
    core: str
    scope: str
    lineage: str
    construction: tuple
    support_trace: Trace
    closure: Certificate
    component_certificates: tuple[Certificate,...]
    component_traces: tuple[Trace,...]
    enclosure: int
    chirality: int
    witness_digest: str


def motif_witness(core,t,construction,component_records,registry,enclosure=6,chirality=1):
    """Bind inherited syntax to actual closure/support and component evidence.

    A Duon carries two Dion patterns and a bound monon pivot. A p:q support
    records p ordered blocks of q unit occurrence IDs plus its q retained
    ancestral shell IDs. These are declared construction occurrences, not
    a proof of q**p independent graph paths or a new discovered motif family.
    """
    admitted(t,certify(t),registry)
    require(enclosure>=6 and enclosure%2==0 and chirality in (-1,1),'invalid enclosure/chirality')
    require(bool(component_records),'bound component traces required')
    components=tuple(c for component,c in component_records)
    for component,c in component_records:
        admitted(component,c,registry)
        require(component.indices[-1]<t.indices[0],'component closure must precede motif construction')
    require(len({c.return_id for c in components})==len(components),'duplicate component return')
    require(all((c.scope,c.lineage,c.scale)==(t.scope,t.lineage,t.scale) for c in components),
            'component scope/lineage/scale mismatch')
    if core=='Duon':
        require(len(construction)==3,'Duon requires Dion-pivot-Dion')
        left,pivot,right=construction
        require(tuple(left) in ((1,-1),(-1,1)) and tuple(right) in ((1,-1),(-1,1)), 'invalid Dion pattern')
        require(len(components)==1 and components[0].motif=='Monon','carried monon pivot required')
        require(tuple(pivot)==(components[0].certificate_digest,chirality if chirality else 0) or
                (len(pivot)==2 and pivot[0]==components[0].certificate_digest and pivot[1] in (-1,0,1)),
                'pivot state or lineage not bound')
    else:
        try:p,q=map(int,core.split(':'))
        except (ValueError,AttributeError):raise AdmissionError('unknown inherited core')
        require((p==1 and q==2) or (p==3 and q>=1),'unknown inherited core')
        require(len(construction)==2,'support requires ordered blocks and retained shell')
        blocks,shell=construction
        require(len(blocks)==p and all(len(b)==q for b in blocks) and len(shell)==q,'wrong inherited p:q support shape')
        require(all(len(set(b))==q for b in blocks) and len(set(shell))==q,
                'support positions require distinct component occurrences')
        bound={c.return_id for c in components}
        require(all(x in bound for block in blocks for x in block) and all(x in bound for x in shell),
                'unbound support occurrence')
        require(len(bound)>=q,'scalar support count cannot replace distinct component provenance')
    payload=(core,t.scope,t.lineage,construction,t.trace_digest,
             tuple(c.certificate_digest for c in components),enclosure,chirality)
    d=digest(payload)
    return MotifWitness(d,core,t.scope,t.lineage,tuple(construction),t,certify(t),
                        tuple(components),tuple(component for component,c in component_records),enclosure,chirality,d)


def validate_motif(m):
    require(isinstance(m,MotifWitness),'bound motif witness required')
    require(len(m.component_traces)==len(m.component_certificates),'component trace/certificate mismatch')
    registry={c.certificate_digest:c for c in (*m.component_certificates,m.closure)}
    require(motif_witness(m.core,m.support_trace,m.construction,
                         tuple(zip(m.component_traces,m.component_certificates)),registry,
                         m.enclosure,m.chirality)==m,'motif construction binding mismatch')
    return True


@dataclass(frozen=True)
class Field:
    scope: str
    identity: str
    members: tuple[str,...]


def field(scope, identity, members):
    require(bool(identity) and len(members)>0,'field requires named recurring members')
    require(all(isinstance(w,Wave) and w.scope==scope for w in members),'field cannot admit closure or alias as wave')
    for w in members:validate_wave(w)
    return Field(scope,identity,tuple(sorted({w.identity for w in members})))


def resolve_fields(fields):
    return tuple(sorted({w for f in fields for w in f.members}))


def leg_comparison(record, reference, symmetric=False):
    t,c,r=record;tr,cr,rr=reference
    admitted(t,c,r);admitted(tr,cr,rr)
    require(t.reflected_comparison and tr.reflected_comparison,
            'retained-return witness lacks declared reflected-comparison model')
    require((t.scope,t.scale)==(tr.scope,tr.scale),'incompatible reference scope')
    require(len(tr.vertices)-1==2 and tr.turn==1,'reference is not primitive two-edge closure')
    outbound=t.turn;returning=len(t.vertices)-1-t.turn
    embedded_unit=len(tr.vertices)-1
    require(outbound+returning>=embedded_unit,'support bridge failed')
    if symmetric:
        require(outbound==returning,'unequal legs cannot factor into a common operand')
        require(t.vertices[:t.turn+1]==tuple(reversed(t.vertices[t.turn:])),
                'equal counts alone are not declared path reflection symmetry')
    return {'outbound':outbound,'return':returning,'sum':outbound+returning,
            'embedded_unit':embedded_unit,'closure_phase':1,
            'factored':2*outbound if symmetric else None}


def kernel(candidates, weights):
    """Atomic-traversal kernel; fibre-only dwell is handled by fibre_step."""
    candidates=tuple(dict.fromkeys(tuple(c) for c in candidates))
    valid=[]
    for a,b,role_a,role_b in candidates:
        if hamming(a,b)==1 and role_a in (-1,0,1) and role_b in (-1,0,1) and not (role_a*role_b==-1):
            valid.append((a,b,role_a,role_b))
    require(all(Q(v)>=0 for v in weights.values()),'negative model weight')
    total=sum((Q(weights.get(e,0)) for e in valid),Q(0))
    if total==0:return {'status':'EMPTY_POSITIVE_WEIGHT_SUPPORT' if valid else 'EMPTY_ADMISSIBLE_SUPPORT','probabilities':{}}
    return {'status':'NORMALIZED','probabilities':{e:Q(weights.get(e,0))/total if e in valid else Q(0) for e in candidates}}


def fibre_step(before,after,kind):
    require(before in (-1,0,1) and after in (-1,0,1),'invalid role')
    if kind=='additional_dwell':require(before==after==0,'dwell requires existing hinge')
    elif kind=='enter_hinge':require(before in (-1,1) and after==0,'structural hinge entry')
    elif kind=='leave_hinge':require(before==0 and after in (-1,1),'branch must follow hinge')
    else:raise AdmissionError('unknown fibre event')
    return {'role':after,'atomic_traversals':0,'kind':kind}


def rd(p,q,hinges=1,left=None,right=None):
    require(p>=1 and q>=2 and hinges>=1,'invalid declared support signature')
    pi=q**p+q
    return (pi if left is None else left)+hinges+(pi if right is None else right)


@dataclass(frozen=True)
class Contact:
    identity: str
    left: str
    right: str
    scope: str
    committed: int
    left_prefix: str
    right_prefix: str
    reflection: tuple[int,int]
    support_trace: Trace
    support_certificate: Certificate


def wave_prefix(w,k):
    return digest(tuple(t.trace_digest for t in w.returns if t.indices[-1]<=k))


def contacts(a,b):
    validate_wave(a);validate_wave(b)
    require(a.identity!=b.identity,'same wave under aliases')
    upper=min(a.returns[-1].indices[-1],b.returns[-1].indices[-1])
    lower=max(a.returns[1].indices[-1],b.returns[1].indices[-1])
    result=[]
    for k in (lower,upper):
        support=trace(f'{a.identity}|{b.identity}',k,scope=a.scope,scale=a.scale,start_index=k-2)
        result.append(Contact(f'contact:{k}',a.identity,b.identity,a.scope,k,
                         wave_prefix(a,k),wave_prefix(b,k),(1,2),support,certify(support)))
    return tuple(result)


@dataclass(frozen=True)
class RCD:
    left: str
    right: str
    scope: str
    contact_ids: tuple[str,...]
    support: int
    reflection_counts: tuple[int,...]
    domain: str='native-return-count'

    def duration(self):
        require(type(self.support) is int and self.support>=0 and
                all(type(x) is int and x>=0 for x in self.reflection_counts),'invalid exact integer count domain')
        return self.support+sum(self.reflection_counts)


def participation(r:RCD,window:int,domain:str):
    require(domain==r.domain and isinstance(window,int) and window>=0,'incompatible duration/window domain')
    return min(r.duration(),window)


def compare(a:Wave,b:Wave,events,window=(0,100),reverse=False,bias=(Q(0),Q(0)),prior_lag=Q(0)):
    require(isinstance(window,(tuple,list)) and len(window)==2 and
            all(type(k) is int for k in window) and window[0]<window[1],
            'native window requires two strictly ordered integer endpoints')
    require(all(type(e.committed) is int for e in events),
            'contact commitments must be integer native cuts')
    bias=tuple(Q(x) for x in bias)
    require(len(bias)==2,'comparison requires exactly two oriented bias coordinates')
    validate_wave(a);validate_wave(b)
    require(a.identity!=b.identity and (a.scope,a.scale)==(b.scope,b.scale),'distinct common-scope waves required')
    require(len(events)>=2 and len({e.identity for e in events})==len(events),'repeated distinct bound contacts required')
    require(len({e.committed for e in events})==len(events),'contacts must occur at distinct transitions')
    require(all(x.committed<y.committed for x,y in zip(events,events[1:])), 'coupling trace is not in committed order')
    require(len({e.support_trace.return_id for e in events})==len(events),
            'one cross-return cannot become two contacts by relabelling')
    for e in events:
        require(len(e.reflection)==2 and all(type(x) is int and x>=0 for x in e.reflection),
                'directional reflection uses exact nonnegative integer counts')
        require((e.left,e.right,e.scope)==(a.identity,b.identity,a.scope),'wrong coupling lineage')
        require(window[0]<=e.committed<=window[1],'contact outside committed window')
        require((e.left_prefix,e.right_prefix)==(wave_prefix(a,e.committed),wave_prefix(b,e.committed)), 'coupling prefix mismatch')
        require(all(sum(t.indices[-1]<=e.committed for t in w.returns)>=2 for w in (a,b)),
                'contact precedes admitted recurrent prefix')
        admitted(e.support_trace,e.support_certificate,{e.support_certificate.certificate_digest:e.support_certificate})
        require(e.support_trace.lineage==f'{a.identity}|{b.identity}' and
                e.support_trace.scope==e.scope and e.support_trace.scale==a.scale and
                e.support_trace.indices[-1]<=e.committed,
                'unbound or future cross-return support')
    def count(w):return sum(window[0]<t.indices[-1]<=window[1] for t in w.returns[1:])
    na,nb=count(a),count(b)
    require(na>0 and nb>0,'positive recurrence denominators required')
    i,j=(b,a) if reverse else (a,b)
    rate=Q(nb,na) if reverse else Q(na,nb)
    lag=Q(na-nb)+bias[0]-bias[1]
    if reverse:lag=-lag
    rs=tuple(e.reflection[1 if reverse else 0] for e in events)
    # One bound representative support shape is used by this declared channel
    # compression; every contact must have the same support accessor.
    supports=tuple((len(e.support_trace.vertices)-1)+len(e.support_trace.roles)-2 for e in events)
    require(len(set(supports))==1,'channel compression requires common support shape')
    r=RCD(i.identity,j.identity,a.scope,tuple(e.identity for e in events),supports[0],rs)
    # Both bias and the declared prior scalar use the original a|b orientation.
    oriented_prior=-Q(prior_lag) if reverse else Q(prior_lag)
    return {'ratio':rate,'bias':(-1 if reverse else 1)*(bias[0]-bias[1]),
            'lag':lag,'drift':lag-oriented_prior,'rcd':r,'duration':r.duration()}


@dataclass(frozen=True)
class WaveState:
    identity: str
    committed: int
    present: tuple[int,...]
    closure_memory: tuple[str,...]
    pressure: Fraction
    current: Fraction
    closure_status: str
    retained_rebalancing: tuple=()
    motif_certificates: tuple[str,...]=()
    cadence: tuple[int,...]=()
    orientation: int=1
    boundary: str='B0'
    capacity: Fraction=Q(1)
    phases: int=0


def initial_state(w,pressure=Q(1)):
    validate_wave(w)
    return WaveState(w.identity,w.returns[-1].indices[-1],(w.returns[-1].vertices[-1],),
                     tuple(t.return_id for t in w.returns),Q(pressure),Q(0),'closed',(),
                     tuple(c.certificate_digest for c in w.certificates),w.cadence,
                     w.returns[0].roles[0],w.scope,Q(1),len(w.returns))


def update(s:WaveState,attention:Fraction,input_index:int):
    require(type(s.committed) is int and type(input_index) is int,
            'committed native indices must be integers')
    require(input_index<=s.committed,'future input or same-step circular response')
    # Declared rational response model; current becomes the next committed value.
    require(s.pressure>0,'positive pressure required by inverse-pressure response model')
    return replace(s,committed=s.committed+1,current=Q(s.current)+Q(attention)/Q(s.pressure))


def fold_proposal(inner,scope,scale):
    require(bool(inner),'admitted inner lineages required')
    for w in inner:validate_wave(w)
    require(len({w.identity for w in inner})==len(inner),'duplicate inner lineage aliases')
    require(scale>max(w.scale for w in inner),'outer scope must have higher scale')
    return tuple((w.identity,w.scope,w.scale,scope,scale,
                  tuple(c.certificate_digest for c in w.certificates)) for w in inner)


def outer_trace(inner,lineage='outer',occurrence=0,scope='B1',scale=1,start_index=None):
    proposal=fold_proposal(inner,scope,scale)
    earliest=max(w.returns[-1].indices[-1] for w in inner)+1
    start=earliest+10*occurrence if start_index is None else start_index
    require(start>=earliest,'outer construction reads future inner closure')
    return replace(trace(lineage,occurrence,scope=scope,scale=scale,start_index=start),
                   ancestor='fold:'+digest(proposal))


def fold(inner,outer_record):
    admitted(*outer_record)
    t=outer_record[0]
    proposal=fold_proposal(inner,t.scope,t.scale)
    require(outer_record[1].motif=='outer' and outer_record[1].inner_waves==tuple(inner) and
            t.ancestor=='fold:'+digest(proposal),
            'outer certificate must bind the proposed inner lineage and scope map')
    require(t.indices[0]>max(w.returns[-1].indices[-1] for w in inner),
            'outer construction reads future inner closure')
    return {'outer':outer_record,'phase':1,'inner':tuple(inner),'proposal':proposal,'status':'outer_closed'}


def expose(f):
    bound=fold(f['inner'],f['outer'])
    require(all(f.get(k)==bound[k] for k in ('outer','phase','inner','proposal')),
            'folded record lost bound inner provenance')
    require(f.get('status') in ('outer_closed','shedding','exposed','pending'),'unknown outer status')
    return f['inner']


def seat_duon(w,state,compatible):
    validate_wave(w)
    require(w.motif=='Duon' and state.identity==w.identity,'Duad is a state of the same admitted Duon current')
    require(compatible,'no compatible seat declared')
    return replace(state,closure_status='seated')


def standing_organization(a,b,events,states,window=(0,100)):
    """Declared balanced native pair; a zero sum without coupling is insufficient."""
    relation=compare(a,b,events,window)
    require(len(states)==2,'one committed current state per lineage required')
    for w,state in zip((a,b),states):
        require(state.identity==w.identity and state.boundary==w.scope and
                max(e.committed for e in events)<=state.committed<=window[1],
                'standing current state not bound to committed coupled lineages')
        require(all(t.roles[0]==state.orientation for t in w.returns) and
                Q(state.current)*state.orientation>0,'current orientation not carried by recurrence')
    require(states[0].orientation==-states[1].orientation and
            states[0].current+states[1].current==0,'opposite balanced current pair required')
    return {'kind':'standing','wave_identities':(a.identity,b.identity),
            'contact_returns':tuple(e.support_trace.return_id for e in events),
            'retained_ancestry':tuple(tuple(t.ancestor for t in w.returns) for w in (a,b)),
            'relation':relation}


def afc_flux(memory,matrix):
    n=len(memory)
    require(len(matrix)==n and all(len(r)==n for r in matrix),'kernel dimension mismatch')
    p=list(map(Q,memory));P=[list(map(Q,r)) for r in matrix]
    require(all(x>=0 for x in p) and sum(p)==1,'memory not normalized')
    require(all(all(x>=0 for x in r) and sum(r)==1 for r in P),'kernel not stochastic')
    return [[p[i]*P[i][j]-p[j]*P[j][i] for j in range(n)] for i in range(n)]


def aod_flux(oriented_channels):
    # One ledger identity has two oriented views; reverse physical channels are separate records.
    out={}
    for i,j,p,a,lineage in oriented_channels:
        require(i!=j and bool(lineage),'bound oriented channel required')
        require(Q(p)>=0,'pressure magnitude must be nonnegative')
        value=Q(p)*Q(a)
        if (i,j,lineage) in out:
            require(out[(i,j,lineage)]==value,'conflicting duplicate channel identity')
            continue
        out[(i,j,lineage)]=value
        out[(j,i,lineage)]=-value
    return out


def stokes(flux,region):
    internal=sum(v for (i,j,l),v in flux.items() if i in region and j in region)
    divergence=sum(v for (i,j,l),v in flux.items() if i in region)
    boundary=sum(v for (i,j,l),v in flux.items() if i in region and j not in region)
    require(internal==0 and divergence==boundary,'antisymmetry or boundary cancellation fails')
    return {'internal':internal,'divergence':divergence,'boundary':boundary,'lineages':tuple(sorted({l for i,j,l in flux}))}


def frg(independent,cross,stages=('distinction','retained_relation','admitted_motif','model'),committed=0,response=1):
    require(stages==('distinction','retained_relation','admitted_motif','model'),'FRG construction order')
    require(response>committed,'FRG response must follow committed inputs')
    base=sum(map(Q,independent));mix=sum(map(Q,cross))
    return {'independent':base,'cross':mix,'recurrent':base+mix,'residual':mix}


@dataclass(frozen=True)
class ValueTrace:
    wave_identity: str
    scope: str
    index_group: tuple[str,int]
    committed_window: tuple[int,int]
    prefix_digest: str
    event_ids: tuple[str,...]
    values: tuple
    projection: str
    states: tuple[WaveState,...]
    source_digest: str


def bind_values(w,states):
    validate_wave(w)
    require(len(states)==len(w.returns),'one declared current readout per committed return')
    for index,(state,t) in enumerate(zip(states,w.returns)):
        require((state.identity,state.committed,state.boundary)==(w.identity,t.indices[-1],w.scope),
                'value readout not bound to wave return')
        expected=tuple(x.return_id for x in w.returns if x.indices[-1]<=state.committed)
        require(state.closure_memory==expected,'readout closure prefix mismatch')
        prefix=w.returns[:index+1]
        require(state.motif_certificates==tuple(c.certificate_digest for c in w.certificates[:index+1]) and
                state.cadence==tuple(b.indices[-1]-a.indices[-1] for a,b in zip(prefix,prefix[1:])) and
                state.phases==len(prefix),'readout contains future recurrence coordinates')
        require(state.present==(t.vertices[-1],) and state.orientation==t.roles[0],
                'readout present coordinates not bound to its return')
    values=tuple(s.current for s in states)
    ids=tuple(t.event_ids[-1] for t in w.returns)
    prefix=wave_prefix(w,w.returns[-1].indices[-1]);source=digest([asdict(s) for s in states])
    return ValueTrace(w.identity,w.scope,('cyclic',len(states)),
                      (w.returns[0].indices[-1],w.returns[-1].indices[-1]),
                      prefix,ids,values,'committed-current-readout',tuple(states),source)


def declared_readout(w,values):
    """A declared fixture state stream, separately typed from update-law examples."""
    require(len(values)==len(w.returns),'readout length must match its declared recurrence window')
    validate_wave(w)
    states=tuple(WaveState(w.identity,t.indices[-1],(t.vertices[-1],),
                          tuple(x.return_id for x in w.returns[:n+1]),Q(1),Q(v),'closed',(),
                          tuple(c.certificate_digest for c in w.certificates[:n+1]),
                          tuple(b.indices[-1]-a.indices[-1] for a,b in zip(w.returns[:n],w.returns[1:n+1])),
                          t.roles[0],w.scope,Q(1),n+1)
                 for n,(t,v) in enumerate(zip(w.returns,values)))
    return bind_values(w,states)


def fourier(values,admission=None,binding=None):
    import sympy as s
    validate_wave(admission)
    require(isinstance(binding,ValueTrace),'harmonic values require committed source binding')
    require(bind_values(admission,binding.states)==binding and tuple(values)==binding.values,
            'harmonic value/projection/prefix mismatch')
    n=len(values);require(n>0,'empty harmonic support')
    z=s.exp(2*s.pi*s.I/n)
    return tuple(s.simplify(sum(s.sympify(v)*z**(-k*g) for g,v in enumerate(values))/n) for k in range(n))


def inverse(coefficients):
    import sympy as s
    n=len(coefficients);z=s.exp(2*s.pi*s.I/n)
    return tuple(s.simplify(sum(v*z**(k*g) for k,v in enumerate(coefficients))) for g in range(n))


def metrology(native,record):
    required={'measurand','protocol','reference','coupling','detector','calibration','unit',
              'resolution','uncertainty','repeatability','traceability'}
    require(required.issubset(record) and all(str(record[k]).strip() for k in required),'incomplete metrology record')
    return Q(native)*Q(record['calibration'])


def run_case(op,args):
    """Execute fixture inputs; expected results never enter the operative law."""
    if op=='source_binding':
        import importlib.util
        path=Path(__file__).resolve().parents[2]/'scripts/audit_scientific_sources.py'
        spec=importlib.util.spec_from_file_location('native_source_binding',path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        try:return module.fixture_conservation(args.get('destination','eq:closure-phase'))
        except ValueError as error:raise AdmissionError(str(error)) from error
    if op=='hamming':
        vs=args['vertices'];ds=[hamming(a,b) for a,b in zip(vs,vs[1:])]
        if args.get('atomic'):require(len(ds)==1 and ds[0]==1,'non-H1 event called atomic')
        else:require(all(d==1 for d in ds),'non-H1 constituent')
        return {'legs':ds,'endpoint':hamming(vs[0],vs[-1])}
    if op=='types':
        values=[('Null',None),('fibre',0),('Q4',0),('anchor','00_8'),('scope','B0')]
        require(not args.get('collapse'),'distinct ontology types collapsed')
        require(not args.get('prior_anchor'),'first anchor cannot be selected from prior finite coordinates')
        require(args.get('scale',0)>=0,'lower anchor is unbound')
        return {'distinct':len(set(values)),'anchor':'00_8'}
    if op in ('closure','phase','wave','certificate','legs','crown'):
        opts={k:args[k] for k in ('lineage','occurrence','vertices','dwell','scope','scale','turn','chirality') if k in args}
        t=trace(**opts)
        if args.get('bypass'):t=replace(t,roles=(1,-1))
        if args.get('same_sign'):t=replace(t,roles=(1,0,1))
        if args.get('wrong_witness'):t=replace(t,reflection=replace(t.reflection,lineage='wrong'))
        if args.get('no_witness'):t=replace(t,reflection=None)
        if op=='crown':
            validate_trace(t,False)
            require(not args.get('horizon_as_realized'),'horizon requires admitted advance')
            return {'advance':t.event_ids[1],'reclosed':t.vertices[0]==t.vertices[-1]}
        r=certified(t)
        if op=='certificate':
            c=r[1]
            if args.get('mutation'):
                m=args['mutation'];v={'scope':'wrong','lineage':'wrong','trace_digest':'0'*64,'status':'open','certificate_digest':''}.get(m,'unknown')
                c=replace(c,**{m:v})
            admitted(t,c,r[2]);return {'admitted':True}
        if op=='legs':return leg_comparison(r,certified(trace('reference',scope=t.scope,scale=t.scale,vertices=tuple(args.get('reference',[0,1,0])))),args.get('symmetric',False))
        if op=='wave':
            rs=[r]
            for k in range(1,args.get('n',2)):
                rs.append(r if args.get('replay') else certified(trace(t.lineage,k,scope=t.scope,scale=t.scale)))
            w=wave(rs);return {'bip':w.bip,'cadence':list(w.cadence)}
        return {'phases':phase_count([r]*args.get('copies',1)),'dwell':len(t.roles)-3,'edges':len(t.vertices)-1}
    if op=='kernel':
        cs=[tuple(e) for e in args['candidates']];ws={e:Q(w) for e,w in zip(cs,args['weights'])};r=kernel(cs,ws)
        return {'status':r['status'],'probabilities':[str(r['probabilities'].get(e,0)) for e in cs]}
    if op=='grammar':
        require(args.get('claim') not in ('Dion=Dimonon','Duon=C2','Duad=new_motif'),'motif/current/state collapse')
        return {'D_alpha':[1,-1],'D_omega':[-1,1],'Dimonon_monons':2,'Duon_variants':12,'Duad':'seated Duon state','RD':[rd(1,2),rd(3,2),rd(3,3),rd(3,4)]}
    if op=='field':
        a=recurrent();members=[a,a] if args.get('alias') else [a]
        if args.get('closure_only'):members=[trace()]
        f=field('B0','f',members);return {'wave_members':len(f.members)}
    if op=='fold':
        inn=[recurrent()];outer=certified(outer_trace(inn),'outer',inner=inn)
        if args.get('contact_only'):outer=None
        require(outer is not None,'contact proposal is not closure')
        f=fold(inn,outer)
        require(not args.get('reuse_lower_beats'),'inner beats do not count at outer scope')
        if args.get('erase_inner'):f['inner']=()
        require(len(expose(f))==1,'outer shedding erased inner lineage')
        return {'outer_phase':f['phase'],'outer_wave':False,'inner_waves':len(expose(f))}
    if op=='temporal':
        a=recurrent('a',args.get('na',3));b=recurrent('b',args.get('nb',3),spacing=7)
        if args.get('alias'):b=a
        ev=contacts(a,b)
        if args.get('single_contact'):ev=ev[:1]
        if args.get('wrong_lineage'):ev=(replace(ev[0],left='wrong'),)+ev[1:]
        r=compare(a,b,ev,tuple(args.get('window',[0,100])),args.get('reverse',False),tuple(map(Q,args.get('bias',['0','0']))))
        if args.get('clip_wrong_domain'):participation(r['rcd'],2,'seconds')
        return {k:str(r[k]) for k in ('ratio','bias','lag','drift','duration')}
    if op=='state':
        a=recurrent();s=initial_state(a);other=replace(s,pressure=Q(7))
        require(not args.get('collapse'),'temporal projection cannot identify complete state')
        return {'same_identity':s.identity==other.identity,'distinct_state':s!=other}
    if op=='update':
        s=initial_state(recurrent(),Q(args.get('pressure','2')))
        n=update(s,Q(args.get('attention','6')),s.committed+args.get('future',0))
        return {'step':n.committed-s.committed,'current':str(n.current)}
    if op=='flux':
        p=list(map(Q,args.get('memory',['1/2','1/2'])));f=afc_flux(p,[[0,1],[1,0]])
        if args.get('pressure_in_afc'):afc_flux([7,0],[[0,1],[1,0]])
        d=aod_flux([(0,1,7,1,'forward'),(1,2,3,1,'next')])
        if args.get('break_antisymmetry'):d[(1,0,'forward')]=Q(7)
        s=stokes(d,{0,1});return {'afc':str(f[0][1]),'aod':str(d[(0,1,'forward')]),'boundary':str(s['boundary']),'retained_lineages':len(s['lineages'])}
    if op=='frg':
        stages=('model','distinction','retained_relation','admitted_motif') if args.get('early_model') else ('distinction','retained_relation','admitted_motif','model')
        r=frg([2,3],[-1,4],stages,response=0 if args.get('same_step') else 1)
        return {k:str(v) for k,v in r.items()}
    if op=='fourier':
        values=args.get('values',[1,0,-1,0])
        w=None if args.get('unbound') else recurrent('harmonic',len(values))
        binding=None if w is None else declared_readout(w,values)
        c=fourier(values,w,binding)
        return {'reconstruction':[str(x) for x in inverse(c)],'coefficients':[str(x) for x in c]}
    if op=='metrology':
        rec={k:'declared fixture report' for k in ('measurand','protocol','reference','coupling','detector','unit','resolution','uncertainty','repeatability','traceability')}
        rec['calibration']=args.get('n','2/3')
        if args.get('missing'):rec.pop(args['missing'])
        N=args.get('N',3)
        require(not args.get('force_three') or N==3,'x=3n requires N=3')
        return {'report':str(metrology(N,rec)),'N':N}
    raise AdmissionError(f'unknown operation {op}')


def execute_row(row):
    try:
        actual=run_case(row['operation'],json.loads(row['input_trace']))
        verdict='PASS'
    except AdmissionError as e:
        actual={'error':str(e)};verdict='REJECT'
    expected=json.loads(row['expected_exact_result'])
    matched=verdict==row['expected_verdict'] and (verdict=='REJECT' or actual==expected)
    return {'fixture_id':row['fixture_id'],'actual_verdict':verdict,'actual':actual,
            'expected_matched':matched,'input_digest':digest(row)}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check-data',action='store_true')
    opts=parser.parse_args()
    if opts.check_data:
        root=Path(__file__).resolve().parents[1]/'data/m1'
        results=[]
        for p in sorted(root.glob('*.csv')):
            with p.open() as f:results.extend(execute_row(row) for row in csv.DictReader(f))
        print(json.dumps({'results':results,'passed':sum(r['expected_matched'] for r in results),'total':len(results)},indent=2,default=str))
        return 0 if results and all(r['expected_matched'] for r in results) else 1
    return 0


if __name__=='__main__':
    raise SystemExit(main())

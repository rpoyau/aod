"""Exact new awareness witnesses on the repaired native closure-wave interfaces.

All laws below are declared finite models, not universal dynamics. The only
operative copy of prior rebalancing operands/value is in Retention. World is
an immutable admission/provenance witness, never an alternative residual store.
Lane names, expected answers, passive observations and historical toy names do
not enter transition(). Historical19 originals are not reconstructed here.
"""
from __future__ import annotations
from dataclasses import dataclass,asdict,replace,is_dataclass
from fractions import Fraction
from pathlib import Path
import argparse,json,hashlib,sys
import aod_native_closure_wave as n

Q=n.Q
require=n.require
AdmissionError=n.AdmissionError

def encode(x):
    if is_dataclass(x):return encode(asdict(x))
    if isinstance(x,dict):return {str(k):encode(v) for k,v in x.items()}
    if isinstance(x,(tuple,list)):return [encode(v) for v in x]
    if isinstance(x,Fraction):return str(x)
    return x

def packed(x):return json.dumps(encode(x),sort_keys=True,separators=(',',':'))
def digest(x):return hashlib.sha256(packed(x).encode()).hexdigest()

@dataclass(frozen=True)
class Action:
    identity:str
    issuer:str
    issued:int
    command:Fraction
    channel:str

@dataclass(frozen=True)
class World:
    target:str
    waves:tuple[n.Wave,...]
    actions:tuple[Action,...]=()
    prior_commitments:tuple[str,...]=()

    def get(self,identity):
        found=[w for w in self.waves if w.identity==identity]
        require(len(found)==1,'unknown or duplicate admitted wave identity')
        n.validate_wave(found[0]);return found[0]

@dataclass(frozen=True)
class Prior:
    source:str
    target:str
    scope:str
    scale:int
    input_commit:int
    retained_at:int
    independent:tuple[Fraction,...]
    cross:tuple[Fraction,...]
    contacts:tuple[n.Contact,...]
    relational_type:str
    lag:Fraction
    source_prefix:str
    target_prefix:str
    action:Action|None=None
    action_return:n.Trace|None=None
    observed:Fraction|None=None
    origin:str='local'
    carriage:Carriage|None=None
    comparator_bias:tuple[Fraction,Fraction]=(Q(0),Q(0))

@dataclass(frozen=True)
class Carriage:
    retained:Retention
    inner:tuple[n.Wave,...]
    outer:tuple
    source_actions:tuple[Action,...]=()
    source_commitments:tuple[str,...]=()

@dataclass(frozen=True)
class Retention:
    prior:Prior
    value:Fraction
    lineage_digest:str

@dataclass(frozen=True)
class State:
    # Empty placeholders in X make the split explicit without duplicating M/R.
    present:n.WaveState
    closure_memory:tuple[str,...]
    retained:tuple[Retention,...]

@dataclass(frozen=True)
class Input:
    committed:int
    attention:Fraction=Q(0)
    query:Fraction=Q(0)
    available:tuple[str,...]=()
    query_observed_at:int|None=None

@dataclass(frozen=True)
class Model:
    gain:Fraction=Q(1)
    selector_threshold:Fraction=Q(0)


def residual(prior):
    return n.frg(prior.independent,prior.cross,committed=prior.input_commit,
                 response=prior.retained_at)['residual']


def retain(prior):
    value=residual(prior)
    return Retention(prior,value,digest((prior,value)))


def validate_world(world):
    require(len({v.identity for v in world.waves})==len(world.waves),'duplicate admitted world identity')
    for w in world.waves:n.validate_wave(w)
    require(len({a.identity for a in world.actions})==len(world.actions),'conflicting immutable action identities')
    for a in world.actions:
        require(type(a.issued) is int and a.issued>=0,'action commitment requires an exact native integer')
        require(a.identity==digest((a.issuer,a.issued,Q(a.command),a.channel)), 'action identity does not bind its command/channel')
        for identity in (a.issuer,a.channel):
            wave=world.get(identity)
            require(sum(t.indices[-1]<=a.issued for t in wave.returns)>=2,
                    'action precedes admitted issuer/channel recurrence')
    return True


def validate_retention(r,world,k):
    require(isinstance(r,Retention),'typed retained prior relation required')
    validate_world(world)
    p=r.prior;source=world.get(p.source);target=world.get(p.target)
    require(digest(p) in world.prior_commitments,'retained operands lack a prior immutable commitment')
    require(type(p.input_commit) is int and type(p.retained_at) is int and p.input_commit>=0,
            'prior commitment requires exact native integers')
    require(all(type(c.committed) is int for c in p.contacts),'contact commitment requires exact native integers')
    require(p.target==world.target,'retention addresses another operative target')
    require(type(p.scale) is int and (p.scope,p.scale)==(source.scope,source.scale)==(target.scope,target.scale),
            'cross-scale impostor requires a bound lift, not a local coincidence')
    require(p.input_commit+1==p.retained_at<=k,'prior relation must be retained after its committed inputs')
    require(p.input_commit==max(c.committed for c in p.contacts),'prior commitment not bound to contacts')
    require(p.source_prefix==n.wave_prefix(source,p.input_commit) and
            p.target_prefix==n.wave_prefix(target,p.input_commit),'retained lineage prefix mismatch')
    require(type(p.comparator_bias) is tuple and len(p.comparator_bias)==2,'exact two-operand comparator bias required')
    bias=tuple(Q(x) for x in p.comparator_bias)
    comparison=n.compare(source,target,p.contacts,window=(0,p.input_commit),bias=bias)
    require(p.relational_type=='M1:unwrapped-count-lag' and Q(p.lag)==comparison['lag'],
            'retained relational phase type/provenance mismatch')
    require(Q(r.value)==residual(p) and r.lineage_digest==digest((p,r.value)),
            'retained residual value or lineage digest mismatch')
    require(p.origin in ('local','action','carried'),'unknown retained provenance origin')
    if p.origin=='carried':
        c=p.carriage;require(isinstance(c,Carriage),'cross-scale retention needs an actual carriage witness')
        folded=n.fold(c.inner,c.outer)
        old=c.retained;oldworld=World(old.prior.target,c.inner,c.source_actions,c.source_commitments)
        validate_retention(old,oldworld,c.outer[0].indices[0]-1)
        require(c.outer[1] in target.certificates and c.outer[0] in target.returns,
                'carried retention targets another outer recurrent lineage')
        require(p.cross==(Q(old.value),) and p.input_commit>=c.outer[0].indices[-1],
                'carried value or commitment detached from inner rebalancing')
    else:require(p.carriage is None,'undeclared cross-scale carriage')
    if p.action is not None:
        require(p.origin=='action','action provenance origin required')
        action=p.action;require(action in world.actions,'action was not issued in this admitted world')
        require(action.issuer==p.target and action.channel==p.source,'action channel/issuer mismatch')
        t=p.action_return;require(t is not None and p.observed is not None,'action return evidence missing')
        n.certify(t)
        require(t.lineage=='action:'+action.identity and t.ancestor==action.identity and
                (t.scope,t.scale)==(p.scope,p.scale),'return belongs to another action lineage')
        require(action.issued<t.indices[0] and t.indices[-1]<=p.input_commit,'action consequence did not return in order')
        require(p.cross==(Q(p.observed)-Q(action.command),),'proprioceptive residual must derive from command and return')
        require(Q(p.observed)==Q(len(t.vertices)-1),
                'observed action return must equal the declared atomic-traversal projection')
    else:require(p.origin!='action' and p.action_return is None and p.observed is None,'unissued sensor return is not proprioception')
    return True


def validate_state(s,world):
    require(isinstance(s,State),'complete factored state required')
    x=s.present;w=world.get(world.target)
    validate_world(world)
    require(x.identity==w.identity and x.boundary==w.scope,'present state not bound to target wave')
    require(x.retained_rebalancing==() and x.closure_memory==(),'duplicate closure/retention coordinate inside X')
    require(s.closure_memory==tuple(t.return_id for t in w.returns),'closure memory lineage mismatch')
    require(x.motif_certificates==tuple(c.certificate_digest for c in w.certificates) and
            x.cadence==w.cadence and x.phases==len(w.returns) and type(x.phases) is int and
            type(x.orientation) is int and x.orientation==w.returns[0].roles[0], 'inherited state does not bind the admitted wave prefix')
    require(len(x.present)==2 and all(type(v) is int for v in x.present) and
            0<=x.present[0]<16 and x.present[1] in (-1,0,1),'invalid present vertex/fibre coordinates')
    require(x.closure_status in ('closed','pending') and Q(x.capacity)>0,'invalid closure/capacity state')
    Q(x.current)
    require(x.committed>=w.returns[-1].indices[-1],'present cut precedes retained closure history')
    require(Q(x.pressure)>0 and type(x.committed) is int,'invalid current pressure/cut')
    require(len({r.prior.source for r in s.retained})==len(s.retained),'duplicate retained source channel')
    for r in s.retained:validate_retention(r,world,x.committed)
    return True


def transition(s,world,model,inp):
    """One common law; evidence metadata cannot be an input."""
    validate_state(s,world);x=s.present
    require(type(inp.committed) is int and inp.committed==x.committed,'future, stale or noninteger input commitment')
    require(inp.query_observed_at is None or (type(inp.query_observed_at) is int and 0<=inp.query_observed_at<=x.committed),
            'query observation requires an exact committed native integer')
    require(len(set(inp.available))==len(inp.available),'availability aliases do not add channels')
    require(all(i in {w.identity for w in world.waves} for i in inp.available),'unbound availability source')
    if inp.query!=0:require(inp.query_observed_at is not None and inp.query_observed_at<=x.committed,'query needs a committed observation')
    # World validation never supplies an absent retained value. R is the sole source.
    terms=tuple((r.prior.source,Q(r.value)) for r in s.retained if r.prior.source in inp.available)
    carried=Q(model.gain)*sum((v for _,v in terms),Q(0))
    full=replace(x,closure_memory=s.closure_memory)
    native=n.update(full,Q(inp.attention),inp.committed)
    current=Q(native.current)+(Q(inp.query)+carried)/Q(x.pressure)
    require(len(x.present)==2 and x.present[1] in (-1,0,1),'response needs typed vertex and fibre role')
    vertex,role=x.present
    candidates=[(vertex,vertex^1,role,0 if role else 1),
                (vertex,vertex^2,role,0 if role else -1)]
    support=n.kernel(candidates,{e:Q(1) for e in candidates})
    slot=0 if current>Q(model.selector_threshold) else 1
    edge=(vertex,vertex^(1<<slot));require(n.hamming(*edge)==1,'response selected outside admitted H1 support')
    next_role=candidates[slot][3]
    n.fibre_step(role,next_role,'enter_hinge' if role else 'leave_hinge')
    next_x=replace(native,present=(edge[1],next_role),current=current,closure_memory=(),
                   retained_rebalancing=(),closure_status='pending')
    result=State(next_x,s.closure_memory,s.retained)
    return result,{'at':next_x.committed,'current':current,'edge':edge,'attention':Q(inp.attention),
                   'query':Q(inp.query),'query_observed_at':inp.query_observed_at,
                   'retained_terms':terms,'support':support,
                   'new_phase':0,'native_update_at':native.committed}


def outcome(events):
    # Retained data, labels and passive traces cannot count as their own effect.
    return tuple((e['at'],e['current'],e['edge'],e['new_phase']) for e in events)


def execute(s,world,model,inputs,trace=False):
    states=[];events=[];observations=[]
    for inp in inputs:
        s,event=transition(s,world,model,inp);states.append(s);events.append(event)
        if trace:observations.append({'state_digest':digest(s),'event':encode(event)})
    return {'final':s,'states':tuple(states),'events':tuple(events),'observations':tuple(observations)}


def execution_bytes(result):
    return packed({k:v for k,v in result.items() if k!='observations'})


def matched(a,b,world_a,world_b,model_a,model_b,inputs_a,inputs_b):
    validate_state(a,world_a);validate_state(b,world_b)
    require(a.present==b.present and a.closure_memory==b.closure_memory,'non-retained coordinates differ at intervention')
    require(world_a==world_b and model_a==model_b and inputs_a==inputs_b,'law, world or future exogenous inputs differ')
    left=execute(a,world_a,model_a,inputs_a);right=execute(b,world_b,model_b,inputs_b)
    effect=outcome(left['events'])!=outcome(right['events'])
    require(all(e['at']>a.present.committed for e in left['events']+right['events']),'same-step awareness effect')
    return {'effect':effect,'left':left,'right':right,'boundary':a.present.committed,
            'fixed_projection_digest':digest((a.present,a.closure_memory,world_a,model_a,inputs_a)),
            'left_retention':digest(a.retained),'right_retention':digest(b.retained)}


def context(pressure=1,peers=1,values=None,prefix='w',mode='polyrhythm'):
    target=n.recurrent(prefix+'target',n=4,spacing=10)
    others=tuple(n.recurrent(prefix+'peer'+str(i),n=4,spacing=7+2*i) for i in range(peers))
    require(mode in ('polyrhythm','phase_lock','nonzero_bias','jitter'),'unknown declared recurrence mode')
    if mode in ('phase_lock','nonzero_bias'):
        others=tuple(n.recurrent(prefix+'peer'+str(i),n=4,spacing=10) for i in range(peers))
    elif mode=='jitter':
        others=tuple(n.wave([n.certified(n.trace(prefix+'peer'+str(i),j,start_index=k)) for j,k in enumerate((0,8,15,28))]) for i in range(peers))
    world=World(target.identity,(target,)+others)
    values=tuple(map(Q,values if values is not None else [1]*peers));require(len(values)==peers,'one prior value per source')
    ret=[]
    for source,value in zip(others,values):
        events=n.contacts(source,target);k=max(e.committed for e in events)
        bias=(Q(1,4),Q(0)) if mode=='nonzero_bias' else (Q(0),Q(0))
        relation=n.compare(source,target,events,window=(0,k),bias=bias)
        p=Prior(source.identity,target.identity,target.scope,target.scale,k,k+1,(Q(2),),(value,),
                events,'M1:unwrapped-count-lag',relation['lag'],n.wave_prefix(source,k),n.wave_prefix(target,k),comparator_bias=bias)
        ret.append(retain(p))
    world=replace(world,prior_commitments=tuple(digest(x.prior) for x in ret))
    k=max(w.returns[-1].indices[-1] for w in world.waves)+1
    native=n.initial_state(target,Q(pressure));s=State(replace(native,committed=k,present=(0,1),closure_memory=(),retained_rebalancing=()),native.closure_memory,tuple(ret))
    validate_state(s,world)
    inputs=tuple(Input(k+i,available=tuple(w.identity for w in others)) for i in range(4))
    return s,world,Model(),inputs


def core(pressure=1,gain=1,values=None,trace=False,mode='polyrhythm'):
    s,w,m,inputs=context(pressure,values=values,mode=mode);m=replace(m,gain=Q(gain));empty=replace(s,retained=())
    pair=matched(s,empty,w,w,m,m,inputs,inputs)
    restored=replace(empty,retained=s.retained)
    again=execute(restored,w,m,inputs,trace)
    require(execution_bytes(pair['left'])==execution_bytes(again),'exact restoration did not restore later behavior')
    return {'state':s,'world':w,'model':m,'inputs':inputs,'pair':pair,'restored':again,
            'trace_equal':execution_bytes(again)==execution_bytes(execute(restored,w,m,inputs,not trace))}


def operative(s,w,m,inp):
    base=transition(s,w,m,inp)[1];sources=[]
    for r in s.retained:
        without=replace(s,retained=tuple(x for x in s.retained if x.prior.source!=r.prior.source))
        alt=transition(without,w,m,inp)[1]
        if outcome([base])!=outcome([alt]):sources.append(r.prior.source)
    nodes=tuple(sorted({w.target,*sources})) if sources else ()
    return {'nodes':nodes,'edges':tuple((source,w.target) for source in sources),'sources':tuple(sources),
            'roles':{node:('ME' if node==w.target else 'BETWEEN') for node in nodes},'outside_role':'NOT-ME'}


def label_case(prefix='renamed',impostor=False):
    s,w,m,inputs=context(peers=2,prefix=prefix);g=operative(s,w,m,inputs[0])
    bound={'I':w.target,'notice':tuple(g['sources'])}
    candidate='unconnected-node' if impostor else bound['I']
    require(candidate in g['nodes'] and g['roles'][candidate]=='ME','I label cannot create operative participation')
    return {'operative_count':len(g['nodes']),'edge_count':len(g['edges']),'I_role':g['roles'][candidate],
            'graph':g,'binding':bound}


def proprioception(mutation=None):
    s,w,m,inputs=context();source=w.waves[1];target=w.get(w.target)
    action=Action(digest((w.target,13,Q(1),source.identity)),w.target,13,Q(1),source.identity)
    returned=replace(n.trace('action:'+action.identity,start_index=14),ancestor=action.identity)
    w=replace(w,actions=(action,))
    old=s.retained[0].prior
    p=replace(old,action=action,action_return=returned,observed=Q(2),cross=(Q(1),),origin='action')
    world_commit=digest(p);w=replace(w,prior_commitments=(world_commit,))
    if mutation=='wrong_action':p=replace(p,action=replace(action,identity='other'))
    if mutation=='unissued':w=replace(w,actions=())
    if mutation=='wrong_return':p=replace(p,action_return=replace(returned,ancestor='another-action'))
    if mutation=='future_return':p=replace(p,action_return=replace(n.trace('action:'+action.identity,start_index=100),ancestor=action.identity))
    s=replace(s,retained=(retain(p),));empty=replace(s,retained=())
    result=matched(s,empty,w,w,m,m,inputs,inputs)
    return {'action':action,'return':returned,'match':result,'world':w}


def learning():
    c=core();s=c['state'];w=c['world'];m=c['model'];inputs=c['inputs']
    learned=execute(s,w,m,inputs)['final']
    future=tuple(Input(learned.present.committed+i,available=inputs[0].available) for i in range(3))
    removed=replace(learned,retained=())
    pair=matched(learned,removed,w,w,m,m,future,future)
    restoration=execute(replace(removed,retained=learned.retained),w,m,future)
    return {'acquisition':s.retained,'retained_after_training':learned.retained,'future':future,'pair':pair,
            'restored_equal':execution_bytes(restoration)==execution_bytes(pair['left'])}


def crescendo():
    s,w,m,_=context(peers=3);ids=tuple(x.identity for x in w.waves[1:]);schedule=(ids[:1],ids[:2],ids,(),ids)
    events=[];graphs=[]
    for available in schedule:
        inp=Input(s.present.committed,available=available);graphs.append(operative(s,w,m,inp));s,event=transition(s,w,m,inp);events.append(event)
    return {'cadences':tuple(x.cadence for x in w.waves),'availability':schedule,'events':events,
            'operative_sources':tuple(len(g['sources']) for g in graphs),'graphs':graphs,
            'retained_after_dropout':len(s.retained)}


def future_fold(state,world,model,inp,offer=True):
    later,event=transition(state,world,model,inp)
    if not offer or event['current']<=0:return {'admitted':False,'event':event,'phase':0}
    a,b=world.waves[:2];start=later.present.committed+1
    def outer(occurrence):
        t=n.outer_trace((a,b),'carried-outer',occurrence,'B1',1,start_index=start+10*occurrence)
        return n.certified(t,'outer',inner=(a,b))
    one=n.fold((a,b),outer(0));second=n.fold((a,b),outer(1));third=n.fold((a,b),outer(2))
    higher=n.wave((one['outer'],second['outer'],third['outer']))
    preserved=n.expose(dict(one,status='shedding'))
    # Both outer wave operands commit their actual inner construction.
    peer=n.wave([n.certified(n.outer_trace((a,b),'outer-peer',i,'B1',1,start_index=start+9*i),'outer',inner=(a,b)) for i in range(3)])
    events=n.contacts(higher,peer);comparison=n.compare(higher,peer,events,window=(0,1000))
    return {'admitted':True,'event':event,'outer_one':one,'outer_reclosure':second,'outer_third':third,'higher':higher,
            'phase':one['phase'],'inner_after_shedding':tuple(x.identity for x in preserved),
            'higher_contact':events,'higher_peer':peer,'higher_relation':comparison,'depth':1}


def contact_chain(mutation=None):
    s,w,m,inputs=context()
    if mutation=='local_impostor':
        # A local trace is not an outer construction even if scalar recurrence matches.
        n.fold(w.waves[:2],n.certified(n.trace('local',start_index=100)))
    yes=future_fold(s,w,m,inputs[0]);no=future_fold(replace(s,retained=()),w,m,inputs[0])
    restored=future_fold(replace(s,retained=s.retained),w,m,inputs[0])
    require(digest(yes)==digest(restored),'restored retention changed fold lineage')
    higher= yes['higher'];peer=yes['higher_peer'];events=n.contacts(peer,higher);k=max(e.committed for e in events)
    c=Carriage(s.retained[0],yes['outer_one']['inner'],yes['outer_one']['outer'],w.actions,w.prior_commitments)
    p=Prior(peer.identity,higher.identity,higher.scope,higher.scale,k,k+1,(Q(2),),(Q(c.retained.value),),
            events,'M1:unwrapped-count-lag',n.compare(peer,higher,events,window=(0,k))['lag'],
            n.wave_prefix(peer,k),n.wave_prefix(higher,k),origin='carried',carriage=c)
    ret=retain(p);hw=World(higher.identity,(higher,peer),prior_commitments=(digest(p),))
    native=n.initial_state(higher);cut=max(k+1,higher.returns[-1].indices[-1],peer.returns[-1].indices[-1])+1
    hs=State(replace(native,committed=cut,present=(0,1),closure_memory=()),native.closure_memory,(ret,))
    hi=(Input(cut,available=(peer.identity,)),)
    high_pair=matched(hs,replace(hs,retained=()),hw,hw,m,m,hi,hi)
    def top_offer(state):
        after,event=transition(state,hw,m,hi[0])
        if event['current']<=0:return {'admitted':False,'event':event}
        top_start=after.present.committed+1
        top=n.fold((higher,peer),n.certified(n.outer_trace((higher,peer),'chain-top',0,'B2',2,start_index=top_start),'outer',inner=(higher,peer)))
        return {'admitted':True,'event':event,'fold':top}
    top=top_offer(hs);top_removed=top_offer(replace(hs,retained=()));top_restored=top_offer(replace(hs,retained=(ret,)))
    require(digest(top)==digest(top_restored),'higher-scale exact restoration changed the later fold')
    yes=dict(yes,depth=2 if top['admitted'] else 1);restored=dict(restored,depth=yes['depth'])
    return {'positive':yes,'removal':no,'restoration':restored,'higher_match':high_pair,'higher_world':hw,'higher_state':hs,
            'top_positive':top,'top_removal':top_removed,'top_restoration':top_restored}


def mindfulness(pressure=1,extra_delay=False):
    s,w,m,base=context(pressure);s=replace(s,present=replace(s.present,current=Q(3)))
    # The delayed recurrence declares J_(k0-1)=0 as its initial history value.
    # This is a model initial condition, not an observation inferred from X_k0.
    initial_history=(s.present.committed-1,Q(0)) if extra_delay else None
    previous=initial_history;events=[];observations=[]
    for _ in range(6):
        observed=(s.present.committed,s.present.current);observations.append(observed)
        source_cut,source_value=previous if extra_delay else observed
        inp=Input(s.present.committed,query=-source_value,available=base[0].available,
                  query_observed_at=source_cut)
        previous=observed;s,event=transition(s,w,m,inp);events.append(event)
    return {'events':events,'observations':observations,'constant_forcing':Q(1),
            'declared_delay_initial_history':initial_history,
            'stability_hypothesis':Q(pressure)>Q(1,2) and not extra_delay,
            'operational_only':True}


def run_case(op,args):
    if op=='core':
        c=core(**{k:v for k,v in args.items() if k in ('pressure','gain','values','trace','mode')})
        return {'effect':c['pair']['effect'],'first_positive':c['pair']['left']['events'][0]['current'],
                'first_removal':c['pair']['right']['events'][0]['current'],'trace_equal':c['trace_equal'],
                'restored_equal':execution_bytes(c['restored'])==execution_bytes(c['pair']['left'])}
    if op=='matching':
        mutation=args['mutation']
        s,w,m,inputs=context(peers=3 if mutation=='phase_shuffle' else 1)
        b=replace(s,retained=());wb=w;mb=m;ib=inputs
        if mutation=='pressure':b=replace(b,present=replace(b.present,pressure=Q(2)))
        elif mutation=='closure_memory':b=replace(b,closure_memory=())
        elif mutation=='law':mb=replace(m,gain=Q(2))
        elif mutation=='future':ib=(replace(inputs[0],attention=Q(1)),)+inputs[1:]
        elif mutation=='duplicate':s=replace(s,present=replace(s.present,retained_rebalancing=s.retained))
        elif mutation=='wrong_lineage':
            r=s.retained[0];s=replace(s,retained=(retain(replace(r.prior,source='unknown')),))
        elif mutation=='phase_type':
            r=s.retained[0];s=replace(s,retained=(retain(replace(r.prior,relational_type=args.get('type','Tau'))),))
        elif mutation=='phase_shuffle':
            old=[r.prior.lag for r in s.retained];new=old[-1:]+old[:-1]
            require(sorted(old)==sorted(new) and old!=new,'phase control must preserve marginals and change binding')
            s=replace(s,retained=tuple(retain(replace(r.prior,lag=value)) for r,value in zip(s.retained,new)))
        elif mutation=='cross_scale':
            r=s.retained[0];s=replace(s,retained=(retain(replace(r.prior,scale=r.prior.scale+1)),))
        elif mutation=='same_step':inputs=(replace(inputs[0],committed=s.present.committed+1),)+inputs[1:];ib=inputs
        elif mutation=='value':s=replace(s,retained=(replace(s.retained[0],value=Q(2)),))
        else:raise AdmissionError('unknown hostile mutation')
        return {'effect':matched(s,b,w,wb,m,mb,inputs,ib)['effect']}
    if op=='self':
        s,w,m,inputs=context(peers=2,values=(1,-1) if args.get('cancel') else (1,1));g=operative(s,w,m,inputs[0])
        return {'nodes':len(g['nodes']),'sources':len(g['sources']),'current':transition(s,w,m,inputs[0])[1]['current']}
    if op=='label':
        a=label_case('original');b=label_case(args.get('prefix','renamed'),args.get('impostor',False))
        return {'generalizes':tuple(a[k] for k in ('operative_count','edge_count','I_role'))==tuple(b[k] for k in ('operative_count','edge_count','I_role'))}
    if op=='proprioception':return {'effect':proprioception(args.get('mutation'))['match']['effect']}
    if op=='learning':
        x=learning();return {'effect':x['pair']['effect'],'persistent':x['acquisition']==x['retained_after_training'],'restored_equal':x['restored_equal']}
    if op=='crescendo':
        x=crescendo();return {'sources':x['operative_sources'],'retained':x['retained_after_dropout']}
    if op=='chain':
        x=contact_chain(args.get('mutation'));return {'positive':x['positive']['admitted'],'removal':x['removal']['admitted'],'outer_phase':x['positive']['phase'],'depth':x['positive']['depth']}
    if op=='query':
        s,w,m,inputs=context();ordinary=execute(s,w,m,inputs,True)
        queried=(replace(inputs[0],query=Q(1),query_observed_at=s.present.committed),)+inputs[1:]
        return {'perturbs':outcome(ordinary['events'])!=outcome(execute(s,w,m,queried)['events']),
                'passive_equal':execution_bytes(ordinary)==execution_bytes(execute(s,w,m,inputs,False))}
    if op=='mindfulness':
        x=mindfulness(**args);return {'stable_at_one':all(e['current']==1 for e in x['events']), 'hypothesis':x['stability_hypothesis']}
    if op=='antisymmetry':
        s,w,m,inputs=context(peers=2,values=(1,-1));ledger=n.aod_flux([(0,1,1,1,'a'),(0,1,1,-1,'b')]);n.stokes(ledger,{0})
        return {'net':sum(v for (i,j,l),v in ledger.items() if i==0),'lineages':len({l for i,j,l in ledger}),
                'operative_sources':len(operative(s,w,m,inputs[0])['sources']),
                'antisymmetry':all(v==-ledger[(j,i,l)] for (i,j,l),v in ledger.items())}
    if op=='attention_only':
        s,w,m,inputs=context();s=replace(s,retained=())
        inputs=tuple(replace(i,attention=Q(1)) for i in inputs)
        x=matched(s,s,w,w,m,m,inputs,inputs)
        return {'current':x['left']['events'][0]['current'],'awareness_effect':x['effect'],
                'closure_memory_present':bool(s.closure_memory)}
    if op=='cpu':
        s,w,m,inputs=context();available=() if args.get('uncoupled') else inputs[0].available
        inp=replace(inputs[0],available=available);g=operative(s,w,m,inp)
        # This is an explicit operation-count proxy, not host CPU measurement.
        return {'operative_sources':len(g['sources']),'declared_operation_cost':3*len(available),
                'resource_label_establishes_awareness':False}
    raise AdmissionError('unknown new witness operation')


def execute_row(row):
    try:
        value=encode(run_case(row['operation'],row['inputs']));verdict='PASS';error=None
    except (AdmissionError,ValueError) as e:value=None;verdict='REJECT';error=str(e)
    return {'fixture_id':row['fixture_id'],'verdict':verdict,'actual':value,'error':error,
            'input_digest':digest(row['inputs']), 'expected_matched':verdict==row['expected_verdict'] and (verdict=='REJECT' or value==row['expected_exact'])}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check-data',action='store_true');args=parser.parse_args()
    path=Path(__file__).resolve().parents[1]/'data/m2/awareness_cases.jsonl'
    rows=[json.loads(t) for t in path.read_text().splitlines() if t.strip()]
    results=[execute_row(row) for row in rows];print(json.dumps({'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'results':results},indent=2))
    return 0 if all(x['expected_matched'] for x in results) else 1

if __name__=='__main__':raise SystemExit(main())

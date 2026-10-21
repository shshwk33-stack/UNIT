"""CBP final research prototype: forecast-reserved, single-request plan selection.
All bundled inputs are synthetic. This is not a routing engine or dispatch system.
Money: 10,000 KRW; emissions: kgCO2e; time: hours; quantity: pallets.
"""
from dataclasses import dataclass, asdict, replace
import math,json
from pathlib import Path

@dataclass(frozen=True)
class Plan:
    id:str
    cost:float
    emission:float
    arrival:float
    quantity:int=1000
    capacity:int=1000
    compatible:bool=True
    safe:bool=True
    confirmed:bool=True
@dataclass(frozen=True)
class State:
    budget:float=1000
    actual:float=700
    committed:float=0
    future:float=200
    buffer:float=20
    cost_limit:float=120
    deadline:float=8
    demand:int=1000

PLANS=(Plan('A',100,100,4),Plan('B',108,60,6),Plan('C',115,30,7))
TOL=1e-9

def select(state=State(),plans=PLANS):
    vals=asdict(state)
    for k,v in vals.items():
        if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v<0:raise ValueError(k)
    if state.budget<=0 or state.deadline<=0 or state.demand<=0:raise ValueError('positive budget, deadline, demand required')
    if len({p.id for p in plans})!=len(plans):raise ValueError('duplicate plan ID')
    candidates=[];excluded=[]
    for p in plans:
        if not isinstance(p.id,str) or not p.id:raise ValueError('plan id')
        for k in ['cost','emission','arrival','quantity','capacity']:
            v=getattr(p,k)
            if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v<0:raise ValueError('plan '+k)
        for k in ['compatible','safe','confirmed']:
            if not isinstance(getattr(p,k),bool):raise ValueError('plan '+k)
        why=[]
        for ok,reason in [(p.quantity>=state.demand,'quantity'),(p.capacity>=state.demand,'capacity'),(p.compatible,'compatibility'),(p.safe,'safety'),(p.confirmed,'availability'),(p.arrival<=state.deadline,'deadline'),(p.cost<=state.cost_limit,'cost')]:
            if not ok:why.append(reason)
        (excluded if why else candidates).append({'id':p.id,'reasons':why} if why else p)
    headroom=state.budget-state.actual-state.committed-state.future-state.buffer
    result={'state':vals,'cur':100*state.actual/state.budget,'headroom':headroom,'excluded':excluded,'selected':None,'suggested':None,'baseline':None,'status':'service_exception','requires_approval':True,'projected':None,'projected_with_buffer':None,'gap':None,'delta_cost':None,'delta_emission':None}
    if not candidates:return result
    baseline=min(candidates,key=lambda p:(p.cost,p.emission,p.arrival,p.id))
    fits=[p for p in candidates if p.emission<=headroom+TOL]
    chosen=min(fits,key=lambda p:(p.cost,p.emission,p.arrival,p.id)) if fits else min(candidates,key=lambda p:(p.emission,p.cost,p.arrival,p.id))
    result.update(baseline=baseline.id,suggested=chosen.id,status=('normal' if chosen.id==baseline.id else 'adjust') if fits else 'carbon_exception',requires_approval=not bool(fits),selected=chosen.id if fits else None,projected=state.actual+state.committed+state.future+chosen.emission,projected_with_buffer=state.actual+state.committed+state.future+state.buffer+chosen.emission,gap=max(0,chosen.emission-headroom),delta_cost=chosen.cost-baseline.cost,delta_emission=chosen.emission-baseline.emission)
    return result

def replay(policy,actual_factor=1):
    """20 identical known requests. F=60 kg/request, U=20 except last.
    Synthetic exception protocol: dispatcher approves lowest-emission candidate,
    preserving every request. No assertion this approval exists in operations.
    """
    actual=cost=0;exceptions=0;trace=[]
    for t in range(20):
        future=(19-t)*60 if policy=='forecast' else 0
        st=State(budget=1200,actual=actual,future=future,buffer=(20 if t<19 else 0) if policy=='forecast' else 0)
        r=select(st)
        if policy=='cost':pid='A'
        else:
            pid=r['selected'] or r['suggested'];exceptions+=int(r['requires_approval'])
        p=next(x for x in PLANS if x.id==pid);actual+=p.emission*actual_factor;cost+=p.cost
        trace.append(dict(step=t+1,selected=pid,cost=cost,actual=actual,headroom=r['headroom'],exception=policy!='cost' and r['requires_approval']))
    return dict(policy=policy,actual_factor=actual_factor,cost=cost,emission=actual,overrun=max(0,actual-1200),fulfilled=20,exceptions=exceptions,trace=trace)

def verify():
    checks=0
    def check(x):
        nonlocal checks
        assert x;checks+=1
    base=select();check(base['selected']=='B');check(base['headroom']==80);check(base['projected']==960);check(base['projected_with_buffer']==980);check(base['delta_cost']==8);check(base['delta_emission']==-40)
    check(select(State(actual=800,future=150))['selected']=='C')
    check(select(State(actual=800,future=20))['selected']=='A')
    exc=select(State(actual=760));check(exc['selected'] is None);check(exc['suggested']=='C');check(exc['gap']==10);check(exc['requires_approval'])
    check(select(State(actual=800,future=150,cost_limit=110))['suggested']=='B')
    check(select(State(deadline=3))['status']=='service_exception')
    check(select(State(committed=50))['selected']=='C')
    check(select(State(),[replace(p,safe=False) for p in PLANS])['status']=='service_exception')
    check(select(State(),[replace(p,confirmed=False) for p in PLANS])['status']=='service_exception')
    check(select(State(),[])['status']=='service_exception')
    for future in range(0,401):
        s=State(future=future);r=select(s);eligible=[p for p in PLANS if p.emission<=r['headroom']+TOL]
        check((r['selected'] is not None)==bool(eligible))
        if eligible:check(next(p.cost for p in PLANS if p.id==r['selected'])==min(p.cost for p in eligible))
    for field in ['budget','actual','committed','future','buffer','cost_limit','deadline','demand']:
        try:select(replace(State(),**{field:float('nan')}));raise AssertionError(field)
        except ValueError:checks+=1
    for f in [lambda:select(State(budget=0)),lambda:select(State(),[PLANS[0],PLANS[0]]),lambda:select(State(),[replace(PLANS[0],emission=-1)])]:
        try:f();raise AssertionError('accepted invalid input')
        except ValueError:checks+=1
    # Budget is preserved in exact nominal replay, but not guaranteed under error.
    check(replay('forecast')['emission']<=1200)
    check(replay('forecast',1.5)['emission']>1200)
    return checks

if __name__=='__main__':
    data={'units':{'cost':'10,000 KRW','emission':'kgCO2e','arrival':'h'},'plans':[asdict(p) for p in PLANS],'base':select(),'early':select(State(actual=800,future=150)),'late':select(State(actual=800,future=20)),'exception':select(State(actual=760)),'replays':[replay(p,f) for f in [1,1.25,1.5] for p in ['cost','current','forecast']],'assertions':verify()}
    Path(__file__).with_name('results.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
    print(json.dumps({**{k:data[k] for k in ['base','early','late','exception','assertions']},'replays':[{k:v for k,v in r.items() if k!='trace'} for r in data['replays']]},ensure_ascii=False,indent=2))

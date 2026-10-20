"""CBP decision prototype: explicit feasibility, relative scoring, no dispatch.

All bundled numerical inputs are synthetic. No empirical effectiveness claim.
Units: cost in KRW 10,000; emissions in kgCO2e; time in hours; pallets in units.
"""
from dataclasses import dataclass, asdict, replace
from pathlib import Path
import csv, json, math

@dataclass(frozen=True)
class Plan:
    id: str
    cost: float
    emission: float
    arrival: float
    supply: int = 1000
    capacity: int = 1000
    compatible: bool = True
    load_safe: bool = True

@dataclass(frozen=True)
class State:
    budget: float = 10000
    used: float = 8200
    committed: float = 0
    demand: int = 1000
    deadline: float = 8
    cost_limit: float = 140

PLANS=(Plan('A',100,400,6),Plan('B',110,260,4),Plan('C',140,200,3))
MODES=[('Cost',(0.7,0.1,0.2)),('Balanced',(0.5,0.3,0.2)),('Carbon',(0.2,0.6,0.2)),('Emergency',(0.1,0.8,0.1))]
def mode_index(cur):return 0 if cur<60 else 1 if cur<75 else 2 if cur<90 else 3
def validate(plans,state):
    if not plans:raise ValueError('No input plans')
    if len({p.id for p in plans})!=len(plans):raise ValueError('Duplicate plan identifiers')
    for v in [state.budget,state.used,state.committed,state.demand,state.deadline,state.cost_limit]:
        if not math.isfinite(v) or v<0:raise ValueError('Invalid state')
    if state.budget<=0 or state.deadline<=0 or state.demand<=0:raise ValueError('Positive budget, deadline, and demand required')
    for p in plans:
        for v in [p.cost,p.emission,p.arrival,p.supply,p.capacity]:
            if not math.isfinite(v) or v<0:raise ValueError('Invalid plan')
def select(plans=PLANS,state=State(),policy='CBP'):
    validate(plans,state)
    cur=100*state.used/state.budget;remaining=state.budget-state.used-state.committed
    idx=mode_index(cur);weights=MODES[idx][1] if policy=='CBP' else (.5,.3,.2) if policy=='Fixed' else (1.,0.,0.) if policy=='CostOnly' else None
    if weights is None:raise ValueError('Unknown policy')
    allowed=[];excluded={}
    for p in plans:
        reasons=[]
        if p.supply<state.demand:reasons.append('supply')
        if p.capacity<state.demand:reasons.append('capacity')
        if not p.compatible:reasons.append('compatibility')
        if not p.load_safe:reasons.append('load_safety')
        if p.arrival>state.deadline:reasons.append('deadline')
        if p.cost>state.cost_limit:reasons.append('cost_limit')
        if p.emission>remaining+1e-9:reasons.append('carbon_limit')
        if reasons:excluded[p.id]=reasons
        else:allowed.append(p)
    result={'policy':policy,'CUR':cur,'mode':MODES[idx][0],'weights':weights,'remaining':remaining,'excluded':excluded,'scores':{},'selected':None,'status':'exception_required'}
    if not allowed:return result
    cs=[p.cost for p in allowed];es=[p.emission for p in allowed]
    def norm(v,values):return 1. if max(values)==min(values) else (max(values)-v)/(max(values)-min(values))
    for p in allowed:
        utility=(norm(p.cost,cs),norm(p.emission,es),(state.deadline-p.arrival)/state.deadline)
        result['scores'][p.id]={'utility':utility,'RPS':sum(a*b for a,b in zip(utility,weights))}
    # Deterministic tie handling: least emission, cost, time, then identifier.
    winner=min(allowed,key=lambda p:(-round(result['scores'][p.id]['RPS'],12),p.emission,p.cost,p.arrival,p.id))
    result.update(selected=winner.id,status='recommendation')
    return result

def verify():
    tests=0
    def check(ok):
        nonlocal tests
        assert ok;tests+=1
    for cur,winner in [(0,'A'),(59.999,'A'),(60,'B'),(74.999,'B'),(75,'C'),(89.999,'C'),(90,'C'),(93,'C')]:
        check(select(state=replace(State(),used=cur*100))['selected']==winner)
    r=select();check(all(math.isclose(r['scores'][p]['RPS'],v) for p,v in zip('ABC',[.25,.67,.725])))
    check(select(state=replace(State(),cost_limit=120))['selected']=='B')
    check(select(state=replace(State(),cost_limit=99))['status']=='exception_required')
    check(select(state=replace(State(),used=9800))['selected']=='C')
    check(select(state=replace(State(),used=9800.01))['status']=='exception_required')
    check(select(state=replace(State(),committed=1700))['status']=='exception_required')
    check(select(state=replace(State(),used=11000))['selected'] is None)
    for field,value,reason in [('supply',999,'supply'),('capacity',999,'capacity'),('compatible',False,'compatibility'),('load_safe',False,'load_safety'),('arrival',8.01,'deadline')]:
        candidate=replace(PLANS[2],**{field:value});r=select([*PLANS[:2],candidate]);check(reason in r['excluded']['C']);check(r['selected']!='C')
    r=select([replace(p,cost=100,emission=200,arrival=4) for p in PLANS]);check(r['selected']=='A');check(all(v['utility']==(1.,1.,.5) for v in r['scores'].values()))
    for cur in [50,68,82,93]:
        check(select(state=replace(State(),used=cur*100),policy='Fixed')['selected']=='B')
        check(select(state=replace(State(),used=cur*100),policy='CostOnly')['selected']=='A')
    for state in [replace(State(),budget=0),replace(State(),deadline=0),replace(State(),used=float('nan'))]:
        try:select(state=state)
        except ValueError:tests+=1
        else:raise AssertionError('Bad input accepted')
    # Dense boundary sweep: a recommendation must never violate implemented limits.
    for pct in range(1001):
        st=replace(State(),used=pct*10);r=select(state=st)
        if r['selected']:
            p=next(p for p in PLANS if p.id==r['selected'])
            check(p.emission<=st.budget-st.used+1e-9 and p.cost<=st.cost_limit and p.arrival<=st.deadline)
        else:check(all(p.emission>st.budget-st.used or p.cost>st.cost_limit or p.arrival>st.deadline for p in PLANS))
    return tests

def export():
    out=Path(__file__).parent;tests=verify()
    res={'disclaimer':'Synthetic one-decision examples, not field results.',
         'inputs':[asdict(p) for p in PLANS],'base_state':asdict(State()),'base':select(),
         'by_state':{str(cur):{pol:select(state=replace(State(),used=cur*100),policy=pol) for pol in ['CBP','Fixed','CostOnly']} for cur in [50,68,82,93]},
         'cost_limit_120':select(state=replace(State(),cost_limit=120)),
         'no_feasible':select(state=replace(State(),used=9900)),
         'checks_passed':tests}
    (out/'model_results.json').write_text(json.dumps(res,ensure_ascii=False,indent=2))
    with (out/'scenario.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['plan','cost_10kKRW','emission_kgCO2e','hours','cost_score','carbon_score','slack_score','carbon_mode_RPS'])
        for p in PLANS:w.writerow([p.id,p.cost,p.emission,p.arrival,*res['base']['scores'][p.id]['utility'],res['base']['scores'][p.id]['RPS']])
    print(json.dumps({'checks_passed':tests,'base':res['base']['selected'],'cost_limit_120':res['cost_limit_120']['selected'],'no_feasible':res['no_feasible']['status']}))
if __name__=='__main__':export()

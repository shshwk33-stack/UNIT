"""Validate illustrative arithmetic and operational branches, not field benefit."""
from itertools import combinations
from dataclasses import dataclass

@dataclass(frozen=True)
class Option:
    name: str
    qty: int
    arrival: int
    cost: int
    co2: int

OPTIONS=(Option('전용',160,13*60,120000,90),
         Option('복귀 A',100,12*60+30,55000,35),
         Option('복귀 B',60,13*60+30,80000,30))

def choose(available_co2=70,cost_limit=135000):
    plans=[]
    for n in range(1,len(OPTIONS)+1):
        for xs in combinations(OPTIONS,n):
            if sum(x.qty for x in xs)!=160:continue
            if max(x.arrival for x in xs)>14*60:continue
            cost=sum(x.cost for x in xs);co2=sum(x.co2 for x in xs)
            if cost<=cost_limit and co2<=available_co2:
                plans.append((cost,co2,tuple(x.name for x in xs)))
    return min(plans) if plans else None

def fallback(received,backup_stock,vehicle_available=True,now=14*60,lead=90,buffer=30):
    deadline=16*60
    if min(received,backup_stock,lead,buffer)<0 or received>160:raise ValueError('invalid input')
    short=160-received;cutoff=deadline-lead-buffer
    if short==0:return {'action':'complete','qty':0,'cutoff':cutoff}
    if not vehicle_available or backup_stock<short:
        return {'action':'operator_intervention','qty':short,'cutoff':cutoff}
    if now>cutoff:
        return {'action':'missed_safety_cutoff','qty':short,'cutoff':cutoff}
    return {'action':'propose_backup','qty':short,'cutoff':cutoff,'arrival':now+lead}

if __name__=='__main__':
    assert 300-150-80==70
    assert choose()==(135000,65,('복귀 A','복귀 B'))
    assert choose(available_co2=100)==(120000,90,('전용',))
    assert choose(available_co2=60) is None
    assert choose(cost_limit=130000) is None
    assert fallback(160,60)['action']=='complete'
    r=fallback(100,60)
    assert r=={'action':'propose_backup','qty':60,'cutoff':840,'arrival':930}
    assert fallback(100,0)['action']=='operator_intervention'
    assert fallback(100,60,vehicle_available=False)['action']=='operator_intervention'
    assert fallback(100,60,now=14*60+1)['action']=='missed_safety_cutoff'
    # No fallback action may claim its planned arrival exceeds the service deadline.
    for received in range(161):
        r=fallback(received,160)
        if r['action']=='propose_backup':
            assert r['qty']==160-received and r['arrival']<=16*60
    print('PASS: carbon/cost choices, normal arrival, shortage, missing stock/vehicle, missed cutoff, and 161 quantity cases')

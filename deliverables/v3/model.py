"""Reproducible illustrative CBP model. No empirical performance claims."""
from pathlib import Path
import csv, json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

OUT = Path(__file__).parent
PLANS = [dict(id='A', cost=100, emission=400, hours=6),
         dict(id='B', cost=110, emission=260, hours=4),
         dict(id='C', cost=140, emission=200, hours=3)]
MODES = [('Cost', (0.7,0.1,0.2)), ('Balanced',(0.5,0.3,0.2)),
         ('Carbon',(0.2,0.6,0.2)), ('Emergency',(0.1,0.8,0.1))]
def inverse_minmax(values):
    a=np.asarray(values,dtype=float)
    return np.ones_like(a) if np.ptp(a)==0 else (a.max()-a)/np.ptp(a)
def mode_for(cur):
    return 0 if cur<60 else 1 if cur<75 else 2 if cur<90 else 3
def scores():
    return np.column_stack([inverse_minmax([p['cost'] for p in PLANS]),
        inverse_minmax([p['emission'] for p in PLANS]),
        [(8-p['hours'])/8 for p in PLANS]])
def compute():
    utilities=scores()
    rps={name:(utilities@np.array(w)).tolist() for name,w in MODES}
    result=dict(disclaimer='설명용 가상 입력. 실측·견적·감축 성과가 아님.',
        demand_pallets=1000, deadline_hours=8, budget_kg=10000,
        used_kg=8200, CUR_percent=82, plans=PLANS,
        normalized_scores=utilities.tolist(), RPS=rps,
        winners={k:PLANS[int(np.argmax(v))]['id'] for k,v in rps.items()})
    assert result['winners']==dict(Cost='A',Balanced='B',Carbon='C',Emergency='C')
    assert np.allclose(utilities, [[1,0,.25],[.75,.7,.5],[0,1,.625]])
    assert np.allclose(rps['Carbon'], [.25,.67,.725])
    assert all(abs(sum(w)-1)<1e-12 for _,w in MODES)
    assert [mode_for(x) for x in (59.999,60,74.999,75,89.999,90)]==[0,1,1,2,2,3]
    assert np.allclose(inverse_minmax([3,3,3]),[1,1,1])
    assert all(p['emission']<=10000*(1-.93) for p in PLANS)
    return result
def export():
    r=compute();(OUT/'model_results.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
    with (OUT/'scenario.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.writer(f);w.writerow(['plan','cost_만원','emission_kgCO2e','arrival_hours','cost_score','carbon_score','time_slack_score']+[n+'_RPS' for n,_ in MODES])
        for i,p in enumerate(PLANS):w.writerow([p['id'],p['cost'],p['emission'],p['hours'],*r['normalized_scores'][i],*[r['RPS'][n][i] for n,_ in MODES]])
    font_manager.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
    plt.rcParams.update({'font.family':'Noto Sans CJK JP','font.size':12,'axes.unicode_minus':False,'svg.fonttype':'none'})
    fig,ax=plt.subplots(figsize=(10,4.7),layout='constrained')
    a=np.linspace(0,.8,801);u=scores();colors=['#233B60','#598C9F','#00877F']
    cross1=.265/1.05;cross2=.61/.95
    for left,right,c in [(0,cross1,colors[2]),(cross1,cross2,colors[1]),(cross2,.8,colors[0])]:ax.axvspan(left,right,color=c,alpha=.08)
    for i,p in enumerate(PLANS):ax.plot(a,u[i,0]*a+u[i,1]*(.8-a)+u[i,2]*.2,color=colors[i],lw=2.6,label='운송안 '+p['id'])
    for x,label in [(.2,'Carbon'),(.5,'Balanced'),(.7,'Cost')]:
        ax.axvline(x,color='#97A6B4',ls=':',lw=1);ax.text(x,.97,label,ha='center',fontsize=10,color='#42556B')
    for x,t in [(cross1/2,'C 우선'),((cross1+cross2)/2,'B 우선'),((cross2+.8)/2,'A 우선')]:ax.text(x,.08,t,ha='center',weight='bold',color='#233B60')
    ax.set(xlim=(0,.8),ylim=(0,1.05),xlabel='비용 가중치 α  (탄소 β = 0.8 − α, 시간 여유 γ = 0.2 고정)',ylabel='RPS 종합점수')
    ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',alpha=.18);ax.legend(loc='upper left',frameon=False,ncol=3)
    (OUT/'figures').mkdir(exist_ok=True)
    for ext in ('png','svg','pdf'):fig.savefig(OUT/'figures'/('weight_sensitivity.'+ext),dpi=200,bbox_inches='tight')
    plt.close(fig)
    print(json.dumps({'winners':r['winners'],'Carbon_RPS':r['RPS']['Carbon'],'checks':'passed'},ensure_ascii=False))
if __name__=='__main__':export()

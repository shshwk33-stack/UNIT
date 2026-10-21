from pathlib import Path
import json,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
R=Path(__file__).parent;(R/'figures').mkdir(exist_ok=True)
font=FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
plt.rcParams.update({'svg.fonttype':'path','axes.spines.top':False,'axes.spines.right':False,'axes.spines.left':False,'axes.edgecolor':'#dae3ee','xtick.color':'#687d94','ytick.color':'#687d94','axes.labelcolor':'#14243c'})
data=json.loads((R/'results.json').read_text())
f,ax=plt.subplots(figsize=(8.5,3.7));f.patch.set_facecolor('white')
for name,pol,c in [('비용 우선','cost','#b98152'),('현재 잔여량','current','#4976da'),('예측 반영 CBP','forecast','#087f70')]:
 r=next(x for x in data['replays'] if x['policy']==pol and x['actual_factor']==1)
 ax.plot([0]+[x['step'] for x in r['trace']],[0]+[x['actual'] for x in r['trace']],label=name,color=c,lw=2.6)
ax.axhline(1200,color='#99a9ba',ls='--',lw=1.5,label='관리 목표 1,200kg');ax.set_xlim(0,20);ax.set_ylim(0,2200);ax.set_xticks([0,5,10,15,20]);ax.grid(axis='y',color='#edf1f5');ax.set_xlabel('처리 요청 수 / 건',fontproperties=font);ax.set_ylabel('누적 배출 / kgCO2e',fontproperties=font);ax.legend(prop=font,ncol=2,loc='upper left',frameon=False,fontsize=9);f.tight_layout();f.savefig(R/'figures/replay.svg');plt.close(f)
f,ax=plt.subplots(figsize=(8.5,2.7))
for a,b,c,name in [(0,180,'#d6e7f5','A'),(180,220,'#9edbd1','B'),(220,250,'#087f70','C'),(250,320,'#f3d9ca','예외 검토')]:
 ax.axvspan(a,b,0.20,.80,color=c);ax.text((a+b)/2,0.5,name,ha='center',va='center',fontproperties=font,color='white' if name=='C' else '#14243c',fontsize=14)
ax.set_xlim(0,320);ax.set_ylim(0,1);ax.set_yticks([]);ax.set_xticks([0,100,180,220,250,320]);ax.set_xlabel('미래 공급 예상 배출 F / kgCO2e',fontproperties=font);ax.set_title('미래 공급 부담이 커지면 추천이 달라진다',fontproperties=font,loc='left',color='#14243c',pad=5);f.tight_layout();f.savefig(R/'figures/headroom.svg');plt.close(f)
print('2 figures generated')

for generated_svg in (R/'figures').glob('*.svg'):
    generated_svg.write_text('\n'.join(line.rstrip() for line in generated_svg.read_text().splitlines()).rstrip()+'\n')

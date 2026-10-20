from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np
font_manager.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
plt.rcParams.update({'font.family':'Noto Sans CJK JP','font.size':10,'axes.unicode_minus':False,'svg.fonttype':'path'})
a=np.linspace(0,.8,801)
fig,ax=plt.subplots(figsize=(8.4,3),layout='constrained')
for left,right,c in [(0,53/210,'#07816f'),(53/210,61/95,'#6b8ea8'),(61/95,.8,'#4976da')]:ax.axvspan(left,right,color=c,alpha=.065)
for name,y,c in [('A',a+.05,'#4976da'),('B',.05*a+.66,'#7d91a7'),('C',.925-a,'#07816f')]:ax.plot(a,y,lw=2.2,color=c,label='운송안 '+name)
for x,name in [(.2,'탄소 모드'),(.5,'균형 모드'),(.7,'비용 모드')]:
    ax.axvline(x,color='#a5b3c4',linestyle=':',lw=1)
    ax.text(x,.97,name,ha='center',color='#485e76',fontsize=9)
ax.set(xlim=(0,.8),ylim=(0,1.05),xlabel='비용 가중치 α (γ=0.2, β=0.8−α)',ylabel='RPS')
ax.spines[['top','right']].set_visible(False)
ax.grid(axis='y',alpha=.15)
ax.legend(loc='upper center',bbox_to_anchor=(.5,1.23),ncol=3,frameon=False,fontsize=9)
fig.savefig(Path(__file__).parent/'figures/sensitivity.svg',bbox_inches='tight')

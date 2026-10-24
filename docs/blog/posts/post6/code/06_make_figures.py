"""Publication figures from the official-data estimates; no synthetic observations."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'result/figures';OUT.mkdir(parents=True,exist_ok=True)
TEAL='#176b73';ORANGE='#c16b35';GREY='#596168'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,
 'axes.spines.right':False,'axes.spines.left':False,'axes.edgecolor':'#b7b7b0',
 'axes.labelcolor':'#343b3c','text.color':'#242b2c','xtick.color':'#535b5c','ytick.color':'#535b5c',
 'savefig.facecolor':'white','figure.facecolor':'white'})
def save(fig,name):
 fig.savefig(OUT/name,dpi=300,bbox_inches='tight');plt.close(fig)
d=pd.read_csv(ROOT/'result/pilot_ige.csv')
fig,ax=plt.subplots(figsize=(9,4.7));ys=[3.4,2.4,1,0]
labels=['A · Early career · single year','B · Early career · both averaged',
        'C · Midlife · single year','D · Midlife · both averaged']
for i, row in d.iterrows():
 color=TEAL if i<2 else ORANGE
 ax.errorbar(row.beta,ys[i],xerr=[[row.beta-row.ci_low],[row.ci_high-row.beta]],fmt='o',
             color=color,ecolor=color,capsize=4,ms=7,lw=1.8)
 ax.annotate(f'{row.beta:.3f}',(row.beta,ys[i]),xytext=(0,12),textcoords='offset points',ha='center',weight='bold',color=color)
ax.set_yticks(ys,labels);ax.tick_params(axis='y',length=0,pad=12)
ax.set_xlim(0,.82);ax.set_ylim(-.6,4.1);ax.set_xlabel('Intergenerational family-income elasticity (IGE)',labelpad=12)
ax.set_xticks(np.arange(0,.81,.2));ax.grid(axis='x',color='#e8e8e3');ax.set_axisbelow(True)
ax.axhline(1.7,color='#deded8',lw=1)
fig.subplots_adjust(left=.35,bottom=.18,right=.98,top=.96)
save(fig,'figure1_ige_windows.png')

f=pd.read_csv(ROOT/'result/factorial_ige.csv')
fig,axes=plt.subplots(1,2,figsize=(9,4.8),sharey=True)
for ax,stage,title in zip(axes,['young','midlife'],['Early career','Midlife']):
 for cm,color,marker,label in [('single',TEAL,'o','Child family income: single year'),('multi',ORANGE,'s','Child family income: three observations')]:
  q=f[(f.stage==stage)&(f.child_measure==cm)].set_index('father_measure').loc[['single','multi']]
  ax.plot([0,1],q.beta,color=color,marker=marker,lw=2,ms=7,label=label)
  for xx,beta in enumerate(q.beta):
   ax.annotate(f'{beta:.3f}',(xx,beta),xytext=(0,12 if cm=='single' else -19),textcoords='offset points',ha='center',color=color,weight='bold',fontsize=10)
 ax.set_title(title,loc='left',weight='bold',pad=18);ax.set_xticks([0,1],['Single year','Three observations'])
 ax.set_xlim(-.25,1.25);ax.set_ylim(.10,.59);ax.grid(axis='y',color='#e8e8e3');ax.set_axisbelow(True)
 ax.set_xlabel('Father’s family-income measure',labelpad=12)
axes[0].set_ylabel('Estimated IGE',labelpad=12)
handles,labels=axes[0].get_legend_handles_labels();fig.legend(handles,labels,loc='upper center',ncol=2,frameon=False,bbox_to_anchor=(.5,1.02),fontsize=10)
fig.subplots_adjust(top=.8,left=.09,right=.98,bottom=.19,wspace=.2)
save(fig,'figure2_averaging_decomposition.png')

v=pd.read_csv(ROOT/'result/person_volatility.csv');fig,ax=plt.subplots(figsize=(9,4.8))
for group,color,label in [('Children, early',TEAL,'Early career'),('Children, midlife',ORANGE,'Midlife')]:
 x=np.sort(v[v.group==group].within_log_sd.to_numpy());y=np.arange(1,len(x)+1)/len(x)
 ax.step(x,y,where='post',color=color,lw=2.2,label=label)
 med=np.median(x);ax.plot([med,med],[0,.5],color=color,ls='--',lw=1.2)
 ax.annotate(f'Median {med:.3f}',(med,.5),xytext=(14,15 if group.endswith('early') else -25),textcoords='offset points',color=color,weight='bold')
ax.set_xlim(0,2.4);ax.set_ylim(0,1.02);ax.set_yticks([0,.25,.5,.75,1],['0%','25%','50%','75%','100%'])
ax.set_ylabel('Share of children at or below this fluctuation',labelpad=12)
ax.set_xlabel('Within-person fluctuation in relative log income',labelpad=12)
ax.grid(axis='y',color='#e8e8e3');ax.set_axisbelow(True);ax.legend(frameon=False,loc='lower right')
fig.subplots_adjust(left=.11,right=.98,bottom=.20,top=.97)
save(fig,'figure3_income_dispersion.png')
print('Saved three 300-dpi figures.')

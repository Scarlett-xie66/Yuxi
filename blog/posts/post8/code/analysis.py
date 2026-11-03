#!/usr/bin/env python3
"""Rebuild the June respondent comparison, simulations, charts and article."""
from pathlib import Path
import base64, io, json, re
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import hypergeom

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / 'data/raw/BDJO_Dataset.dta'
OUT = ROOT / 'result'
for p in (ROOT/'data/processed', OUT/'figures', OUT/'tables'): p.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(4082026)
d = pd.read_stata(RAW, convert_categoricals=False).copy()
d['date'] = pd.Timestamp('1960-01-01') + pd.to_timedelta(d.date_code, unit='D')
# Use the first valid, post-transfer interview in June for each person.
z = d[(d.post_treat == 1) & d.treat_constant.isin([0,1]) & d.groupgeneralbusinessstatus.notna() & d.date.between('2020-06-01','2020-06-30')].copy()
z = z.sort_values(['identifier','date']).drop_duplicates('identifier')
z['open'] = (z.groupgeneralbusinessstatus == 0).astype(int)
z[['identifier','date','treat_constant','open']].to_csv(ROOT/'data/processed/june_sample.csv',index=False)
a=z[z.treat_constant==1].open.to_numpy();b=z[z.treat_constant==0].open.to_numpy(); n1,n0=len(a),len(b);k1,k0=int(a.sum()),int(b.sum());p1,p0=a.mean(),b.mean();obs=100*(p1-p0)
assert n1 and n0 and z.identifier.is_unique
B=20000
boot=100*(rng.binomial(n1,p1,B)/n1-rng.binomial(n0,p0,B)/n0)
ci=np.percentile(boot,[2.5,97.5]); pd.DataFrame({'gap_pp':boot}).to_csv(OUT/'tables/bootstrap_draws.csv',index=False)
# Conditional sharp-null illustration. Exact probability uses the fixed number
# open and fixed group sizes; assignments are exchangeable only under the stated model.
N=n1+n0;K=k1+k0; support=np.arange(max(0,n1-(N-K)),min(n1,K)+1)
delta=100*(support/n1-(K-support)/n0); pmf=hypergeom.pmf(support,N,K,n1)
p_exact=float(pmf[np.abs(delta)>=abs(obs)-1e-10].sum())
abs_levels=np.sort(np.unique(np.abs(delta)))
cutoff=next(v for v in abs_levels if pmf[np.abs(delta)>=v-1e-10].sum()<=.05)
reject=pmf[np.abs(delta)>=cutoff-1e-10].sum()
permuted=rng.hypergeometric(K,N-K,n1,B); null=100*(permuted/n1-(K-permuted)/n0)
p_mc=(1+np.count_nonzero(abs(null)>=abs(obs)-1e-10))/(B+1)
pd.DataFrame({'gap_pp':delta,'probability':pmf,'reject_at_5pct':np.abs(delta)>=cutoff-1e-10}).to_csv(OUT/'tables/null_distribution.csv',index=False)
M,J=2000,1000;truth=6.0
s1=rng.binomial(n1,.90,M);s0=rng.binomial(n0,.84,M)
c1=rng.binomial(n1,(s1/n1)[:,None],(M,J))/n1;c0=rng.binomial(n0,(s0/n0)[:,None],(M,J))/n0
intervals=np.percentile(100*(c1-c0),[2.5,97.5],axis=1).T;hit=(intervals[:,0]<=truth)&(truth<=intervals[:,1]);hits=int(hit.sum())
pd.DataFrame({'lower_pp':intervals[:,0],'upper_pp':intervals[:,1],'covers_truth':hit}).to_csv(OUT/'tables/coverage_simulations.csv',index=False)
# Report an auditable count without assuming the unresolved 753-person flow.
eligible=d[(d.week<900)&d.treat_constant.isin([0,1])]; assert eligible.groupby('identifier').treat_constant.nunique().max()==1
person=eligible.drop_duplicates('identifier');counts=person.groupby('treat_constant').identifier.nunique().to_dict(); pd.DataFrame([{'group':'5,000 shillings','identifiers_in_released_file':counts.get(1,0),'valid_june':n1,'open':k1},{'group':'500 shillings','identifiers_in_released_file':counts.get(0,0),'valid_june':n0,'open':k0}]).to_csv(OUT/'tables/sample_counts.csv',index=False)
summary={'seed':4082026,'n_high':n1,'n_low':n0,'open_high':k1,'open_low':k0,'share_high':p1,'share_low':p0,'gap_pp':obs,'ci_low_pp':ci[0],'ci_high_pp':ci[1],'coverage_trials':M,'covered':hits,'coverage_pct':100*hit.mean(),'exact_conditional_p':p_exact,'null_simulation_p':p_mc,'null_rejection_probability':float(reject),'null_absolute_cutoff_pp':float(cutoff)}
(OUT/'tables/summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.spines.left':False,'figure.facecolor':'white','axes.facecolor':'white'})
def save(fig,name):
 p=OUT/'figures'/name;fig.savefig(p,dpi=300,bbox_inches='tight',facecolor='white');plt.close(fig);return 'data:image/png;base64,'+base64.b64encode(p.read_bytes()).decode()
fig,ax=plt.subplots(figsize=(8,2.5));ax.barh([1,0],[100*p1,100*p0],color=['#23737a','#b6c9c7'],height=.49);ax.set_yticks([1,0],['5,000 shillings (~$50)','500 shillings (~$5)']);ax.set_xlim(0,110);ax.set_xlabel('Businesses open at first June interview (%)');ax.tick_params(length=0)
for y,v,n in [(1,100*p1,n1),(0,100*p0,n0)]:ax.text(v+1.5,y,f'{v:.1f}% (n={n})',va='center',weight='bold')
i1=save(fig,'figure1_group_shares.png')
fig,ax=plt.subplots(figsize=(8,3.3));ax.hist(boot,bins=55,color='#8ab4b2',edgecolor='white',linewidth=.3);ax.axvline(obs,color='#145b62',lw=2,label=f'Observed: {obs:.1f} pp');ax.axvline(ci[0],color='#ae633e',ls='--');ax.axvline(ci[1],color='#ae633e',ls='--',label=f'95% interval: {ci[0]:.1f} to {ci[1]:.1f} pp');ax.set_xlabel('Difference in open-business shares (percentage points)');ax.set_ylabel('Bootstrap resamples');ax.legend(frameon=False);i2=save(fig,'figure2_bootstrap.png')
fig,ax=plt.subplots(figsize=(8,4.4));ax.hlines(np.arange(100),intervals[:100,0],intervals[:100,1],color=np.where(hit[:100],'#619e99','#ba674a'),lw=1.6);ax.axvline(truth,color='#1c444b',lw=1.5);ax.set_yticks([]);ax.set_xlabel('Interval for the simulated difference (percentage points)');ax.text(.02,.98,f'{hits:,} of {M:,} intervals include the true 6-point difference',transform=ax.transAxes,va='top',fontsize=10,bbox=dict(facecolor='white',edgecolor='none'));i3=save(fig,'figure3_coverage.png')
fig,ax=plt.subplots(figsize=(9,4));freq=np.array([(permuted==v).sum() for v in support]);vis=(delta>-13)&(delta<13);colors=np.where(abs(delta)>=cutoff-1e-10,'#bb745c','#8fb4b0');ax.bar(delta[vis],freq[vis],width=abs(delta[1]-delta[0])*.87,color=colors[vis],edgecolor='white',linewidth=.35);ax.axvline(obs,color='#163f4a',lw=2.2);ax.axvline(-obs,color='#163f4a',lw=1.2,ls=':');ax.axvline(0,color='#888',lw=.8);ax.set_xlabel('Simulated difference in open-business shares (percentage points)');ax.set_ylabel('Number of simulated assignments');ax.tick_params(length=0);ax.text(.02,.98,'Rust: rejection region (5% test)\nSolid: observed gap  ·  Dotted: opposite gap',transform=ax.transAxes,va='top',fontsize=9,bbox=dict(facecolor='white',alpha=.9,edgecolor='none'));i4=save(fig,'figure4_null.png')
# All four PNG assets are embedded for a reliable offline preview.
s=(ROOT/'code/article_template.html').read_text(encoding='utf-8')
# Replace images in document order, including the Figure 2 no-JS fallback.
images=iter([i1,i2,i3,i4]);s=re.sub(r'data:image/png;base64,[A-Za-z0-9+/=]+',lambda _:next(images),s)
# Dynamic numbers in article text; replacement is limited to prose, not SVG data.
head,script=s.split('<script>',1)
subs={'89.9':f'{100*p1:.1f}','84.3':f'{100*p0:.1f}','258 of 287':f'{k1} of {n1}','274 of 325':f'{k0} of {n0}','5.6':f'{obs:.1f}','0.4 to 10.8':f'{ci[0]:.1f} to {ci[1]:.1f}','1,898':f'{hits:,}','102 miss':f'{M-hits:,} miss','94.9%':f'{100*hit.mean():.1f}%','4.6%':f'{100*p_exact:.1f}%','46 in 1,000':f'{round(1000*p_exact)} in 1,000','about 4.2%':f'about {100*reject:.1f}%'}
for old,new in subs.items():head=head.replace(old,new)
head=head.replace('In June 2020, women who received a larger cash transfer in Dandora, a neighborhood in Nairobi, Kenya, were more likely to report that their businesses were open.', 'During the first wave of COVID-19, customers disappeared from markets in Dandora, a neighborhood in Nairobi, Kenya. For women running small businesses, a sudden loss of sales threatened both daily income and the money needed to restock. Researchers tested whether a one-time cash transfer could help.')
head=head.replace('The p-value asks a related question: how often do simulated gaps fall at least as far from zero as the observed gap? Counting both directions gives approximately <strong>4.2%</strong>, or about 42 in 1,000 shuffles.', 'The p-value asks a related question: if every possible reassignment were considered under this model, how often would the gap be at least as far from zero as the observed gap? Counting both directions gives an exact p-value of approximately <strong>4.2%</strong>, or about 42 in 1,000 possible assignments.')
head=head.replace('Here the simulated difference can take only certain values, so the rejection region cannot contain exactly 5% of the null distribution. Its exact probability is about 4.2%; the 4.2% p-value is estimated from 20,000 simulations and varies with the random draws.', 'Only certain differences are possible with these group sizes, so a rejection region need not contain exactly 5% of the null distribution. Here its exact probability is about 4.2%. The bars use simulated assignments; the reported p-value is calculated from all possible assignments under the same model.')
head=head.replace('Under the simplified no-effect simulation, a gap at least as extreme appeared in <strong>4.2%</strong> of reallocations.', 'Under the simplified no-effect model, the exact probability of a gap at least as extreme was <strong>4.2%</strong>.')
head=head.replace('The result is an illustration of hypothesis testing for June respondents. Because response occurred after payment and the original assignment has not been fully reconstructed, it is not an exact test for everyone in the experiment.', 'This is a teaching illustration for June respondents. Because survey response occurred after payment and the original assignment has not been fully reconstructed, it is not an exact test for everyone in the experiment.')
# The visible orange tails are calculated before observing the statistic, from the null distribution.
head=head.replace('The three red lines shown miss that value; most of the 100 displayed intervals contain it.', f'{int((~hit[:100]).sum())} red lines shown miss that value; most of the 100 displayed intervals contain it.')
head=head.replace('The data point to a higher open-business share among June respondents who received 5,000 shillings. The interval and no-effect simulation help assess that difference, while the size of any causal effect remains uncertain.', 'Among June respondents, the larger-payment group had a higher open-business share. The interval allows a small difference as well as a larger one; the no-effect model provides a benchmark for how unusual the observed gap would be. Survey response prevents this comparison from identifying an effect for all original participants.')
# Accurate reproducibility section, generated paths match the archive.
a=head.index('<section class="repro">');bpos=head.index('</section>',a)+len('</section>')
repro='''<section class="repro"><h2>Reproducibility</h2><p>The accompanying project includes the study data, analysis code and generated results. Render <code>index.qmd</code> to rebuild the calculations, figures and article. The standalone project uses the following structure:</p><pre>index.qmd                         # render entry point
index.html                        # rendered standalone article
README.md                         # setup and replication instructions
code/
├── analysis.py                   # sample, simulations, figures and article
└── article_template.html         # article layout and interactive controls
data/
├── raw/BDJO_Dataset.dta          # authors' study data
└── processed/june_sample.csv     # one valid June interview per participant
result/
├── figures/                      # four 300-dpi PNG figures
└── tables/                       # counts, draws, intervals and null distribution</pre><p>Place the project at <code>blog/posts/post8/</code>, keep the folders together, and render <code>index.qmd</code>. R, knitr and Python with pandas, NumPy, SciPy and Matplotlib must be installed. The script uses a fixed random seed and local data; it saves intermediate data and results before displaying the article. Source: <a href="https://data.mendeley.com/datasets/zs5p47vx8k/1">Donovan (2022), Mendeley Data, version 1</a>, CC BY 4.0.</p></section>'''
head=head[:a]+repro+head[bpos:]
q={str(i):[float(v) for v in np.percentile(boot,[(100-i)/2,100-(100-i)/2])] for i in range(80,100)};h,e=np.histogram(boot,bins=45,range=(-10,22));hist={'hist':h.tolist(),'edges':e.tolist()}
script=re.sub(r'const q=\{.*?\};const slider', 'const q='+json.dumps(q,separators=(',',':'))+';const slider',script,count=1)
script=re.sub(r'const histogram=\{.*?\};function draw', 'const histogram='+json.dumps(hist,separators=(',',':'))+';function draw',script,count=1)
script=script.replace('X(5.587778)',f'X({obs})').replace('observed gap (5.6 points)',f'observed gap ({obs:.1f} points)')
final=head+'<script>'+script
(ROOT/'index.html').write_text(final,encoding='utf-8')
# Knitr emits only the body and styles. The standalone layout remains centered.
style=re.search(r'<style>(.*?)</style>',final,re.S).group(0) + '<style>#title-block-header { display: none; }</style>'
body=final.split('<body>',1)[1].rsplit('</body>',1)[0]
(OUT/'article_body.html').write_text(style+'\n'+body,encoding='utf-8')
print(json.dumps(summary,indent=2))

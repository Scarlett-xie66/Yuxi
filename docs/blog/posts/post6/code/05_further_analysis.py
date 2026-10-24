"""Fixed-sample factorial income-measure comparisons; no new records or exclusions."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
d = pd.read_csv(ROOT / 'result/matched_income.csv')
ids, inv = np.unique(d.father_id, return_inverse=True)
specs = [(stage, fm, cm, f'father_log_{fm}', f'{stage}_log_{cm}')
         for stage in ['young', 'midlife'] for fm in ['single', 'multi']
         for cm in ['single', 'multi']]
def slope(x, y, w=None):
    xm, ym = np.average(x, weights=w), np.average(y, weights=w)
    return np.sum((x-xm)*(y-ym) if w is None else w*(x-xm)*(y-ym)) / np.sum((x-xm)**2 if w is None else w*(x-xm)**2)

point = np.array([slope(d[x].to_numpy(), d[y].to_numpy()) for _,_,_,x,y in specs])
rng = np.random.default_rng(20261023)
boot = np.zeros((1000, len(specs)))
for b in range(len(boot)):
    freq = np.bincount(rng.integers(len(ids), size=len(ids)), minlength=len(ids))
    w = freq[inv]
    for j, (_,_,_,x,y) in enumerate(specs):
        boot[b,j] = slope(d[x].to_numpy(), d[y].to_numpy(), w)
rows = []
for j, (stage, fm, cm, x, y) in enumerate(specs):
    lo, hi = np.quantile(boot[:,j], [.025,.975])
    loo = [slope(d.loc[d.father_id.ne(f),x].to_numpy(), d.loc[d.father_id.ne(f),y].to_numpy()) for f in ids]
    rows.append(dict(stage=stage, father_measure=fm, child_measure=cm, beta=point[j], ci_low=lo, ci_high=hi,
                     n_children=len(d), n_fathers=len(ids), leave_one_father_min=min(loo), leave_one_father_max=max(loo)))
pd.DataFrame(rows).to_csv(ROOT/'result/factorial_ige.csv', index=False)
contrasts = []
def contrast(name, a, b):
    lo, hi = np.quantile(boot[:,a]-boot[:,b], [.025,.975])
    contrasts.append(dict(comparison=name, difference=point[a]-point[b], ci_low=lo, ci_high=hi))
contrast('Midlife minus early; single-year incomes',4,0)
contrast('Midlife minus early; both incomes averaged',7,3)
for offset, stage in [(0,'Early'),(4,'Midlife')]:
    contrast(stage+': average father only; child single',offset+2,offset)
    contrast(stage+': average child only; father single',offset+1,offset)
    contrast(stage+': average both versus neither',offset+3,offset)
pd.DataFrame(contrasts).to_csv(ROOT/'result/paired_contrasts.csv', index=False)

# Compare within-person dispersion after subtracting the mean in each observed year.
p = pd.read_csv(ROOT/'result/person_income.csv')
vols=[]
for label, who, years in [('Fathers',d.father_id.unique(),[1999,2001,2003]),
                          ('Children, early',d.child_id,[1999,2001,2003]),
                          ('Children, midlife',d.child_id,[2015,2017,2019])]:
    q=p[p.person_id.isin(who)&p.survey_year.isin(years)].copy()
    assert q.groupby('person_id').size().eq(3).all()
    q['centered_log']=q.log_income-q.groupby('survey_year').log_income.transform('mean')
    z=q.groupby('person_id').centered_log.std().rename('within_log_sd').reset_index()
    z['group']=label;vols.append(z)
v=pd.concat(vols,ignore_index=True);v.to_csv(ROOT/'result/person_volatility.csv',index=False)
wide=v[v.group.ne('Fathers')].pivot(index='person_id',columns='group',values='within_log_sd')
volsummary={'children':len(wide),'fraction_with_lower_midlife_dispersion':float((wide['Children, midlife']<wide['Children, early']).mean()),
            'median_early':float(wide['Children, early'].median()),'median_midlife':float(wide['Children, midlife'].median()),
            'median_fathers':float(v[v.group.eq('Fathers')].within_log_sd.median())}
volsummary['proportional_median_drop']=1-volsummary['median_midlife']/volsummary['median_early']
(ROOT/'result/further_analysis.json').write_text(json.dumps(volsummary,indent=2)+'\n')
np.savez_compressed(ROOT/'result/factorial_bootstrap.npz',slopes=boot,point=point)
print(pd.DataFrame(rows).to_string(index=False))
print(pd.DataFrame(contrasts).to_string(index=False))
print(json.dumps(volsummary,indent=2))

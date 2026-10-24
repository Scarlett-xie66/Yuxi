"""Independent pandas reconstruction, log-log pilot estimates, and diagnostic checks."""
from pathlib import Path
import hashlib,json,sqlite3
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];mapping=json.loads((ROOT/'data/wave_mapping.json').read_text())
x=pd.read_csv(ROOT/'data/selected/individual.csv');b=x[mapping['birthyear_vars']];birth=b.where(b.ge(1850)&b.le(2023)).ffill(axis=1).iloc[:,-1]
p=pd.DataFrame({'person_id':x.ER30001*1000+x.ER30002,'birth':birth,'sex':x.ER32000,'father_id':np.where(x.ER32016.gt(0)&x.ER32017.between(1,399),x.ER32016*1000+x.ER32017,np.nan)})
assert p.person_id.is_unique
links=p[p.birth.between(1972,1976)].merge(p[['person_id','birth']].rename(columns={'person_id':'father_id','birth':'father_birth'}),on='father_id',validate='many_to_one')
links=links[(2000-links.father_birth).between(45,60)&(links.birth-links.father_birth).between(15,55)]
assert len(links)==1490
panel=[];source_rows=0
for w in mapping['individual']:
 year=w['survey_year'];fmap=next(v for v in mapping['family'] if v['survey_year']==year);f=pd.read_csv(ROOT/f'data/selected/family_{year}.csv');source_rows+=len(f)
 f=f.rename(columns={fmap['id_var']:'family_id',fmap['income_var']:'income'})
 assert f.family_id.is_unique
 r=pd.DataFrame({'person_id':p.person_id,'family_id':x[w['family_id_var']],'sequence':x[w['sequence_var']],'relationship':x[w['relationship_var']],'survey_age':x[w['age_var']],'birth':birth})
 r=r[r.family_id.gt(0)&r.sequence.between(1,20)&r.relationship.isin([10,20,22])&r.birth.notna()].merge(f[['family_id','income']],on='family_id',validate='many_to_one')
 r=r[r.income.gt(0)&r.income.le(9999999 if year<=2003 else 9999997)].copy();r['survey_year']=year;r['income_year']=year-1;r['stage']='early' if year<=2003 else 'midlife';r['log_income']=np.log(r.income);panel.append(r)
panel=pd.concat(panel,ignore_index=True);assert not panel.duplicated(['person_id','survey_year']).any()
sumtab=panel.groupby(['person_id','stage']).log_income.agg(['size','mean']);early=sumtab.xs('early',level='stage');late=sumtab.xs('midlife',level='stage')
expected=links[links.father_id.isin(early[early['size']==3].index)&links.person_id.isin(early[early['size']==3].index)&links.person_id.isin(late[late['size']==3].index)].copy()
# Exclude any common family unit while both generations' early incomes are used.
cy=panel[panel.stage=='early'].merge(expected[['person_id','father_id']],on='person_id')
cy=cy.merge(panel[panel.stage=='early'][['person_id','survey_year','family_id']].rename(columns={'person_id':'father_id','family_id':'father_family'}),on=['father_id','survey_year'])
bad=set(cy[cy.family_id==cy.father_family].person_id);expected=expected[~expected.person_id.isin(bad)]
d=pd.read_csv(ROOT/'result/matched_income.csv');assert set(d.child_id)==set(expected.person_id) and len(d)==187
for col,vals in [('father_log_multi',d.father_id.map(early['mean'])),('young_log_multi',d.child_id.map(early['mean'])),('midlife_log_multi',d.child_id.map(late['mean']))]:np.testing.assert_allclose(d[col],vals,rtol=1e-12)
for col,ids,year in [('father_log_single',d.father_id,2001),('young_log_single',d.child_id,2001),('midlife_log_single',d.child_id,2017)]:
 vals=panel[panel.survey_year==year].set_index('person_id').log_income;np.testing.assert_allclose(d[col],ids.map(vals),rtol=1e-12)
# Keep complete rows and the same fathers for all specification comparisons.
def fit(x,y):
 return np.linalg.lstsq(np.column_stack([np.ones(len(x)),x]),y,rcond=None)[0]
specs=[('Early career, single year','father_log_single','young_log_single'),('Early career, 3-observation mean logs','father_log_multi','young_log_multi'),('Midlife, single year','father_log_single','midlife_log_single'),('Midlife, 3-observation mean logs','father_log_multi','midlife_log_multi')]
ids,inv=np.unique(d.father_id,return_inverse=True);rng=np.random.default_rng(20261023);boot=np.zeros((1000,4));rows=[]
for rep in range(1000):
 freq=np.bincount(rng.integers(len(ids),size=len(ids)),minlength=len(ids));weights=freq[inv]
 for j,(name,xc,yc) in enumerate(specs):
  xx,yy=d[xc].to_numpy(),d[yc].to_numpy();xm=np.average(xx,weights=weights);ym=np.average(yy,weights=weights)
  boot[rep,j]=np.sum(weights*(xx-xm)*(yy-ym))/np.sum(weights*(xx-xm)**2)
for j,(name,xc,yc) in enumerate(specs):
 a,beta=fit(d[xc],d[yc]);lo,hi=np.quantile(boot[:,j],[.025,.975]);rows.append({'specification':name,'beta':beta,'ci_low':lo,'ci_high':hi,'children':len(d),'fathers':len(ids),'associated_pct_for_10pct_higher_father_income':100*(1.1**beta-1)})
est=pd.DataFrame(rows);est.to_csv(ROOT/'result/pilot_ige.csv',index=False)
# Source-field birth-year correction and age consistency diagnostics; do not silently exclude records.
relevant=panel[(panel.person_id.isin(d.child_id))|((panel.person_id.isin(d.father_id))&(panel.stage=='early'))].copy()
relevant['calendar_age']=relevant.survey_year-relevant.birth;relevant['age_discrepancy']=relevant.calendar_age-relevant.survey_age
relevant[['person_id','survey_year','survey_age','calendar_age','age_discrepancy']].to_csv(ROOT/'result/age_checks.csv',index=False)
role_sample=panel[panel.person_id.isin(d.child_id)].copy();role_sample.groupby('stage').agg(children=('person_id','nunique'),income_min=('income','min'),income_median=('income','median'),income_max=('income','max')).reset_index().to_csv(ROOT/'result/sample_income_ranges.csv',index=False)
# Within-person time variation in generation-wave-centered log income, to remove common period shifts.
vol=[]
for name,who,stage in [('Fathers',set(d.father_id),'early'),('Children, early career',set(d.child_id),'early'),('Children, midlife',set(d.child_id),'midlife')]:
 q=panel[panel.person_id.isin(who)&(panel.stage==stage)].copy();q['centered']=q.log_income-q.groupby('survey_year').log_income.transform('mean');sd=q.groupby('person_id').centered.std()
 vol.append({'group':name,'people':len(sd),'median_within_person_log_sd':sd.median(),'mean_within_person_log_sd':sd.mean()})
pd.DataFrame(vol).to_csv(ROOT/'result/income_variability.csv',index=False)
summary={'status':'passed','provenance':'Only the seven official PSID ZIPs uploaded by the user; no third-party records or CPI','source_individual_rows':len(x),'source_family_rows':source_rows,'cohort_children':4925,'eligible_links':len(links),'matched_children':len(d),'distinct_fathers':len(ids),'daughters':int((d.child_sex==2).sum()),'sons':int((d.child_sex==1).sum()),'complete_sample_topcoded_records':int(d.n_topcoded.sum()),'minimum_common_sample_income':float(relevant.income.min()),'sample_records_one_dollar':int((relevant.income==1).sum()),'age_records_checked':len(relevant),'age_discrepancies_outside_0_1':int((~relevant.age_discrepancy.isin([0,1])).sum()),'age_discrepancies_abs_gt_2':int((relevant.age_discrepancy.abs()>2).sum()),'birthyear_fields_conflict_all_people':int((b.where(b.ge(1850)&b.le(2023)).nunique(axis=1)>1).sum()),'all_raw_person_year_keys_unique':True,'independent_pandas_sample_and_six_income_measures_match_sql':True,'balanced_3_observations_each_window':bool((d[['father_n','young_n','midlife_n']]==3).all().all()),'bootstrap_draws':1000,'paired_midlife_minus_young_single_ci':np.quantile(boot[:,2]-boot[:,0],[.025,.975]).tolist(),'paired_midlife_minus_young_multi_ci':np.quantile(boot[:,3]-boot[:,1],[.025,.975]).tolist(),'pilot_estimates':rows}
(ROOT/'result/validation.json').write_text(json.dumps(summary,indent=2)+'\n')
print(est[['specification','beta','ci_low','ci_high']].to_string(index=False));print(json.dumps(summary,indent=2))

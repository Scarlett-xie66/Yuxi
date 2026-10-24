"""Insert executed SQL previews and calculated results into the editable article."""
from pathlib import Path
import argparse,base64,html,json,re,sqlite3
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--body-only',action='store_true')
args=parser.parse_args()
database = ROOT / 'data/processed/analysis.sqlite'
if not database.is_file():
    raise FileNotFoundError(f'Analysis database not found: {database}')
c = sqlite3.connect(str(database))
def table(df):
    return '<div class="table-scroll">\n'+df.to_html(index=False,border=0,classes='data-table',float_format=lambda x:f'{x:,.3f}')+'\n</div>'
def query(sql):return table(pd.read_sql_query(sql,c))
sql=(ROOT/'sql/02_match.sql').read_text(encoding='utf-8')
def statement(name):
    start=sql.index('CREATE TABLE '+name+' AS')
    end=sql.index(';',start)+1
    return sql[start:end]
tokens={
 'SQL_LINKS':statement('father_child_links'),
 'SQL_PERSON_INCOME':statement('person_income'),
 'SQL_SUMMARY':statement('income_summary'),
 'SQL_COMMON':statement('common_before_household_check'),
 'SQL_MATCHED':statement('matched_income'),
 'RAW_PREVIEW':query('SELECT ER17002,ER20456 FROM raw_2001 ORDER BY ER17002 LIMIT 5'),
 'LINK_PREVIEW':query('SELECT child_id,father_id,child_birth_year,father_birth_year FROM father_child_links ORDER BY child_id LIMIT 5'),
 'JOIN_AUDIT':table(pd.read_csv(ROOT/'result/roster_join_audit.csv')[['survey_year','responding_people','unmatched_family_ids']]),
 'INCOME_PREVIEW':query('SELECT person_id,income_year,family_interview_id,income_nominal FROM person_income WHERE person_id=4031 ORDER BY income_year'),
 'SUMMARY_PREVIEW':query('SELECT person_id,stage,n_obs,log_multi,log_single FROM income_summary WHERE person_id IN (4003,4031,7035) ORDER BY person_id,stage LIMIT 5'),
 'MATCHED_PREVIEW':query('SELECT child_id,father_id,father_income_2000,child_income_2000,child_income_2016 FROM matched_income ORDER BY child_id LIMIT 5'),
 'SELECTION':table(pd.read_csv(ROOT/'result/selection_counts.csv').rename(columns={'step':'Sample rule','children':'Children'})),
}
f=pd.read_csv(ROOT/'result/factorial_ige.csv')
rows=[]
for stage in ['young','midlife']:
 for fm in ['single','multi']:
  q=f[(f.stage==stage)&(f.father_measure==fm)].set_index('child_measure')
  rows.append({'Child stage':'Early career' if stage=='young' else 'Midlife','Father’s family income':'Single year' if fm=='single' else 'Three observations',
               'Child’s family: single year':q.loc['single','beta'],'Child’s family: three observations':q.loc['multi','beta'],
               'Change from averaging child’s family income':f"{q.loc['multi','beta']-q.loc['single','beta']:+.3f}"})
tokens['FACTORIAL_TABLE']=table(pd.DataFrame(rows))
main=pd.read_csv(ROOT/'result/pilot_ige.csv')
models=[('A','Early career','2000','2000'),
        ('B','Early career','1998 / 2000 / 2002','1998 / 2000 / 2002'),
        ('C','Midlife','2000','2016'),
        ('D','Midlife','1998 / 2000 / 2002','2014 / 2016 / 2018')]
spec_rows=[];interpret=[]
for j,(label,stage,fy,cy) in enumerate(models):
    r=main.iloc[j]
    spec_rows.append({'Model / child stage':f'{label} · {stage}',
                     'Father’s family: years':fy,'Child’s family: years':cy,
                     'IGE':f'{r.beta:.3f}','95% interval':f'[{r.ci_low:.3f}, {r.ci_high:.3f}]'})
    effect=100*(1.1**r.beta-1)
    assert abs(effect-r.associated_pct_for_10pct_higher_father_income)<1e-10
    interpret.append({'model':label,'child_stage':stage,'beta':r.beta,
                      'illustrative_father_difference_pct':10,
                      'model_implied_child_difference_pct':effect})
tokens['SPECIFICATION_TABLE']=table(pd.DataFrame(spec_rows))
interp=pd.DataFrame(interpret)
interp.to_csv(ROOT/'result/income_interpretation.csv',index=False)
display=interp.copy()
display['model']=display.model+' · '+display.child_stage
display['beta']=display.beta.map(lambda v:f'{v:.3f}')
display['illustrative_father_difference_pct']='10% (chosen comparison)'
display['model_implied_child_difference_pct']=display.model_implied_child_difference_pct.map(lambda v:f'{v:.2f}%')
tokens['INTERPRETATION_TABLE']=table(display.drop(columns='child_stage').rename(columns={
    'model':'Model','beta':'IGE used','illustrative_father_difference_pct':'Father’s family-income gap',
    'model_implied_child_difference_pct':'Implied child family-income gap'}))
contrasts=pd.read_csv(ROOT/'result/paired_contrasts.csv').iloc[:2]
tokens['AGE_CONTRAST_TABLE']=table(pd.DataFrame({
    'Income measure':['Single year (C − A)','Both averaged (D − B)'],
    'Midlife minus early IGE':contrasts.difference.map(lambda v:f'{v:.3f}'),
    '95% paired interval':[f'[{r.ci_low:.3f}, {r.ci_high:.3f}]' for _,r in contrasts.iterrows()]}))
stats=json.loads((ROOT/'result/further_analysis.json').read_text(encoding='utf-8'))
vol=pd.read_csv(ROOT/'result/person_volatility.csv')
wide=vol[vol.group.ne('Fathers')].pivot(index='person_id',columns='group',values='within_log_sd')
lower=int((wide['Children, midlife']<wide['Children, early']).sum())
assert abs(lower/len(wide)-stats['fraction_with_lower_midlife_dispersion'])<1e-12
disp=[{'Result':'Early-career median income fluctuation','Value':f'{stats["median_early"]:.3f}',
       'Calculation':'Median across the same 187 children'},
      {'Result':'Midlife median income fluctuation','Value':f'{stats["median_midlife"]:.3f}',
       'Calculation':'Median across the same 187 children'},
      {'Result':'Reduction in the median','Value':f'{100*stats["proportional_median_drop"]:.1f}%',
       'Calculation':'100 × (1 − midlife median / early median)'},
      {'Result':'Children with smaller midlife fluctuations','Value':f'{100*lower/len(wide):.1f}%',
       'Calculation':f'100 × {lower} / {len(wide)}'}]
pd.DataFrame(disp).to_csv(ROOT/'result/dispersion_summary.csv',index=False)
tokens['DISPERSION_TABLE']=table(pd.DataFrame(disp))
influence=f[(f.father_measure=='multi')&(f.child_measure=='multi')]
tokens['INFLUENCE_TABLE']=table(pd.DataFrame({
    'Both-generation averages':['Early career (B)','Midlife (D)'],
    'Lowest leave-one-father IGE':influence.leave_one_father_min.map(lambda v:f'{v:.3f}'),
    'Highest leave-one-father IGE':influence.leave_one_father_max.map(lambda v:f'{v:.3f}')}))
tokens['STYLE']=(ROOT/'code/article_style.html').read_text(encoding='utf-8')
for key,name in [('FIGURE1_DATA','figure1_ige_windows.png'),
                 ('FIGURE2_DATA','figure2_averaging_decomposition.png'),
                 ('FIGURE3_DATA','figure3_income_dispersion.png')]:
    tokens[key]='data:image/png;base64,'+base64.b64encode((ROOT/'result/figures'/name).read_bytes()).decode('ascii')
body=(ROOT/'code/_article_body.md').read_text(encoding='utf-8')
for k,v in tokens.items():body=body.replace('@@'+k+'@@',v)
assert '@@' not in body
match=re.fullmatch(r'---\n(.*?)\n---\n(.*)',body,re.S)
assert match,'Article template must have one YAML header'
header,content=match.groups()
(ROOT/'result/_article_rendered.md').write_text(content,encoding='utf-8')
preview_header=header.replace('  enabled: true','  enabled: false')
(ROOT/'result/_preview.qmd').write_text('---\n'+preview_header+'\n---\n'+content,encoding='utf-8')
if not args.body_only:
    entry=(ROOT/'code/_quarto_entry.py').read_text(encoding='utf-8')
    (ROOT/'index.qmd').write_text('---\n'+header+'\n---\n\n```{python}\n'+entry.rstrip()+'\n```\n',encoding='utf-8')
print('Generated article outputs'+(' without changing index.qmd.' if args.body_only else ' and executable index.qmd.'))

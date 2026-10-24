"""Execute every displayed analysis block and compare its full table to production."""
from pathlib import Path
import argparse,contextlib,io,json,os,re,tempfile
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--archives-dir',type=Path);args=ap.parse_args()
qmd=(ROOT/'result/_article_rendered.md').read_text(encoding='utf-8')
blocks=re.findall(r'^```(python|sql)\n(.*?)^```',qmd,re.M|re.S)
env={};counts={'python_executed':0,'sql_executed':0,'source_extraction':'compiled; original ZIP optional'}
os.chdir(ROOT)
with contextlib.redirect_stdout(io.StringIO()):
 for lang,code in blocks:
  if lang=='python':
   compile(code,'article_python','exec')
   if 'archive = Path(' in code:
    if args.archives_dir:
     archive=(args.archives_dir/'fam2001er.zip').resolve()
     with tempfile.TemporaryDirectory() as tmp:
      raw=Path(tmp)/'data/raw';raw.mkdir(parents=True)
      (raw/archive.name).symlink_to(archive)
      os.chdir(tmp)
      try:exec(code,env)
      finally:os.chdir(ROOT)
     expected=pd.read_csv(ROOT/'data/selected/family_2001.csv')[['ER17002','ER20456']]
     pd.testing.assert_frame_equal(env['raw_2001'],expected)
     counts['source_extraction']='executed; all 7,406 rows match selected source columns'
    continue
   exec(code,env);counts['python_executed']+=1
  else:
   if code.lstrip().startswith('CREATE TABLE'):env['con'].executescript(code)
   else:pd.read_sql_query(code,env['con'])
   counts['sql_executed']+=1
 rebuilt=env['d'].sort_values('child_id').reset_index(drop=True)
 expected=pd.read_csv(ROOT/'result/matched_income.csv').sort_values('child_id').reset_index(drop=True)
 pd.testing.assert_frame_equal(rebuilt,expected,check_dtype=False,rtol=1e-12)
 actual=env['comparison'];target=pd.read_csv(ROOT/'result/factorial_ige.csv')
 for _,r in actual.iterrows():
  v=target[(target.stage==r.stage)&(target.father_measure==r.father_measure)&(target.child_measure==r.child_measure)].beta.iloc[0]
  np.testing.assert_allclose(r.IGE,v,rtol=1e-12)
 stats=json.loads((ROOT/'result/further_analysis.json').read_text(encoding='utf-8'));sd=env['paired_sd']
 np.testing.assert_allclose(sd['Early career'].median(),stats['median_early'],rtol=1e-12)
 np.testing.assert_allclose(sd.Midlife.median(),stats['median_midlife'],rtol=1e-12)
 np.testing.assert_allclose((sd.Midlife<sd['Early career']).mean(),stats['fraction_with_lower_midlife_dispersion'])
 # Four main estimates must use the same bootstrap draws as the expanded analysis.
 main=pd.read_csv(ROOT/'result/pilot_ige.csv');full=pd.read_csv(ROOT/'result/factorial_ige.csv').iloc[[0,3,4,7]]
 np.testing.assert_allclose(main[['beta','ci_low','ci_high']],full[['beta','ci_low','ci_high']],rtol=1e-12)
 # Check the displayed interpretation against coefficients, rather than rounded labels.
 conversion=pd.read_csv(ROOT/'result/income_interpretation.csv')
 shown=pd.DataFrame(env['interpretation'])
 np.testing.assert_allclose(shown.implied_child_difference_pct,100*(1.10**main.beta-1),rtol=1e-12)
 np.testing.assert_allclose(conversion.model_implied_child_difference_pct,shown.implied_child_difference_pct,rtol=1e-12)
 assert conversion.illustrative_father_difference_pct.eq(10).all()
 assert int((sd.Midlife<sd['Early career']).sum())==129
 reduction=100*(1-sd.Midlife.median()/sd['Early career'].median())
 np.testing.assert_allclose(reduction,100*stats['proportional_median_drop'],rtol=1e-12)
counts.update(status='passed',matched_rows=len(rebuilt),matched_columns=len(rebuilt.columns),eight_slopes_match=True,
              dispersion_matches=True,main_bootstrap_matches=True,percentage_conversion_matches=True,
              paired_dispersion_count=129)
(ROOT/'result/tutorial_validation.json').write_text(json.dumps(counts,indent=2)+'\n')
print(json.dumps(counts,indent=2))

"""Matched annual changes; one piecewise growth specification with sex comparisons."""
from pathlib import Path
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
os.environ.setdefault('OMP_NUM_THREADS', '1')
import hashlib
import json
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from file_io import write_csv, write_text

ROOT = Path(__file__).resolve().parents[1]

def analyze():
    raw = ROOT / 'data/raw'; out = ROOT / 'result'; out.mkdir(exist_ok=True)
    manifest = json.loads((raw / 'manifest.json').read_text(encoding='utf-8'))
    for s in manifest['sources']:
        assert hashlib.sha256((raw / s['file']).read_bytes()).hexdigest() == s['sha256']
    records = json.loads((raw / 'countries.json').read_text(encoding='utf-8'))[1]
    meta = pd.DataFrame([{'iso3': x['id'], 'country': x['name'], 'region': x['region']['value'].strip()}
        for x in records if x['region']['id'] != 'NA'])
    data = None
    for name in ['gdp', 'female_national', 'male_national', 'female_modeled', 'male_modeled']:
        source = json.loads((raw / (name + '.json')).read_text(encoding='utf-8'))[1]
        q = pd.DataFrame([{'iso3': x['countryiso3code'], 'year': int(x['date']), name: x['value'],
            name + '_note': x.get('footnote', '')} for x in source if x['countryiso3code'] in set(meta.iso3)])
        assert not q.duplicated(['iso3', 'year']).any()
        data = q if data is None else data.merge(q, on=['iso3', 'year'], validate='one_to_one')
    data = data.merge(meta, on='iso3', validate='many_to_one').sort_values(['iso3', 'year'])
    data['known_break'] = False
    for sex in ['female', 'male']:
        field = sex + '_national'
        notes = data[field + '_note'].str.lower()
        data[sex + '_scope_flag'] = notes.str.contains('age coverage|main cities|urban areas only', regex=True)
        data['known_break'] |= notes.str.contains('break in series', regex=False)
        data[sex + '_rate'] = data[field].mask(data[sex + '_scope_flag'])
        data['d_' + sex] = data.groupby('iso3')[sex + '_rate'].diff()
        data['d_' + sex + '_modeled'] = data.groupby('iso3')[sex + '_modeled'].diff()
    consecutive = data.year - data.groupby('iso3').year.shift() == 1
    usable = data[['d_female', 'd_male', 'gdp']].notna().all(axis=1) & consecutive
    candidates = data[usable].copy()
    audit = meta.merge(candidates.groupby('iso3').size().rename('paired_changes_before_break_filter'), on='iso3', how='left')
    clean = candidates[~candidates.known_break].copy()
    counts = clean.groupby('iso3').size()
    ids = counts[counts >= 10].index
    panel = clean[clean.iso3.isin(ids)].copy()
    assert panel.year.between(2001, 2024).all() and not panel.known_break.any()
    assert not panel.duplicated(['iso3', 'year']).any()
    audit = audit.merge(counts.rename('changes_after_break_filter'), on='iso3', how='left').fillna(0)
    audit['included'] = audit.iso3.isin(ids)
    write_csv(out / 'coverage.csv', audit)
    panel['difference'] = panel.d_female - panel.d_male
    panel['depth'] = (-panel.gdp).clip(lower=0)
    panel['expansion'] = panel.gdp.clip(lower=0)
    panel['contraction'] = panel.gdp.lt(0)
    write_csv(out / 'analysis_panel.csv', panel)
    write_csv(ROOT / 'data/processed/analysis_panel.csv', panel)
    display_columns = ['iso3', 'country', 'region', 'year', 'gdp', 'female_rate', 'male_rate', 'known_break']
    display = data[data.iso3.isin(ids)][display_columns].copy()
    display.loc[display.known_break, ['female_rate', 'male_rate']] = np.nan
    write_csv(out / 'country_history.csv', display)
    quality_cols = ['iso3', 'country', 'year', 'known_break', 'female_scope_flag', 'male_scope_flag',
        'female_national_note', 'male_national_note']
    write_csv(out / 'source_quality_flags.csv', data[quality_cols])

    formula = '{outcome} ~ depth + expansion + C(iso3) + C(year)'
    results = []; residuals = []
    common = panel.dropna(subset=['d_female_modeled', 'd_male_modeled']).copy()
    specifications = [('National: all years', panel), ('National: before 2020', panel[panel.year < 2020]),
        ('National: common source sample', common), ('Modeled: common source sample', common)]
    for label, frame in specifications:
        q = frame.copy()
        if label.startswith('Modeled'):
            q['d_female'] = q.d_female_modeled; q['d_male'] = q.d_male_modeled
            q['difference'] = q.d_female - q.d_male
        for outcome, human in [('d_female', 'Women'), ('d_male', 'Men'), ('difference', 'Women minus men')]:
            m = smf.ols(formula.format(outcome=outcome), q).fit(cov_type='cluster',
                cov_kwds={'groups': q.iso3}, use_t=True)
            for term in ['depth', 'expansion']:
                lo, hi = m.conf_int().loc[term]
                results.append(dict(specification=label, outcome=human, term=term,
                    estimate=float(m.params[term]), se=float(m.bse[term]), ci_low=float(lo), ci_high=float(hi),
                    p_value=float(m.pvalues[term]), n=int(m.nobs), countries=q.iso3.nunique(),
                    contraction_observations=int(q.contraction.sum()), formula=formula.format(outcome=outcome)))
            if label == 'National: all years' and outcome == 'difference':
                f = q[['iso3', 'year']].copy(); f['residual'] = m.resid; residuals.append(f)
    result = pd.DataFrame(results)
    # On identical rows and regressors, the directly estimated sex contrast equals the slope difference.
    for label in result.specification.unique():
        for term in ['depth', 'expansion']:
            q = result[(result.specification == label) & (result.term == term)].set_index('outcome')
            np.testing.assert_allclose(q.loc['Women', 'estimate'] - q.loc['Men', 'estimate'],
                q.loc['Women minus men', 'estimate'], atol=1e-10)
    write_csv(out / 'model_results.csv', result)
    write_csv(out / 'model_residuals.csv', pd.concat(residuals, ignore_index=True))
    recessions = panel[panel.contraction]
    summaries = panel.groupby('contraction').agg(observations=('iso3', 'size'),
        countries=('iso3', 'nunique'), women_change_pp=('d_female', 'mean'), men_change_pp=('d_male', 'mean'),
        mean_difference_pp=('difference', 'mean')).reset_index()
    write_csv(out / 'descriptive_results.csv', summaries)
    summary = dict(countries=panel.iso3.nunique(), observations=len(panel), contraction_observations=len(recessions),
        contraction_countries=recessions.iso3.nunique(), female_mean=float(recessions.d_female.mean()),
        male_mean=float(recessions.d_male.mean()), female_better=int((recessions.difference > 0).sum()),
        both_fell=int(((recessions.d_female < 0) & (recessions.d_male < 0)).sum()),
        women_fell=int((recessions.d_female < 0).sum()),
        pre2020_contractions=int((recessions.year < 2020).sum()),
        source_manifest_sha256=hashlib.sha256((raw / 'manifest.json').read_bytes()).hexdigest(),
        paired_changes_before_flags=len(candidates), explicit_break_changes_removed=int(candidates.known_break.sum()),
        minimum_matched_changes=10, first_change_year=int(panel.year.min()), last_change_year=int(panel.year.max()))
    write_text(out / 'summary.json', json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))
    print(result[(result.term == 'depth') & (result.outcome == 'Women minus men')].to_string(index=False))
    return panel, display, result, summary

if __name__ == '__main__':
    analyze()

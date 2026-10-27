"""Independent data checks, fixed-effect reconstruction and HTML/word-count checks."""
from pathlib import Path
from html.parser import HTMLParser
import json
import re
import numpy as np
import pandas as pd
from scipy.stats import t
from file_io import write_text

ROOT = Path(__file__).resolve().parents[1]

class ArticleParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.stack=[]; self.ids=[]; self.words=[]
    def handle_starttag(self, tag, attrs):
        attrs=dict(attrs)
        if 'id' in attrs:self.ids.append(attrs['id'])
        if tag in ['article','figure','div','details','section','script','style']:self.stack.append(tag)
    def handle_endtag(self, tag):
        if tag in ['article','figure','div','details','section','script','style']:
            assert self.stack and self.stack.pop()==tag, 'Unclosed/misnested HTML: '+tag
    def handle_data(self, value):self.words.append(value)

class MainTextParser(HTMLParser):
    """Count article paragraphs only, stopping before Reproducibility.

    Keep inline emphasis text; exclude headings, figure content, controls,
    footnotes and superscript note markers. Join inline nodes without adding
    spaces so markup does not change the count.
    """
    def __init__(self):
        super().__init__(); self.stack=[]; self.paragraphs=[]; self.current=[]; self.stopped=False
    def handle_starttag(self, tag, attrs):
        if tag not in {'br','hr','meta','link','input','img'}: self.stack.append(tag)
        if self.stack==['article','p']: self.current=[]
    def handle_endtag(self, tag):
        if tag=='p' and self.stack==['article','p'] and not self.stopped:
            self.paragraphs.append(''.join(self.current).strip())
        if tag in self.stack:
            self.stack=self.stack[:len(self.stack)-1-self.stack[::-1].index(tag)]
    def handle_data(self, value):
        if self.stack==['article','h2'] and value.strip()=='Reproducibility': self.stopped=True
        if not self.stopped and self.stack[:2]==['article','p'] and 'sup' not in self.stack:
            self.current.append(value)

def validate():
    out=ROOT/'result'; p=pd.read_csv(out/'analysis_panel.csv'); m=pd.read_csv(out/'model_results.csv')
    summary=json.loads((out/'summary.json').read_text())
    lookup={}
    for name in ['female_national','male_national','gdp']:
        lookup[name]={(x['countryiso3code'],int(x['date'])):x
            for x in json.loads((ROOT/'data/raw'/f'{name}.json').read_text())[1] if x['countryiso3code']}
    for row in p.itertuples():
        for sex in ['female','male']:
            now=lookup[sex+'_national'][(row.iso3,row.year)]
            prev=lookup[sex+'_national'][(row.iso3,row.year-1)]
            assert now['value'] is not None and prev['value'] is not None
            for record in [now,prev]:
                note=record.get('footnote','').lower()
                assert not any(k in note for k in ['age coverage','main cities','urban areas only'])
            assert 'break in series' not in now.get('footnote','').lower()
            np.testing.assert_allclose(getattr(row,'d_'+sex),now['value']-prev['value'],atol=1e-12)
        np.testing.assert_allclose(row.gdp,lookup['gdp'][(row.iso3,row.year)]['value'],atol=1e-12)
    assert p.groupby('iso3').size().ge(10).all() and not p.duplicated(['iso3','year']).any()
    np.testing.assert_allclose(p.difference,p.d_female-p.d_male,atol=1e-12)
    q=p[p.contraction]
    assert len(q)==summary['contraction_observations']
    np.testing.assert_allclose([q.d_female.mean(),q.d_male.mean()],[summary['female_mean'],summary['male_mean']])
    assert int((q.difference>0).sum())==summary['female_better']
    assert int((q.d_female<0).sum())==summary['women_fell']

    # Independent alternating demeaning, not the production formula/dummy implementation.
    Z=p[['depth','expansion','difference']].to_numpy().copy()
    codes=[pd.factorize(p.iso3)[0],pd.factorize(p.year)[0]]
    for iteration in range(500):
        old=Z.copy()
        for groups in codes:
            n=np.bincount(groups)
            for j in range(3):Z[:,j]-=(np.bincount(groups,weights=Z[:,j])/n)[groups]
        if np.max(np.abs(Z-old))<1e-12:break
    else:raise AssertionError('Fixed-effect absorption did not converge')
    X,y=Z[:,:2],Z[:,2]; beta=np.linalg.lstsq(X,y,rcond=None)[0]
    e=y-X@beta; inv=np.linalg.inv(X.T@X)
    groups=codes[0];G=len(np.unique(groups));N=len(p);K=G+len(np.unique(codes[1]))-1+2
    scores=np.stack([X[groups==g].T@e[groups==g] for g in np.unique(groups)])
    cov=(G/(G-1))*((N-1)/(N-K))*inv@(scores.T@scores)@inv
    lo,hi=beta[0]+np.array([-1,1])*t.ppf(.975,G-1)*np.sqrt(cov[0,0])
    target=m[(m.specification=='National: all years')&(m.outcome=='Women minus men')&(m.term=='depth')].iloc[0]
    np.testing.assert_allclose([beta[0],lo,hi],[target.estimate,target.ci_low,target.ci_high],atol=1e-9)
    common1=m[m.specification=='National: common source sample'];common2=m[m.specification=='Modeled: common source sample']
    assert common1.n.unique().tolist()==common2.n.unique().tolist()
    assert common1.countries.unique().tolist()==common2.countries.unique().tolist()
    payload=json.loads((out/'dashboard_data.json').read_text())
    assert len(payload['recessions'])==len(q)
    for row in payload['recessions']:
        source=q[(q.iso3==row['iso3'])&(q.year==row['year'])].iloc[0]
        np.testing.assert_allclose([row[k] for k in ['d_female','d_male','difference','gdp']],
            [source[k] for k in ['d_female','d_male','difference','gdp']],atol=1e-10)
    body=(out/'_article_body.html').read_text();html=ArticleParser();html.feed(body)
    assert not html.stack and len(html.ids)==len(set(html.ids))
    assert body.count('<h2>Takeaway</h2>')==1
    main=MainTextParser(); main.feed(body)
    wc={'main_text_words':sum(len(p.split()) for p in main.paragraphs),
        'counting_rule':'Whitespace-separated words in main article paragraphs, including standfirst, opening question and Takeaway. Excludes title, byline, section headings, figures, captions, chart controls, source notes, footnotes, note markers and Reproducibility.',
        'main_text_paragraphs':len(main.paragraphs)}
    assert 650<=wc['main_text_words']<=850,wc
    write_text(out/'word_count.json',json.dumps(wc,indent=2)+'\n')
    for f in ROOT.rglob('*'):
        # R keeps this log open while Python runs; Windows may deny reading it.
        if f == out / 'rebuild_log.txt':
            continue
        if f.is_file() and f.suffix in ['.py','.js','.md','.qmd','.json','.html','.css','.txt','.csv']:
            assert not re.search('[\u3400-\u9fff]',f.read_text(encoding='utf-8')),str(f)
    receipt={'status':'passed','matched_changes_independently_rebuilt':len(p),'countries':G,
        'contractions':len(q),'source_scope_and_break_flags_checked':True,
        'independent_fixed_effect_slope_and_cluster_interval_match':True,
        'direct_gender_contrast_identity':True,'payload_matches_csv':True,'html_balanced':True,
        'word_count':wc,'native_r_quarto':'not available; not executed',
        'browser_rendering':'not verified; interaction logic checked separately'}
    write_text(out/'validation.json',json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))

if __name__=='__main__':validate()

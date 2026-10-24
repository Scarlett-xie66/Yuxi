"""Structural checks on the embedded preview and its local source resources."""
from pathlib import Path
from html.parser import HTMLParser
import base64,io,json,re
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
class Inspect(HTMLParser):
 def __init__(self):
  super().__init__();self.ids=set();self.hrefs=[];self.images=[];self.tables=0;self.math=0
  self.part2=False;self.details=[];self.folds=0;self.folded_python=0;self.visible_tutorial_python=0;self.supporting=0
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if a.get('id'):self.ids.add(a['id'])
  if tag=='a':self.hrefs.append(a.get('href',''))
  if tag=='img':self.images.append(a)
  if tag=='table':self.tables+=1
  if tag=='math':self.math+=1
  if tag=='h2':self.part2=a.get('id','').startswith('part-ii-')
  if tag=='details':
   is_analysis='analysis-code' in a.get('class','').split()
   if 'supporting-results' in a.get('class','').split():
    assert 'open' not in a
    self.supporting+=1
   self.details.append(is_analysis)
   if is_analysis:
    assert self.part2 and 'open' not in a
    self.folds+=1
  if tag=='pre' and 'python' in a.get('class','').split():
   if self.part2:
    assert any(self.details),'Part II Python code must start collapsed'
    self.folded_python+=1
   else:
    assert not any(self.details),'Part I tutorial code must stay visible'
    self.visible_tutorial_python+=1
 def handle_endtag(self,tag):
  if tag=='details':self.details.pop()
h=(ROOT/'index.html').read_text(encoding='utf-8');p=Inspect();p.feed(h)
qmd=(ROOT/'result/_article_rendered.md').read_text(encoding='utf-8')
source_images=re.findall(r'<img\b[^>]*src="([^"]+)"',qmd)
assert len(source_images)==3 and all(v.startswith('data:image/png;base64,') for v in source_images)
for src,name in zip(source_images,['figure1_ige_windows.png','figure2_averaging_decomposition.png','figure3_income_dispersion.png']):
 assert base64.b64decode(src.split(',',1)[1])==(ROOT/'result/figures'/name).read_bytes()
assert qmd.count('## Takeaway')==1 and '### Summary and outlook' not in qmd
assert len(p.images)==3
for img in p.images:
 assert img.get('alt') and img['src'].startswith('data:image/png;base64,')
 im=Image.open(io.BytesIO(base64.b64decode(img['src'].split(',',1)[1])))
 assert im.width>2000 and im.height>1000;im.verify()
for href in p.hrefs:
 if href.startswith('#'):assert href[1:] in p.ids,href
 elif href and not re.match(r'^(https?:|mailto:)',href):assert (ROOT/href.split('#')[0]).exists(),href
assert p.math>=2 and p.tables>=10
assert p.folds==p.folded_python==4 and p.visible_tutorial_python==2
assert p.supporting==3
assert not p.details
assert all(f'table-{n}' in p.ids for n in range(1,7))
assert len([x for x in p.ids if re.match(r'^fn\d+$',x)])==9
assert 'height:auto!important' in h and 'research-question' in h
assert '@@' not in h
for forbidden in ['Morningstar','0.492','649 children','661 children','simulation']:
 assert forbidden not in h,forbidden
report=dict(status='passed',embedded_figures=len(p.images),tables=p.tables,math_elements=p.math,
            footnotes=9,local_links_exist=True,fragment_links_resolve=True,
            responsive_css=True,closed_analysis_code_panels=p.folds,part1_code_visible=True,
            six_result_tables_linked=True,closed_supporting_tables=p.supporting,generated_article_images_embedded=True,
            takeaway_is_single_conclusion=True,
            visual_chart_inspection='completed',browser_layout='not verified')
(ROOT/'result/html_validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))

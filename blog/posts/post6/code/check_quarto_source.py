"""Check render discovery, self-contained metadata and warning-free Pandoc parsing.

This is a source check, not a claim that native Quarto/its Lua filters ran.
"""
from pathlib import Path
import json,re,shutil,subprocess
ROOT=Path(__file__).resolve().parents[1]
qmd=(ROOT/'index.qmd').read_text(encoding='utf-8')
assert not re.search(r'^:{3,}',qmd,re.M), 'Avoid outer fenced Divs in this HTML post'
assert 'include-in-header:' not in qmd and 'header-includes:' not in qmd
assert 'body-classes: blog6-report' in qmd
assert 'jupyter: python3' in qmd and '  enabled: true' in qmd
assert '  cache: false' in qmd and '  freeze: false' in qmd
assert '```{python}' in qmd and '#| output: asis' in qmd
assert not (ROOT/'code/article_body.md').exists(), 'Legacy template would become a render target'
assert (ROOT/'code/_article_body.md').exists()
assert not (ROOT/'Chinese_guide.md').exists()
# The Chinese usage guide is optional documentation, not an analysis dependency.
targets=[]
for p in ROOT.rglob('*'):
 if not p.is_file() or p.suffix.lower() not in ['.qmd','.md','.ipynb','.rmd']:continue
 parts=p.relative_to(ROOT).parts
 if any(s.startswith(('_','.')) for s in parts):continue
 if p.name.lower() in ['readme.md','readme.qmd']:continue
 targets.append(str(p.relative_to(ROOT)))
assert targets==['index.qmd'],targets
for ext in ['body.blog6-report main.content','height:auto!important']:
 assert ext in (ROOT/'code/article_style.html').read_text(encoding='utf-8')
pandoc=shutil.which('pandoc')
parser='not available'
if pandoc:
 for source in ['index.qmd','result/_preview.qmd']:
  p=subprocess.run([pandoc,source,'--from=markdown','--to=json','--fail-if-warnings'],cwd=ROOT,capture_output=True,text=True)
  assert p.returncode==0,p.stderr
  assert not p.stderr.strip(),p.stderr
  doc=json.loads(p.stdout)
  assert doc['blocks']
 parser='passed with --fail-if-warnings'
result=dict(status='passed',normal_render_targets=targets,executable_qmd=True,cache=False,freeze=False,external_header_dependency=False,
            fenced_divs=False,pandoc_parser=parser,native_quarto='not available; not executed')
(ROOT/'result/quarto_source_validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))

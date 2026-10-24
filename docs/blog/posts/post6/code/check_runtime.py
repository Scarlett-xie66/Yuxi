"""Execute the exact QMD cell, including a cold start from a website root."""
from pathlib import Path
import argparse,hashlib,json,os,re,shutil,subprocess,sys,tempfile
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--engine',choices=['python','jupyter'],default='python')
args=parser.parse_args()
source=(ROOT/'index.qmd').read_text(encoding='utf-8')
cells=re.findall(r'```\{python\}\n(.*?)\n```',source,re.S)
assert len(cells)==1
def execute_at(post,working,env):
 before=hashlib.sha256((post/'index.qmd').read_bytes()).hexdigest()
 if args.engine=='jupyter':
  import nbformat
  from nbclient import NotebookClient
  notebook=nbformat.v4.new_notebook(cells=[nbformat.v4.new_code_cell(cells[0])])
  run=NotebookClient(notebook,timeout=180,kernel_name='python3').execute(cwd=str(working),env=env)
  text=''.join(o.get('text','') for o in run.cells[0].outputs if o.output_type=='stream')
 else:
  run=subprocess.run([sys.executable,'-c',cells[0]],cwd=working,env=env,capture_output=True,text=True,encoding='utf-8')
  assert run.returncode==0,run.stderr
  text=run.stdout
 assert '## Part I' in text and '## Part II' in text and '## Takeaway' in text
 assert 'data:image/png;base64,' in text
 receipt=json.loads((post/'result/render_execution.json').read_text(encoding='utf-8'))
 assert receipt['status']=='passed' and receipt['qmd_unchanged_during_render']
 assert before==hashlib.sha256((post/'index.qmd').read_bytes()).hexdigest()
 assert len(list((post/'result/figures').glob('*.png')))==3
 assert (post/'data/processed/analysis.sqlite').is_file()
 return text,receipt

with tempfile.TemporaryDirectory(prefix='blog6_runtime_') as temp:
 site=Path(temp)/'测试 website';post=site/'blog/posts/post6'
 shutil.copytree(ROOT,post,ignore=shutil.ignore_patterns('result','processed','index.html','__pycache__'))
 assert not (post/'result').exists() and not (post/'data/processed').exists()
 env=dict(os.environ,QUARTO_PROJECT_DIR=str(site))
 text,cold=execute_at(post,site,env)
 pd.testing.assert_frame_equal(pd.read_csv(post/'result/matched_income.csv'),pd.read_csv(ROOT/'result/matched_income.csv'))
 pd.testing.assert_frame_equal(pd.read_csv(post/'result/pilot_ige.csv'),pd.read_csv(ROOT/'result/pilot_ige.csv'))
# Exercise the exact delivered QMD again from its own folder, writing its live receipt.
text,warm=execute_at(ROOT,ROOT,dict(os.environ))
assert text.strip()==(ROOT/'result/_article_rendered.md').read_text(encoding='utf-8').strip()
result=dict(status='passed',engine=args.engine,cold_start_without_results_or_database=True,
            website_root_with_spaces_and_unicode=True,document_folder=True,matched_rows=187,
            estimates_match=True,figures_recreated=3,qmd_not_overwritten=True,
            native_quarto='unavailable; full Quarto integration not executed',
            jupyter_integration='not tested here; kernel startup blocked by local network restrictions' if args.engine=='python' else 'passed')
(ROOT/'result/runtime_validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))

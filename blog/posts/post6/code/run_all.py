"""Offline rebuild from included original source columns; full extraction is optional."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--from-quarto',action='store_true')
args=parser.parse_args()
os.environ['PYTHONUTF8']='1'
os.environ['PYTHONIOENCODING']='utf-8'
for name in ['result','result/figures','data/selected','data/processed']:(ROOT/name).mkdir(parents=True,exist_ok=True)
mp=ROOT/'data/source_manifest.json'
need_extract=not mp.exists()
if not need_extract:
    m=json.loads(mp.read_text())
    need_extract=any(not (ROOT/'data'/v['filename']).exists() for v in m['selected_files'])
if need_extract:
    archives=['ind2023er.zip']+[f'fam{y}er.zip' for y in [1999,2001,2003,2015,2017,2019]]
    if any(not (ROOT/'data/raw'/f).exists() for f in archives):
        raise FileNotFoundError('Supply the included data/selected files or all seven official ZIPs in data/raw/.')
    subprocess.run([sys.executable,str(ROOT/'code/01_extract_official.py')],cwd=ROOT,check=True)
manifest=json.loads((ROOT/'data/source_manifest.json').read_text())
for item in manifest['selected_files']:
 p=ROOT/'data'/item['filename']
 digest = hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda: f.read(1024 * 1024), b''):
   digest.update(chunk)
 actual = digest.hexdigest()
 assert actual==item['sha256'],f'Source snapshot changed: {p.name}'
for script in ['02_sql_audit.py','03_validate_estimate.py','05_further_analysis.py','06_make_figures.py','build_article.py','check_article.py','check_quarto_source.py']:
 print('\nRunning',script,flush=True)
 command=[sys.executable,str(ROOT/'code'/script)]
 if script=='build_article.py' and args.from_quarto:command.append('--body-only')
 subprocess.run(command,cwd=ROOT,check=True)
print('Rebuild and tutorial checks passed. Run python code/render_preview.py for HTML.')

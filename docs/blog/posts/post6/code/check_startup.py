"""Check missing-file/version errors and explicit location hints without running analysis."""
from pathlib import Path
import json,os,re,subprocess,sys,tempfile
ROOT=Path(__file__).resolve().parents[1]
cell=re.search(r'```\{python\}\n(.*?)\n```',(ROOT/'index.qmd').read_text(encoding='utf-8'),re.S)[1]
base_env={k:v for k,v in os.environ.items() if k not in ['QUARTO_PROJECT_DIR','QUARTO_DOCUMENT_PATH','BLOG6_POST_DIR']}
with tempfile.TemporaryDirectory(prefix='blog6_startup_') as temp:
 base=Path(temp);post=base/'测试 website/blog/posts/post6';post.mkdir(parents=True)
 for name in ['code','sql','data']:(post/name).mkdir()
 (post/'index.qmd').write_text('fixture',encoding='utf-8')
 (post/'code/run_all.py').write_text('# --from-quarto',encoding='utf-8')
 run=subprocess.run([sys.executable,'-c',cell],cwd=post,env=base_env,capture_output=True,text=True,encoding='utf-8')
 assert run.returncode!=0 and 'Found post6:' in run.stderr and 'code/_article_body.md' in run.stderr
 check=json.loads((post/'result/startup_diagnostic.json').read_text())
 assert 'code/_article_body.md' in check['missing_files']
 for name in ['code/_article_body.md','sql/01_prepare.sql','sql/02_match.sql']:(post/name).write_text('',encoding='utf-8')
 (post/'code/run_all.py').write_text('# old version',encoding='utf-8')
 (post/'code/build_article.py').write_text('# old version',encoding='utf-8')
 env=dict(base_env,BLOG6_POST_DIR='"'+str(post)+'"')
 run=subprocess.run([sys.executable,'-c',cell],cwd=base,env=env,capture_output=True,text=True,encoding='utf-8')
 assert run.returncode!=0 and 'Older incompatible scripts: code/run_all.py, code/build_article.py' in run.stderr
 check=json.loads((post/'result/startup_diagnostic.json').read_text())
 assert Path(check['post_root'])==post and not check['missing_files']
 run=subprocess.run([sys.executable,'-c',cell],cwd=base,env=base_env,capture_output=True,text=True,encoding='utf-8')
 assert run.returncode!=0 and 'Python cwd:' in run.stderr and '--execute-dir .' in run.stderr
result=dict(status='passed',missing_files_identified=True,old_code_identified=True,
 quoted_explicit_path_resolved=True,unrelated_working_directory_explained=True)
(ROOT/'result/startup_validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))

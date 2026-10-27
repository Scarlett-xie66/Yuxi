"""Rebuild from an empty result directory and confirm stable preview resources."""
from pathlib import Path
import os
import sys
import tempfile
import shutil
import subprocess
import json
import pandas as pd
from file_io import write_text

ROOT=Path(__file__).resolve().parents[1]

def run():
 with tempfile.TemporaryDirectory(prefix='blog7_contraction_') as temp:
  post=Path(temp)/'Test website/blog/posts/post7'
  shutil.copytree(ROOT,post,ignore=shutil.ignore_patterns('result','processed','index.html','__pycache__'))
  before=(post/'index.qmd').read_bytes()
  assert not(post/'result').exists()
  command=[sys.executable,str(post/'code/run_all.py'),'--from-quarto']
  first=subprocess.run(command,cwd=post.parents[2],capture_output=True,text=True,encoding='utf-8')
  assert first.returncode==0,first.stdout+first.stderr
  pd.testing.assert_frame_equal(pd.read_csv(post/'result/model_results.csv'),pd.read_csv(ROOT/'result/model_results.csv'))
  watched=list((post/'result').glob('*.csv'))+list((post/'result/figures').glob('*'))+[post/'result/_article_fragment.html']
  times={str(p):p.stat().st_mtime_ns for p in watched}
  again=subprocess.run(command,cwd=post,capture_output=True,text=True,encoding='utf-8')
  assert again.returncode==0,again.stdout+again.stderr
  assert all(p.stat().st_mtime_ns==times[str(p)] for p in watched)
  assert (post/'index.qmd').read_bytes()==before
  assert not(post/'index.html').exists()
  parser='unavailable'
  pandoc=shutil.which('pandoc')
  if pandoc:
   raw='````{=html}\n'+(post/'result/_article_fragment.html').read_text()+'\n````\n'
   test=subprocess.run([pandoc,'--from=markdown','--to=json','--fail-if-warnings'],input=raw,capture_output=True,text=True,encoding='utf-8')
   assert test.returncode==0 and not test.stderr.strip(),test.stderr
   blocks=json.loads(test.stdout)['blocks'];assert len(blocks)==1 and blocks[0]['t']=='RawBlock'
   parser='one raw HTML block, no warnings'
  receipt=dict(status='passed',cold_start_without_results=True,offline_rebuild=True,
   identical_model_results=True,qmd_unchanged=True,unchanged_resource_mtimes_preserved=True,
   source_side_html_not_written=True,raw_output_parser=parser,native_r_quarto='unavailable; not executed')
  write_text(ROOT/'result/rebuild_validation.json',json.dumps(receipt,indent=2)+'\n')
  print(json.dumps(receipt,indent=2))

if __name__=='__main__':run()

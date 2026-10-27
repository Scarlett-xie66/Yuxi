"""Called automatically by the RStudio QMD entry point; rebuild offline."""
from pathlib import Path
import os
os.environ['PYTHONUTF8'] = '1'
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--from-quarto', action='store_true')
args = parser.parse_args()
from analyze import analyze
from build_article import build
from validate import validate
analyze()
build(preview=not args.from_quarto)
validate()
print('Rebuild passed. Results and figures saved under result/.')

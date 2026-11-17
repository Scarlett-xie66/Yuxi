"""Run the whole Blog 9 analysis in one call.

index.qmd executes this file on every render, so the article numbers, tables and
figures are rebuilt from data/raw/SP500.csv rather than read from a saved copy.
Each stage is a separate script so the pipeline can also be run step by step.
"""

import runpy
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGES = ("run_model.py", "evaluate_investment.py", "make_figures.py", "article_numbers.py")


def main():
    start = time.time()
    for stage in STAGES:
        print(f"[blog9] running {stage}", flush=True)
        runpy.run_path(str(HERE / stage), run_name="__main__")
    print(f"[blog9] finished in {time.time() - start:.1f}s", flush=True)


if __name__ == "__main__":
    main()

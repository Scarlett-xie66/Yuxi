# Blog 9: Predicting stock returns with gradient boosting

This project reproduces a classroom stock-prediction experiment on the S&P 500, then tests whether a deliberately restricted gradient-boosting model beats a no-model forecast out of sample and whether its signals survive trading costs. The article is `index.qmd`; rendering it rebuilds every number, table and figure below from `data/raw/SP500.csv`. No value in the text is typed by hand: the article reads `result/tables/numbers.csv`, which `code/analysis.py` rewrites on each render.

## Run the whole article

1. Install Quarto, R (with the `knitr` and `rmarkdown` packages), and Python 3.10 or later with NumPy, pandas, scikit-learn, SciPy and Matplotlib. For example: `python -m pip install numpy pandas scikit-learn scipy matplotlib`.
2. Keep `index.qmd`, `code/`, `data/` and `result/` together. If your R session selects a different Python, set `BLOG9_PYTHON` to its full executable path (or set `RETICULATE_PYTHON`).
3. Put this `post9` folder in the website project at `blog/posts/post9/`. Open the website project (the directory containing `_quarto.yml`) in RStudio, then open `blog/posts/post9/index.qmd` and click **Render**. Alternatively, from the website root run `quarto render .` to build the website, including its listing. Each render runs `code/analysis.py`, which refits the models, recomputes the investment results and redraws the five figures. No network connection is needed after setup.
4. Results are saved in `data/processed/` (`panel.csv`, `forecasts.csv`), `result/tables/` and `result/figures/`. Five standalone figures are saved at 300 dpi.

The twelve checks in `code/test_pipeline.py` can be run on their own:

```bash
python -m unittest discover -s code -p "test_*.py" -v
```

## Data and methods

Source: S&P Dow Jones Indices LLC, "S&P 500" (ticker `SP500`), downloaded from FRED, <https://fred.stlouisfed.org/series/SP500>, snapshot committed as `data/raw/SP500.csv` (SHA-256 verified on every run). The series is a **price index**: dividends are excluded.

Features are nine numbers known at the close of each session (`lag1`–`lag5`, cumulative return over 5 and 20 sessions, volatility over 5 and 20 sessions). The target is the one-session return from close `t+1` to close `t+2`, in percentage points, so a forecast made after close `t` can be traded at close `t+1` without using information from the traded session.

Splits: fit 2017–2021 (1,239 sessions), choose settings 2022–2023 (501), evaluate once 2024–2025 (502). The original configuration is 100 trees of depth three, learning rate 0.1 and no leaf minimum; the revised configuration cuts capacity to depth one, learning rate 0.03 and 50 sessions per leaf, selected from four candidates on validation mean squared error and fixed before the test years were touched. Two no-model references are reported: the pre-test average return (0.049% a session) and a five-session average of realised returns.

The trading rule holds the index when the forecast is positive and zero-interest cash otherwise, with orders at the next close and 5 basis points per one-way trade (0 and 10 basis points in the sensitivity table). Inference uses a paired bootstrap of 2,000 resamples and Diebold–Mariano tests; every stage is seeded (20261116). Output includes `test_metrics.csv`, `forecasts.csv`, `validation_grid.csv`, `investment_metrics.csv`, `cost_sensitivity.csv`, `inference.csv`, `cash_days.csv`, `diagnostics.json`, `experiment.json` and `numbers.csv`.

## Article layout

The article text, embedded layout, captions, footnotes and the reproducibility section live in `index.qmd`, written as HTML inside one scoped `.blog9-page` wrapper so the website's own navigation is not disturbed. Inline R expressions read `v`, a list built by the hidden chunk from `result/tables/numbers.csv`. The analysis code does not generate or overwrite the article; it only writes data and results. This folder contains no separate Quarto project configuration: the parent website controls the output directory and its blog listing.

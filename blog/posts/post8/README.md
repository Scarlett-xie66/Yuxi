# Blog 8: Bootstrap, coverage and hypothesis testing

This project reproduces the June 2020 comparison in the authors' public Kenya replication data. The analysis focuses on respondents' first valid June interview; it is an illustrative conditional analysis, not an exact reconstruction of the original experimental assignment. See the article's footnotes and `result/tables/sample_counts.csv` for the sample scope.

## Run the whole article

1. Install Quarto, R (with the `knitr` and `rmarkdown` packages), and Python 3.10 or later with NumPy, pandas, SciPy and Matplotlib. For example: `python -m pip install numpy pandas scipy matplotlib`.
2. Keep `index.qmd`, `code/`, and `data/raw/` together. If your R session selects a different Python, set `BLOG8_PYTHON` to its full executable path (or set `RETICULATE_PYTHON`).
3. Open `index.qmd` in RStudio and click **Render**, or run `quarto render index.qmd --to html` from this folder. Each render runs `code/analysis.py`, builds the tables and figures, and includes the generated article. No network connection or Stata installation is needed after setup.
4. Results are saved in `data/processed/` and `result/figures/` and `result/tables/`; `result/article_body.html` is generated for rendering. Four standalone figures are saved at 300 dpi.

## Data and methods

Source: Donovan, Kevin (2022), “Cash Transfers as a Response to COVID-19: Experimental Evidence from Kenya (Journal of Development Economics, 2022) Replication,” Mendeley Data V1, https://doi.org/10.17632/zs5p47vx8k.1, CC BY 4.0. `data/raw/BDJO_Dataset.dta` is the authors' public data; the raw README is included.

The group variable is `treat_constant`; `groupgeneralbusinessstatus==0` indicates open. The analysis selects the first valid post-transfer June 2020 record per `identifier`. The separate group bootstrap uses 20,000 draws. Coverage uses 2,000 independently simulated samples and 1,000 bootstrap draws each, with true open shares 90% and 84%; the first 100 intervals are shown. Seed: 4082026. The no-effect simulation keeps June outcomes and group sizes fixed, using a sharp no-effect/exchangeable-label model. The highlighted rejection region and p-value come from the exact hypergeometric distribution; bars display 20,000 Monte Carlo draws. This conditional model is not a full experimental randomization analysis and does not correct post-treatment survey selection.

Output includes `sample_counts.csv`, `bootstrap_draws.csv`, `coverage_simulations.csv`, `null_distribution.csv`, and `summary.json`. The original published study reports 753 enrolled, while the 2022 release includes 776 identifiers in its analysis table; the reason is unresolved. The script reports its own counts rather than inventing an explanation.

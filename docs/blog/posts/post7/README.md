# When Economies Shrink, Whose Employment Rate Falls More?

The approved Blog7 topic is a concise comparison of women's and men's employment-rate changes in economic contractions. The earlier participation explorer is retained in its separate project; it is not the central analysis here. No age-composition extension is included.

## RStudio: render one QMD

Keep the full `post7/` directory intact. Place it at `blog/posts/post7/` in your website. Open `index.qmd` in RStudio and click Render. The R/knitr cell calls Python, rebuilds the analysis, saves results under `result/`, then inserts a raw HTML article with Plotly. No Jupyter session, reticulate initialization or manually executed analysis script is needed.

Install dependencies once in the Python interpreter used by the QMD:

```bash
python -m pip install -r requirements.txt
```

Use R with `knitr` installed. If selecting your Anaconda interpreter explicitly, run in R before rendering:

```r
Sys.setenv(BLOG7_PYTHON = "D:/app.anaconda/python.exe")
```

The QMD checks `BLOG7_PYTHON`, then `QUARTO_PYTHON`, then python/python3 on PATH. All production scripts use APIs available in Python 3.10. Normal renders are offline; failures stop rendering and write `result/rebuild_log.txt`. Rendering never rewrites the QMD, source code or unchanged watched resources.

## Official data and acquisition

All source responses are downloaded directly from World Bank API v2. The raw manifest contains exact URLs, retrieval time, response row counts, provider update dates and SHA-256 hashes. Raw files are not manually edited. Normal rendering verifies hashes rather than downloading a changing vintage.

- [Real GDP growth](https://data.worldbank.org/indicator/NY.GDP.MKTP.KD.ZG): `NY.GDP.MKTP.KD.ZG`, annual percentage change in total real GDP. This is **not** per-capita growth and **not** a quarterly recession definition.
- [Women's employment-to-population ratio, national estimate](https://data.worldbank.org/indicator/SL.EMP.TOTL.SP.FE.NE.ZS): `SL.EMP.TOTL.SP.FE.NE.ZS`.
- [Men's employment-to-population ratio, national estimate](https://data.worldbank.org/indicator/SL.EMP.TOTL.SP.MA.NE.ZS): `SL.EMP.TOTL.SP.MA.NE.ZS`.
- The corresponding ILO modeled series, `SL.EMP.TOTL.SP.FE.ZS` and `SL.EMP.TOTL.SP.MA.ZS`, are used only for a same-sample source comparison in the saved results.

Employment-rate denominators are the corresponding sex's population aged 15+. The numerator is employment, excluding people merely seeking work. These rates are neither the female share of workers nor a count of lost jobs. National series are country-reported estimates, not microdata collected for this blog. Definitions can still differ even after metadata screening.

`python code/fetch_data.py` deliberately refreshes the snapshot. It is not part of a normal render. A refresh can change the results and calls for a fresh editorial review of the title and findings.

## Sample rules, fixed before final estimation

1. Remove World Bank aggregate regions using the official economy catalogue.
2. Validate unique `(iso3, year)` keys and join all series one-to-one for 2000–2024.
3. Exclude employment levels whose source notes explicitly flag age coverage or urban-only/main-city coverage. These are incompatible with the intended common national age scope. Do not substitute modeled values.
4. Compute annual changes only if both sex-specific levels exist in consecutive calendar years. Never bridge missing years.
5. Exclude a change if either sex's current-year metadata explicitly marks a break in series. The following year's change within the new regime can still be used.
6. Require at least ten matched changes after screening per country/territory. Do not require a particular sign of employment or a recession in every country.
7. Require observed GDP growth for the change year. A contraction is strictly `gdp < 0`.

The final primary panel has 1,731 country-year changes across 85 countries/territories in 2001–2024. There are 251 contraction observations across 79 of those places. Six countries with no matched contraction still contribute positive-growth observations to the regression. Coverage is unbalanced and selected; this is not a population-weighted global estimate. The sample differs from the earlier 182-place participation exercise because the outcomes and source requirements changed.

`coverage.csv` records country eligibility; `source_quality_flags.csv` retains original notes and all flags. Screening uses metadata and missingness, never employment outcomes, coefficients or significance. Large valid employment movements are not dropped merely for being large. Unknown reporting breaks remain a limitation. Country histories leave gaps at unavailable/flagged levels rather than interpolating.

## One core model

For each sex, and directly for their difference:

```text
annual employment-rate change
    = country fixed effects + year fixed effects
    + b_depth * max(-real_GDP_growth, 0)
    + b_expansion * max(real_GDP_growth, 0) + error
```

The specification allows different slopes below and above zero GDP growth, with a continuous relationship at zero. It estimates short-run associations, not a causal effect. Country effects capture country-specific average changes, and year effects capture common annual movements; time-varying national shocks remain. The output growth and employment outcomes are jointly determined.

The direct outcome `difference = d_female - d_male` tests the female-minus-male slope. Positive values mean women's rate changes are higher (including smaller declines). Coefficients from this regression equal the differences in the two sex-specific regressions on identical rows. Its interval is estimated directly, not made by subtracting separate confidence intervals. Standard errors are clustered by country with a finite-sample correction; intervals use a t reference with country-cluster degrees of freedom.

Full-sample national estimates and the pre-2020 estimate are shown in the article. Both use the same model. A national-versus-modeled comparison is saved on **identical common rows**, so a data-source difference is not confused with a sample change. It is a diagnostic, not independent causal validation. ILO modeled estimates can incorporate macroeconomic information in their production; the primary regression therefore uses national series.

## Saved outputs

```text
index.qmd
index.html                    # standalone, offline review
README.md
requirements.txt
code/                         # acquisition, analysis, article, Plotly, validation
data/raw/                     # six unchanged API responses plus manifest
data/processed/analysis_panel.csv
result/
  analysis_panel.csv          # 1,731 matched changes and growth measures
  country_history.csv
  coverage.csv
  source_quality_flags.csv
  descriptive_results.csv
  model_results.csv           # all estimates, clustered intervals and sample sizes
  model_residuals.csv
  summary.json
  dashboard_data.json
  _article_body.html
  _article_fragment.html
  validation.json
  interaction_validation.json
  rebuild_validation.json
  word_count.json
  figures/                    # Plotly JSONs and a 300-dpi listing thumbnail
```

The standalone HTML embeds Plotly.js, chart data and CSV/README evidence links. It can be reviewed offline with JavaScript enabled. In the Quarto website, source links stay project-relative and listed resources are copied normally. Figure 1's region/year controls filter observations; they do not refit Figure 2. The model menu switches between all years and the pre-2020 sample. Country click or selection changes the history, which marks GDP contractions independently of whether an employment change could enter the regression.

## Checks and their limits

`validate.py` checks independent reconstruction of matched changes, source flags, descriptive values, an independent fixed-effect residualization calculation, gender-contrast identity, payload values, HTML structure and English-only content. Interaction logic tests use Node with lightweight DOM/Plotly test doubles. A cold-start test rebuilds without result/ or processed data and checks unchanged-resource modification times. Native R/Quarto and real-browser tests are only claimed if their reports explicitly say so. Statistical intervals do not include all survey error or unknown source-definition changes.

The main article contains 691 words. This counts the standfirst, opening question, narrative paragraphs and Takeaway; it excludes the title, byline, section headings, figures, captions, chart controls, source notes, footnotes, note markers and Reproducibility. Words are separated by whitespace, with inline HTML joined before counting. `result/word_count.json` records the count and exact rule. The analysis does not infer sectoral causes, discrimination, hours, wages or individual job-loss probabilities from aggregate rates.

For the standalone review, download the HTML and open it in Chrome, Edge or Firefox. A file viewer may show HTML source rather than execute a webpage. The HTML-only review ZIP provides the same self-contained page for extracting and opening locally; it is not the complete project package.

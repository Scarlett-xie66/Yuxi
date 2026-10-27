# The Employment Gap That Unemployment Misses

Final editorial edition: October 26, 2026. Blog3 compares employment for adults aged 25–54 with an own child aged 0–5 at home against adults of the same recorded sex with no own child under 18 at home. It describes the composition of employment differences, not the causes of parenthood or policy effects.

## Open the delivered article

Open `index.html` in a browser. All three figures are embedded; no R installation or internet connection is needed to read it. This delivered edition uses earlier supplied weighted aggregate estimates. The HTML was assembled with Python and Pandoc; it is not evidence of a new R microdata fit. The original person-level extract was not available for this delivery, and R/Quarto execution was not tested in this environment.

## Reproduce by rendering the QMD

1. Extract the complete ZIP and open `Blog3.Rproj` in RStudio. Install R and Quarto if necessary.
2. Run `source("code/install_packages.R")` once.
3. Configure one of the input options below.
4. Open `index.qmd` and click **Render**. The QMD contains the complete R workflow: estimates, supporting model, three figures, result tables and HTML. Separate scripts do not need to be run first.

The primary mode is `microdata`. Rendering in this mode requires a valid local CPS extract or private IPUMS credentials. Supplied aggregate files are used only when `reference` mode is explicitly selected; there is no silent fallback after a failed download.

## Input option A: your existing CPS extract

Keep the XML dictionary and matching compressed data file together in a private folder. Set the dictionary path in your user-level `.Renviron` so that the Render process can see it:

```text
BLOG3_DDI_PATH=C:/your/private/folder/cps_00001.xml
BLOG3_ANALYSIS_MODE=microdata
```

Restart RStudio after editing `.Renviron`. The extract must contain the 2025 ASEC sample, `cps2025_03s`, and YEAR, AGE, SEX, YNGCH, EMPSTAT, EDUC, ASECWT and all 160 REPWTP person replicate weights. No licensed person records are included in the ZIP.

## Input option B: acquire your extract through IPUMS

Register your own account for [IPUMS CPS](https://cps.ipums.org/cps/). Obtain an API key from your account and save it privately in your user-level `.Renviron`:

```text
IPUMS_API_KEY=YOUR_PRIVATE_KEY
BLOG3_ANALYSIS_MODE=microdata
```

Do not paste the key into the QMD, scripts, README or GitHub. Restart RStudio, then render the QMD. It requests the sample and variables above, caches the submitted request and downloaded originals in `~/.ipums-cps-blog3-cache`, and reuses complete cached inputs. `BLOG3_CACHE_DIR` optionally selects another private cache. Multiple candidate extracts require choosing `BLOG3_DDI_PATH`. A 401 error requires checking the key and CPS registration; it does not justify switching to reference data without labeling the result.

## Input option C: redraw the supplied aggregate results

To reproduce the delivered numerical comparisons without licensed records, set this in your user-level `.Renviron`, restart RStudio and render:

```text
BLOG3_ANALYSIS_MODE=reference
```

This explicitly reads `data/reference_only/weighted_rates.csv` and `adjusted_gaps.csv`, regenerates charts and tables and labels the HTML as an aggregate review. It does not fit the model again or verify the original raw sample. Set the mode back to `microdata` for original-record estimation. Alternatively, from a terminal with dependencies installed:

```bash
BLOG3_ANALYSIS_MODE=reference quarto render index.qmd
```

## Optional script workflow

From the standalone project root, run `source("code/01_clean_analyze.R")`, followed by `source("code/02_make_figures.R")`. The first stage saves aggregate analysis objects; the second makes the figures and execution audit. `code/blog3_analysis.R` contains every QMD R chunk in order and is an alternative. On the website, retain the folder as `blog/posts/post3/` and source the scripts at those paths. Rendering the QMD already runs all stages, so a prior script run is unnecessary.

## What the figures measure

- Figure 1: weighted employment shares across four youngest-child groups, separately for women and men.
- Figure 2: employed, unemployed and outside the labor force per 100 adults in the young-child and reference groups.
- Figure 3: the signed differences in those same three shares, young-child minus reference. Positive means more adults in the state; negative means fewer. In each sex, the outside-labor-force difference is larger in absolute size than the unemployment difference.

If E, J and N denote employed, unemployed and outside-labor-force shares using all adults, E + J + N = 1. Therefore the employment-share difference equals the negative sum of the other two differences. This is an exact description of composition, not an estimate of a mechanism or causal contribution. The conventional unemployment rate uses labor-force participants, not all adults; the charts deliberately retain a common denominator.

The internal `employment_decomposition.csv` retains accounting columns named `outside_contribution_pp` and `unemployed_contribution_pp`; these are the negatives of the corresponding state-share differences, so that they sum to the employment gap. Figure 3 reverses those signs to show actual state-share differences. `state_share_differences.csv`, supplied with this delivery, records the actual chart values directly.

## Supporting model and weights

ASECWT supplies person weights. The original-record workflow uses all 160 REPWTP columns for successive-difference replicate uncertainty, `mse=TRUE`, retaining valid negative replicate weights. A survey-weighted linear probability model fits `employed ~ sex * child_group + age_band + college`, with ages 25–34, 35–44 and 45–54 and bachelor’s-degree status. Adjusted contrasts use covariance and t(159) intervals. The women’s contrast sums the relevant main and interaction terms; the final comparison subtracts the men’s within-sex gap from the women’s. It is not a direct female-minus-male comparison in the young-child group. Model bounds and full coefficients are exported on microdata runs. The model is a supporting check and does not identify causes.

The data describe employment status in the 2025 survey reference week, not an annual average or a 2024–2026 time series. Children are own biological, adopted or stepchildren living at home; the reference includes some parents of adult or nonresident children. No earnings, working-hours or policy effects are estimated.

## Outputs and checks

`result/figures/` contains the three 300-dpi PNGs. `result/tables/` contains the delivered display values and `delivery_validation.json`. Generated model contrasts, sampling intervals, diagnostics and execution audits are written by R when you run it. `data/processed/` receives regenerated aggregate estimates on microdata runs. Raw records remain private.

After a run, inspect `run_status.txt` and `execution_audit.csv`. Only `analysis_mode=microdata` with `microdata_model_refitted=TRUE` documents a fresh model fit. If new estimates no longer support this edition’s written claims, the editorial guard stops the report for review. Completion of a program does not independently verify its source data or causal interpretation.

Set YAML `params: repository-url` to your actual repository link if publishing the code. The default does not invent a GitHub URL.

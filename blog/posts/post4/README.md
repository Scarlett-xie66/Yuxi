# Inflation and Jobs: A Trade-off That Kept Changing

**Scarlett Xie · Blog Post 4 · October 6, 2026**

This project examines how US inflation and unemployment evolved together from January 2019 through August 2026. It asks whether the decline from the 2022 inflation peak coincided with a sharp rise in unemployment. Between June 2022 and December 2024, annual inflation fell by 6.2 percentage points while unemployment rose by 0.5 points. Later readings show that progress was uneven.

The article uses a newspaper-report structure, with a lead chart, a highlighted research question, three connected analyses, policy implications and a concise Takeaway. Definitions and research references appear in numbered footnotes. The R code is hidden in the published article.

## Project structure

```text
index.qmd
README.md
Blog4.Rproj
code/
├── 00_config.R                      # project paths and analysis settings
├── 01_clean_analyze.R               # clean data and calculate estimates
├── 02_make_figures.R                # generate the three figures
├── blog4_analysis.R                 # run the analysis workflow
└── render_html.R                    # optional HTML rendering fallback
data/
├── raw/
│   ├── CPIAUCNS.csv                 # saved consumer-price index series
│   ├── UNRATE.csv                   # saved unemployment-rate series
│   └── source_manifest.csv          # download URLs and snapshot metadata
└── processed/
    └── analysis_monthly.csv         # calendar-aligned monthly analysis
result/
├── figures/
│   ├── figure1_inflation_and_jobs.png
│   ├── figure2_changing_relationship.png
│   └── figure3_change_by_stage.png
└── tables/
    ├── checkpoints.csv              # rates at selected dates
    ├── stage_changes.csv            # changes in percentage points
    ├── series_availability.csv      # coverage of each series
    ├── calendar_audit.csv           # calendar and lag checks
    ├── missing_observations.csv     # unavailable observations
    ├── analysis_objects.rds         # saved analysis objects
    └── session_info.txt             # R and package versions
```

`index.html` is the rendered article with embedded figures. The QMD includes its own CSS and final chart styling; the older `article.css` is not required by the current article. Additional translation, workflow or rubric documents in earlier project archives are supporting materials rather than inputs to rendering.

## Requirements

Use R, RStudio and Quarto. Install the required R packages once:

```r
install.packages(c("ggplot2", "knitr"), repos = "https://cloud.r-project.org")
```

The saved data support reproduction without an internet connection once the software and packages are installed. No FRED API key or IPUMS extract is needed. Keep the complete `code/` and `data/` folders beside `index.qmd`; replacing the QMD alone does not install its external scripts.

## Reproduce the standalone article

1. Open `Blog4.Rproj` in the complete project folder.
2. Generate the analysis tables and base figures:

   ```r
   source("code/01_clean_analyze.R")
   source("code/02_make_figures.R")
   ```

   Alternatively, run `source("code/blog4_analysis.R")`.

3. Open `index.qmd` and click **Render** in RStudio, or run this command in the project terminal:

   ```bash
   quarto render index.qmd --to html
   ```

4. Open the generated `index.html`.

Rendering the QMD reruns both scripts and applies the article's final white-background chart styling, percentage-axis labels and peak annotations. Running `02_make_figures.R` alone produces the base figures; render the QMD afterward to reproduce the current article's presentation. The three PNG paths remain unchanged.

## Use in the Quarto website

Place the complete post under `blog/posts/post4/`. From the website project root, run:

```r
source("blog/posts/post4/code/01_clean_analyze.R")
source("blog/posts/post4/code/02_make_figures.R")
```

Then render the post:

```bash
quarto render blog/posts/post4/index.qmd --to html
```

The QMD resolves the post directory before sourcing its scripts. Preserve the folder structure and raw files at `blog/posts/post4/data/raw/`. Website output settings determine where the rendered HTML is written.

## Data and calculations

| Series | Measure | Adjustment | Source |
| --- | --- | --- | --- |
| CPIAUCNS | All-items consumer-price index for urban consumers, 1982–84 = 100 | Not seasonally adjusted | [BLS via FRED](https://fred.stlouisfed.org/series/CPIAUCNS) |
| UNRATE | Unemployed people as a percentage of the civilian labor force, age 16 and older | Seasonally adjusted | [BLS via FRED](https://fred.stlouisfed.org/series/UNRATE) |

The snapshot was acquired on October 6, 2026. CPI observations end in August 2026 and unemployment observations in September; joint analysis therefore ends in August. Raw prices begin in January 2018 to provide 12-month lags for the analysis beginning in January 2019.

Annual inflation is calculated as:

```text
100 × (CPI in the current month / CPI in the same month a year earlier − 1)
```

Stage changes subtract the starting rate from the ending rate and are reported in **percentage points**. October 2025 remains in the calendar with missing observations; values are not interpolated, and plotted paths break across the gap. See the BLS explanations for [CPI](https://www.bls.gov/cpi/additional-resources/2025-federal-government-shutdown-impact-cpi-faq.htm) and [CPS unemployment data](https://www.bls.gov/cps/methods/2025-federal-government-shutdown-impact-cps.htm).

The scripts use cached CSVs by default. To acquire a new snapshot, set `refresh_data <- TRUE` in `code/00_config.R`; a missing raw file also triggers a download. Restore `FALSE` afterward for cached reproduction. Download URLs, retrieval timestamps and file hashes are recorded in `data/raw/source_manifest.csv`. Preserve the supplied snapshot before refreshing: later downloads may revise earlier observations. Changing dates or data coverage also requires reviewing the fixed checkpoints, annotations, footnotes and Takeaway.

## Figures

1. **Unemployment surged first. Inflation followed.** Aligned time-series panels distinguish the 2020 employment shock from the 2022 inflation peak.
2. **Almost the same unemployment, nearly four times the inflation.** Monthly points and a chronological path show how similar unemployment rates coincided with different inflation rates. The path is not a fitted Phillips curve.
3. **Inflation’s retreat brought a modest rise in unemployment.** Paired bars compare endpoint changes across four explicitly dated intervals.

The current figures are PNGs exported at 180 dpi and displayed responsively without changing their proportions. The analysis describes co-movement; it does not estimate causal policy effects or forecast future inflation and unemployment. Interval lengths differ, and unchanged unemployment between two endpoints does not imply no movement within the interval.

## Rendering and checks

The current QMD was executed using R/knitr and system Pandoc to produce the supplied standalone HTML. Checks covered embedded figures, computed values, the highlighted question, directory-tree formatting and footnote links. The PNGs were visually inspected. Native Quarto rendering and browser layout should be checked in the target RStudio environment.

`code/render_html.R` provides an optional knitr/Pandoc fallback. Run it from the standalone project root after installing Pandoc; set `BLOG4_PANDOC` to its executable path if necessary. Normal reproduction should use Quarto.

## Publication

Upload the complete project to the intended GitHub repository and publish the rendered post through the website workflow. Add the actual repository URL to the article's Reproducibility section once available. Submit both the published post URL and repository URL when required by the assignment.

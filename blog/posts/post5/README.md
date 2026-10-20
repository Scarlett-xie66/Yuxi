# Philadelphia's Poverty Extends Beyond Its Poorest Neighborhoods

**Scarlett Xie · Blog Post 5 · October 18, 2026**

A GIS analysis of income and poverty across Philadelphia census tracts, using the 2020–2024 American Community Survey (ACS) and official 2024 tract boundaries.

## Purpose and argument

**Where could Philadelphia focus poverty outreach first, and how much need would a narrow geographic rule overlook?**

The article argues for focused outreach alongside citywide access to assistance. It quantifies poverty concentration, maps a joint poverty-rate and population-count screen, measures the omissions from an income-only screen, and compares alternative screening thresholds. The final conclusion and outlook connect these findings to reviewing service capacity, travel access and resident participation.

The screen is an illustrative planning tool. It does not determine individual eligibility or estimate optimal allocations, program enrollment or poverty reduction.

## Main findings

- **Concentration:** in the income-complete sample, tracts with median household income below $40,000 contain 20.0% of the poverty-status population and 36.3% of people below poverty. Their population-weighted poverty rate is 37.8%, versus 8.1% in tracts at $100,000 or above—a 29.7 percentage-point gap.
- **Joint screen:** requiring a poverty rate of at least 30% and at least 1,000 people below poverty identifies 74 tracts, containing an estimated 128,471 people below poverty: 39.2% of the county poverty count. These tracts contain 20.5% of the county poverty-status population.
- **Rate/count mismatch:** another 52 tracts have at least 1,000 people below poverty but a rate below 30%. They contain 22.9% of the county poverty count. The 22 high-rate-only tracts contain 5.0%.
- **Income-screen omissions:** 63.7% of people below poverty in the income-complete sample live outside the under-$40,000 tract-income band. Among the 74 jointly selected tracts, 18 have median incomes at or above $40,000 and eight have no usable income estimate.
- **Threshold sensitivity:** with the 1,000-person cutoff fixed, rate cutoffs of 25%, 30% and 35% select 102, 74 and 56 tracts, containing 53.1%, 39.2% and 30.4% of the county poverty count, respectively.

**Denominators matter:** the income comparison uses 375 tracts with both measures, covering 97.3% of the county poverty-status population. The joint-screen and sensitivity shares use the full county poverty count. The 63.7% omission figure therefore does not use the same denominator as the 39.2% joint-screen figure.

## Repository structure

Save the supplied article as `index.qmd` beside `code/`, `data/` and `result/`. If the downloaded filename includes a suffix such as `index(1).qmd`, rename it before following these commands.

```text
index.qmd
index.html
README.md
Blog5.Rproj
code/
├── 00_config.R                    # project paths, income bands and source URLs
├── 01_acquire_data.R              # cached inputs or public Census downloads
├── 02_clean_analyze.R             # cleaning, joins, screening and sensitivity
├── 03_make_figures.R              # two maps and one weighted-rate chart
├── blog5_analysis.R               # analysis and figure workflow
└── render_html.R                  # optional knitr/Pandoc HTML fallback
data/
├── raw/
│   ├── b19013_philadelphia.dat     # original income table rows
│   ├── b17001_philadelphia.dat     # original poverty table rows
│   ├── tract_boundaries_2024.json  # projected official tract polygons
│   ├── source_manifest.json       # table sources, retrieval times and hashes
│   └── boundary_manifest.json     # boundary query and provenance
└── processed/
    ├── tract_estimates.csv        # joined tract estimates and income uncertainty
    └── map_vertices.csv           # projected vertices, ring IDs and GEOIDs
result/
├── figures/
│   ├── figure1_income_map.png     # 300-dpi income map
│   ├── figure2_poverty_map.png    # 300-dpi joint-screen map
│   └── figure3_income_poverty.png # 300-dpi weighted poverty-rate chart
└── tables/
    ├── priority_tracts.csv        # 74 jointly selected tracts
    ├── tract_priority_screen.csv # all 408 tracts and screen categories
    ├── screen_coverage.csv        # category counts and population/poverty shares
    ├── screen_sensitivity.csv     # 25%, 30% and 35% rate-cutoff comparison
    ├── income_band_poverty.csv    # population-weighted income-band comparisons
    ├── county_benchmark.csv       # directly published county estimates
    ├── uncertainty_audit.csv      # income margins and classification uncertainty
    ├── map_label_positions.csv    # approximate map orientation labels
    ├── summary.json              # computed values used by the article
    ├── analysis_objects.rds       # saved analysis objects
    ├── session_info.txt           # R session information
    └── validation.json            # recorded analysis/output checks
```

The accompanying project may also include `Chinese_translation.md` and `workflow_and_checks.md`. These are companion documents, not rendering dependencies.

## Requirements

- R 4.3 or later.
- R packages: `ggplot2`, `jsonlite` and `knitr`, with their dependencies.
- Quarto with an R execution environment; RStudio is recommended.
- Internet access for initial package installation or data reacquisition. The supplied raw snapshots support offline data reproduction once packages are installed.

Install the required R packages once:

```r
install.packages(
  c("ggplot2", "jsonlite", "knitr"),
  repos = "https://cloud.r-project.org"
)
```

No Census API key, IPUMS extract, online basemap or `sf` installation is required by these scripts.

## Reproduce the standalone article

Open `Blog5.Rproj`, or set the working directory to the folder containing `index.qmd` and `code/`.

Run in R:

```r
source("code/02_clean_analyze.R")
source("code/03_make_figures.R")
```

Alternatively, run both stages with:

```r
source("code/blog5_analysis.R")
```

Then use **Render** on `index.qmd` in RStudio, or run this in the terminal:

```bash
quarto render index.qmd --to html
```

The QMD itself reruns the analysis and figure scripts before evaluating inline R expressions and result tables, so rendering also rebuilds the outputs. Code, messages and warnings are hidden in the article. Figure images and article CSS are embedded in the HTML.

Keep the complete project together: the QMD checks for all four numbered R scripts, and rendering requires their data inputs or the ability to reacquire them.

## Reproduce within the website

Place the complete post in `blog/posts/post5/`. From the website's RStudio project root, run:

```r
source("blog/posts/post5/code/02_clean_analyze.R")
source("blog/posts/post5/code/03_make_figures.R")
```

To render this article:

```bash
quarto render blog/posts/post5/index.qmd --to html
```

To rebuild the website and refresh the blog listing:

```bash
quarto render
```

The QMD explicitly sets `image: result/figures/figure1_income_map.png` and lists all three PNGs under `resources`. Preserve these paths so the listing thumbnail and article figures remain available. The website configuration determines the output directory. For a site using `docs/`, verify that `docs/blog/posts/post5/result/figures/figure1_income_map.png` exists after the full render, then publish through the site's existing workflow.

## Sources and acquisition

| Input | Source | Use |
|:--|:--|:--|
| ACS B19013 | [2024 ACS median household income](https://data.census.gov/table/ACSDT5Y2024.B19013) | Tract and county income medians and margins of error; amounts are in 2024 dollars |
| ACS B17001 | [2024 ACS poverty status](https://data.census.gov/table/ACSDT5Y2024.B17001) | People below poverty and the population with poverty status determined |
| Tract boundaries | [2024 generalized TIGERweb tract layer](https://tigerweb.geo.census.gov/arcgis/rest/services/Generalized_ACS2024/Tracts_Blocks/MapServer/4) | Philadelphia polygons selected using state `42` and county `101` |

Acquisition uses public [ACS table-based Summary Files](https://www.census.gov/programs-surveys/acs/data/summary-file.2024.html). The saved `.dat` files retain the original header and Philadelphia County/tract rows, including source columns and sentinel codes. The initial manifests record download URLs, retrieval times and hashes. Geometry is requested in NAD83 / UTM zone 18N (`EPSG:26918`).

`01_acquire_data.R` uses cached snapshots by default and downloads missing inputs. To force a refresh, set `refresh_data <- TRUE` in `00_config.R`, run the analysis, and restore `FALSE`. Refreshing downloads the national tables before retaining Philadelphia rows, transferring about 136 MB. Refresh manifests are stored separately from the original provenance records. Keep the supplied snapshots for exact replication; later source revisions can change results.

## Calculations and spatial processing

1. Join all 408 tracts to geometry using the full eleven-digit GEOID. Preserve polygon rings and holes; draw in a metric projection with a scale bar and north arrow. Place labels are orientation aids, not analytical neighborhood boundaries.
2. Convert negative Census sentinel codes to missing values. Preserve unavailable estimates on maps rather than substituting zero. Income is usable in 375 tracts; poverty rates in 390.
3. Calculate each tract's poverty rate as `100 * people_below_poverty / poverty_status_population`. A zero denominator gives a missing rate. The official poverty population excludes some groups; see the article's numbered notes for definitions.
4. Calculate each income band's rate from summed poverty counts divided by summed poverty-status population. Do not average tract percentages. Read the county income median directly rather than averaging tract medians.
5. Apply the joint rule in `02_clean_analyze.R`: rate ≥30% and count ≥1,000. Assign each tract to high rate/high count, rate only, count only, below both cutoffs, or unavailable rate. The 18 unavailable-rate tracts have zero published poverty-status population.
6. Export the full screen and the 74-tract shortlist, ordered by poverty count for auditing. Repeat the rule at rate cutoffs of 25%, 30% and 35%, holding the count cutoff fixed.

### What the figures contribute

| Figure | Analytical contribution |
|:--|:--|
| 1: income map | Locates the broad income divide that motivates the concentration comparison |
| 2: joint-screen map | Distinguishes hardship intensity from caseload size and locates the shortlisted and high-count-only tracts |
| 3: income–poverty chart | Shows the weighted rate gradient and why a tract's median income does not imply an absence of poverty |

The filename `figure2_poverty_map.png` is retained for compatibility; it now displays the joint screen, not a poverty-rate-only choropleth. Income-band cutoffs are defined in `00_config.R`; screening cutoffs and sensitivity scenarios are defined in `02_clean_analyze.R`.

## Interpretation and checks

The ACS release pools observations from 2020–2024; it is not a single-year 2024 or current 2026 reading. Tract-level relationships are descriptive and do not establish individual or causal neighborhood effects. Income margins of error use the standard 90% confidence level. Grouped rates and screened coverage are point estimates without calculated confidence intervals. Threshold sensitivity tests the selected rate cutoff, not every source of uncertainty.

For reproduction, check that:

- All 408 GEOIDs match the geometry exactly once and tract poverty counts sum to the county total.
- The income-complete comparison contains 375 tracts, while the joint screen uses the full county poverty denominator.
- The 30%/1,000 rule returns 74 tracts and the 25% and 35% alternatives return 102 and 56.
- All three PNGs are complete, the HTML contains both result tables, and the figure and footnote links resolve.

`validation.json` records checks on the accompanying analysis/output snapshot. It does not by itself certify a later-edited QMD or a newly rendered website; rerender the current article in the target environment.

## Optional HTML fallback

If the Quarto command is unavailable, `code/render_html.R` can build standalone HTML with `knitr` and Pandoc:

```r
source("code/render_html.R")
```

Pandoc must be on `PATH`, or its executable can be supplied through `BLOG5_PANDOC`. This fallback is for standalone HTML; use Quarto to rebuild the website and its listing.

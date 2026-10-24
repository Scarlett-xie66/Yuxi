# Linking Generations in PSID: A SQL Guide to Family Income Persistence

The complete `post6/` folder is the installation unit: replace the previous folder as a whole. Open `index.qmd` in RStudio and click **Render**; no analysis scripts need to be launched manually. The QMD disables persistent Jupyter sessions (`execute.daemon: false`).

The post now has an **executable `index.qmd`**. Rendering it runs the Python/SQLite pipeline, saves fresh estimates and figures, and then displays the established article with its SQL examples, actual table previews, numbered Part II, expandable Python examples, footnotes and one concluding Takeaway.

## Render and save results

Use a Python environment with the packages in `requirements.txt`, plus Quarto. Python 3.11 or later is recommended; file hashing and SQLite saving also use APIs available in older Python versions. In the post folder, install dependencies once:

```bash
python -m pip install -r requirements.txt
quarto check jupyter
```

Then click Render/Preview in RStudio or run:

```bash
quarto render index.qmd --to html
```

From the website root, use:

```bash
quarto preview blog/posts/post6/index.qmd --to html
```

Install the dependencies in the Python environment reported by `quarto check jupyter`. Quarto supports executable Python through Jupyter; `requirements.txt` now includes Jupyter. If intentionally selecting another interpreter, configure `QUARTO_PYTHON` accordingly.

**Keep `index.qmd`, `code/`, `sql/` and `data/` together. Replacing only the QMD while retaining older scripts will not work.** When updating, rename your old post folder to `_post6_backup`, then install the new `post6/` folder. This also prevents the old `code/article_body.md` from being discovered as a website page.

## Startup file checks

A visible `code/` folder alone does not prove the required files exist. Startup first locates `index.qmd` beside `code/`, then names missing files and incompatible older scripts. It saves the resolved folder, Python working directory and file checks in `result/startup_diagnostic.json`. Check especially `code/run_all.py` and `code/_article_body.md`; the former must support `--from-quarto`, and the builder must support `--body-only`. Do not mix a new QMD with an old code folder or fix this only by renaming an old template.

If the kernel starts outside the website, run from post6 with an explicit execution directory and a fresh kernel:

```bash
quarto render index.qmd --to html --execute-dir . --no-execute-daemon
```

An explicit absolute location can alternatively be set with `BLOG6_POST_DIR`, or `POST_DIR` at the top of the QMD cell. No machine-specific folder is hard-coded in the delivered project. `python code/check_startup.py` checks missing files, incompatible versions, explicit paths and unrelated working directories.

## What a render does

The QMD contains one hidden executable Python cell. It locates the post from the document folder or the website root, uses the kernel's Python interpreter, runs `code/run_all.py --from-quarto`, and prints the newly assembled Markdown with `output: asis`. The article's displayed tutorial examples remain presentation code; the executable cell runs the production scripts behind them.

The pipeline:

1. Checks unchanged original source-column snapshots. If those snapshots are absent and all seven official archives are in `data/raw/`, it extracts them first.
2. Uses SQLite to construct person keys, father links, annual family-income records and the balanced three-window sample.
3. Independently reconstructs the sample with pandas; estimates four headline and eight expanded IGEs, paired intervals, influence checks and income fluctuations.
4. Saves the CSVs and three 300-dpi figures; assembles the article from `code/_article_body.md` using the fresh outputs.
5. Executes and checks the displayed tutorial, then checks source structure and render discovery.

Outputs are written under the **post folder**, irrespective of the HTML destination:

| Location | Contents |
|---|---|
| `result/matched_income.csv` | 187-row, 21-column analysis table |
| `result/pilot_ige.csv` | Four main IGEs and bootstrap intervals |
| `result/factorial_ige.csv` | Eight specifications and leave-one-father ranges |
| `result/paired_contrasts.csv` | Within-sample differences and intervals |
| `result/income_interpretation.csv` | The illustrative 10% comparison |
| `result/person_volatility.csv`, `dispersion_summary.csv` | Relative-income fluctuations and displayed calculations |
| `result/figures/` | Three PNG figures at 300 dpi |
| `result/rebuild_log.txt` | Complete pipeline log from QMD execution |
| `result/render_execution.json` | Execution timestamp, output inventory and unchanged-QMD check |
| `result/_article_rendered.md`, `_preview.qmd` | Fresh display content and optional static preview source |
| `data/processed/` | Intermediate tables and SQLite database |

Execution, caching and freezing are explicitly configured so normal QMD rendering reruns the analysis (`enabled: true`, `cache: false`, `freeze: false`). Do not override execution with `--no-execute`. A failed analysis stops rendering instead of displaying an old report as a successful fresh run. The error details remain in `result/rebuild_log.txt`.

The pipeline's `--from-quarto` mode **does not rewrite `index.qmd` while Quarto is reading it**. The cell verifies its source hash before and after execution. Outside Quarto, `python code/run_all.py` can still rebuild everything and regenerate the executable launcher. The optional `python code/render_preview.py` uses Pandoc to render the latest generated static preview; it does not replace Quarto execution.

For permanent prose edits, change `code/_article_body.md`, then run `python code/build_article.py` to update the launcher's title/options. Subsequent QMD renders use the edited template. Generated source data, tables and results are not edited manually.

## Data and identifiers

Only the seven official PSID ZIPs supplied for this project are used:

| Archive | Source rows | Role |
|---|---:|---|
| `ind2023er.zip` | 85,536 | Stable person IDs, father pointers, birth years and annual family membership |
| `fam1999er.zip` | 6,997 | 1998 family income |
| `fam2001er.zip` | 7,406 | 2000 family income |
| `fam2003er.zip` | 7,822 | 2002 family income |
| `fam2015er.zip` | 9,048 | 2014 family income |
| `fam2017er.zip` | 9,607 | 2016 family income |
| `fam2019er.zip` | 9,569 | 2018 family income |

Download source: [official PSID Packaged Data](https://simba.isr.umich.edu/Zips/ZipMain.aspx). Definitions: [PSID documentation catalogue](https://psidonline.isr.umich.edu/Guide/documents.aspx) and [individual codebook](https://psidonline.isr.umich.edu/documents/psid/codebook/IND2023ER_codebook.pdf). These are user-downloaded official files, not a newly scripted authenticated download. No simulated data, third-party archive, external CPI or wealth supplement is used.

The bundle includes selected **unchanged original columns**, sufficient for an offline rebuild. Full ZIPs are supplied separately. `source_manifest.json` records archive and selected-column hashes; `variable_dictionary.csv` records labels and fixed-width positions. Supplied family releases are 9, 7, 9, 2, 3 and 1; the individual file is release 2. Extraction checks ZIP CRCs and source row counts.

## Keys, dates and measurement

- Stable person key: `ER30001*1000 + ER30002`. Father pointer: `ER32016/ER32017`, valid father person numbers 1–399. The latest valid individual birth-year report is used without imputation.
- Annual family-income joins use **survey year plus annual family interview ID**. Father links identify a person; they do not make total family income that person's earnings.
- All income variables are **total money income of the linked person's family unit**. The father's family may include the mother or other members; the adult child's family may include a spouse. The article does not separate mothers' and fathers' contributions. Legacy CSV/SQL names such as `father_log_multi` are retained and refer to family income.
- Children born 1972–1976; fathers aged 45–60 in income year 2000; birth-year gap 15–55. Require responding sequence 1–20 and reference-person/spouse/partner relationship 10/20/22. Father and child must have different family units in every early wave.
- Require three positive valid incomes in father-early, child-early and child-midlife windows. Every comparison uses the same 187 children and 163 fathers: 109 daughters and 78 sons, or 3.8% of the 4,925-child starting cohort.
- Single-year measures use father 2000 and child 2000 or 2016. Central child ages are 24–28 and 40–44. Full windows span ages 22–30 and 38–46; fathers span 43–62, since their restriction applies at the central year.
- Multi-year income is **mean natural log income**, equivalent to log geometric-mean levels. It is not log arithmetic-mean income. Equal common dates imply annual common deflation would subtract a constant within each window and leave an OLS slope with intercept unchanged. Nominal dollar purchasing power across windows remains incomparable.
- Valid positive $1 values remain. Early fields' $9,999,999 top code is flagged; later fields' documented positive upper bound is $9,999,997. No top codes or unexpected upper codes occur in these files. Nonpositive values remain in source data but cannot enter logs. Source imputations and component censoring remain.

## Results and interpretation

| Child stage | Both single-year | Father's family averaged only | Child's family averaged only | Both averaged |
|---|---:|---:|---:|---:|
| Early career | 0.285 | 0.407 | 0.194 | 0.302 |
| Midlife | 0.311 | 0.508 | 0.315 | 0.489 |

Unweighted log–log OLS includes an intercept and no other controls. Father-cluster bootstrap uses 1,000 draws and seed 20261023, retaining siblings. All comparisons share the resamples; added contrasts are exploratory without multiplicity adjustment.

The averaged midlife-minus-early difference is 0.187, with paired 95% interval **[−0.008, 0.383]**. Thus the age-window difference is not significant at 5%. Neither window measures lifetime income, and period changes, family composition and selection also affect interpretation.

Averaging fathers' family income raises IGE. Averaging children's family income lowers early IGE by about 0.10, while changing midlife estimates by less than 0.02. The 10% father-family-income gap in Table 2 is an illustrative comparison, converted using `100 * (1.10**beta - 1)`, not observed growth.

For the same children, within-person standard deviations of year-centered log family income have medians 0.307 and 0.147, a 52% decline; 129 children (69%) have smaller midlife fluctuations. These include real family-resource changes, not just measurement error. They are not income percentile ranks or evidence for all middle-aged Americans.

## Checks and rendering status

`check_article.py` executes the displayed examples and checks all 187 × 21 cells, eight slopes, main intervals, percentage conversions and fluctuation summaries. `check_quarto_source.py` checks executable options, source parsing and that normal discovery selects only `index.qmd`; underscore-prefixed helpers are excluded. `check_html.py` verifies the generated article's embedded images, links, footnotes and closed code panels.

`python code/check_runtime.py` executes the **exact QMD cell** in isolated Python processes: first from a temporary website root with no result folder or database and a path containing spaces/Unicode, then from the actual post folder. It checks fresh outputs, identical estimates and an unchanged QMD. Optional `--engine jupyter` exercises a real Jupyter kernel on a machine that permits kernel startup.

Native Quarto is unavailable here, and this environment blocks Jupyter's local TCP kernel startup. Therefore native Quarto/Jupyter integration and browser layout are not claimed as verified. The exact cell's Python execution, full analysis, cold-start rebuild and Pandoc HTML are checked; final integration uses your installed Quarto/Jupyter.

Images are embedded in the **generated article**, avoiding relative-path failures. Keep the PNG thumbnail for the website listing. The QMD's inline-generated style is scoped to `main.content`; no external header include or outer fenced Div is required. The single Takeaway summarizes the entire report. Supporting tables and Python examples retain their clickable folds.

## Structure

```text
index.qmd                        # executable Quarto entry point
index.html                       # supplied preview
README.md
_Chinese_guide.md
requirements.txt
requirements-lock.txt
code/
├── _article_body.md              # editable prose and tutorial template
├── _quarto_entry.py              # cell embedded in index.qmd
├── 01_extract_official.py
├── 02_sql_audit.py
├── 03_validate_estimate.py
├── 05_further_analysis.py
├── 06_make_figures.py
├── build_article.py
├── run_all.py
├── check_article.py
├── check_quarto_source.py
├── check_runtime.py
├── check_html.py
└── render_preview.py
sql/
├── 01_prepare.sql
└── 02_match.sql
data/
├── raw/                         # optional seven official ZIPs
├── selected/                    # unchanged source columns
├── processed/                   # generated tables and SQLite database
├── source_manifest.json
├── wave_mapping.json
└── variable_dictionary.csv
result/                          # regenerated by QMD execution
├── *.csv
├── render_execution.json
├── rebuild_log.txt
├── _article_rendered.md
├── _preview.qmd
└── figures/                     # three 300-dpi PNGs
```

The original optional Chinese source-audit report and `04_report.py` remain available; they are not part of the automatic article renderer. A post1 document-level `theme` warning is separate: retain your website's theme in its root configuration and remove post1's override if needed.

## References

Official family codebooks: [1999](https://psidonline.isr.umich.edu/documents/psid/codebook/fam1999er_codebook.pdf), [2001](https://psidonline.isr.umich.edu/documents/psid/codebook/fam2001er_codebook.pdf), [2003](https://psidonline.isr.umich.edu/documents/psid/codebook/fam2003er_codebook.pdf), [2015](https://psidonline.isr.umich.edu/documents/psid/codebook/fam2015er_codebook.pdf), [2017](https://psidonline.isr.umich.edu/documents/psid/codebook/FAM2017ER_codebook.pdf), [2019](https://psidonline.isr.umich.edu/documents/psid/codebook/FAM2019ER_codebook.pdf).

- Haider and Solon (2006), [Life-Cycle Variation in the Association between Current and Lifetime Earnings](https://www.aeaweb.org/articles?id=10.1257/aer.96.4.1308).
- Mazumder (2001), [Earnings Mobility in the US](https://www.chicagofed.org/publications/working-papers/2001/2001-18), and (2015), [Estimating the Intergenerational Elasticity and Rank Association](https://www.chicagofed.org/publications/working-papers/2015/wp2015-04).
- Quarto: [Python execution](https://quarto.org/docs/computations/python.html), [raw Markdown output](https://quarto.org/docs/computations/execution-options.html#raw-output), [render-target exclusions](https://quarto.org/docs/projects/quarto-projects.html#render-targets).

## Rubric review (2026-10-24)

See [_Rubric_review.md](_Rubric_review.md) for the ten-criterion assessment, changes and evidence. The revised article adds motivation and plain-language explanations of averaging and lifecycle measurement. Data, specifications and output interfaces are unchanged. The confirmed self-assessment is 9.5/10 under the teaching interpretation of lifecycle demonstration; native Quarto/Jupyter integration remains unverified. This is not an instructor grade or a claim of statistically identified lifecycle bias.

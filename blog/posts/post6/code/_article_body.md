---
title: "Linking Generations in PSID: A SQL Guide to Family Income Persistence"
subtitle: "How income averaging and life stage change estimates of intergenerational family-income persistence"
author: "Yuxi Xie"
date: "2026-10-23"
categories: [SQL, Python, PSID, Economic Mobility]
description: "Seven official PSID files, 187 matched children, and a closer look at how age and income averaging shape estimates of intergenerational persistence."
image: result/figures/figure1_ige_windows.png
resources:
  - result/figures/*.png
  - README.md
  - _Chinese_guide.md
  - code/*.py
  - code/*.html
  - sql/*
  - result/*.csv
  - data/*.json
  - data/*.csv
format:
  html:
    toc: false
    code-copy: true
    embed-resources: true
    body-classes: blog6-report
jupyter: python3
execute:
  daemon: false
  enabled: true
  echo: false
  warning: false
  error: false
  cache: false
  freeze: false
---

@@STYLE@@

Income measurement changes the mobility story. Averaging both generations’ incomes gives an IGE of **0.302 in early adulthood and 0.489 in midlife** ([models B and D](#table-1)); separating the measures shows which generation drives the change.

<span class="research-question">**How do we build a reliable parent–child family income table in SQL, and what changes when we measure income at different ages and over several years?**</span>

Measuring children too early can make economic mobility look greater if their incomes have yet to reflect their longer-run prospects. The practical challenge is to separate changes in income measurement from changes in who enters the sample.

SQL links seven official PSID files into one row per child. Python estimates **intergenerational income elasticity (IGE)**: the percentage difference in child family income associated with a 1% difference in father family income.[^ige]

**Income always means total family money income.** The father link identifies whose family to follow; that family’s income can include the mother or other members. Adult children’s family income can include a partner’s income. The analysis compares two generations’ family resources, not individual wages.

## Part I · Build the evidence in SQL

### 1. Start with people, then add family income

From [PSID Packaged Data](https://simba.isr.umich.edu/Zips/ZipMain.aspx), use the cross-year **Individual File** for people and father links, and six **Family Files** for income.[^source]

| Official archive | One source row represents | Role in this analysis |
|:--|:--|:--|
| `ind2023er.zip` | A person, with fields across survey waves | Stable identifiers, father pointers, birth years and annual family membership |
| `fam1999er.zip` | A family unit interviewed in 1999 | 1998 income: fathers and young adult children |
| `fam2001er.zip` | A family unit interviewed in 2001 | 2000 income: fathers and young adult children |
| `fam2003er.zip` | A family unit interviewed in 2003 | 2002 income: fathers and young adult children |
| `fam2015er.zip` | A family unit interviewed in 2015 | 2014 income: the same children in midlife |
| `fam2017er.zip` | A family unit interviewed in 2017 | 2016 income: the same children in midlife |
| `fam2019er.zip` | A family unit interviewed in 2019 | 2018 income: the same children in midlife |

Python reads the supplied official ZIPs using their SAS column positions: **85,536 people and 50,449 family-wave records** ([source manifest](data/source_manifest.json)). The extracted CSVs preserve original fields and values.

This example reads 2000 income from the 2001 Family File; the [full parser](code/01_extract_official.py) checks all seven archives.

```python
from pathlib import Path
import io, re, zipfile
import pandas as pd

archive = Path("data/raw/fam2001er.zip")
with zipfile.ZipFile(archive) as z:
    sas = z.read("FAM2001ER.sas").decode("ascii")
    positions = {
        name: (int(start)-1, int(end))
        for name, start, end in re.findall(
            r"\b(\w+)\s+(\d+)\s*-\s*(\d+)", sas
        )
    }
    fields = ["ER17002", "ER20456"]
    with z.open("FAM2001ER.txt") as source:
        raw_2001 = pd.read_fwf(
            io.TextIOWrapper(source, encoding="ascii"),
            colspecs=[positions[v] for v in fields],
            names=fields, header=None
        )
print(raw_2001.sort_values("ER17002").head())
```

**Actual first five rows.** `ER17002` is the 2001 family interview number; `ER20456` is total family income for 2000.

@@RAW_PREVIEW@@

### 2. Give each table the right key

Use `ER30001*1000 + ER30002` as the stable **person key**. Annual **family keys** require both the interview number and survey year.[^keys]

| Working table | Row unit | Unique key |
|:--|:--|:--|
| `persons` | Person | `person_id` |
| `roster` | Responding person in a survey wave | `person_id, survey_year` |
| `family_income` | Family unit in a survey wave | `survey_year, family_interview_id` |
| `matched_income` | Child with all required income measures | `child_id` |

From the post folder, load the original columns into SQLite. Preparation SQL creates keys, selects the latest valid birth year and stacks waves with `UNION ALL`; unique indexes reject duplicates.

```python
from pathlib import Path
import math, sqlite3
import numpy as np
import pandas as pd

root = Path.cwd()
con = sqlite3.connect(":memory:")
con.create_function("LN", 1, lambda x: math.log(x) if x and x > 0 else None)
con.create_function("EXP", 1, math.exp)
pd.read_csv(root / "data/selected/individual.csv").to_sql(
    "individual_raw", con, index=False
)
for year in [1999, 2001, 2003, 2015, 2017, 2019]:
    pd.read_csv(root / f"data/selected/family_{year}.csv").to_sql(
        f"raw_{year}", con, index=False
    )
con.executescript((root / "sql/01_prepare.sql").read_text())
```

Run creation statements with `con.executescript(sql_text)` and display queries with `pd.read_sql_query(sql_text, con)`.

### 3. Find fathers with a self-join

Father fields `ER32016/ER32017` point to another person’s stable ID. A self-`JOIN` resolves that link; `SELECT` keeps the required fields.

Follow children born **1972–1976** with fathers **45–60 in 2000** and a birth-year gap of 15–55. Children are approximately **24–28 in 2000** and **40–44 in 2016**; father-family-income dates stay fixed.

```sql
@@SQL_LINKS@@
```

```sql
SELECT child_id, father_id, child_birth_year, father_birth_year
FROM father_child_links
ORDER BY child_id
LIMIT 5;
```

@@LINK_PREVIEW@@

The [sample audit](result/selection_counts.csv) narrows **4,925** cohort children to **1,878** resolved father links and **1,490** age-eligible pairs.

### 4. Join each person to the correct year’s income

Attach income on **survey year and family interview number**. Family numbers alone can join unrelated waves.

| Survey year | Individual-file family field | Family-file identifier | Total family income |
|--:|:--|:--|:--|
| 1999 | `ER33501` | `ER13002` | `ER16462` |
| 2001 | `ER33601` | `ER17002` | `ER20456` |
| 2003 | `ER33701` | `ER21002` | `ER24099` |
| 2015 | `ER34301` | `ER60002` | `ER65349` |
| 2017 | `ER34501` | `ER66002` | `ER71426` |
| 2019 | `ER34701` | `ER72002` | `ER77448` |

A `LEFT JOIN` keeps unmatched roster records visible for the audit.

```sql
SELECT r.survey_year, COUNT(*) AS responding_people,
       SUM(f.family_interview_id IS NULL) AS unmatched_family_ids
FROM roster r
LEFT JOIN family_income f
  ON r.survey_year = f.survey_year
 AND r.family_interview_id = f.family_interview_id
GROUP BY r.survey_year;
```

@@JOIN_AUDIT@@

<p class="result-source">Source: <a href="result/roster_join_audit.csv">annual roster-to-family join audit</a>. Counts include all responding roster members before the adult-role and income filters.</p>

**All roster records match.** Next retain reference persons, spouses and partners with positive valid income: this measures each adult’s own family resources and permits logarithms.

```sql
@@SQL_PERSON_INCOME@@
```

```sql
SELECT person_id, income_year, family_interview_id, income_nominal
FROM person_income
WHERE person_id = 4031
ORDER BY income_year;
```

@@INCOME_PREVIEW@@

The [income audit](result/income_quality.csv) records **42 negative and 485 zero incomes**, preserved in source data but excluded from logs. Valid $1 incomes remain; no top-coded record enters the final sample.[^income]

### 5. Turn annual rows into comparable income measures

`GROUP BY` creates person-window rows. `COUNT(*)` checks coverage, `AVG(log_income)` averages logs, and conditional `MAX` selects the central year—2000 or 2016.

```sql
@@SQL_SUMMARY@@
```

```sql
SELECT person_id, stage, n_obs, log_multi, log_single
FROM income_summary
WHERE person_id IN (4003, 4031, 7035)
ORDER BY person_id, stage
LIMIT 5;
```

@@SUMMARY_PREVIEW@@

Use **1998/2000/2002** or **2014/2016/2018**, without interpolating off-years. Everyone contributes three dates. The **mean of logs** equals log geometric-mean income, not log arithmetic-mean income.[^averaging]

### 6. Make one row per child—and account for exclusions

Join father-early, child-early and child-midlife summaries, requiring `n_obs=3` in each. `NOT EXISTS` excludes pairs sharing an early family unit, preventing a comparison of the same income with itself.

```sql
@@SQL_COMMON@@

@@SQL_MATCHED@@
```

```sql
SELECT child_id, father_id, father_income_2000,
       child_income_2000, child_income_2016
FROM matched_income
ORDER BY child_id
LIMIT 5;
```

**Merged table, first five rows.** Dollar values are nominal amounts in the named years.

@@MATCHED_PREVIEW@@

@@SELECTION@@

<p class="result-source">Source: <a href="result/selection_counts.csv">sample-selection counts</a>. Each row adds the stated requirement to the preceding rules.</p>

The [matched table](result/matched_income.csv) contains **187 children and 163 fathers**: 109 daughters and 78 sons. Complete-history requirements leave **3.8%** of the cohort ($187/4{,}925$), so these results describe a selected sample.[^sample]

## Part II · What the linked table reveals

### 1. Whose family income is averaged matters

A log–log regression measures the income association between generations, holding the 187-child sample fixed:

$$
\log Y_i^{C,s}=\alpha_s+\beta_s\log Y_i^F+\varepsilon_i,
$$

Here $Y^F$ and $Y^{C,s}$ are total income in the father’s and adult child’s respective family units; $s$ is the child’s life stage and $\beta_s$ the IGE.

Table 1 defines Figure 1’s four models: two child life stages, with either single-year incomes or averages for both generations.

<p class="result-label" id="table-1">Table 1. Four models, defined by their income years</p>

@@SPECIFICATION_TABLE@@

<p class="result-source">Source: <a href="result/pilot_ige.csv">four-model regression results</a>. Income calendar years; A/C use one observation, B/D mean log income. Same 187 children in every model.</p>

<details class="analysis-code">
<summary>Show / hide Python code · estimate the four models</summary>

```python
d = pd.read_sql_query("SELECT * FROM matched_income ORDER BY child_id", con)

def estimate_ige(frame, father_col, child_col):
    X = np.column_stack([np.ones(len(frame)), frame[father_col]])
    return np.linalg.lstsq(X, frame[child_col], rcond=None)[0][1]

specifications = [
    ("Early, single", "father_log_single", "young_log_single"),
    ("Early, mean logs", "father_log_multi", "young_log_multi"),
    ("Midlife, single", "father_log_single", "midlife_log_single"),
    ("Midlife, mean logs", "father_log_multi", "midlife_log_multi"),
]
for label, father_col, child_col in specifications:
    print(label, round(estimate_ige(d, father_col, child_col), 3))
```

</details>

<figure>
<figcaption><span class="figure-number">Figure 1.</span> The midlife estimate rises most when income is averaged</figcaption>
<p class="figure-deck">Models A–D are defined in Table 1. Points show IGE; bars show 95% father-cluster bootstrap intervals.</p>
<img class="report-chart" src="@@FIGURE1_DATA@@" alt="Four IGE estimates by child life stage and income measure; models A–D are defined in Table 1.">
<p class="figure-source">Source: author’s calculations from official PSID files; <a href="result/pilot_ige.csv">underlying estimates and intervals</a>. Teal: early career; orange: midlife. “Both averaged” means three log-income observations for each generation. Bootstrap: 1,000 draws, clustered by father.</p>
</figure>

For interpretation, consider two fathers whose families’ measured incomes differ by **10%**—an illustrative comparison, not observed income growth. The fitted child-family-income difference is:

$$
\text{Implied child family-income gap (\%)}
=100\left[(1.10)^{\hat\beta}-1\right].
$$

Thus **model B’s 0.302** implies about $100[(1.10)^{0.302}-1]=2.9\%$ higher child family income; **model D’s 0.489** implies about $4.8\%$. Table 2 uses unrounded coefficients for all four conversions.

<p class="result-label" id="table-2">Table 2. What a chosen 10% father-family-income difference implies</p>

@@INTERPRETATION_TABLE@@

<p class="result-source">Source: coefficients from <a href="result/pilot_ige.csv">the four-model results</a>, transformed using the displayed formula; calculations saved in <a href="result/income_interpretation.csv">the interpretation table</a>. These are fitted cross-family associations, not forecasts or causal effects.</p>

<details class="analysis-code">
<summary>Show / hide Python code · convert slopes into percentage differences</summary>

```python
interpretation = []
for label, father_col, child_col in specifications:
    beta = estimate_ige(d, father_col, child_col)
    interpretation.append({
        "model": label,
        "IGE": beta,
        "chosen_father_difference_pct": 10,
        "implied_child_difference_pct": 100 * (1.10**beta - 1),
    })
print(pd.DataFrame(interpretation).round(3))
```

</details>

The age gap is small with single-year incomes (**0.285 versus 0.311**) and larger with averages (**0.302 versus 0.489**).

<details class="supporting-results">
<summary>Age-window differences and uncertainty</summary>

<p class="result-label" id="table-3">Table 3. The age-window difference remains statistically uncertain</p>

@@AGE_CONTRAST_TABLE@@

<p class="result-source">Source: <a href="result/paired_contrasts.csv">paired differences and bootstrap intervals</a>. Differences are calculated before rounding the coefficients in Figure 1.</p>

</details>

The averaged difference is **0.187**, with a 95% paired interval of **[−0.008, 0.383]**. It includes zero, so the age-window difference is not statistically significant at 5%.[^uncertainty]

Table 4 and Figure 2 isolate **which generation’s averaging matters**.

<details class="analysis-code">
<summary>Show / hide Python code · separate father and child averaging</summary>

```python
factorial = []
for stage in ["young", "midlife"]:
    for father_measure in ["single", "multi"]:
        for child_measure in ["single", "multi"]:
            beta = estimate_ige(
                d, f"father_log_{father_measure}",
                f"{stage}_log_{child_measure}"
            )
            factorial.append([stage, father_measure, child_measure, beta])
comparison = pd.DataFrame(factorial, columns=[
    "stage", "father_measure", "child_measure", "IGE"
])
print(comparison.round(3))
```

</details>

<p class="result-label" id="table-4">Table 4. Change one generation’s income measure at a time</p>

@@FACTORIAL_TABLE@@

<p class="result-source">Source: <a href="result/factorial_ige.csv">all eight regression specifications</a>. Read across each row to change only child family income. The last column is averaged minus single-year child IGE; dates follow Table 1.</p>

<figure>
<figcaption><span class="figure-number">Figure 2.</span> Father and child family income averages change the estimate differently</figcaption>
<p class="figure-deck">Moving right changes only the father’s measure. Switching lines changes only the child’s measure.</p>
<img class="report-chart" src="@@FIGURE2_DATA@@" alt="IGE comparisons separating father-family-income averaging from child-family-income averaging.">
<p class="figure-source">Source: <a href="result/factorial_ige.csv">eight-model results in Table 4</a>. Circles/teal: single-year child family income; squares/orange: three-observation child mean log income. Lines connect alternative specifications, not a time trend. <a href="result/paired_contrasts.csv">Paired comparison intervals</a> are available with the results.</p>
</figure>

**Averaging the father’s family income raises IGE.** Holding child family income to one year, the estimate rises **0.285 → 0.407** in early adulthood and **0.311 → 0.508** in midlife.

**Averaging the child’s family income lowers early IGE but barely changes midlife IGE.** Across the two fixed father measures, early estimates fall **0.285 → 0.194** and **0.407 → 0.302**; midlife estimates change **0.311 → 0.315** and **0.508 → 0.489**.

Child averaging therefore offsets much of father averaging’s early-career increase. A temporary windfall or setback in the father’s measured income can blur the relationship with longer-run resources, pulling the estimated slope toward zero under standard measurement-error assumptions. Averaging can reduce that distortion. Independent temporary variation in the child’s income instead makes the relationship harder to estimate precisely; it need not lower the slope. The different effects here show why averaging both sides is not one uniform correction.[^measurement]

### 2. Family income fluctuates less in midlife

To assess whether one year’s income is a stable snapshot of family resources, compare the **same 187 children** across life stages. Subtract each year’s sample mean log income, then calculate each child’s standard deviation across three observations. Smaller values mean less movement relative to the group’s yearly average.

<details class="analysis-code">
<summary>Show / hide Python code · compare each child’s family income fluctuations</summary>

```python
panel = pd.read_sql_query("SELECT * FROM person_income", con)
dispersion = []
for stage, years in [
    ("Early career", [1999, 2001, 2003]),
    ("Midlife", [2015, 2017, 2019]),
]:
    q = panel[panel.person_id.isin(d.child_id)
              & panel.survey_year.isin(years)].copy()
    q["centered_log"] = q.log_income - q.groupby(
        "survey_year"
    ).log_income.transform("mean")
    sd = q.groupby("person_id").centered_log.std()
    dispersion.append(sd.rename(stage))
paired_sd = pd.concat(dispersion, axis=1)
print(paired_sd.median().round(3))
print(round((paired_sd.Midlife < paired_sd["Early career"]).mean(), 3))
```

</details>

<figure>
<figcaption><span class="figure-number">Figure 3.</span> The same children’s relative family income fluctuates less in midlife</figcaption>
<p class="figure-deck">Further left means smaller within-person fluctuations relative to the group’s yearly average.</p>
<img class="report-chart" src="@@FIGURE3_DATA@@" alt="Relative-income fluctuations for the same 187 children in early adulthood and midlife.">
<p class="figure-source">Source: <a href="result/person_volatility.csv">person-level fluctuation measures</a> for the same 187 children. Teal: 1998/2000/2002; orange: 2014/2016/2018. Cumulative distributions; dashed lines mark medians.</p>
</figure>

The median fluctuation measure falls **0.307 → 0.147**, a **52%** reduction: $100(1-\text{midlife median}/\text{early median})$. **129 of 187 children (69%)** have smaller midlife fluctuations; Table 5 shows the calculations.

<details class="supporting-results">
<summary>Income-fluctuation calculations</summary>

<p class="result-label" id="table-5">Table 5. Relative family income fluctuates less in midlife for most children</p>

@@DISPERSION_TABLE@@

<p class="result-source">Source: <a href="result/person_volatility.csv">individual dispersion measures</a>; <a href="result/dispersion_summary.csv">summary calculations</a>. Calculations use unrounded medians. The 52% compares two medians; the 69% counts children with a lower individual value.</p>

</details>

Within these windows, a single midlife observation is generally more stable. Fluctuations still include real family-resource changes, so this check does not establish how well an observation represents lifetime income.

Leaving out each father and his children preserves the averaged estimates’ ordering (Table 6).

<details class="supporting-results">
<summary>Leave-one-father sensitivity check</summary>

<p class="result-label" id="table-6">Table 6. The averaged estimates remain ordered when one father is left out</p>

@@INFLUENCE_TABLE@@

<p class="result-source">Source: leave-one-father minimum and maximum columns in <a href="result/factorial_ige.csv">the regression results</a>, for the two models averaging both generations. These ranges are sensitivity checks, not confidence intervals.</p>

</details>

**Why age matters.** Early-career income may understate longer-run resources for people whose incomes rise more steeply. If that growth is related to parental resources, observing children young can understate intergenerational persistence. Averaging nearby early years can smooth temporary shocks without correcting this age-related mismatch.[^lifecycle]

The sample illustrates the concern: averaged IGE is higher in midlife (Figure 1), while relative family income is steadier (Figure 3). These are complementary checks, not a measurement of true lifetime-income bias. The age contrast remains statistically uncertain, neither window observes lifetime resources, and age changes alongside the calendar period and family composition.

## Takeaway

SQL turns seven official PSID files into an auditable table of **187 children and 163 fathers**. On this fixed sample, averaging fathers’ family income raises IGE; averaging children’s family income lowers early IGE by about 0.10 but barely changes midlife estimates ([Table 4](#table-4)). Relative family income also fluctuates less in midlife for **69% of children** (Figure 3).

**Income measurement changes the mobility story.** Averaging smooths short-run fluctuations; measuring at a suitable life stage addresses a different problem. The averaged IGE rises from 0.302 to 0.489, but the age-window difference remains statistically uncertain ([Table 3](#table-3)). Longer histories and broader cohorts would help separate lifecycle patterns from period and family changes.

## Reproducibility

The analysis code is available in the [accompanying project](README.md), with [SQL preparation](sql/01_prepare.sql), [matching queries](sql/02_match.sql) and [Python analysis](code/05_further_analysis.py). Original archives come from the [official PSID Packaged Data page](https://simba.isr.umich.edu/Zips/ZipMain.aspx); variable definitions are linked in the [PSID documentation catalogue](https://psidonline.isr.umich.edu/Guide/documents.aspx).

The standalone project uses the following structure:

```text
index.qmd
README.md
code/                  # extraction, SQL execution, analysis and checks
sql/
├── 01_prepare.sql     # stable keys and annual tables
└── 02_match.sql       # father links and income-window joins
data/
├── raw/               # seven original PSID ZIPs, supplied separately
├── selected/          # unchanged source columns
└── processed/         # generated tables and SQLite database
result/
├── matched_income.csv # final analysis table
├── *.csv              # estimates, calculations and audits
└── figures/           # three 300-dpi PNGs
```

Install `requirements.txt`, then render `index.qmd`. Each render reruns the Python and SQL analysis, saves results and figures in `result/`, and displays the freshly generated article. Keep the whole post folder together; the [README](README.md) contains the source-data and environment instructions.

[^ige]: A higher IGE means a closer link between generations’ incomes—and less relative mobility by this measure. “Income” here covers the whole family, including a partner’s income, rather than just one person’s pay.

[^source]: The data come from the [University of Michigan’s PSID](https://simba.isr.umich.edu/Zips/ZipMain.aspx). This analysis uses the seven official files supplied for the project; their versions and record counts are listed in the [README](README.md).

[^keys]: A person keeps the same identifier as families change. The father link is recorded in PSID’s [individual-file codebook](https://psidonline.isr.umich.edu/documents/psid/codebook/IND2023ER_codebook.pdf); it is not guessed from who lives together.

[^income]: A 2001 interview reports income for 2000. Zero and negative incomes are kept in the source data but left out of the log calculation; PSID’s own imputed values remain. Details are in the [data notes](README.md#keys-dates-and-measurement).

[^averaging]: The averages use logs, giving less weight to unusually large dollar amounts than a simple dollar average would. Everyone contributes the same dates, so a common annual inflation adjustment would leave these slopes unchanged; nominal dollars still cannot measure changes in purchasing power across the two periods.

[^sample]: Requiring complete income histories leaves a small, selected group. The results describe these families, without survey weights, rather than all American families.

[^uncertainty]: The intervals come from repeatedly resampling fathers, keeping siblings together. The age comparison uses each resampled group for both estimates, so it measures uncertainty in their difference directly.

[^measurement]: A good or bad year can make income a misleading guide to longer-run resources. [Research by Bhash Mazumder](https://www.chicagofed.org/publications/working-papers/2001/2001-18) shows why observing more years can matter; averaging does not automatically remove every source of error.

[^lifecycle]: [Steven Haider and Gary Solon](https://www.aeaweb.org/articles?id=10.1257/aer.96.4.1308) find that the age at which earnings are observed affects how well they represent lifetime earnings. [Mazumder’s later PSID work](https://www.chicagofed.org/publications/working-papers/2015/wp2015-04) uses longer income histories around midlife.

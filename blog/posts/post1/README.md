# Two Measurements, One Score—and 99% of the Variation

**Author:** Scarlett Xie. **Blog 1:** eigenvalues, eigenvectors and PCA.

## Render the complete project from the QMD

1. Extract the ZIP and keep the entire `post1` folder together.
2. Open `Blog1.Rproj` in RStudio, then open `index.qmd`.
3. Click **Render**. You do not need to run the analysis scripts individually.

The QMD uses R/knitr to check the Python environment, execute `code/build.py`, generate every analysis output, then insert the newly generated article. It does not use reticulate or a Jupyter kernel. `result/` can be deleted before rendering; it is rebuilt automatically.

For an existing website, put the complete folder at `blog/posts/post1/`, open the website's RStudio project and Render that QMD. The website's output directory determines the HTML destination, often `docs/blog/posts/post1/index.html`. The embedded report CSS comes unchanged from the supplied Blog 5 template. Website navigation and the global theme come from your existing website configuration.

From a terminal in `post1`, the equivalent command is:

```bash
quarto render index.qmd --to html
```

Use **Render** for a one-time build. It is not necessary to keep a Preview server running. The Python analysis avoids rewriting unchanged files and never overwrites `index.qmd`, analysis code or an existing data CSV.

## One-time requirements

- R and RStudio with Quarto available.
- R packages `knitr` and `rmarkdown`. If missing, run in the R console:

```r
install.packages(c("knitr", "rmarkdown"))
```

- Python 3.10+ with NumPy, Matplotlib and scikit-learn. In a terminal opened in `post1`:

```bash
python -m pip install -r requirements.txt
```

Once these dependencies are installed, the archived data support offline analysis. Rendering does not download external data or install packages automatically.

The QMD checks `BLOG1_PYTHON` first, then an existing `RETICULATE_PYTHON` setting, then Python executables on PATH. It verifies imports before choosing an environment. If Python is not found, or RStudio selects a different installation, set the executable once in the R console before clicking Render:

```r
# Use your actual Python executable path. This matches your reported Anaconda setup.
Sys.setenv(BLOG1_PYTHON = "D:/app.anaconda/python.exe")
```

To install dependencies into that exact environment from RStudio, run once after opening `Blog1.Rproj`:

```r
system2("D:/app.anaconda/python.exe",
        c("-m", "pip", "install", "-r", shQuote("requirements.txt")))
```

This selects a standalone Python process. R does not load Python into its own session, so an initialized reticulate session does not affect this analysis. No machine-specific executable path is required in `index.qmd`.

## Project files

| Location | Purpose |
|---|---|
| `index.qmd` | Render entry; executes analysis and displays the generated article |
| `index.html` | Self-contained preview of the approved article |
| `Blog1.Rproj` | Standalone RStudio project |
| `requirements.txt` | Python dependencies |
| `code/run_analysis.R` | Python discovery, preflight, execution and error logging |
| `code/check_environment.py` | Python version and dependency checks |
| `code/build.py` | Analysis, figures, numerical checks and article generation |
| `code/article_template_editorial.txt` | Approved English article with computed-value placeholders |
| `code/style.css` | Report CSS copied from the supplied QMD |
| `code/preview_header.html` | Title block for the standalone Pandoc preview |
| `data/iris.csv` | All 150 flowers, four measurements and species labels |
| `data/provenance.json` | Dataset source and analysis scope |
| `result/figures/` | Three figures, each in SVG and 300-dpi PNG |
| `result/pca_components.csv` | Eigenvectors, eigenvalues and variance shares |
| `result/reconstruction.csv` | Observed values, scores, reconstructed values and distances |
| `result/direction_search.csv` | Independent angle-grid check of projected variance |
| `result/article.txt` | Complete article assembled with computed values |
| `result/validation.json` | Numerical checks and data hash |
| `result/environment.json` | Python executable and package versions used |
| `result/rebuild_log.txt` | Execution log created by a QMD/R render |

The numerical results and figures can also be rebuilt independently with `python code/build.py`. Optional `python code/build.py --html` regenerates the supplied standalone preview using Pandoc 2.19+. Pandoc is not needed as a separate installation for the ordinary Quarto render route; Quarto supplies its own renderer.

## Scope and validation

The analysis uses petal length and width in centimeters, centered but not standardized. Sample covariance uses `n-1`. All three figures use the same observed covariance matrix; constructed direction vectors illustrate its geometry. Species labels are not fitted or predicted. Reconstruction errors are descriptive in-sample measures.

Checks verify the eigen equation, orthonormality, score variances, total-variance identity, lossless two-component rotation, and the identity between squared reconstruction loss and discarded variance. Manual eigendecomposition and reconstructions agree with scikit-learn PCA. A fine angle grid independently verifies the maximum-variance direction.

The approved article contains approximately 776 main-text words, excluding figure captions, chart notes, source notes, displayed equations and reproducibility instructions. It ends with one abstract-style **Takeaway** and short **Notes and sources**.

The authoring environment verified the complete Python pipeline from a clean output directory, source preservation, deterministic repeat execution, Unicode/space paths and ZIP extraction. **R and Quarto were unavailable there, so a native RStudio/Quarto render has not been verified.** The QMD contains the R entry point that executes the verified Python pipeline. `CHECKS.txt` records the precise test scope.

## If a render fails

- A missing-environment message lists checked interpreters and package problems. Install the dependencies into the selected Python and Render again.
- An analysis failure is printed by R and saved in `result/rebuild_log.txt`.
- Do not copy only `index.qmd`: keep its `code/` and `data/` directories alongside it.
- Do not add a per-document theme to this post. The existing website owns the global theme.

## Sources

- [Iris data documentation](https://scikit-learn.org/stable/datasets/toy_dataset.html#iris-plants-dataset)
- [PCA explanation, Carnegie Mellon University](https://stat.cmu.edu/~cshalizi/dm/19/lectures/05/lecture-05.html)
- [scikit-learn PCA guide](https://scikit-learn.org/stable/modules/decomposition.html#pca)

## Website listing repair

When updating an older post1, delete the obsolete code/article_template_editorial.md and result/article.md first. The current project uses .txt for these auxiliary files so a website listing does not mistake them for articles. Then copy this complete post1 folder and render the website from the project root.

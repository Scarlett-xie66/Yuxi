# Run from Blog4.Rproj or the website project containing blog/posts/post4.
post_root <- if (file.exists("code/00_config.R")) "." else "blog/posts/post4"
if (!file.exists(file.path(post_root, "code/00_config.R"))) {
  stop("Open Blog4.Rproj, or run from the website project root.")
}
project_dir <- normalizePath(post_root, winslash = "/")
as_of <- as.Date("2026-10-06")
request_start <- as.Date("2018-01-01") # Supplies the 12-month inflation lag.
analysis_start <- as.Date("2019-01-01")
refresh_data <- FALSE # TRUE downloads a new snapshot through the fixed cutoff.
raw_dir <- file.path(project_dir, "data", "raw")
processed_dir <- file.path(project_dir, "data", "processed")
table_dir <- file.path(project_dir, "result", "tables")
figure_dir <- file.path(project_dir, "result", "figures")
for (path in c(raw_dir, processed_dir, table_dir, figure_dir)) {
  dir.create(path, recursive = TRUE, showWarnings = FALSE)
}
invisible(Sys.setlocale("LC_TIME", "C"))
options(timeout = max(120, getOption("timeout")))
series <- data.frame(
  id = c("CPIAUCNS", "UNRATE"),
  label = c("All-items Consumer Price Index, urban consumers", "Civilian unemployment rate"),
  units = c("Index, 1982-84 = 100", "Percent of civilian labor force, age 16+"),
  adjustment = c("Not seasonally adjusted", "Seasonally adjusted"),
  source = "US Bureau of Labor Statistics via FRED",
  documentation = paste0("https://fred.stlouisfed.org/series/", c("CPIAUCNS", "UNRATE")),
  stringsAsFactors = FALSE)
series$download_url <- paste0("https://fred.stlouisfed.org/graph/fredgraph.csv?id=",
  series$id, "&cosd=", request_start, "&coed=", as_of)

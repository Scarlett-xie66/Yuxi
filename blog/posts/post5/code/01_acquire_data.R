post_root <- if (file.exists("code/00_config.R")) "." else "blog/posts/post5"
source(file.path(post_root, "code/00_config.R"), local = TRUE)
if (!requireNamespace("jsonlite", quietly = TRUE)) stop("Install jsonlite first.")
# Official table-based Summary Files provide a public alternative to the keyed API.
# Keep original Philadelphia lines, including sentinels and margins of error.
records <- list()
for (table in c("B19013", "B17001")) {
  dest <- file.path(raw_dir, paste0(tolower(table), "_philadelphia.dat"))
  if (refresh_data || !file.exists(dest)) {
    url <- paste0(summary_base, "acsdt5y2024-", tolower(table), ".dat")
    tmp <- tempfile(fileext = ".dat")
    download.file(url, tmp, mode = "wb", method = "libcurl", quiet = TRUE)
    con <- file(tmp, open = "rt", encoding = "UTF-8")
    header <- readLines(con, n = 1L, warn = FALSE)
    selected <- header
    repeat {
      lines <- readLines(con, n = 5000L, warn = FALSE)
      if (!length(lines)) break
      selected <- c(selected, lines[startsWith(lines, "1400000US42101") | startsWith(lines, "0500000US42101|")])
    }
    close(con)
    if (length(selected) != 410L) stop("Unexpected 2024 Philadelphia table coverage.")
    writeLines(selected, dest, useBytes = TRUE)
    records[[table]] <- list(table = table, url = url, retrieved_utc = format(Sys.time(), tz = "UTC", usetz = TRUE),
      source_md5 = unname(tools::md5sum(tmp)), subset_md5 = unname(tools::md5sum(dest)),
      selection = "Header plus Philadelphia County and tract rows; original field values retained")
    unlink(tmp)
  }
}
if (length(records)) jsonlite::write_json(records, file.path(raw_dir, "source_manifest_refresh.json"), pretty = TRUE, auto_unbox = TRUE)
boundary_file <- file.path(raw_dir, "tract_boundaries_2024.json")
if (refresh_data || !file.exists(boundary_file)) {
  tmp <- tempfile(fileext = ".json")
  download.file(boundary_url, tmp, mode = "wb", method = "libcurl", quiet = TRUE)
  x <- jsonlite::fromJSON(tmp, simplifyVector = FALSE)
  if (!is.null(x$error) || isTRUE(x$exceededTransferLimit) || length(x$features) != 408L) stop("Incomplete boundary download.")
  file.copy(tmp, boundary_file, overwrite = TRUE); unlink(tmp)
  jsonlite::write_json(list(url = boundary_url, retrieved_utc = format(Sys.time(), tz = "UTC", usetz = TRUE),
    md5 = unname(tools::md5sum(boundary_file)), feature_count = length(x$features), spatial_reference = x$spatialReference),
    file.path(raw_dir, "boundary_manifest_refresh.json"), pretty = TRUE, auto_unbox = TRUE)
}

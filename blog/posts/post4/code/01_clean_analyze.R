post_root <- if (file.exists("code/00_config.R")) "." else "blog/posts/post4"
source(file.path(post_root, "code/00_config.R"), local = TRUE)
read_series <- function(path, id) {
  x <- read.csv(path, na.strings = c(".", "", "NA"), check.names = FALSE)
  if (ncol(x) != 2 || !id %in% names(x)) stop("Unexpected CSV for ", id)
  x[[1]] <- as.Date(x[[1]])
  names(x)[1] <- "date"
  stopifnot(!anyNA(x$date), !anyDuplicated(x$date), is.numeric(x[[id]]))
  x <- x[x$date >= request_start & x$date <= as_of, ]
  x[order(x$date), ]
}
manifest_file <- file.path(raw_dir, "source_manifest.csv")
old_manifest <- if (file.exists(manifest_file)) read.csv(manifest_file) else NULL
observations <- vector("list", nrow(series))
retrieved <- character(nrow(series))
for (j in seq_len(nrow(series))) {
  id <- series$id[j]
  path <- file.path(raw_dir, paste0(id, ".csv"))
  if (refresh_data || !file.exists(path)) {
    tmp <- tempfile(fileext = ".csv")
    tryCatch({
      download.file(series$download_url[j], tmp, method = "libcurl", mode = "wb", quiet = TRUE)
      read_series(tmp, id)
      if (!file.copy(tmp, path, overwrite = TRUE)) stop("Cannot save downloaded CSV.")
    }, finally = unlink(tmp))
    retrieved[j] <- format(Sys.time(), "%Y-%m-%dT%H:%M:%SZ", tz = "UTC")
  } else {
    previous <- if (!is.null(old_manifest)) match(id, old_manifest$id) else NA_integer_
    retrieved[j] <- if (!is.na(previous)) old_manifest$retrieved_utc[previous] else
      format(file.info(path)$mtime, "%Y-%m-%dT%H:%M:%SZ", tz = "UTC")
  }
  observations[[j]] <- read_series(path, id)
}
manifest <- series
manifest$retrieved_utc <- retrieved
manifest$md5 <- unname(tools::md5sum(file.path(raw_dir, paste0(series$id, ".csv"))))
write.csv(manifest, manifest_file, row.names = FALSE)
availability <- data.frame(id = series$id, last_month = vapply(observations,
  function(x) format(max(x$date[!is.na(x[[2]])])), character(1)))
write.csv(availability, file.path(table_dir, "series_availability.csv"), row.names = FALSE)
last_common <- min(as.Date(availability$last_month))
panel <- data.frame(date = seq(request_start, last_common, by = "month"))
for (x in observations) panel <- merge(panel, x, by = "date", all.x = TRUE, sort = TRUE)
stopifnot(all(panel$CPIAUCNS > 0, na.rm = TRUE),
  all(panel$UNRATE >= 0 & panel$UNRATE <= 100, na.rm = TRUE))
# Calendar-based lag: never delete missing months before calculating inflation.
lag12 <- match(seq_len(nrow(panel)) - 12L, seq_len(nrow(panel)))
panel$inflation <- 100 * (panel$CPIAUCNS / panel$CPIAUCNS[lag12] - 1)
analysis <- panel[panel$date >= analysis_start, ]
analysis$phase <- ifelse(analysis$date <= as.Date("2020-02-01"), "Before the shock",
  ifelse(analysis$date <= as.Date("2022-06-01"), "Shock and reopening",
  ifelse(analysis$date <= as.Date("2024-12-01"), "Inflation retreat", "Recent period")))
analysis$phase <- factor(analysis$phase, levels = c("Before the shock", "Shock and reopening",
  "Inflation retreat", "Recent period"))
analysis$run <- cumsum(!complete.cases(analysis[c("inflation", "UNRATE")]))
write.csv(analysis, file.path(processed_dir, "analysis_monthly.csv"), row.names = FALSE, na = "")
calendar_audit <- data.frame(date = analysis$date, cpi_available = !is.na(analysis$CPIAUCNS),
  unemployment_available = !is.na(analysis$UNRATE), inflation_available = !is.na(analysis$inflation))
write.csv(calendar_audit, file.path(table_dir, "calendar_audit.csv"), row.names = FALSE)
missing <- calendar_audit[!apply(calendar_audit[-1], 1, all), ]
write.csv(missing, file.path(table_dir, "missing_observations.csv"), row.names = FALSE)
if (nrow(missing) && any(missing$date != as.Date("2025-10-01"))) {
  stop("Unexpected missing month. Inspect source documentation before proceeding.")
}
at <- function(date, column) {
  value <- analysis[[column]][match(as.Date(date), analysis$date)]
  if (length(value) != 1 || is.na(value)) stop("Unavailable checkpoint: ", date)
  value
}
checkpoint_dates <- as.Date(c("2020-02-01", "2020-04-01", "2022-06-01", "2024-12-01", format(last_common)))
checkpoints <- analysis[match(checkpoint_dates, analysis$date), c("date", "inflation", "UNRATE")]
stopifnot(!anyNA(checkpoints), !anyDuplicated(checkpoints$date))
write.csv(checkpoints, file.path(table_dir, "checkpoints.csv"), row.names = FALSE)
changes <- data.frame(stage = c("Pandemic shock", "Reopening to inflation peak",
  "Peak to end of 2024", "Since end of 2024"),
  start = head(checkpoints$date, -1), end = tail(checkpoints$date, -1),
  inflation_pp = diff(checkpoints$inflation), unemployment_pp = diff(checkpoints$UNRATE))
write.csv(changes, file.path(table_dir, "stage_changes.csv"), row.names = FALSE)
latest <- tail(analysis, 1)
peak <- analysis[which.max(analysis$inflation), ]
month_label <- format(last_common, "%B %Y")
peak_label <- format(peak$date, "%B %Y")
pct <- function(x) sprintf("%.1f%%", x)
num <- function(x) sprintf("%.1f", x)
capture.output(sessionInfo(), file = file.path(table_dir, "session_info.txt"))
saveRDS(list(analysis = analysis, checkpoints = checkpoints, changes = changes),
  file.path(table_dir, "analysis_objects.rds"))

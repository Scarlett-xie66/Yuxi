# Called automatically by index.qmd. No reticulate or Jupyter is used.
run_blog1_analysis <- function(post_dir) {
  post_dir <- normalizePath(post_dir, winslash = "/", mustWork = TRUE)
  explicit_python <- Sys.getenv("BLOG1_PYTHON", unset = "")
  available <- unique(c(
    explicit_python,
    Sys.getenv("RETICULATE_PYTHON", unset = ""),
    unname(Sys.which(c("python", "python3")))
  ))
  available <- available[nzchar(available)]
  if (nzchar(explicit_python)) available <- explicit_python
  probe <- file.path(post_dir, "code", "check_environment.py")
  attempts <- character()
  python <- NULL
  for (candidate in available) {
    output <- tryCatch(
      suppressWarnings(system2(candidate, shQuote(probe), stdout = TRUE, stderr = TRUE)),
      error = function(e) structure(conditionMessage(e), status = 1L)
    )
    status <- attr(output, "status")
    if (is.null(status) || identical(as.integer(status), 0L)) {
      python <- candidate
      break
    }
    attempts <- c(attempts, paste0(candidate, "\n", paste(output, collapse = "\n")))
  }
  if (is.null(python)) {
    stop(paste0(
      "No working Python 3.10+ environment with the required packages was found.\n",
      "Install the packages once: python -m pip install -r requirements.txt\n",
      "If needed, set BLOG1_PYTHON to your Python executable in the R console, then Render again.\n",
      "For your Anaconda setup, for example: ",
      "Sys.setenv(BLOG1_PYTHON = 'D:/app.anaconda/python.exe')\n\n",
      paste(attempts, collapse = "\n\n")
    ), call. = FALSE)
  }
  before_qmd <- unname(tools::md5sum(file.path(post_dir, "index.qmd")))
  previous_dir <- getwd()
  on.exit(setwd(previous_dir), add = TRUE)
  setwd(post_dir)
  dir.create("result", recursive = TRUE, showWarnings = FALSE)
  output <- tryCatch(
    suppressWarnings(system2(python, shQuote(file.path(post_dir, "code", "build.py")),
                            stdout = TRUE, stderr = TRUE)),
    error = function(e) structure(conditionMessage(e), status = 1L)
  )
  log_path <- file.path(post_dir, "result", "rebuild_log.txt")
  existing <- if (file.exists(log_path)) readLines(log_path, warn = FALSE, encoding = "UTF-8") else character()
  if (!identical(existing, as.character(output))) {
    writeLines(as.character(output), log_path, useBytes = TRUE)
  }
  status <- attr(output, "status")
  if (!is.null(status) && as.integer(status) != 0L) {
    stop(paste0("Analysis failed. See result/rebuild_log.txt.\n",
                paste(output, collapse = "\n")), call. = FALSE)
  }
  if (!identical(before_qmd, unname(tools::md5sum(file.path(post_dir, "index.qmd"))))) {
    stop("Analysis must not modify index.qmd during rendering.", call. = FALSE)
  }
  invisible(python)
}

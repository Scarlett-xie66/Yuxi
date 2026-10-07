# Optional HTML fallback when the Quarto command is unavailable.
# Requires knitr and Pandoc; the main workflow remains Quarto Render.
post_root <- if (file.exists("index.qmd")) "." else "blog/posts/post4"
oldwd <- getwd()
setwd(post_root)
input <- readLines("index.qmd", warn=FALSE, encoding="UTF-8")
header_end <- which(input == "---")[2]
header <- input[seq_len(header_end)]
format_start <- which(header == "format:")
execute_start <- which(header == "execute:")
header <- c(header[seq_len(format_start-1)],
  'output:', '  html_document:', '    self_contained: true',
  '    css: article.css', '    toc: false', '---')
body <- input[-seq_len(header_end)]
body[body == "```{r}"] <- "```{r, echo=FALSE, include=FALSE, warning=FALSE, message=FALSE}"
body <- body[!grepl("^#\\|", body)]
fallback <- ".render_blog4.Rmd"
writeLines(c(header, body), fallback, useBytes=TRUE)
knitr::knit(fallback, output=".render_blog4.md", quiet=TRUE,
  envir=new.env(parent=globalenv()))
pandoc <- Sys.getenv("BLOG4_PANDOC", unset=Sys.which("pandoc"))
if (!nzchar(pandoc)) stop("Install Pandoc or set BLOG4_PANDOC to the Pandoc executable.")
status <- system2(pandoc, c(".render_blog4.md", "--from=markdown", "--to=html5",
  "--standalone", "--embed-resources", "--css=article.css", "--output=index.html"))
if (status != 0) stop("Pandoc rendering failed.")
unlink(c(fallback, ".render_blog4.md", ".render_blog4_files"), recursive=TRUE)
setwd(oldwd)

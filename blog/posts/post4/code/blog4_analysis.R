# Convenience entry point: complete analysis, then all three figures.
post_root <- if (file.exists("code/01_clean_analyze.R")) "." else "blog/posts/post4"
source(file.path(post_root, "code/01_clean_analyze.R"))
source(file.path(post_root, "code/02_make_figures.R"))

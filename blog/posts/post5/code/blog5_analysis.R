post_root <- if (file.exists("code/00_config.R")) "." else "blog/posts/post5"
source(file.path(post_root,"code/02_clean_analyze.R"),local=TRUE)
source(file.path(post_root,"code/03_make_figures.R"),local=TRUE)

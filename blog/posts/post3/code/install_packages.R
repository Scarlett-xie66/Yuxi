packages <- c("ggplot2","knitr","rmarkdown","zip","ipumsr","dplyr","srvyr","survey","readr")
missing <- packages[!vapply(packages,requireNamespace,logical(1),quietly=TRUE)]
if(length(missing)) install.packages(missing,repos="https://cloud.r-project.org",type=if(.Platform$OS.type=="windows") "binary" else "source")
stopifnot(all(vapply(packages,requireNamespace,logical(1),quietly=TRUE)))

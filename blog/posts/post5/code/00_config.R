# Open Blog5.Rproj, or run from the website root containing blog/posts/post5/.
post_root <- if (file.exists("code/00_config.R")) "." else "blog/posts/post5"
if (!file.exists(file.path(post_root, "code/00_config.R"))) stop("Open Blog5.Rproj or the website project root.")
project_dir <- normalizePath(post_root, winslash = "/", mustWork = TRUE)
raw_dir <- file.path(project_dir, "data/raw")
processed_dir <- file.path(project_dir, "data/processed")
figure_dir <- file.path(project_dir, "result/figures")
table_dir <- file.path(project_dir, "result/tables")
for (p in c(raw_dir, processed_dir, figure_dir, table_dir)) dir.create(p, recursive = TRUE, showWarnings = FALSE)
refresh_data <- FALSE
acs_year <- 2024L
options(timeout = max(300, getOption("timeout")))
summary_base <- "https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/data/5YRData/"
boundary_url <- paste0("https://tigerweb.geo.census.gov/arcgis/rest/services/Generalized_ACS2024/Tracts_Blocks/MapServer/4/query?", "where=STATE%3D%2742%27%20AND%20COUNTY%3D%27101%27&outFields=GEOID,NAME,CENTLAT,CENTLON&outSR=26918&returnGeometry=true&f=json")
income_breaks <- c(0, 40000, 60000, 80000, 100000, Inf)
income_labels <- c("Under $40,000", "$40,000-$59,999", "$60,000-$79,999", "$80,000-$99,999", "$100,000 or more")
poverty_breaks <- c(0, 10, 20, 30, 40, Inf)
poverty_labels <- c("Under 10%", "10%-19.9%", "20%-29.9%", "30%-39.9%", "40% or more")

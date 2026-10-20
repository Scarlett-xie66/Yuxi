post_root <- if (file.exists("code/00_config.R")) "." else "blog/posts/post5"
source(file.path(post_root, "code/01_acquire_data.R"), local = TRUE)
read_table <- function(name) read.delim(file.path(raw_dir, paste0(name, "_philadelphia.dat")), sep = "|", check.names = FALSE, stringsAsFactors = FALSE, colClasses = "character")
a <- read_table("b19013"); b <- read_table("b17001")
stopifnot(!anyDuplicated(a$GEO_ID), !anyDuplicated(b$GEO_ID), setequal(a$GEO_ID, b$GEO_ID))
clean_number <- function(x) {x <- suppressWarnings(as.numeric(x)); x[x < 0] <- NA_real_; x}
a$income <- clean_number(a$B19013_E001); a$income_moe <- clean_number(a$B19013_M001)
b$poverty_universe <- clean_number(b$B17001_E001); b$poor <- clean_number(b$B17001_E002)
b$poverty_universe_moe <- clean_number(b$B17001_M001); b$poor_moe <- clean_number(b$B17001_M002)
a <- a[c("GEO_ID", "income", "income_moe")]
b <- b[c("GEO_ID", "poverty_universe", "poor", "poverty_universe_moe", "poor_moe")]
joined <- merge(a, b, by = "GEO_ID", all = TRUE)
county <- joined[joined$GEO_ID == "0500000US42101", ]
tracts <- joined[startsWith(joined$GEO_ID, "1400000US"), ]
tracts$geoid <- sub("^1400000US", "", tracts$GEO_ID)
tracts$poverty_rate <- ifelse(tracts$poverty_universe > 0, 100 * tracts$poor / tracts$poverty_universe, NA_real_)
tracts$income_band <- cut(tracts$income, income_breaks, labels = income_labels, right = FALSE)
tracts$poverty_band <- cut(tracts$poverty_rate, poverty_breaks, labels = poverty_labels, right = FALSE)
# Income MOEs are published 90% margins. No confidence interval is invented for grouped poverty rates.
tracts$income_lower <- pmax(0, tracts$income - tracts$income_moe)
tracts$income_upper <- tracts$income + tracts$income_moe
tracts$relative_income_moe <- tracts$income_moe / tracts$income
tracts$classification_uncertain <- as.character(cut(tracts$income_lower, income_breaks, labels=income_labels,right=FALSE)) != as.character(cut(tracts$income_upper, income_breaks, labels=income_labels,right=FALSE))
geo <- jsonlite::fromJSON(file.path(raw_dir, "tract_boundaries_2024.json"), simplifyVector = FALSE)
stopifnot(length(geo$features) == 408L, geo$spatialReference$wkid == 26918L, !isTRUE(geo$exceededTransferLimit))
geographies <- do.call(rbind, lapply(geo$features, function(f) data.frame(geoid=f$attributes$GEOID, tract_name=f$attributes$NAME, latitude=as.numeric(f$attributes$CENTLAT), longitude=as.numeric(f$attributes$CENTLON))))
stopifnot(!anyDuplicated(geographies$geoid), setequal(tracts$geoid, geographies$geoid))
tracts <- merge(geographies, tracts, by="geoid", all=TRUE)
vertices <- list(); k <- 0L
for (f in geo$features) for (i in seq_along(f$geometry$rings)) {
  xy <- do.call(rbind, lapply(f$geometry$rings[[i]], unlist)); k <- k+1L
  vertices[[k]] <- data.frame(geoid=f$attributes$GEOID, ring=paste(f$attributes$GEOID,i,sep="_"), vertex=seq_len(nrow(xy)), x=xy[,1], y=xy[,2])
}
vertices <- do.call(rbind, vertices)
stopifnot(all(is.finite(vertices$x)), all(is.finite(vertices$y)), all(nchar(tracts$geoid)==11L), all(tracts$poor <= tracts$poverty_universe,na.rm=TRUE), all(tracts$poverty_rate >=0 & tracts$poverty_rate <=100,na.rm=TRUE))
map_data <- merge(vertices, tracts, by="geoid", sort=FALSE)
map_data <- map_data[order(map_data$geoid, map_data$ring, map_data$vertex), ]
# Each rate is the ratio of population counts, not an unweighted average of tract percentages.
band_summary <- do.call(rbind,lapply(income_labels,function(label){
 d <- tracts[!is.na(tracts$income_band) & tracts$income_band==label & !is.na(tracts$poverty_rate),]
 data.frame(income_band=label,tracts=nrow(d),poverty_universe=sum(d$poverty_universe),poor=sum(d$poor),poverty_rate=100*sum(d$poor)/sum(d$poverty_universe))
}))
county_rate <- 100*county$poor/county$poverty_universe
valid <- tracts[!is.na(tracts$income) & !is.na(tracts$poverty_rate),]
under <- valid[valid$income <40000,]; high <- valid[valid$income >=100000,]
summary <- list(n_tracts=nrow(tracts),income_valid=sum(!is.na(tracts$income)),income_missing=sum(is.na(tracts$income)),poverty_valid=sum(!is.na(tracts$poverty_rate)),both_valid=nrow(valid),county_income=county$income,county_income_moe=county$income_moe,county_poverty=county_rate,low_rate=band_summary$poverty_rate[1],high_rate=band_summary$poverty_rate[5],low_poor_share=100*sum(under$poor)/sum(valid$poor),low_population_share=100*sum(under$poverty_universe)/sum(valid$poverty_universe),low_tracts=nrow(under),high_tracts=nrow(high),income_moe_over30=sum(tracts$relative_income_moe>.3,na.rm=TRUE),uncertain_classes=sum(tracts$classification_uncertain,na.rm=TRUE),complete_population_share=100*sum(valid$poverty_universe)/sum(tracts$poverty_universe,na.rm=TRUE),tract_county_population_gap=sum(tracts$poverty_universe,na.rm=TRUE)-county$poverty_universe,tract_county_poor_gap=sum(tracts$poor,na.rm=TRUE)-county$poor)
# Reproducible planning screen: intensity AND caseload, not an eligibility rule.
rate_cutoff <- 30
count_cutoff <- 1000
screen <- tracts
screen$screen_group <- ifelse(is.na(screen$poverty_rate), "Estimate unavailable",
 ifelse(screen$poverty_rate >= rate_cutoff & screen$poor >= count_cutoff, "High rate, high count",
 ifelse(screen$poverty_rate >= rate_cutoff, "High rate only",
 ifelse(screen$poor >= count_cutoff, "High count only", "Below both cutoffs"))))
screen_levels <- c("High rate, high count", "High rate only", "High count only", "Below both cutoffs", "Estimate unavailable")
screen$screen_group <- factor(screen$screen_group, levels=screen_levels)
coverage <- do.call(rbind,lapply(screen_levels,function(label){
 d <- screen[screen$screen_group==label,]
 data.frame(screen_group=label,tracts=nrow(d),poor=sum(d$poor,na.rm=TRUE),
 poverty_universe=sum(d$poverty_universe,na.rm=TRUE),
 poor_share=100*sum(d$poor,na.rm=TRUE)/sum(tracts$poor,na.rm=TRUE),
 population_share=100*sum(d$poverty_universe,na.rm=TRUE)/sum(tracts$poverty_universe,na.rm=TRUE))
}))
sensitivity <- do.call(rbind,lapply(c(25,30,35),function(cutoff){
 d <- screen[!is.na(screen$poverty_rate)&screen$poverty_rate>=cutoff&screen$poor>=count_cutoff,]
 data.frame(rate_cutoff=cutoff,count_cutoff=count_cutoff,tracts=nrow(d),poor=sum(d$poor),
 poor_share=100*sum(d$poor)/sum(tracts$poor,na.rm=TRUE),
 population_share=100*sum(d$poverty_universe)/sum(tracts$poverty_universe,na.rm=TRUE))
}))
priority <- screen[screen$screen_group=="High rate, high count",]
priority <- priority[order(-priority$poor,priority$geoid),]
summary$priority_tracts <- nrow(priority)
summary$priority_poor <- sum(priority$poor)
summary$priority_poor_share <- coverage$poor_share[1]
summary$priority_population_share <- coverage$population_share[1]
summary$count_only_tracts <- coverage$tracts[3]
summary$count_only_poor_share <- coverage$poor_share[3]
summary$priority_missing_income <- sum(is.na(priority$income))
summary$priority_above_income_cutoff <- sum(priority$income>=40000,na.rm=TRUE)
summary$income_screen_missed_share <- 100-summary$low_poor_share
summary$poverty_gap_pp <- summary$low_rate-summary$high_rate
summary$poverty_ratio <- summary$low_rate/summary$high_rate
summary$poor_outside_income_screen <- sum(valid$poor)-sum(under$poor)
summary$income_screen_missing_poor <- sum(tracts$poor[is.na(tracts$income)],na.rm=TRUE)
summary$rate_only_tracts <- coverage$tracts[2]
summary$rate_only_poor_share <- coverage$poor_share[2]
summary$sensitivity_lo_tracts <- sensitivity$tracts[1]
summary$sensitivity_lo_share <- sensitivity$poor_share[1]
summary$sensitivity_hi_tracts <- sensitivity$tracts[3]
summary$sensitivity_hi_share <- sensitivity$poor_share[3]
write.csv(screen,file.path(table_dir,"tract_priority_screen.csv"),row.names=FALSE,na="")
write.csv(priority,file.path(table_dir,"priority_tracts.csv"),row.names=FALSE,na="")
write.csv(coverage,file.path(table_dir,"screen_coverage.csv"),row.names=FALSE)
write.csv(sensitivity,file.path(table_dir,"screen_sensitivity.csv"),row.names=FALSE)
write.csv(tracts,file.path(processed_dir,"tract_estimates.csv"),row.names=FALSE,na="")
write.csv(vertices,file.path(processed_dir,"map_vertices.csv"),row.names=FALSE)
write.csv(band_summary,file.path(table_dir,"income_band_poverty.csv"),row.names=FALSE)
write.csv(county,file.path(table_dir,"county_benchmark.csv"),row.names=FALSE)
write.csv(tracts[c("geoid","tract_name","income","income_moe","relative_income_moe","classification_uncertain","poverty_rate")],file.path(table_dir,"uncertainty_audit.csv"),row.names=FALSE,na="")
jsonlite::write_json(summary,file.path(table_dir,"summary.json"),pretty=TRUE,auto_unbox=TRUE,digits=12)
writeLines(capture.output(sessionInfo()),file.path(table_dir,"session_info.txt"))
saveRDS(list(tracts=tracts,vertices=vertices,summary=summary,band_summary=band_summary),file.path(table_dir,"analysis_objects.rds"))
pct <- function(x) paste0(formatC(x,format="f",digits=1),"%")
dollars <- function(x) paste0("$",format(round(x),big.mark=",",scientific=FALSE,trim=TRUE))

number <- function(x) format(round(x),big.mark=",",scientific=FALSE,trim=TRUE)

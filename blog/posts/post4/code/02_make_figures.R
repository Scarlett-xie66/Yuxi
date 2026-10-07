post_root <- if (file.exists("code/00_config.R")) "." else "blog/posts/post4"
if (!exists("analysis")) source(file.path(post_root, "code/01_clean_analyze.R"), local = TRUE)
if (!requireNamespace("ggplot2", quietly = TRUE)) stop("Install ggplot2: install.packages('ggplot2')")
library(ggplot2)
blue <- "#2f6276"; orange <- "#b65b3c"
report_theme <- theme_minimal(base_size = 13, base_family = "sans") +
  theme(panel.grid.minor = element_blank(), panel.grid.major.x = element_blank(),
    plot.background = element_rect(fill = "#fffdf9", colour = NA),
    panel.background = element_rect(fill = "#fffdf9", colour = NA),
    axis.title = element_text(colour = "#263b48"), legend.position = "none",
    plot.margin = margin(12, 22, 12, 12), strip.text = element_text(face = "bold", hjust = 0))
long <- rbind(data.frame(date = analysis$date, value = analysis$inflation,
  indicator = "Consumer-price inflation: change from a year earlier (%)"),
  data.frame(date = analysis$date, value = analysis$UNRATE,
  indicator = "Unemployment: share of the labor force (%)"))
long$indicator <- factor(long$indicator, levels = unique(long$indicator))
long$run <- ave(is.na(long$value), long$indicator, FUN = cumsum)
ends <- long[long$date == last_common, ]; ends$label <- pct(ends$value)
ends$label_date <- last_common + 85
gap <- data.frame(xmin = as.Date("2025-10-01"), xmax = as.Date("2025-11-01"))
fig1 <- ggplot(long, aes(date, value, colour = indicator)) +
  geom_rect(data = gap, aes(xmin = xmin, xmax = xmax, ymin = -Inf, ymax = Inf),
    inherit.aes = FALSE, fill = "#dedede", alpha = .85) +
  geom_line(aes(group = interaction(indicator, run)), linewidth = .85, na.rm = TRUE) +
  geom_point(data = ends, size = 2.3) +
  geom_text(data = ends, aes(x = label_date, label = label), hjust = 0, fontface = "bold", size = 4) +
  facet_wrap(~indicator, ncol = 1) + scale_colour_manual(values = c(blue, orange)) +
  scale_x_date(breaks = seq(as.Date("2019-01-01"), as.Date("2026-01-01"), by = "year"), date_labels = "%Y",
    limits = c(analysis_start, last_common + 260), expand = expansion(mult = c(.01, .01))) +
  scale_y_continuous(limits = c(0, 16), breaks = seq(0, 16, 4)) +
  labs(x = NULL, y = NULL) + report_theme
ggsave(file.path(figure_dir, "figure1_inflation_and_jobs.png"), fig1, width = 9.4, height = 6.2, dpi = 180)
# The chronological path is descriptive. Break it at missing observations.
path <- analysis[complete.cases(analysis[c("inflation", "UNRATE")]), ]
labels <- checkpoints
labels$label <- c("Feb 2020", "Apr 2020", "Jun 2022", "Dec 2024", format(last_common, "%b %Y"))
labels$lx <- c(1.8, 13.4, 5.0, 1.1, 6.5)
labels$ly <- c(3.5, 1.5, 9.5, 1.2, 4.5)
fig2 <- ggplot(path, aes(UNRATE, inflation)) +
  geom_path(aes(group = run), colour = "#aab3b6", linewidth = .5, alpha = .75) +
  geom_point(aes(colour = phase), size = 2.2, alpha = .85) +
  geom_segment(data = labels, aes(xend = lx, yend = ly), colour = "#687780", linewidth = .35) +
  geom_point(data = labels, shape = 21, fill = "#fffdf9", size = 2.5, stroke = .8) +
  geom_label(data = labels, aes(x = lx, y = ly, label = label), size = 3.5,
    fill = "#fffdf9", colour = "#263b48", label.size = 0) +
  scale_colour_manual(values = c(blue, orange, "#478578", "#7b6388")) +
  scale_x_continuous(limits = c(0, 16), breaks = seq(0, 16, 2)) +
  scale_y_continuous(limits = c(0, 10), breaks = seq(0, 10, 2)) +
  labs(x = "Unemployment rate (%)", y = "Annual consumer-price inflation (%)") + report_theme
ggsave(file.path(figure_dir, "figure2_changing_relationship.png"), fig2, width = 9.4, height = 5.5, dpi = 180)
bars <- rbind(data.frame(changes[c("stage", "start", "end")],
  indicator = "Inflation", change = changes$inflation_pp),
  data.frame(changes[c("stage", "start", "end")],
  indicator = "Unemployment", change = changes$unemployment_pp))
stage_labels <- paste0(changes$stage, "\n", format(changes$start, "%b %Y"), " to ", format(changes$end, "%b %Y"))
bars$stage_label <- factor(stage_labels[match(bars$stage, changes$stage)], levels = rev(stage_labels))
bars$label <- sprintf("%+.1f", bars$change)
bars$label_pos <- bars$change + ifelse(bars$change >= 0, .28, -.28)
fig3 <- ggplot(bars, aes(change, stage_label, fill = indicator)) +
  geom_vline(xintercept = 0, colour = "#657780", linewidth = .5) +
  geom_col(position = position_dodge(width = .72), width = .6, orientation = "y") +
  geom_text(aes(x = label_pos, label = label, group = indicator,
    hjust = ifelse(change >= 0, 0, 1)), position = position_dodge(width = .72), size = 3.8) +
  scale_fill_manual(values = c(Inflation = blue, Unemployment = orange)) +
  scale_x_continuous(limits = c(-13.5, 13.5), breaks = seq(-12, 12, 4)) +
  labs(x = "Change between the two named months (percentage points)", y = NULL) +
  report_theme + theme(panel.grid.major.y = element_blank(), panel.grid.major.x = element_line(colour = "#e5e8e7"))
ggsave(file.path(figure_dir, "figure3_change_by_stage.png"), fig3, width = 10, height = 5.6, dpi = 180)

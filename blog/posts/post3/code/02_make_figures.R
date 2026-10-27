# Locate this post when sourced from either the website or standalone project.
script_file <- tryCatch(sys.frame(1)$ofile,error=function(e) NULL)
if(is.null(script_file)) stop("Source this file from RStudio: source('code/02_make_figures.R')")
script_root <- dirname(dirname(normalizePath(script_file,winslash="/",mustWork=TRUE)))
previous_working_directory <- getwd()
setwd(script_root)
tryCatch({
project_dir <- script_root
result_dir <- file.path(project_dir,"result","tables")
object_path <- file.path(result_dir,"analysis_objects.rds")
if(!file.exists(object_path)) stop("Run 01_clean_analyze.R before 02_make_figures.R")
list2env(readRDS(object_path),envir=.GlobalEnv)
processed_dir <- file.path(project_dir,"data","processed")
figure_dir <- file.path(project_dir,"result","figures")
dir.create(figure_dir,recursive=TRUE,showWarnings=FALSE)
fig1_data <- rates
fig1_data$sex <- factor(as.character(fig1_data$sex),levels=c("Women","Men"))
fig1_data$family <- factor(child_labels[as.character(rates$child_group)],levels=rev(unname(child_labels)))
fig1_data$value <- 100*rates$employment
p1 <- ggplot2::ggplot(fig1_data,ggplot2::aes(family,value,fill=sex))+
 ggplot2::geom_col(width=.66,show.legend=FALSE)+
 ggplot2::geom_text(ggplot2::aes(y=value-1.7,label=sprintf("%.1f%%",value)),hjust=1,color="white",fontface="bold",size=3.4)+
 ggplot2::facet_wrap(~sex,ncol=2)+ggplot2::coord_flip()+
 ggplot2::scale_fill_manual(values=chart_colors)+
 ggplot2::scale_y_continuous(limits=c(0,100),breaks=c(0,25,50,75,100),labels=function(x)paste0(x,"%"),expand=c(0,0))+
 ggplot2::labs(y="Employed, share of all adults",x=NULL)+chart_theme()
ggplot2::ggsave(file.path(figure_dir,"figure1_employment.png"),p1,width=8.5,height=5.6,dpi=300,bg="white")
p1

states <- rbind(data.frame(rates[,c("sex","child_group")],state="Employed",share=rates$employment),
 data.frame(rates[,c("sex","child_group")],state="Unemployed",share=rates$participation-rates$employment),
 data.frame(rates[,c("sex","child_group")],state="Outside labor force",share=1-rates$participation))
states <- states[as.character(states$child_group) %in% c("no_minor","age0_5"),]
states$sex <- factor(as.character(states$sex),levels=c("Women","Men"))
states$state <- factor(states$state,levels=c("Employed","Unemployed","Outside labor force"))
states$family <- factor(child_labels[as.character(states$child_group)],levels=rev(unname(child_labels)))
stopifnot(all(states$share>=-1e-8))
p2 <- ggplot2::ggplot(states,ggplot2::aes(family,100*share,fill=state))+
 ggplot2::geom_col(width=.66,position=ggplot2::position_stack(reverse=TRUE))+
 ggplot2::geom_text(data=subset(states,state=="Outside labor force"),
 ggplot2::aes(y=ifelse(share<.16,103,100-50*share),label=sprintf("%.1f%%",100*share),hjust=ifelse(share<.16,0,.5)),color="#39434b",size=3.8)+
 ggplot2::facet_wrap(~sex,ncol=2)+ggplot2::coord_flip()+
 ggplot2::scale_fill_manual(values=c(Employed="#2f6276",Unemployed="#d4a25f",`Outside labor force`="#d8dee1"),name=NULL)+
 ggplot2::scale_y_continuous(limits=c(0,117),breaks=c(0,25,50,75,100),labels=function(x)paste0(x,"%"),expand=c(0,0))+
 ggplot2::labs(y="Share of all adults",x=NULL)+chart_theme()+
 ggplot2::theme(legend.position="none")
ggplot2::ggsave(file.path(figure_dir,"figure2_labor_force.png"),p2,width=8.5,height=4.1,dpi=300,bg="white")
p2

fig3_data <- do.call(rbind,lapply(seq_len(nrow(status_decomposition)),function(i) {
 z <- status_decomposition[i,]
 data.frame(sex=z$sex,state=c("Outside the labor force","Unemployed","Employed"),
 difference=c(-z$outside_contribution_pp,-z$unemployed_contribution_pp,z$employment_gap_pp))
}))
utils::write.csv(fig3_data,file.path(result_dir,"state_share_differences.csv"),row.names=FALSE)
fig3_data$sex <- factor(fig3_data$sex,levels=c("Women","Men"))
fig3_data$state <- factor(fig3_data$state,levels=c("Employed","Unemployed","Outside the labor force"))
p3 <- ggplot2::ggplot(fig3_data,ggplot2::aes(x=difference,y=state,fill=state))+
 ggplot2::geom_vline(xintercept=0,color="#7a898f",linewidth=.6)+
 ggplot2::geom_col(width=.52,show.legend=FALSE)+
 ggplot2::geom_text(ggplot2::aes(x=difference+ifelse(difference>=0,.65,-.65),
 label=sprintf("%+.1f",difference),hjust=ifelse(difference>=0,0,1)),size=3.8,fontface="bold")+
 ggplot2::facet_wrap(~sex,ncol=2)+
 ggplot2::scale_fill_manual(values=c("Employed"="#2f6276","Outside the labor force"="#b65b3c","Unemployed"="#d4a25f"))+
 ggplot2::scale_x_continuous(limits=c(-16,18),breaks=c(-10,-5,0,5,10,15),labels=function(x)ifelse(x==0,"0",sprintf("%+g",x)))+
 ggplot2::labs(x="Difference in people per 100 adults",y=NULL)+chart_theme()+
 ggplot2::theme(panel.grid.major.y=ggplot2::element_blank(),strip.text=ggplot2::element_text(face="bold"))
ggplot2::ggsave(file.path(figure_dir,"figure3_status_differences.png"),p3,width=8.5,height=4.1,dpi=300,bg="white")
p3

utils::write.csv(data.frame(series="IPUMS CPS ASEC",sample="cps2025_03s",analysis_year=2025,
 frequency="Single ASEC cross-section",reason="Intentional 2025 comparison; no 2024-2026 trend estimated",
 analysis_mode=analysis_mode,read_timestamp_utc=format(Sys.time(),tz="UTC",usetz=TRUE)),
 file.path(result_dir,"data_coverage.csv"),row.names=FALSE)

capture.output(sessionInfo(),file=file.path(result_dir,"session_info_report.txt"))
utils::write.csv(data.frame(run_id=run_id,analysis_mode=analysis_mode,microdata_model_refitted=analysis_mode=="microdata",
 figures_regenerated=TRUE),file.path(result_dir,"execution_audit.csv"),row.names=FALSE)

writeLines(paste("COMPLETE",run_id),file.path(result_dir,"run_status.txt"))
# Aggregate-only handoff: never copy raw microdata, .Renviron or request credentials.
review_dir <- file.path(project_dir,"result","review_for_codex")
dir.create(review_dir,recursive=TRUE,showWarnings=FALSE)
for(p in list.files(review_dir,full.names=TRUE)) if(!dir.exists(p)) unlink(p)
for(d in c(result_dir,figure_dir)) {
 files <- list.files(d,full.names=TRUE)
 files <- files[grepl("[.](csv|txt|png)$",files,ignore.case=TRUE)]
 if(length(files)) file.copy(files,review_dir,overwrite=TRUE)
}
file.copy(file.path(project_dir,"EDITORIAL_WINDOW.md"),review_dir,overwrite=TRUE)
writeLines(c(if(analysis_mode=="microdata") "Editorial status: MICRODATA RUN COMPLETED; review prose against results." else "Editorial status: REFERENCE PREVIEW; original microdata model not refitted.",
 "Send this folder (or its zip) for final analysis, interpretation and recommendations.",
 "Do not add raw CPS records, API keys or .Renviron."),file.path(review_dir,"HANDOFF.txt"))
if(requireNamespace("zip",quietly=TRUE)) {
 bundle <- file.path(project_dir,"result","review_for_codex.zip")
 zip::zipr(bundle,files=list.files(review_dir,full.names=TRUE),root=review_dir)
 message("Send: ",bundle)
} else message("Send the result/review_for_codex folder; zip it in Windows Explorer if needed.")

},finally=setwd(previous_working_directory))

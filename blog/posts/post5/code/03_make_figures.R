post_root <- if (file.exists("code/00_config.R")) "." else "blog/posts/post5"
if (!exists("map_data")) source(file.path(post_root,"code/02_clean_analyze.R"),local=TRUE)
if (!requireNamespace("ggplot2",quietly=TRUE)) stop("Install ggplot2 first.")
library(ggplot2)
income_colors <- c("#e1e8e6","#bdcfca","#89aca4","#507f79","#174b4d")
poverty_colors <- c("#f3e8d9","#e6c6a1","#cf9874","#ac654e","#703a3d")
limits_x <- range(vertices$x)+c(-2200,2200);limits_y <- range(vertices$y)+c(-2200,2200)
map_theme <- theme_void(base_size=12,base_family="sans") + theme(legend.position="right",legend.title=element_text(size=12,face="bold"),legend.text=element_text(size=10),legend.key.height=grid::unit(.55,"cm"),plot.margin=margin(12,12,12,12),plot.background=element_rect(fill="white",colour=NA))
# Broad place labels orient the reader; they do not define analysis zones.
places <- data.frame(label=c("Northwest", "Northeast", "North", "West", "Center City", "South"),
 latitude=c(40.075,40.09,40.005,39.97,39.955,39.92),longitude=c(-75.21,-75.035,-75.15,-75.225,-75.16,-75.17))
for (i in seq_len(nrow(places))) {
 distance <- (geographies$latitude-places$latitude[i])^2 + ((geographies$longitude-places$longitude[i])*cos(40*pi/180))^2
 id <- geographies$geoid[which.min(distance)]; v <- vertices[vertices$geoid==id,]
 places$x[i] <- mean(range(v$x)); places$y[i] <- mean(range(v$y))
}
write.csv(places,file.path(table_dir,"map_label_positions.csv"),row.names=FALSE)
map_base <- function(field, labels, colors, legend_title) {
 ggplot(map_data,aes(x,y,group=geoid,subgroup=ring))+
  geom_polygon(aes(fill=.data[[field]]),rule="evenodd",colour="white",linewidth=.16)+
  scale_fill_manual(values=setNames(colors,labels),limits=labels,drop=FALSE,na.value="#d5d5d5",na.translate=TRUE,name=legend_title)+
  geom_label(data=places,aes(x=x,y=y,label=label),inherit.aes=FALSE,
    size=3,fill="white",alpha=.88,colour="#333333",label.size=0,label.padding=grid::unit(.12,"lines"))+
  coord_equal(xlim=limits_x,ylim=limits_y,expand=FALSE)+map_theme+
  annotate("segment",x=limits_x[1]+1500,xend=limits_x[1]+1500,y=limits_y[2]-7000,yend=limits_y[2]-3000,arrow=grid::arrow(length=grid::unit(.15,"cm")),linewidth=.45)+
  annotate("text",x=limits_x[1]+1500,y=limits_y[2]-2100,label="N",size=3.5)+
  annotate("segment",x=limits_x[1]+1800,xend=limits_x[1]+6800,y=limits_y[1]+1300,yend=limits_y[1]+1300,linewidth=.8)+
  annotate("text",x=limits_x[1]+4300,y=limits_y[1]+2400,label="5 km",size=3)+
  annotate("text",x=limits_x[1]+1800,y=limits_y[1]+350,label="0",size=2.5)+
  annotate("text",x=limits_x[1]+6800,y=limits_y[1]+350,label="5",size=2.5)
}
fig1 <- map_base("income_band",income_labels,income_colors,"Median household\nincome (2024 dollars)")
# A joint map makes rate/count mismatches visible; all original output paths stay valid.
screen_map <- merge(vertices,screen[c("geoid","screen_group")],by="geoid",sort=FALSE)
screen_map <- screen_map[order(screen_map$geoid,screen_map$ring,screen_map$vertex),]
fig2 <- ggplot(screen_map,aes(x,y,group=geoid,subgroup=ring))+
 geom_polygon(aes(fill=screen_group),rule="evenodd",colour="white",linewidth=.16)+
 scale_fill_manual(values=c("High rate, high count"="#843b42","High rate only"="#d3a069",
 "High count only"="#487f7a","Below both cutoffs"="#e9e9e5","Estimate unavailable"="#bcbcbc"),
 limits=screen_levels,drop=FALSE,name="Poverty screen")+
 geom_label(data=places,aes(x=x,y=y,label=label),inherit.aes=FALSE,size=3,
 fill="white",alpha=.88,colour="#333333",label.size=0,label.padding=grid::unit(.12,"lines"))+
 coord_equal(xlim=limits_x,ylim=limits_y,expand=FALSE)+map_theme+
 annotate("segment",x=limits_x[1]+1500,xend=limits_x[1]+1500,y=limits_y[2]-7000,yend=limits_y[2]-3000,arrow=grid::arrow(length=grid::unit(.15,"cm")),linewidth=.45)+
 annotate("text",x=limits_x[1]+1500,y=limits_y[2]-2100,label="N",size=3.5)+
 annotate("segment",x=limits_x[1]+1800,xend=limits_x[1]+6800,y=limits_y[1]+1300,yend=limits_y[1]+1300,linewidth=.8)+
 annotate("text",x=limits_x[1]+4300,y=limits_y[1]+2400,label="5 km",size=3)

band_summary$income_band <- factor(band_summary$income_band,levels=rev(income_labels))
fig3 <- ggplot(band_summary,aes(poverty_rate,income_band))+
 geom_vline(xintercept=county_rate,colour="#777777",linetype="dashed",linewidth=.5)+
 geom_col(fill="#507f79",width=.6)+geom_text(aes(label=pct(poverty_rate)),hjust=-.15,size=4)+
 scale_x_continuous(limits=c(0,45),breaks=seq(0,40,10),labels=function(x)paste0(x,"%"),expand=expansion(mult=c(0,.02)))+
 labs(x="Population-weighted poverty rate",y=NULL)+theme_minimal(base_size=13,base_family="sans")+
 theme(panel.grid.minor=element_blank(),panel.grid.major.y=element_blank(),plot.background=element_rect(fill="white",colour=NA),axis.text.y=element_text(colour="#333333"),plot.margin=margin(12,25,12,12))+
 annotate("text",x=county_rate+.6,y=5.55,label=paste0("Citywide: ",pct(county_rate)),hjust=0,size=3.4,colour="#666666")
# Save to a temporary PNG, verify its end marker, then replace the final asset.
# This prevents a partial export from becoming a published figure.
save_checked_png <- function(plot, filename, height) {
 temporary <- tempfile(pattern="blog5_",tmpdir=figure_dir,fileext=".png")
 on.exit(unlink(temporary),add=TRUE)
 expected_end <- as.raw(c(0,0,0,0,73,69,78,68,174,66,96,130))
 complete <- FALSE
 for (attempt in seq_len(3)) {
  ggsave(temporary,plot,width=8.8,height=height,dpi=300)
  size <- file.info(temporary)$size
  connection <- file(temporary,"rb")
  seek(connection,where=size-12,origin="start")
  ending <- readBin(connection,"raw",n=12)
  close(connection)
  complete <- identical(ending,expected_end)
  if (complete) break
 }
 if (!complete) stop("PNG export is incomplete: ",filename)
 destination <- file.path(figure_dir,filename)
 if (!file.copy(temporary,destination,overwrite=TRUE)) stop("Cannot save figure: ",filename)
}
save_checked_png(fig1,"figure1_income_map.png",7.2)
save_checked_png(fig2,"figure2_poverty_map.png",7.2)
save_checked_png(fig3,"figure3_income_poverty.png",4.7)

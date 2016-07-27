library(ggplot2)
library(reshape2)
library(dplyr)
library(stringr)
library(magrittr)
library(RColorBrewer)
library(rPython)

source("scripts/myUtilityFunctions-copy.R")


#####
#Load datasets
#####

activ_df <-  read.csv("intermediate_outputs/domain_activity_not_norm.csv")
activ_norm_df <-  read.csv("intermediate_outputs/domain_activity_norm.csv")

#####
#Timelines
#####
timeline <- read.csv("tech_event_timelines.csv")
timeline$month_date <- as.Date(as.character(timeline$month_date),
                               format = "%d/%m/%y")

#Tidy up factors
timeline$metric <- factor(timeline$metric,
                               levels=c("group_id","attendees",
                                        "average_attendees"),ordered = TRUE)
levels(timeline$metric) <- c("Events","Attendees","Attendes per event")

timeline_events = timeline %>%
     filter(metric=="Events")

#####
#Plot
#####
#Focus on activ.
#Tasks: modify date, melt, plot freeing up y scale, add annotations.

#Modify date and remove post March 2016
activ_df$month_date <-  as.Date(as.character(activ_df$month_date),
                              format = "%Y-%m-%d")
#Melt
activ_long_df <-  activ_df %>% select(-X) %>%  
     filter(month_date < as.Date("2016-04-01",format="%Y-%m-%d")) %>%
     melt(id.vars = c("month_date","topic_id")) %>%
     rename(metric=variable)
     
#Plot
#Tidy up factors
activ_long_df$metric <- factor(activ_long_df$metric,
                               levels=c("group_id","attendees",
                                        "average_attendees"),ordered = TRUE)
levels(activ_long_df$metric) <- c("Events","Attendees","Attendes per event")

#Plot
activ_plot <-  ggplot(data=activ_long_df,
                    aes(x=month_date,y=value,group=topic_id,
                        colour=topic_id))+
     geom_line()+
     facet_grid(metric~.,scales='free') +
     geom_vline(data=timeline,aes(xintercept = as.numeric(month_date),
                                  color=topic_id),linetype=3,alpha=1)+
     geom_text(data=timeline_events,aes(x=month_date,
                                 y=10,label=ev_label,color=topic_id),
               size=3,hjust=-0.7)+
     scale_color_manual(values=c("#1f78b4","#33a02c","#e31a1c"))+
     scale_x_date(date_labels="%Y")+
     labs(title="Tech area activity in Meetup, 2013-2016 (Rolling average, not normalised)",
          y="Number",x=NULL,color="Tech area")+
     theme_light()+
     theme(plot.title=element_text(family='Palatino'))

WriteChart(activ_plot,"plots/",w=9,h=6)

######
#Activ norm
######
#Modify date
activ_norm_df$month_date <-  as.Date(as.character(activ_norm_df$month_date),
                              format = "%Y-%m-%d")
#Melt
activ_long_norm_df <-  activ_norm_df %>% select(-X) %>%
     filter(month_date < as.Date("2016-04-01",format="%Y-%m-%d")) %>%
     melt(id.vars = c("month_date","metric")) %>%
     rename(topic_id=variable)

levels(activ_long_norm_df$topic_id) <- 
     levels(activ_long_df$topic_id)

#Tidy up factors
activ_long_norm_df$metric <- factor(activ_long_norm_df$metric,
                               levels=c("group_id","attendees",
                                        "average_attendees"),ordered = TRUE)
levels(activ_long_norm_df$metric) <- c("Events","Attendees","Attendes per event")

#Subset Df to focus on months where there was activity
activ_long_norm_df <- activ_long_norm_df[activ_long_norm_df$month_date>
                                    min(activ_long_df$month_date),]

#Plot
activ_norm_plot <-  ggplot(data=activ_long_norm_df,
                      aes(x=month_date,y=value,group=topic_id,
                          colour=topic_id))+
     geom_line()+
     facet_grid(metric~.,scales='free') +
     geom_vline(data=timeline,aes(xintercept = as.numeric(month_date),
                                  color=topic_id),linetype=3,alpha=1)+
     geom_text(data=timeline_events,aes(x=month_date,
                                        y=0.3,label=ev_label,color=topic_id),
               size=3,hjust=-0.7,vjust=1)+
     scale_color_manual(values=c("#1f78b4","#33a02c","#e31a1c"))+
     scale_x_date(date_labels="%Y")+
     labs(title="Tech area activity in Meetup, 2013-2016 (Rolling average, normalised)",
          y="Normalised value",x=NULL,color="Tech area")+
     theme_light()+
     theme(plot.title=element_text(family='Palatino'))

WriteChart(activ_norm_plot,"plots/",w=9,h=6)

#Recent activity
recent_activity_df = 
     read.csv("intermediate_outputs/recent_activity.csv") %>% melt(id.vars='topic_id')

#Reorder topic levels (by number of groups)

ordered_topics = recent_activity_df %>% 
     filter(variable=='attendees') %>%
     arrange(desc(value)) %>%
     as.data.frame() %>% extract(,"topic_id")


recent_activity_df$topic_id = factor(recent_activity_df$topic_id,
                                     levels=ordered_topics,ordered=TRUE)

recent_activity_df$variable = factor(recent_activity_df$variable,
                                     levels=
                                          c("attendees",
                                            "event_number","group_number",
                                            "events_per_group",
                                            "attendees_per_event"))

levels(recent_activity_df$variable) = 
     c("Attendees","Events","Groups","Events \n per group",
       "Attendees \n per event")

levels(recent_activity_df$topic_id)[1] <- 
     "bring-angel-investors \n -and-startups-together"


recent_activity_plot = 
     ggplot(data=recent_activity_df,
            aes(x=topic_id,y=value))+
     geom_bar(stat='identity',fill='#e31a1c',width=0.5,color="black",
              size=0.05)+
     facet_grid(variable~.,scales='free')+
     theme_light()+
     theme(axis.text.x=element_text(angle=45,hjust=1,size=7))+
     labs(title="UK Meetup activity in most popular new keywords, March 2015 /March-2016",
          x=NULL,y="Value")+
     theme(plot.title=element_text(family='Palatino'))

WriteChart(recent_activity_plot,"plots/",w=7.5,h=7)



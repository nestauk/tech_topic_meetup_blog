
# coding: utf-8

# # Data processing of Meetup data for Nesta blog

# ## 0. Imports and preliminaries

# In[33]:

import os
import json
import requests
import urllib
from urllib.request import urlopen
import re
import random
import datetime
import ratelim
import scipy
import numpy as np
import pandas as pd
import praw


# In[42]:

#File paths

#Create intermediate output path
os.listdir()

#Path to data files
main_directory = os.path.dirname(os.getcwd())

data_path = os.path.join(os.path.dirname(os.getcwd()),"meetup_data")
intermediate_output_path = os.path.dirname(os.getcwd()) + "/" + "intermediate_outputs"
plot_path = os.path.dirname(os.getcwd()) + "/" + "plots"

if 'intermediate_outputs' not in os.listdir(main_directory):
    os.mkdir(intermediate_output_path)
if 'plots' not in os.listdir(main_directory):
    os.mkdir(plot_path)

#Read api key from config file 'my_api_key'
with open(os.path.join(main_directory,"my_api_key.json"),'r') as data_file:
    my_api_key = json.load(data_file)['api_key']


# ## 1. Functions

# In[35]:

## Functions for data crawling

#Meetup API url
api_base_url = "https://api.meetup.com/2/"

#Rate limits
RATELIM_DUR = 60 * 60
RATELIM_QUERIES = 9000

#Event crawler
@ratelim.patient(RATELIM_QUERIES,RATELIM_DUR)
def crawl_events(group_id):
    '''
    Input: a meetup group id
    Output: a json object with information about the group events.
    '''
    
    #Build request
    api_url = api_base_url + 'events'
    request_parameters = "?group_id={}&status=past&key={}".format(group_id,my_api_key)
    
    event_request = api_url + request_parameters
    
    #Make API call and obtain response using the get method in requests.
    response = requests.get(event_request)
    
    return(response.json())

#RSVP crawler. NB we haven't used this function in this analysis. 
@ratelim.patient(RATELIM_QUERIES,RATELIM_DUR)
def crawl_rspvs(event_id):
    '''
    Input: event_id
    Output: a json object with information about attendees at events
    '''
    
    #Build request:
    api_url = api_base_url + "rsvps"
    request_parameters = "?&event_id={}&key={}".format(event_id,my_api_key)
    
    rsvps_request = api_url + request_parameters
    
    #Make request
    response = requests.get(rsvps_request)
    
    return(response.json())


# In[36]:

#Utilities to process data
def extract_topics_from_dict(topic,container):
    '''
    This function goes through a list where each element is a topic with a dictionary containing name,
        urlkey (unique identifier) and id. It extracts the urlkey.
    
    input: a container (list) of dictionaries and a key (topic) to extract
    output: a list with the topics
    '''
    
    out = [top[topic] for top in container]
    return(out)

#Work with datetimes
def extract_date_from_epoch(posix_date):
    '''
    input: a POSIX timestamp.
    output: a local date
    '''
    out = datetime.datetime.fromtimestamp(posix_date).strftime("%d-%m-%Y")
    
    return(out)

def get_month(date_var):
    '''
    input: a date
    returnd: A date that bins all days for that month into a single month (day 1)
    '''
    outvar = datetime.datetime.strptime("01-" + date_var[3:],"%d-%m-%Y")  
    return(outvar)


# In[60]:

#Functions to extract groups from 
def extract_groups_with_keyword(kw):
    """
    input: a keyword kw
    returns: A df with a boolean columns indicating if kw is in the keyword list for the group
    """
    group_topics_df['has_keyword'] = [kw in 
                              topic_set for topic_set in group_topics_df['group_topics']]
    
    return(group_topics_df)     
    
def get_groups_with_keyword(kw):
    '''
    Returns the group metadata for groups that contain a keyword.
    
    Input: kw, the keyword
    Output: A dataframe with group metadata.
    
    '''
    #Extract dataframe with labelled groups
    domain_df = extract_groups_with_keyword(kw)
    
    #Subset by variable of interest
    domain_mask = domain_df['has_keyword']==True
    
    #Extract relevant ids
    domain_ids = list(domain_df.ix[domain_mask,'group_id'])
    
    #Extract information about relevant ids
    domain_groups_df = group_metadata_df[[gid in domain_ids 
                                       for gid in group_metadata_df['group_id']]]
    
    domain_groups_df['topic_id'] = kw
    
    #Return data
    return(domain_groups_df)

def extract_novel_keywords(threshold_date):
    '''
    input: a threshold date (string) in %d-%m-%Y format
    output: novel keywords after the threshold.
    
    '''
    
    threshold_date = datetime.datetime.strptime(threshold_date,"%d-%m-%Y")

    #Unique kws before threshold
    first_period_kws = set([kw for kw_list,date in 
                           zip(group_topics_df['group_topics'],
                               group_topics_df['created_date']) for kw in kw_list if
                            date < threshold_date])

    snd_period_kws = set([kw for kw_list,date in 
                           zip(group_topics_df['group_topics'],
                               group_topics_df['created_date']) for kw in kw_list if
                           date > threshold_date])

    novel_kws = [tag for tag in snd_period_kws if tag not in first_period_kws]

    #Count novel kws
    novel_counts = [kw for kw_list,date in 
                           zip(group_topics_df['group_topics'],
                               group_topics_df['created_date']) for kw in kw_list if
                           date > threshold_date and kw in novel_kws]

    #Count all kw appearances in period
    novel_freqs = pd.Series(novel_counts).value_counts()

    return(novel_freqs)


#Function to extract all event activity for a keyword
def extract_keyword_activity(keyword):
    '''
    Input: a meetup keyword
    Output: Outputs with event activity: a df with groups active in the keyword, and events for those groups.
    
    '''
    
    #Extract groups
    groups_df = get_groups_with_keyword(keyword)
    
    #Extract group ids
    group_ids = list(groups_df['group_id'])
    
    #Extract events and their results
    events = [crawl_events(i) for i in group_ids]
    
    #Extract event ids and their rsvps
    event_results = [event['results'] for event in events if
                       len(event['results'])>0]
    event_ids= [event['id'] for event_list in event_results for event in event_list]

    #Crawl event ids
    #rsvps = [crawl_rspvs(i) for i in event_ids]
    
    #Parse events
    event_results = [{
        "event_id":event_result['id'],
        "date":extract_date_from_epoch(int(event_result['time'])/1000),
        "group_id": event_result['group']['id'],
        "attendees":event_result['yes_rsvp_count']} for
                     event_list in event_results for event_result in event_list]
    event_df = pd.DataFrame(event_results)
    
    if (len(event_df)>0):
        events_labelled_df = pd.merge(event_df,
                                    groups_df[['group_id','topic_id']],
                                     left_on='group_id',
                                     right_on='group_id')

        outputs = [events_labelled_df]
        return(outputs)


# ## 2a. Data processing: Generate dataset with group/event activity in selected keywords

# In[39]:

#The input for this analysis is a json file with information about tech groups obtained with
#a Meetup API wrapper developed by Matt Williams: https://github.com/mattjw/exploring_tech_meetups

#Observations: json loads works with strings so we had to decode the lines.
tech_groups = [json.loads(line.decode()) for line in open(data_path + "/" + "tech_groups.json","rb")]

#Group topics is a lis of dict with group ids, date when they were created, and their topics.
group_topics = [{"group_id": g["_id"],
                 "group_created": extract_date_from_epoch(
            int(g["created"]['$numberLong'])/1000),
                   "group_topics":extract_topics_from_dict('urlkey',g['topics'])} for
                g in tech_groups]
#Create dataframe
group_topics_df = pd.DataFrame(group_topics)

#Create a month bin where day is always one
group_topics_df['created_date'] = group_topics_df[
    'group_created'].apply(lambda x:
                           datetime.datetime.strptime("01-" + x[3:],"%d-%m-%Y"))  

#Create list of documents with keywords
group_topics_list = [g['group_topics'] for g in group_topics]


# In[40]:

#Parse group metadata
group_metadata_df = pd.DataFrame([{"group_id": g["_id"],
                        "group_name": g["name"],
                        "group_city": g["city"],
                        "group_lon":g["lon"],
                        "group_lat":g["lat"],
                        "group_created": 
                                   extract_date_from_epoch(int(g["created"]['$numberLong'])/1000),
                   "group_topics":extract_topics_from_dict('urlkey',g['topics'])} for
                                   g in tech_groups])
    


# In[43]:

#Generate dataframe with groups in the keywords of interest (they could be something else)
domain_list = ['virtual-reality','deep-learning','bitcoin']

domain_dfs = [get_groups_with_keyword(x) for x in
                                      domain_list]

all_domains_df = pd.concat(domain_dfs,axis=0)

#Output
all_domains_df.to_csv(os.path.join(intermediate_output_path,"domain_activity_df.csv"))


# In[44]:

#Extract events and RSVPs for all relevant groups

#Extract ids for all relevant groups
domain_gr_ids = list(all_domains_df['group_id'])

#Crawl events
domain_events = [crawl_events(i) for i in domain_gr_ids]

#Extract results (for events where there are results)
domain_event_results = [event['results'] for event in domain_events if
                       len(event['results'])>0]
domain_event_ids= [event['id'] for event_list in domain_event_results for event in event_list]

#Each group contains a list of events. We extract their date, rsvp count and location.
all_event_results = [{
        "event_id":event_result['id'],
        "date":extract_date_from_epoch(int(event_result['time'])/1000),
        "group_id": event_result['group']['id'],
        "attendees":event_result['yes_rsvp_count']} for
                     event_list in domain_event_results for event_result in event_list]

#Put everythingin a dataframe
all_event_df = pd.DataFrame(all_event_results)

all_events_labelled_df = pd.merge(all_event_df,
                                all_domains_df[['group_id','topic_id']],
                                 left_on='group_id',
                                 right_on='group_id')
all_events_labelled_df.to_csv(os.path.join(intermediate_output_path,"domain_events_df.csv"))


# ## 2b. Data processing: Generate processed outputs for visualisation

# In[45]:

#Generate df with counts of groups formed and attendees at events by keyword/month combination
#Create month variable
all_events_labelled_df['month_date'] = all_events_labelled_df['date'].map(lambda x:
                                                                         get_month(x))
#Group_by month and generate summaries

#Create dict with functions per variable. We want, for each month/keyword combo,
#    a count of all groups created and the sum of all attendees to events in those groups
summ_funcs = {'group_id': ['count'],'attendees': ['sum']}

#Group by month and extract summary statistics.
all_activity_df = all_events_labelled_df.groupby([
        'month_date','topic_id']).agg(summ_funcs).reset_index(drop=False)

#We have multi-index columns. Drop the lower index
all_activity_df.columns = all_activity_df.columns.droplevel(level=1)

#Pivot table
all_activity_pivot = all_activity_df.pivot_table(columns='topic_id',
                                                 index='month_date',
                                                 values=['attendees','group_id'])
all_activity_pivot.fillna(value=0,inplace=True)
all_act_rm = all_activity_pivot.apply(lambda x: pd.rolling_mean(x,window=4))

#Create additional metrics for visualisation, and output.
all_event_metrics = pd.melt(all_act_rm.reset_index(drop=False),
                            id_vars='month_date')
all_event_metrics.rename(columns={None:"metric"},inplace=True)

all_event_pivot = pd.pivot_table(all_event_metrics,
                                index=['month_date','topic_id'],columns='metric',
                                values='value')

#Average attendees
all_event_pivot['average_attendees'] = all_event_pivot['attendees']/all_event_pivot['group_id']
all_event_pivot.fillna(value=0,inplace=True)
all_event_pivot.reset_index(level=1,drop=False,inplace=True)


#my_mask = [x.year >= 2013 for x in all_event_pivot.index]
#all_event_pivot = all_event_pivot[my_mask]

all_event_pivot.reset_index(drop=False,inplace=True)
all_event_pivot.to_csv(os.path.join(intermediate_output_path,"domain_activity_not_norm.csv"))


# In[49]:

#We want to normalise all the above by 'average' levels of activity in Meetup, based on 200 randomly selected
#groups.
random.seed(123)

#Extract random sample of 200 groups
#Extract 200 random indices based on the tech_groups list
random_groups = random.sample(range(0,len(tech_groups)),200)

#Get the ids for those
random_group_ids = [g['id'] for num,g in enumerate(tech_groups) if num in random_groups]

#Extract them from Meetup
random_event_results = [crawl_events(gid)['results'] for gid in random_group_ids]

#Create df
random_events_df = pd.DataFrame([{"event_id":event_result['id'],
                    "date":extract_date_from_epoch(int(event_result['time'])/1000),
                    "group_id": event_result['group']['id'],
                    "attendees":event_result['yes_rsvp_count']} for
                     event_list in random_event_results for event_result in event_list])

#Same processing as we did above, yoink repetitive.
#Extract month
random_events_df['month_date'] = random_events_df['date'].map(lambda x:
                                                                         get_month(x))

#Extract summary stats (not aggregating by keyword because it is unnecessary)
random_activity_df = random_events_df.groupby([
        'month_date']).agg(summ_funcs)

random_activity_df.columns = random_activity_df.columns.droplevel(level=1)

random_activity_df = random_activity_df[['attendees','group_id']]

random_rolling = random_activity_df.apply(lambda x: pd.rolling_mean(x,window=4))

#Create domain activity dataframe for plotting (normalised)

random_rolling['average_attendees']=random_rolling['attendees']/random_rolling['group_id']
random_rolling['topic_id'] = 'all'
random_rolling.reset_index(drop=False,inplace=True)

#Process: melt both, concatenate over rows and pivot
random_melted = pd.melt(random_rolling,
                        id_vars=['month_date','topic_id'])
random_melted.rename(columns={'variable':'metric'},inplace=True)


all_event_melted = pd.melt(all_event_pivot,
                           id_vars=['month_date','topic_id'])


# In[57]:

#Normalise the domain df by activity in the random set
event_random_long = pd.concat([all_event_melted,random_melted],axis=0)
event_random_wide = pd.pivot_table(event_random_long,index=['month_date','metric'],
                                  columns='topic_id',values='value')

event_random_norm = event_random_wide.apply(
    lambda x: x/event_random_wide['all']).reset_index(level=1,drop=False)

#my_mask = [np.isnan()] >= 2013 for x in event_random_norm.index]

all_event_norm = event_random_norm.ix[:,['metric','bitcoin','deep-learning',
                                              'virtual-reality']].reset_index(drop=False)
all_event_norm.to_csv(os.path.join(intermediate_output_path,"domain_activity_norm.csv"))


# ## 2c: Extract data about emerging trends

# In[62]:

#Extract top 10 keywords from last year.
top_10_last_year = extract_novel_keywords("01-03-2015")[:20]

top_10_keywords_list = [i for i in top_10_last_year.index]

recent_keywords_info = [extract_keyword_activity(i) for i in top_10_keywords_list]
recent_activity_df = pd.concat([x[0] for x in recent_keywords_info],axis=0)


# In[63]:

#recent_activity_df for plotting with R (similar processing to above, and some repetition)

summ_funcs = {'group_id': ['count','unique'],'attendees': ['sum']}

recent_activity_df['month_year'] = recent_activity_df['date'].apply(get_month)

recent_activity_stats= recent_activity_df.groupby(['topic_id']).agg(summ_funcs)

recent_activity_stats.columns = recent_activity_stats.columns.droplevel(level=0)

recent_activity_stats['group_number'] = [len(x) for x in recent_activity_stats['unique']]

recent_activity_stats.rename(columns={'count':'event_number','sum':'attendees'},inplace=True)

recent_activity_stats = recent_activity_stats[['event_number','group_number','attendees']]

#New variablws
recent_activity_stats['attendees_per_event'] = recent_activity_stats['attendees']/recent_activity_stats['event_number']
recent_activity_stats['events_per_group'] = recent_activity_stats['event_number']/recent_activity_stats['group_number']

#Write out
recent_activity_stats.to_csv(os.path.join(intermediate_output_path,"recent_activity.csv"))


# In[ ]:




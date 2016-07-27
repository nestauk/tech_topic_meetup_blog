# Code for analysis of emerging tech topics in web data

This repo contains Python and R scripts for the analysis of meetup data in this Nesta blog. In order to run the script, you need to create a `my_api__key.json` file in the folder with your [Meetup API key](https://secure.meetup.com/meetup_api/key/) 

If you want to update the analysis, you will need to crawl tech group information from Meetup. You can get the data using this a Meetup API wrapper from [here](https://github.com/mattjw/exploring_tech_meetups)

Run `meetup_analysis_blog.py` script to process the data, and `meetup_plots.R` to produce the visualisations.

Note that some of the annotations in the blog charts were added in inkscape.

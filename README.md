# Code for analysis of emerging tech topics in web data

This repo contains R and Python scripts for the analysis of meetup data in this Nesta blog.

In order to run the script, you need to create a `my_api__key.json` file in the folder with your [Meetup API key](https://secure.meetup.com/meetup_api/key/) 

If you want to update the analysis, you will need to crawl tech group information from [here](https://github.com/mattjw/exploring_tech_meetups)

Otherwise, just use the `tech_groups` JSON file included in the `meetup_data` folder.

Run `meetup_analysis_blog.py` script to process the data, and `meetup_plots.R` to produce the visualisations.

You can also run both from the terminal.

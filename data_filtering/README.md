Raw data from experiments: Filtering procedure
====================

## Introduction

This folder contains the code used to filter the database used in ref. [1] (see main README).

## Workflow

Input: On database imported from *raw_data.sql* with name *BeePath2012_filtered*:

	1. Filtering script "filtering.py"
		
		- Removes from database paths accuracy lower than 6 metres.
		- Removes from paths consecutive points with average velocity between updates higher than 50 km/h
		- Removes from database users and paths with less than 4 Flights and 4 updates
		- Stores backups of database in folder "dumps"
	
Input: In folder "dumps" files "filtered_updates.csv" and "filtered_users.csv"	
	2. Checking script "visual_check.py"
		
		- Returns population statistics on flights in file "visual_check.log'
		- Plots all traces for each user in folder "maps"
		- Plots long flights and analyzes statistics for long flights (to make sure the tail does not belong to the same user)



# System Libraries
import csv
import os
from datetime import date, datetime, time, timedelta
import argparse
# Third-Party
import xlrd
# Our own modules
import importing
import database

# Note: This file has to be here because python has a hard time importing
# files from inside another directory.

# Note: Make sure all timestamps are ending values
# Ex: 12/1/2012 1:00AM means the hour from 12 to 1.

# CONSTANTS ########################################

# All input files are in /inputs

fuel_prices = ''

# Load Forcasts File
# Contains the load forecasts in MW
# Headers: Timestamp, 2012,2013,2014 ...
load_forcasts_name = 'Hourly_Load_Forecasts.xlsx'
load_forcasts_table = 'loads'

# All output files are in /ouputs
# All outputs will have date appended to them to ensure no overwriting.

resource_table_name = 'Resource_Table'

# GLOBAL VARS #######################################

# A map of file names to their data in an array format.
# NOTE: Idk if we want to do row/cols or arrays of dictionaries
inputs_map = {}

def main():

	# Note: To make CSV loading more efficient you could have just one start date and
	# then hour offsets from it. That might fail with leap years though!

	# NOTE: One super cool optimization would be to look at the date modified
	# times of the input files and on the first run cache everything, but
	# once something is modified you then will regenerate it!
	# http://stackoverflow.com/questions/375154/how-do-i-get-the-time-a-file-was-last-modified-in-python

	# Note: I did a time test and found that loading from excel is way faster than parsing through a csv
	# It looks like the only optimization from excel would be to put it into a database.
	# You could also store it in memory and be able to still do the optimization above, only reloading the files that need reloading.

	# Maybe just use a legit database
	# http://docs.python.org/2/library/sqlite3.html


	# Note: Replace this with something that detects the dates
	parser = argparse.ArgumentParser(description='Open Dispatch Model')
	parser.add_argument('-r','--reload',required=False, help='Reload all files from excel')
	args = parser.parse_args()

	if args.reload:
		print 'Reloading all from excel files'
		importing.loadFileIntoDatabase('Hourly_Load_Forecasts.xlsx', 'loads')
		importing.loadFileIntoDatabase('Hourly_Gas_Forecasts.xlsx', 'gas_prices')
		importing.loadFileIntoDatabase('Hourly_Coal_Forecasts.xlsx', 'coal_prices')
		importing.loadFileIntoDatabase('Hourly_Wind_Production.xlsx', 'wind_prod')
		importing.loadFileIntoDatabase('Hourly_Solar_Production.xlsx', 'solar_prod')

	else:
		print 'Loading from database'
		array = database.loadTable('loads');
		array = database.loadTable('gas_prices');
		array = database.loadTable('coal_prices');
		array = database.loadTable('wind_prod');
		array = database.loadTable('solar_prod');
		print 'Loaded loads'


	print 'Got array...'


	# Create a map of file input names to data


	# Hmmm
	# Not sure if we should create an array of [date,load]
	# and then you could have a function getLoadAtDate() which does

	# Note: have a module of excel processing
	# This has methods to take table formats and convert them to 

	# Another idea is to have modules for each file like a load loading module

	# loop through input files
		# put them into memory
	# make calculations
	# Write output files



if __name__ == "__main__":
	main()
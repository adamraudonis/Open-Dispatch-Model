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
import LoadResourceImport
from pprint import pprint

# Note: This file has to be here because python has a hard time importing
# files from inside another directory.

# Note: Make sure all timestamps are ending values
# Ex: 12/1/2012 1:00AM means the hour from 12 to 1.

# # CONSTANTS ########################################

# # All input files are in /inputs

# fuel_prices = ''

# # Load Forcasts File
# # Contains the load forecasts in MW
# # Headers: Timestamp, 2012,2013,2014 ...
# load_forcasts_name = 'Hourly_Load_Forecasts.xlsx'
# load_forcasts_table = 'loads'

# # All output files are in /ouputs
# # All outputs will have date appended to them to ensure no overwriting.

# resource_table_name = 'Resource_Table'

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
		# These are 8760 data from the start year till the end year (MW)
		importing.forecastsToDatabase('Hourly_Load_Forecasts.xlsx', 'loads')
		importing.forecastsToDatabase('Hourly_Gas_Forecasts.xlsx', 'gas_prices')
		importing.forecastsToDatabase('Hourly_Coal_Forecasts.xlsx', 'coal_prices')

		# These are 8760 data for ONE year that should be assumed constant for all years (MW)
		# There are different sites in the file
		importing.variableProdToDatabase('Hourly_Wind_Production.xlsx', 'wind_prod')
		importing.variableProdToDatabase('Hourly_Solar_Production.xlsx', 'solar_prod')

		#importing.resourceInfoToDatabase('PGE_Resource.xlsx','resources')

	print 'Loading from database'
	loads = database.loadTableAll('loads'); # date, power (MW)
	gas_prices = database.loadTableAll('gas_prices');
	coal_prices = database.loadTableAll('coal_prices');

	site_test = database.loadVariableSite('wind_prod','26797_Onshore')
	# TODO: Will Scale by LoadResource capacity size
	#print site_test
	#wind_prod = database.loadTable('wind_prod');   # date, site, power
	#solar_prod = database.loadTable('solar_prod');

	print site_test[8700][2]
	LR = LoadResourceImport.loadDictionary()
	pprint(LR)
	for i in LR:
		if i['Resource Name'] == 'PaTu Wind' and i['Total Capacity (MW)'] != '':
			resource_capacity = i['Total Capacity (MW)'] # ISSUE HERE WITH TYPE FLOAT
			print resource_capacity
			for hour in site_test:
				hour[2] = hour[2] * resource_capacity

	print site_test[8700][2] # Check to see if *3

	print 'Got array...'

	# Scale wind and solar

	# The database doesn't really need dates.

	# Check all same lengths

	#dispatched_array = []

	#for interval in loads:
		#dispatched_resources = {}
		# Name is type + '_' + resource name
		#dispatched_resources[]
		#dispatched_array.append(dispatched_resources)
		
		# Dispatch wind - required
		# Dispatch solar - required
		# Dispatch hydro - like a battery
		# Now sort by variable cost which should look like
		# Dispatch coal
		# Dispatch gas CCCT
		# Dispatch gas SCCT
		# Where electrical batteries should be (Could be used to curtail wind)

	# Dispatching a resource involves, looking up it'

	#resources = []
	#for resource in resources:

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
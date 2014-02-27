# System Libraries
import csv
import os
# Third-Party
import xlrd
# Our own modules
import importing

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

# All output files are in /ouputs
# All outputs will have date appended to them to ensure no overwriting.

resource_table_name = 'Resource_Table'

# GLOBAL VARS #######################################

# A map of file names to their data in an array format.
# NOTE: Idk if we want to do row/cols or arrays of dictionaries
inputs_map = {}

def main():
	print 'Starting...'
	# I think there should only be several lines of code here!

	importing.inputFileArrayForName(load_forcasts_name)

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
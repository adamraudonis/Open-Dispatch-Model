# System Libraries
import csv
import os
# Third-Party
import xlrd
# Our own modules
import importing
from datetime import date, datetime, time, timedelta

import sqlite3 as lite


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

	con = lite.connect('test.db')
	cur = con.cursor()
	cur.execute('SELECT SQLITE_VERSION()')
	data = cur.fetchone()

	print "SQLite version: %s" % data

	# I think there should only be several lines of code here!
	print datetime.now().time()
	importing.inputFileArrayForName(load_forcasts_name)
	print datetime.now().time()
	print 'Done 1'
	print datetime.now().time()
	# rawArray = importing.loadArrayFromCSV('Hourly_Load_Forecasts.csv')
	print datetime.now().time()
	print 'Done 2'

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
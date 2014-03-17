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
import integrate
from pprint import pprint
import hydro
import ev_load
import dispatch

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
		#importing.forecastsToDatabase('Hourly_Load_Forecasts.xlsx', 'loads')
		#importing.forecastsToDatabase('Test_Hourly_Load.xlsx', 'loads')
		importing.forecastsToDatabase('Test_Hourly_Load2.xlsx', 'loads')

		#importing.forecastsToDatabase('Hourly_Gas_Forecasts.xlsx', 'gas_prices')
		#importing.forecastsToDatabase('Hourly_Coal_Forecasts.xlsx', 'coal_prices')

		# These are 8760 data for ONE year that should be assumed constant for all years (MW)
		# There are different sites in the file
		importing.variableProdToDatabase('Hourly_Wind_Production.xlsx', 'wind')
		importing.variableProdToDatabase('Hourly_Solar_Production.xlsx', 'solar')

		#importing.resourceInfoToDatabase('PGE_Resource.xlsx','resources')

	print 'Loading from database'
	
	loads = database.loadTableAll('loads'); # date, power (MW)
	gas_prices = database.loadForecastsNumOnly('gas_prices');
	coal_prices = database.loadForecastsNumOnly('coal_prices');

	# importing.variableProdToDatabase('Hourly_Wind_Production.xlsx', 'wind_prod')
	# site_test = database.loadVariableSite('wind_prod','26797_Onshore')
	
	# TODO: Will Scale by LoadResource capacity size
	#print site_test
	#wind_prod = database.loadTable('wind_prod');   # date, site, power
	#solar_prod = database.loadTable('solar_prod');

	resources = importing.importToDictArray('PGE_Resources.xlsx')

	# In the format of [jan to dec]
	# raw_hydro_map = {} # map of months to percents
	# historical_sum = 0
	# for pair in raw_hydro_pairs:
	# 	historical_sum += float(raw_hydro_pairs[pair])
	# 	raw_hydro_map.update(pair) # Combine all the "MONTH":123 pairs

	# for pair in raw_hydro_pairs:
	# 	raw_hydro_map.update({pair.lower():(float(raw_hydro_pairs[pair])/historical_sum)})

	battery_power_cap = 1000
	battery_energy_cap = 2000

	# Add EVs to Load
	# - Smart charging should occur after wind
	# Get yearly statistics

	#'hydro_resource_name':{1:{'energy':1234,'capacity':123},...}

	# where 0 index is january and so on.
	# 'hydro_resource_name':{'erergies':[123,234,543,654],'capacity':225}

	# Scale and Aggregate Wind and Solar
	# Maybe have the option of just scaling.
	# Actually maybe aggregate last.
	# Assume that every generator has different cap ex, variable costs.

	# If wind curve not present, use first wind curve?
	# Use constant january capacity?

	EV_LoadScenario = 'Standard Load Fraction'
	EV_LoadScenario = 'Smart Charging'
	EV_GrowthScenario = 'PG&E High'

	dispatched_array = dispatch.create_dispatch_array(loads)

	if not EV_LoadScenario == 'Smart Charging':
		dispatched_array = ev_load.addEVsToLoad(dispatched_array, EV_LoadScenario,EV_GrowthScenario)

	# Dispatch all non-dispatachable resources such as solar, wind, and river
	#
	dispatched_array = dispatch.dispatch_renewables(dispatched_array,resources)

	# Smartly charge EVs to minimize peaks and fill valleys
	#
	if EV_LoadScenario == 'Smart Charging':
		dispatched_array = ev_load.smart_charge(dispatched_array,EV_GrowthScenario)

	# Dispatch Reservoir Dispatchable Hydro
	#
	dispatched_array = hydro.dispatchReservoirs(dispatched_array,resources)

	# Dispatch Battery Here
	#
	# Note: You could dispatch li, followed by flow
	dispatched_array = integrate.dispatchBatteries(dispatched_array, battery_power_cap, battery_energy_cap)

	# Determine order and dispatch thermal resources
	#
	dispatched_array = dispatch.dispatch_thermal(dispatched_array,resources, gas_prices, coal_prices)

	# Deficit must be made up by market purchases (just determine deficit) 
	#
	#dispatched_array = dispatch.dispatch_excess(dispatched_array)
	#pprint(dispatched_array)
	# Aggregate by type (reservoir, river, wind, solar, gas, coal, battery)
	#
	aggregate_array = dispatch.aggregate_on_type(dispatched_array)

	# (Optional) Write dispatch to file
	#
	dispatch.writeToCSV(aggregate_array)


	print 'Got array...'



if __name__ == "__main__":
	main()
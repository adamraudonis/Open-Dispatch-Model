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
import resource_import
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

	resources = resource_import.loadDictionary()

	# Scale and Aggregate Wind and Solar
	# Maybe have the option of just scaling.
	# Actually maybe aggregate last.
	# Assume that every generator has different cap ex, variable costs.

	# If wind curve not present, use first wind curve?
	# Use constant january capacity?

	wind_resource_map = {}
	windnames = database.getVarSiteNames('wind')
	for sitename in windnames:
		wind_resource_map[sitename] = database.loadVariableNumsOnly('wind',sitename)

	solar_resource_map = {}
	solarnames = database.getVarSiteNames('solar')
	for sitename in solarnames:
		solar_resource_map[sitename] = database.loadVariableNumsOnly('solar',sitename)

	# Create map of renewable resources in memory
	# var_resource_map = {}
	# for resource in resources:
	# 	if resource['Type'].lower() == 'wind' or resource['Type'].lower() == 'solar':
	# 		var_resource_map[resource['Name']] = database.loadVariableNumsOnly(resource['Type'].lower(),resource['Name'])

	# sdf

	dispatched_array = []
	yearhour = 0
	totalhour = 0
	for interval in loads:
		dispatched_resources = {'Timestamp':interval[0],'Load':interval[1],'resources':[]}
		# [name,type,power]
		# dispatched_resources['resources'].append(['26797_Onshore','wind',23])
		# dispatched_resources['resources'].append(['23095_Offshore','wind',18])
		# dispatched_resources['resources'].append(['Gasthing','gas',455])

		dispatched_array.append(dispatched_resources)

		power_generated = 0
		# Consider moving the solar and wind loop outside
		# Dispatch solar and wind
		for resource in resources:
			#print resource

			if resource['Type'].lower() == 'solar':
				resource_curve = []
				if resource['Name'] in solar_resource_map:
					resource_curve = solar_resource_map[resource['Name']]
				else:
					resource_curve = solar_resource_map.values()[0] # TODO
				scaledValue = float(resource_curve[yearhour]) * int(float(resource['Rated Capacity (MW)']))
				dispatched_resources['resources'].append([resource['Name'],resource['Type'].lower(),scaledValue])
				power_generated += scaledValue

			if resource['Type'].lower() == 'wind':
				resource_curve = []
				if resource['Name'] in wind_resource_map:
					resource_curve = wind_resource_map[resource['Name']]
				else:
					resource_curve = wind_resource_map.values()[0] # TODO

				scaledValue = float(resource_curve[yearhour]) * int(float(resource['Rated Capacity (MW)']))
				dispatched_resources['resources'].append([resource['Name'],resource['Type'].lower(),scaledValue])
				power_generated += scaledValue

		dispatchOrder = []
		total_load = interval[1]
		for resource in resources:
			if len(resource['Heatrate (btu/kWh)']) > 0:
				fuelCost = 0
				if resource['Type'].lower() == 'gas':
					fuelCost = float(gas_prices[totalhour]) * float(resource['Heatrate (btu/kWh)']) / 1000 # $/MMBTU to

				if resource['Type'].lower() == 'coal':
					fuelCost = float(coal_prices[totalhour]) * float(resource['Heatrate (btu/kWh)']) / 1000 # $/MMBTU to

				#fixedOM = float(resource['Fixed O&M ($/kW)'])*1000*float(resource['Rated Capacity (MW)'])

				totalVarCost = float(resource['Var O&M ($/MWh)']) + fuelCost
				dispatchOrder.append([totalVarCost,resource])

		dispatchOrder = sorted(dispatchOrder,key=lambda interval: interval[0])
		for resourceArr in dispatchOrder:
			resource = resourceArr[1]
			#print "%s %s" % (resourceArr[0],resource['Name'])
			netLoad = total_load - power_generated
			if netLoad < 0:
				raise Exception('Produced more power than load. Are you sure???')
			else:
				if netLoad - float(resource['Rated Capacity (MW)']) < 0:
					dispatched_resources['resources'].append([resource['Name'],resource['Type'].lower(),netLoad])
					power_generated += netLoad
				else:
					dispatched_resources['resources'].append([resource['Name'],resource['Type'].lower(),float(resource['Rated Capacity (MW)'])])
					power_generated += float(resource['Rated Capacity (MW)'])

		if yearhour == 8759:
			yearhour = 0
		yearhour += 1
		totalhour += 1

	print 'Got to aggregate'

	# Aggregate on type
	aggregated_dispatch = []
	for dispatched in dispatched_array:
		type_map = {}
		for resource in dispatched['resources']:
			if resource[1].lower() in type_map:
				type_map[resource[1].lower()].append(resource[2])
			else:
				type_map[resource[1].lower()] = [resource[2]]

		dispatched_resources = {}
		for type_key in type_map:
			dispatched_resources[type_key] = sum(type_map[type_key])

		dispatched_resources['Timestamp'] = dispatched['Timestamp']
		dispatched_resources['Load'] = dispatched['Load']
		aggregated_dispatch.append(dispatched_resources)

	# Write to CSV
	f = open('8760_dispatch.csv','wb')
	aggregated_dispatch[0].keys()
	acopy = aggregated_dispatch[0].copy()
	del acopy['Timestamp']
	del acopy['Load']
	keys = ['Timestamp','Load']
	keys.extend(acopy.keys())
	dict_writer = csv.DictWriter(f, keys,extrasaction='ignore')
	dict_writer.writer.writerow(keys)
	dict_writer.writerows(aggregated_dispatch)
	f.close()

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

def sToi(string):
	if len(string) > 0:
		return int(float(string))
	else:
		return 0;

if __name__ == "__main__":
	main()
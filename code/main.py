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

	print NumToMonth(1)

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
	raw_hydro = importing.importTo2DArray('HydroMonthMap.xlsx')[1]
	print raw_hydro
	# raw_hydro_map = {} # map of months to percents
	# historical_sum = 0
	# for pair in raw_hydro_pairs:
	# 	historical_sum += float(raw_hydro_pairs[pair])
	# 	raw_hydro_map.update(pair) # Combine all the "MONTH":123 pairs

	# for pair in raw_hydro_pairs:
	# 	raw_hydro_map.update({pair.lower():(float(raw_hydro_pairs[pair])/historical_sum)})

	sum_hydro = 0
	for value in raw_hydro:
		sum_hydro += float(value)

	hydro_energy_map = {}
	for resource in resources:
		if resource['Type'].lower() == 'reservoir':
			print 'inside'
			newhydro = []
			for month_value in raw_hydro:
				newhydro.append(float(month_value)/sum_hydro * sToi(resource['Energy Potential (MWh/year)']))
			hydro_energy_map[resource['Name']] = newhydro

	#'hydro_resource_name':{1:{'energy':1234,'capacity':123},...}

	# where 0 index is january and so on.
	# 'hydro_resource_name':{'erergies':[123,234,543,654],'capacity':225}

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

	dispatched_array = []
	yearhour = 0
	for interval in loads:
		dispatched_resources = {'Timestamp':interval[0],'Load':interval[1],'resources':[]}
		# [name,type,power]

		power_generated = 0
		# Consider moving the solar and wind loop outside
		# Dispatch solar and wind
		for resource in resources:

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

			if resource['Type'].lower() == 'river':
				ratedCap = float(resource['Rated Capacity (MW)'])
				yearlyE = sToi(resource['Energy Potential (MWh/year)'])
				capFactor = yearlyE / (ratedCap * 8760)
				river_power = capFactor * ratedCap # Average Capacity Factor
				dispatched_resources['resources'].append([resource['Name'],resource['Type'].lower(),river_power])
				power_generated +=  river_power 

		dispatched_resources['Gen'] = power_generated

		dispatched_array.append(dispatched_resources)

		if yearhour == 8759:
			yearhour = 0
		yearhour += 1


	# Dispatch Hydro
	#
	# Create month map (different for each year too)
	# Maybe just go one month at a time.

	for resource in resources:
		if resource['Type'].lower() == 'reservoir':
			new_dispatched_array = []
			#print len(hydro_energy_map[resource['Name']])

			prevIntervalMonth = 0 # impossible month
			rindex = 0
			for resourceDict in dispatched_array:
				month = resourceDict['Timestamp'].month
				#print month
				if not prevIntervalMonth == month:
					#print resourceDict
					# print resource['Name']
					# print month
					energyLimit = int(float(hydro_energy_map[resource['Name']][month-1]))
					capacity = int(float(resource['Rated Capacity (MW)']))

					# an inefficient, but accurate way to determine the load per month
					finalIndex = 0
					monthArray = []
					for i in xrange(rindex,rindex + 24 * 35):
						if i == len(dispatched_array):
							finalIndex = i
							break
						else:
							#print dispatched_array[i]['Timestamp']
							#print i
							if not dispatched_array[i]['Timestamp'].month == month:
								finalIndex = i
								break

					analyze_month = dispatched_array[rindex:finalIndex]
					# print 'MONTH--------------------'
					# for period in analyze_month:
					# 	print period['Timestamp']
					# 	print period['Timestamp'].month
					#pprint(analyze_month)
					#print len(analyze_month)
					intervals = []
					for rdict in analyze_month:
						#print rdict
						intervals.append([rdict['Timestamp'],(float(rdict['Load']) - float(rdict['Gen']))*-1])
					#print len(intervals)
					# Using a reversed fill valleys because we want to use up all hydro energy.
					# When doing peak shaving we keep getting cut off at the peak
					reducedIntervals = integrate.fillValleyArray(intervals,capacity,energyLimit)
					# print '-----------------------'
					# for period in reducedIntervals:
					# 	print period[0]

					#print len(reducedIntervals)
					for i in xrange(0,len(analyze_month)):
						interval = reducedIntervals[i]
						analyze_month[i]['Gen'] = float(analyze_month[i]['Gen']) + interval[2]
						analyze_month[i]['resources'].append([resource['Name'],resource['Type'].lower(),interval[2]])
					new_dispatched_array.extend(analyze_month)

				prevIntervalMonth = month
				rindex += 1

			dispatched_array = new_dispatched_array
			#pprint(dispatched_array[0])
			#asdfasdf




	totalhour = 0
	for dispatched_resources in dispatched_array:
		# Get the dispatch order for thermal plants (coal and gas)
		dispatchOrder = []
		total_load = dispatched_resources['Load']
		year = dispatched_resources['Timestamp'].year
		for resource in resources:
			if len(resource['Heatrate (btu/kWh)']) > 0:
				if year >= sToi(resource['In-service date']) and year <= sToi(resource['Retirement year']):
					fuelCost = 0
					if resource['Type'].lower() == 'gas':
						fuelCost = float(gas_prices[totalhour]) * float(resource['Heatrate (btu/kWh)']) / 1000 # $/MMBTU to

					if resource['Type'].lower() == 'coal':
						fuelCost = float(coal_prices[totalhour]) * float(resource['Heatrate (btu/kWh)']) / 1000 # $/MMBTU to

					#fixedOM = float(resource['Fixed O&M ($/kW)'])*1000*float(resource['Rated Capacity (MW)'])

					totalVarCost = float(resource['Var O&M ($/MWh)']) + fuelCost
					dispatchOrder.append([totalVarCost,resource])

		dispatchOrder = sorted(dispatchOrder,key=lambda interval: interval[0])
		# for resourceArr in dispatchOrder:
		# 	print "%s %s %s" % (resourceArr[0],resourceArr[1]['Name'],resourceArr[1]['Type'])
		# sdfdf

		genLoad = dispatched_resources['Gen']
		for resourceArr in dispatchOrder:
			resource = resourceArr[1]
			# print "%s %s" % (resourceArr[0],resource['Name'])
			#print resource
			netLoad = float(dispatched_resources['Load']) - genLoad
			if netLoad < 0:
				print 'TOO MUCH RENEWABLES'
				#raise Exception('Produced more power than load. Are you sure???')
			else:
				if netLoad - float(resource['Rated Capacity (MW)']) < 0:
					dispatched_resources['resources'].append([resource['Name'],resource['Type'].lower(),netLoad])
					genLoad += netLoad
				else:
					dispatched_resources['resources'].append([resource['Name'],resource['Type'].lower(),float(resource['Rated Capacity (MW)'])])
					genLoad += float(resource['Rated Capacity (MW)'])

		# For contracts $42.56/MWh
		# for resourceArr in dispatchOrder:
		# 	netLoad = total_load - power_generated
		# 	if netLoad < 0:
		# 		pass

		totalhour += 1

	print 'Got to aggregate'

	# Aggregate on type
	#
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
	#keys.extend(acopy.keys())
	keys.extend(['river','coal','reservoir','gas','wind','solar'])
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

def monthToNum(date):

	return {
	        'Jan' : 1,
	        'Feb' : 2,
	        'Mar' : 3,
	        'Apr' : 4,
	        'May' : 5,
	        'Jun' : 6,
	        'Jul' : 7,
	        'Aug' : 8,
	        'Sep' : 9, 
	        'Oct' : 10,
	        'Nov' : 11,
	        'Dec' : 12
	}[date]

def NumToMonth(num):

	return {
	        1: 'Jan',
	        2: 'Feb',
	        3: 'Mar',
	        4: 'Apr',
	        5: 'May',
	        6: 'Jun',
	        7: 'Jul',
	        8: 'Aug',
	        9: 'Sep', 
	        10: 'Oct',
	        11: 'Nov',
	        12: 'Dec'
	}[num]


def sToi(string):
	if len(string) > 0:
		return int(float(string))
	else:
		return 0;

if __name__ == "__main__":
	main()
# System Libraries
import csv
import os
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
import statistics

# Note: This file has to be here because python has a hard time importing
# files from inside another directory.

def main():

	# Note: To make CSV loading more efficient you could have just one start date and
	# then hour offsets from it. That might fail with leap years though!

	# NOTE: One super cool optimization would be to look at the date modified
	# times of the input files and on the first run cache everything, but
	# once something is modified you then will regenerate it!
	# http://stackoverflow.com/questions/375154/how-do-i-get-the-time-a-file-was-last-modified-in-python

	parser = argparse.ArgumentParser(description='Open Dispatch Model')
	parser.add_argument('-r','--reload',required=False, help='Reload all files from excel')
	args = parser.parse_args()

	if args.reload:
		print 'Reloading all data from excel files'
		# These are 8760 data from the start year till the end year (MW)
		importing.forecastsToDatabase('Hourly_Load_Forecasts.xlsx', 'loads')
		#importing.forecastsToDatabase('Test_Hourly_Load.xlsx', 'loads')
		#importing.forecastsToDatabase('Test_Hourly_Load2.xlsx', 'loads')

		importing.forecastsToDatabase('Hourly_Gas_Forecasts.xlsx', 'gas_prices')
		importing.forecastsToDatabase('Hourly_Coal_Forecasts.xlsx', 'coal_prices')

		# These are 8760 data for ONE year that should be assumed constant for all years (MW)
		# There are different sites in the file
		importing.variableProdToDatabase('Hourly_Wind_Production.xlsx', 'wind')
		importing.variableProdToDatabase('Hourly_Solar_Production.xlsx', 'solar')

		#importing.resourceInfoToDatabase('PGE_Resource.xlsx','resources')

	print 'Loading from database'
	
	loads = database.loadTableAll('loads'); # date, power (MW)
	gas_prices = database.loadForecastsNumOnly('gas_prices');
	coal_prices = database.loadForecastsNumOnly('coal_prices');

	resources = importing.importToDictArray('PGE_Baseline.xlsx')

	battery_power_cap = 0
	battery_energy_cap = 0

	EV_LoadScenario = 'Standard Load Fraction'
	EV_LoadScenario = 'Smart Charging'
	EV_GrowthScenario = 'PG&E High'

	scenario_name = 'Baseload'

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
	dispatched_array = dispatch.dispatch_excess(dispatched_array)

	# Aggregate by type (reservoir, river, wind, solar, gas, coal, battery)
	#
	aggregate_array = dispatch.aggregate_on_type(dispatched_array)

	# Get yearly statistics on deificits ,etc
	#
	statistics.yearlyEnergy(aggregate_array, scenario_name)
	statistics.yearlyCapacity(aggregate_array, scenario_name)

	# (Optional) Write dispatch to file
	#
	dispatch.writeToCSV(aggregate_array, scenario_name)

	print 'Outputted files.'



if __name__ == "__main__":
	main()
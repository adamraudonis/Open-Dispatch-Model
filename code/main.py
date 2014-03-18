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
import files

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
		#importing.forecastsToDatabase('Hourly_EE_Forecasts.xlsx', 'ee')

		#importing.forecastsToDatabase('Test_Hourly_Load.xlsx', 'loads')
		#importing.forecastsToDatabase('Test_Hourly_Load2.xlsx', 'loads')

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

	# Small excel files we can add every time for now
	resources = importing.importToDictArray('PGE_Baseline.xlsx')
	year_forecasts = importing.import_year_forecasts('Year_Forecasts.xlsx') # EE, DR, DSG

	battery_power_cap = 0
	battery_energy_cap = 0

	#EV_LoadScenario = 'Standard Load Fraction'
	#EV_LoadScenario = 'Smart Charging'
	EV_LoadScenario = ''
	EV_GrowthScenario = ''
	#EV_GrowthScenario = 'PG&E High'

	scenario_name = 'Baseload'

	dispatched_array = dispatch.create_dispatch_array(loads)

	if not EV_LoadScenario == 'Smart Charging':
		print 'Adding Dumb EV Charging...'
		dispatched_array = ev_load.addEVsToLoad(dispatched_array, EV_LoadScenario,EV_GrowthScenario)

	print 'Adding Energy Efficiency...'

	# Dispatch Efficiency
	#
	dispatched_array = dispatch.add_efficiency(dispatched_array, year_forecasts)

	print 'Adding Renewables...'

	# Dispatch all non-dispatachable resources such as solar, wind, and river
	#
	dispatched_array = dispatch.add_renewables(dispatched_array,resources)


	# Smartly charge EVs to minimize peaks and fill valleys
	#
	if EV_LoadScenario == 'Smart Charging':
		print 'Dispatching Smart EV Charging...'
		dispatched_array = ev_load.smart_charge(dispatched_array,EV_GrowthScenario)


	print 'Dispatching Hydro Reservoirs...'

	# Dispatch Reservoir Dispatchable Hydro
	#
	dispatched_array = hydro.dispatchReservoirs(dispatched_array,resources)



	print 'Dispatching Battery Resources...'

	# Dispatch Battery Here
	#
	# Note: You could dispatch li, followed by flow
	dispatched_array = integrate.dispatchBatteries(dispatched_array, battery_power_cap, battery_energy_cap)


	print 'Dispatching Long-term Contracts ...'

	# Dispatch Long-term Contracts
	#
	dispatched_array = dispatch.dispatch_contracts(dispatched_array, resources)

	print 'Dispatching Thermal Resources...'

	# Determine order and dispatch thermal resources
	#
	dispatched_array = dispatch.dispatch_thermal(dispatched_array,resources, gas_prices, coal_prices)

	print 'Dispatching DR...'

	# Dispatch demand response
	#
	dispatched_array = dispatch.dispatch_DR(dispatched_array, year_forecasts)

	print 'Dispatching DSG...'

	# Dispatch distributed standby generation
	#
	dispatched_array = dispatch.dispatch_DSG(dispatched_array, year_forecasts)

	# Deficit must be made up by market purchases (just determine deficit) 
	#
	dispatched_array = dispatch.dispatch_excess(dispatched_array)

	print 'Aggregating by type...'

	# Aggregate by type (reservoir, river, wind, solar, gas, coal, battery)
	#
	aggregate_array = dispatch.aggregate_on_type(dispatched_array)

	print 'Generating yearly statistics...'

	# Get yearly statistics on deificits ,etc
	#
	statistics.yearlyEnergy(aggregate_array, scenario_name)
	statistics.yearlyCapacity(aggregate_array, scenario_name)

	print 'Generating 8760_dispatch.csv...'

	# (Optional) Write dispatch to file
	#
	dispatch.writeToCSV(aggregate_array, scenario_name)

	# (Optional)
	#
	# dispatch.writeAllToCSV(dispatched_array, scenario_name)

	# Verification
	if not len(dispatched_array) == len(loads):
		raise Exception("Interval length mismatch! Error somewhere.")

	print 'Outputted files.'



if __name__ == "__main__":
	main()
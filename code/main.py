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
		# importing.forecastsToDatabase('Test_Hourly_Load2.xlsx', 'loads')

		#importing.forecastsToDatabase('Hourly_Gas_Forecasts.xlsx', 'gas_prices')
		#importing.forecastsToDatabase('Hourly_Coal_Forecasts.xlsx', 'coal_prices')

		# These are 8760 data for ONE year that should be assumed constant for all years (MW)
		# There are different sites in the file
		importing.variableProdToDatabase('Hourly_Wind_Production.xlsx', 'wind')
		importing.variableProdToDatabase('Hourly_Solar_Production.xlsx', 'solar')

		#importing.resourceInfoToDatabase('PGE_Resource.xlsx','resources')

	print 'Loading from database'
	


	# Small excel files we can add every time for now
	#resources = importing.importToDictArray('PGE_Baseline.xlsx')
	#resources = importing.importToDictArray('PGE_Baseline_No_Coal.xlsx')
	#resources = importing.importToDictArray('PGE_Baseline_No_Coal_2000Wind.xlsx')





	EV_LoadScenario = 'Standard Load Fraction'
	#EV_LoadScenario = 'Work-Heavy Load Fraction'
	#EV_LoadScenario = 'Smart Charging'
	#EV_GrowthScenario = 'PG&E High'
	#EV_LoadScenario = ''

	#scenario_name = 'EV_Smart_No_Coal_2000W'
	#scenario_name = 'EV_Dumb_No_Coal_2000W'


	#scenario_name = 'Baseline2'
	run_scenario('Baseline_Will', '', 'PGE_Baseline.xlsx',0,0)
	run_scenario('No_Coal', '', 'PGE_Baseline_No_Coal.xlsx',0,0)
	# run_scenario('EV_Smart_No_Coal', 'Smart Charging', 'PGE_Baseline_No_Coal.xlsx',0,0)
	# run_scenario('EV_Dumb_No_Coal', 'Standard Load Fraction', 'PGE_Baseline_No_Coal.xlsx',0,0)
	# run_scenario('EV_Smart_No_Coal_2000W', 'Smart Charging', 'PGE_Baseline_No_Coal_2000Wind.xlsx',0,0)
	# run_scenario('EV_Dumb_No_Coal_2000W', 'Standard Load Fraction', 'PGE_Baseline_No_Coal_2000Wind.xlsx',0,0)
	# run_scenario('Smart_NC_2000W_100-200B', 'Smart Charging', 'PGE_Baseline_No_Coal_2000Wind.xlsx',100,200)
	# run_scenario('Smart_NC_2000W_100-400B', 'Smart Charging', 'PGE_Baseline_No_Coal_2000Wind.xlsx',100,400)

	#run_scenario('Smart_NC_2000W_500-1000B', 'Smart Charging', 'PGE_Baseline_No_Coal_2000Wind.xlsx',500,1000)
	run_scenario('Smart_NC_2000W_1000-2000B', 'Smart Charging', 'PGE_Baseline_No_Coal_2000Wind.xlsx',1000,2000)
	#run_scenario('Smart_NC_2000W_1000-4000B', 'Smart Charging', 'PGE_Baseline_No_Coal_2000Wind.xlsx',1000,4000)
	#run_scenario('Smart_NC_2000W_1000-8000B', 'Smart Charging', 'PGE_Baseline_No_Coal_2000Wind.xlsx',1000,8000)
	# Note: Also, test with dumb charging
	#run_scenario('Smart_NC_2000W_2000-2001B', 'Smart Charging', 'PGE_Baseline_No_Coal_2000Wind.xlsx',2000,2001)
	#run_scenario('Smart_NC_2000W_2000-4000B', 'Smart Charging', 'PGE_Baseline_No_Coal_2000Wind.xlsx',2000,4000)
	#raise Exception('done')


def run_scenario(scenario_name, EV_LoadScenario, resource_file, bmw, bmwh):
	print '----'
	print scenario_name
	if EV_LoadScenario == '':
		print 'No EVs'
	print resource_file
	print '----'
	EV_GrowthScenario = 'PG&E High'

	battery_power_cap = bmw
	battery_energy_cap = bmwh

	resources = importing.importToDictArray(resource_file)
	year_forecasts = importing.import_year_forecasts('Year_Forecasts.xlsx') # EE, DR, DSG
	
	loads = database.loadTableAll('loads'); # date, power (MW)
	gas_prices = database.loadForecastsNumOnly('gas_prices');
	coal_prices = database.loadForecastsNumOnly('coal_prices');

	dispatched_array = dispatch.create_dispatch_array(loads)

	if not EV_LoadScenario == 'Smart Charging' and len(EV_LoadScenario) > 0:
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

	#dispatch.print_ramp_rate_stats(dispatched_array)

	print 'Dispatching Battery Resources...'

	# Dispatch Battery Here
	#
	# Note: You could dispatch li, followed by flow
	dispatched_array = integrate.dispatchBatteries(dispatched_array, battery_power_cap, battery_energy_cap)

	dispatch.print_ramp_rate_stats(dispatched_array)


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
	dispatch.writeAllToCSV(dispatched_array, scenario_name)

	# Verification
	if not len(dispatched_array) == len(loads):
		raise Exception("Interval length mismatch! Error somewhere.")

	print 'Outputted files.'



if __name__ == "__main__":
	main()
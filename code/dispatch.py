import database	
import csv
from pprint import pprint
import files
import integrate

def create_dispatch_array(loads):
	dispatched_array = []
	for interval in loads:
		dispatched_array.append({'Timestamp':interval[0],'Load':int(float(interval[1])),'Pre_EV_Load':int(float(interval[1])),'resources':[]}) # [name,type,power]
	return dispatched_array

def add_renewables(dispatched_array, resources):
	wind_resource_map = {}
	windnames = database.getVarSiteNames('wind')
	for sitename in windnames:
		wind_resource_map[sitename] = database.loadVariableNumsOnly('wind',sitename)

	solar_resource_map = {}
	solarnames = database.getVarSiteNames('solar')
	for sitename in solarnames:
		solar_resource_map[sitename] = database.loadVariableNumsOnly('solar',sitename)

	yearhour = 0
	minLoad = 9999
	maxRampUp = 0
	maxRampDn = 0
	index = 0
	new_dispatched_array = []
	for interval in dispatched_array:
		# Note: Interval not uesed because we're just using index
		dispatched_resources = dispatched_array[index]

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
		dispatched_resources['Net'] = dispatched_resources['Load'] - power_generated

		dispatched_resources['Renew'] = float(dispatched_resources['Net']) + 0
		new_dispatched_array.append(dispatched_resources)

		if yearhour == 8759:
			yearhour = 0
		yearhour += 1

		if dispatched_resources['Net'] < minLoad:
			minLoad = dispatched_resources['Net']

		if index > 0:
			netLoad = dispatched_resources['Net']
			prevNet = dispatched_array[index - 1]['Net']
			if netLoad - prevNet > 0:
				if netLoad - prevNet > maxRampUp:
					maxRampUp = netLoad - prevNet
			else:
				if prevNet - netLoad  > maxRampDn:
					maxRampDn = prevNet - netLoad
		index += 1

	print 'Stats:'
	print maxRampUp
	print maxRampDn
	print minLoad
	return new_dispatched_array


def dispatch_thermal(dispatched_array, resources, gas_prices, coal_prices):

	totalhour = 0
	for dispatched_resources in dispatched_array:
		# Get the dispatch order for thermal plants (coal and gas)
		dispatchOrder = []
		#total_load = dispatched_resources['Load']
		year = dispatched_resources['Timestamp'].year
		for resource in resources:
			if len(resource['Heatrate (btu/kWh)']) > 0:
				if year >= sToi(resource['In-service date']) and year < sToi(resource['Retirement year']):
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

		# Dispatch the thermal resources
		#
		netLoad = float(dispatched_resources['Net'])
		for resourceArr in dispatchOrder:
			resource = resourceArr[1]
			if netLoad <= 0:
				dispatched_resources['resources'].append([resource['Name'],resource['Type'].lower(),0])
				# print 'TOO MUCH RENEWABLES'
				#raise Exception('Produced more power than load. Are you sure???')
			else:
				if netLoad - float(resource['Rated Capacity (MW)']) < 0:
					dispatched_resources['resources'].append([resource['Name'],resource['Type'].lower(),netLoad])
				else:
					dispatched_resources['resources'].append([resource['Name'],resource['Type'].lower(),float(resource['Rated Capacity (MW)'])])
					netLoad -= float(resource['Rated Capacity (MW)'])

		# For contracts $42.56/MWh
		# for resourceArr in dispatchOrder:
		# 	netLoad = total_load - power_generated
		# 	if netLoad < 0:
		# 		pass

		totalhour += 1
	return dispatched_array

def aggregate_on_type(dispatched_array):

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

		arr = ['Timestamp','Load','EV_Load','Bat_Load','Renew','Pre_EV_Load','Post_EV_Ren','Bat_Net', 'Post_Hydro']
		for thing in arr:
			if thing in dispatched:
				dispatched_resources[thing] = dispatched[thing]

		# dispatched_resources['Post_EV_Ren'] = dispatched['Renew'] + dispatched['EV_Load']
		# dispatched_resources['Timestamp'] = dispatched['Timestamp']
		# dispatched_resources['Load'] = dispatched['Load']
		# dispatched_resources['EV_Load'] = dispatched['EV_Load']
		# dispatched_resources['Bat_Load'] = dispatched['Bat_Load']
		# dispatched_resources['Net_Renew'] = dispatched['Net_Renew']
		# dispatched_resources['Pre_EV_Load'] = dispatched['Pre_EV_Load']
		# dispatched_resources['Bat_Net'] = dispatched['Bat_Net']

		aggregated_dispatch.append(dispatched_resources)
	return aggregated_dispatch

# Assumes it is going first!
def add_efficiency(dispatched_array, yearly_forecasts):
	startYear = dispatched_array[0]['Timestamp'].year

	for dictionary in dispatched_array:
		yearIndex = dictionary['Timestamp'].year - startYear
		value = float(yearly_forecasts['EE'][yearIndex])
		dictionary['resources'].append(['Efficiency','EE',value])
		dictionary['Net'] = dictionary['Load'] - value
	return dispatched_array

def dispatch_contracts(dispatched_array, resources):
	for dispatched_resources in dispatched_array:
		for resource in resources:
			if resource['Type'].lower() == "contract":
				year = dispatched_resources['Timestamp'].year
				if year >= sToi(resource['In-service date']) and year < sToi(resource['Retirement year']):
					value = float(resource['Rated Capacity (MW)'])
					dispatched_resources['resources'].append([resource['Name'],'contracts',value])
					dispatched_resources['Net'] = dispatched_resources['Net'] - value
				else:
					dispatched_resources['resources'].append([resource['Name'],'contracts',0])
	return dispatched_array

def dispatch_DR(dispatched_array, yearly_forecasts):
	return dispatch_yearly_forecast(dispatched_array, yearly_forecasts, 'DR', 100)

def dispatch_DSG(dispatched_array, yearly_forecasts):
	return dispatch_yearly_forecast(dispatched_array, yearly_forecasts, 'DSG', 50)

def dispatch_yearly_forecast(dispatched_array, yearly_forecasts, d_type, factor):

	startYear = dispatched_array[0]['Timestamp'].year
	numYears = len(dispatched_array) / 8760

	for yearIndex in xrange(0,numYears):
		yeararray = dispatched_array[yearIndex*8760:(yearIndex+1)*8760]
		battery_power_cap = float(yearly_forecasts[d_type][yearIndex]) # Power Value
		battery_energy_cap = factor * battery_power_cap	# Energy Limit 50 hrs a year if DSG

		inputArray = integrate.convertDispatchToArray(yeararray)
		peakArray = integrate.shavePeakArray(inputArray, battery_power_cap, battery_energy_cap)
		if not len(inputArray) == len(peakArray):
			print len(inputArray)
			print len(peakArray)
			raise Exception("DATE ERROR")

		for i in xrange(0,len(peakArray)):
			interval = peakArray[i]
			dis_resources = dispatched_array[yearIndex*8760+i]
			dis_resources['Net'] = dis_resources['Net'] + interval[2]
			dis_resources['resources'].append([d_type,d_type,interval[2] * -1])

	return dispatched_array



def dispatch_excess(dispatched_array):
	return dispatched_array

def writeToCSV(aggregated_dispatch, scenario_name):

	f = open(files.outputFilePath(scenario_name,'8760_dispatch.csv'),'wb')
	# aggregated_dispatch[0].keys()
	# acopy = aggregated_dispatch[0].copy()
	#del acopy['Timestamp']
	#del acopy['Load']
	keys = ['Timestamp','Pre_EV_Load','EV_Load','Load','Renew','Post_EV_Ren','Post_Hydro','Bat_Net','Bat_Load','battery','river','coal','reservoir','gas','wind','solar']
	#keys.extend(acopy.keys())
	# keys.extend(['river','coal','reservoir','gas','wind','solar'])
	dict_writer = csv.DictWriter(f, keys,extrasaction='ignore')
	dict_writer.writer.writerow(keys)
	dict_writer.writerows(aggregated_dispatch)
	f.close()

def writeAllToCSV(dispatched_array, scenario_name):
	outputArray = []
	header = []
	for resource in dispatched_array[0]['resources']:
		header.append(resource[0])
	outputArray.append(header)

	for dispatched_resources in dispatched_array:
		rarr = []
		for resource in dispatched_resources['resources']:
			rarr.append(resource[2])
		outputArray.append(rarr)
	files.writeArrayToCSV(files.outputFilePath(scenario_name,'8760_All_Sources'),outputArray)

def sToi(string):
	if len(string) > 0:
		return int(float(string))
	else:
		return 0;

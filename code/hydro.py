import importing
import integrate

	# Dispatchable Hydro
	#
	# Create month map (different for each year too)
	# Maybe just go one month at a time.
def dispatchReservoirs(dispatched_array, resources):

	raw_hydro = importing.importTo2DArray('HydroMonthMap.xlsx')[1]

	sum_hydro = 0
	for value in raw_hydro:
		sum_hydro += float(value)

	hydro_energy_map = {}
	for resource in resources:
		if resource['Type'].lower() == 'reservoir':
			newhydro = []
			for month_value in raw_hydro:
				newhydro.append(float(month_value)/sum_hydro * sToi(resource['Energy Potential (MWh/year)']))
			hydro_energy_map[resource['Name']] = newhydro

	for resource in resources:
		if resource['Type'].lower() == 'reservoir':
			new_dispatched_array = []
			#print len(hydro_energy_map[resource['Name']])

			prevIntervalMonth = 0 # impossible month
			rindex = 0
			for resourceDict in dispatched_array:
				year = resourceDict['Timestamp'].year

				if year >= sToi(resource['In-service date']) and year < sToi(resource['Retirement year']):

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
						for i in xrange(rindex,rindex + 24 * 34):
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
						for i in xrange(0,len(reducedIntervals)):
							interval = reducedIntervals[i]
							dispatched_array[rindex+i]['Gen'] = float(dispatched_array[rindex+i]['Gen']) + interval[2]
							dispatched_array[rindex+i]['Net'] = float(dispatched_array[rindex+i]['Net']) - interval[2]
							dispatched_array[rindex+i]['Post_Hydro'] = float(dispatched_array[rindex+i]['Net'])
							dispatched_array[rindex+i]['resources'].append([resource['Name'],resource['Type'].lower(),interval[2]])

					prevIntervalMonth = month
				rindex += 1
	return dispatched_array

def sToi(string):
	if len(string) > 0:
		return int(float(string))
	else:
		return 0;
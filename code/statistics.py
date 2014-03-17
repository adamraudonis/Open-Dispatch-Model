import files

def yearlyEnergy(aggregate_array, scenario_name):
	outputYearlyStats(aggregate_array, scenario_name, "Yearly Energy", sumOnKey)

def yearlyCapacity(aggregate_array, scenario_name):
	outputYearlyStats(aggregate_array, scenario_name, "Yearly Capacity", maxOnKey)

def outputYearlyStats(aggregate_array, scenario_name, file_name, function):
	numYears = len(aggregate_array) / 8760
	startYear = aggregate_array[0]['Timestamp'].year
	years = range(startYear,startYear+numYears)
	years.insert(0, '')

	outputArray = [years]
	for key in aggregate_array[0]:
		if not isOnof(key,['Timestamp','Load','EV_Load','Bat_Load','Renew','Pre_EV_Load','Post_EV_Ren','Bat_Net', 'Post_Hydro']):
			resourceArr = [key]
			for yearIndex in xrange(0,numYears):
				yeararray = aggregate_array[yearIndex*8760:(yearIndex+1)*8760]
				resourceArr.append(function(key,yeararray))
			outputArray.append(resourceArr)
	files.writeArrayToCSV(files.outputFilePath(scenario_name,file_name),outputArray)
	print "Wrote %s to output/%s" % (file_name,scenario_name)


def isOnof(key, array):
	for item in array:
		if key == item:
			return True
	return False

def sumOnKey(key, array):
	theSum = 0
	for item in array:
		theSum += int(item[key])
	return theSum

def maxOnKey(key, array):
	theMax = -99999
	for item in array:
		if int(item[key]) > theMax:
			theMax = int(item[key])
	return theMax

def minOnKey(key, array):
	theMin = 99999
	for item in array:
		if float(item[key]) < theMax:
			theMin = float(item[key])
	return theMin



import importing
import os
import os.path
import xlrd
from xlrd import XLRDError
from xlrd import open_workbook
from pprint import pprint
import database
import integrate
import csv

def main():
	a = getHourlyEVLoad('Standard Load Fraction','PG&E High')
	importing.writeArrayToCSV('EV_Load',a)

def addEVsToLoad(dispatched_array, EV_LoadScenario, EV_GrowthScenario):
	ev_load = getHourlyEVLoad(EV_LoadScenario, EV_GrowthScenario)
	for i in xrange(0,len(dispatched_array)):
		dispatched_r = dispatched_array[i]
		dispatched_r['Load'] = dispatched_r['Load'] + ev_load[i]
		dispatched_r['EV_Load'] = ev_load[i]
	return dispatched_array

def smart_charge(dispatched_array,EV_GrowthScenario):
	ev_load = getHourlyEVLoad('Standard Load Fraction', EV_GrowthScenario)
	daily_charges = []
	numdays = len(ev_load) / 24
	for i in xrange(0,numdays):
		daily_charges.append(sum(ev_load[i*24:(i+1)*24]))

	inputarray = integrate.convertDispatchToArray(dispatched_array)

	intervalMap = {}
	for i in xrange(0,len(dispatched_array)):
		intervalMap[i] = [i,0,0]

	for i in xrange(0,numdays):
		#print ' DAY %s' % i

		dailyMaxIndex = integrate.indexOfDailyMax(inputarray,i)
		#print 'Daily max %s' % dailyMaxIndex

		nextDailyMax = integrate.indexOfDailyMax(inputarray,i+1)
		#print 'Next Daily max %s' % nextDailyMax

		#peakSearchRange = inputarray[i*24:(i+1)*24]
		valleySearchRange = inputarray[dailyMaxIndex:nextDailyMax]

		#sdarr = shavePeakArray(peakSearchRange,battery_power_cap,battery_energy_cap)
		#energyused = 0
		#for interval in sdarr:
		#	energyused -= interval[2] #minus cuz we were discharging

		# Note: Assuming that the cars have 2x energy storage capacity as power to charge
		# This is probably an optimistic assumption as cars have inherent limitions on ramping too
		# A more accurate simulation approach would be to model each car individually and add them into
		# the grid in a probalistic fasion
		#
		fsarr = integrate.fillValleyArray(valleySearchRange,daily_charges[i] / 2,daily_charges[i])

		# for interval in sdarr:
		# 	if interval[0] in intervalMap:
		# 		if not interval[2] == 0:
		# 			intervalMap[interval[0]] = interval
		# 	else:
		# 		intervalMap[interval[0]] = interval

		for interval in fsarr:
			intervalMap[interval[0]] = interval

	intervalArray = []
	for key in intervalMap:
		interval = intervalMap[key]
		#print interval
		intervalArray.append([interval[0],interval[1],interval[2] + interval[1],interval[2]])

	sorted_array = sorted(intervalArray, key=lambda interval: interval[0])
	#pprint(sorted_array)
	print len(sorted_array)
	print len(dispatched_array)

	for i in xrange(0,len(sorted_array)):
		dispatched_array[i]['Load'] = dispatched_array[i]['Load'] + sorted_array[i][3]
		dispatched_array[i]['Net'] = dispatched_array[i]['Net'] + sorted_array[i][3]
		dispatched_array[i]['EV_Load'] = sorted_array[i][3]

	f = open("test_%sMW_%sMWh.csv" % (1, 1),"wb")
	writer = csv.writer(f, delimiter=',',quotechar='"', quoting=csv.QUOTE_MINIMAL)
	writer.writerow(['date','load','new_load','battery'])
	for row in sorted_array:
		writer.writerow(row)
	f.close()

	return dispatched_array

def loadArray(filename):
	parentdir = importing.lvl_down(os.path.dirname(os.path.realpath(__file__)))
	inputdir = importing.lvl_up(parentdir,'inputs')
	fullfilepath = os.path.join(inputdir, filename)
	return importing.excelToArray(fullfilepath)

def getHourlyEVLoad(loadScenario, growthScenario):
	evLoadFactorFilename = 'EV.xlsx'
	evLoadGrowthFilename = 'EV_Load_Growth.xlsx'
	loadGrowth = loadArray(evLoadGrowthFilename)
	loadFactor = loadArray(evLoadFactorFilename)
	indexOfLoadFactors = loadFactor[0].index(loadScenario)
	i = 0
	indexOfLoadGrowthScenario = 0

	# Find the correct growth scenario row of array
	for row in loadGrowth:
		if row[0] == growthScenario:
			indexOfLoadGrowthScenario = i
		i += 1

	toReturn = []
	#toReturn[0] = ['Hour','EV Load']
	indexFromStart = 1
	i = 2
	while i < len(loadGrowth[indexOfLoadGrowthScenario]):
		j = 1 # Essentially counts hours through each year
		while j < len(loadFactor):
			# Linearly scale loadGrowth according to how far through the year we are
			toReturn.append(100*(float(loadGrowth[indexOfLoadGrowthScenario][i-1]) + (float(loadGrowth[indexOfLoadGrowthScenario][i])-float(loadGrowth[indexOfLoadGrowthScenario][i-1]))*float(j)/8760)*float(loadFactor[j][indexOfLoadFactors]))
			j += 1
			indexFromStart += 1
		i += 1

	return toReturn

if __name__ == "__main__":
    main()
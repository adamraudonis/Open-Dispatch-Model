import importing
import os
import os.path
import xlrd
from xlrd import XLRDError
from xlrd import open_workbook
from pprint import pprint
import database

def main():
	a = getHourlyEVLoad('Standard Load Fraction','PG&E High')
	importing.writeArrayToCSV('EV_Load',a)

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

	toReturn = [[]]
	toReturn[0] = ['Hour','EV Load']
	indexFromStart = 1
	i = 2
	while i < len(loadGrowth[indexOfLoadGrowthScenario]):
		j = 1 # Essentially counts hours through each year
		while j < len(loadFactor):
			# Linearly scale loadGrowth according to how far through the year we are
			toReturn.append([indexFromStart-1,(float(loadGrowth[indexOfLoadGrowthScenario][i-1]) + (float(loadGrowth[indexOfLoadGrowthScenario][i])-float(loadGrowth[indexOfLoadGrowthScenario][i-1]))*float(j)/8760)*float(loadFactor[j][indexOfLoadFactors])])
			j += 1
			indexFromStart += 1
		i += 1

	return toReturn

if __name__ == "__main__":
    main()
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

	pprint(a)

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
	for row in loadGrowth:
		if row[0] == growthScenario:
			indexOfLoadGrowthScenario = i
		i += 1
	print indexOfLoadGrowthScenario
	print indexOfLoadFactors

	toReturn = [[]]
	toReturn[0] = ['hour','EV Load']
	indexFromStart = 1
	i = 2
	while i < len(loadGrowth[indexOfLoadGrowthScenario]):
		j = 1
		while j < len(loadFactor):
			toReturn[indexFromStart][0] = indexFromStart-1
			toReturn[indexFromStart][1] = loadGrowth[indexOfLoadGrowthScenario][i]*loadFactor[j][indexOfLoadFactors]
			j += 1
		i += 1

	return toReturn

#def getDailyEVLoad(growthScenario):
	# Returns [[dayMWh needed that day]]




if __name__ == "__main__":
    main()
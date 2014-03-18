import importing
import os
import os.path
import xlrd
from xlrd import XLRDError
from xlrd import open_workbook
from pprint import pprint
import database
import random
import math

def main():
	#resourceName = 'Beaver1-6'
	resourcesFilename = 'PGE_Baseline.xlsx'
	dispatchFilename = '8760_DispatchByName.xlsx'
	startYear = 2014
	endYear = 2015
	# pprint(getAvoidedCosts(dispatchFilename, startYear, endYear))
	supplyCurve = generateSupplyCurve(resourcesFilename, dispatchFilename, startYear, endYear)
	outputToExcel(supplyCurve)

def generateSupplyCurve(resourcesFilename, dispatchFilename, startYear, endYear):
	dispatch = getDispatch(dispatchFilename, startYear, endYear)
	resources = getResources(resourcesFilename)
	LCOE = {}

	for resource in resources:
		###### ONLY DO IF IN SERVICE!!!!!!!
		if resource['Economic Life (Years)'] != '':
			# print(resource['Economic Life (Years)'])
			# print resource['Name']
			# print dispatch[0]
			LCOE[resource['Name']] = calculateLCOE(resource['Name'], float(resource['WACC (%)']), float(resource['Economic Life (Years)']), float(resource['Rated Capacity (MW)']), float(resource['Overnight Capital Cost ($/kW)']), float(resource['Fixed O&M ($/kW)']), float(resource['Var O&M ($/MWh)']), dispatch, startYear, endYear)

	avoidedCosts = getAvoidedCosts(dispatchFilename, startYear, endYear)
	netLCOE = getNetLCOE(LCOE, avoidedCosts) # returns dictionary of {'Name' = netLCOE}
	
	# in netLCOE, 'Name' points to [netLCOE] for each hour of the year
	# in dispatch, 'Name' is in dispatch[0][something] and production each hour is below that
	#pprint(netLCOE) # dispatch
	#pprint(dispatch)
	joinedArray = join(netLCOE, dispatch)
	sortedArray = sort(joinedArray) # sorts in order of increasing net LCOE
	supplyCurve = addGen(sortedArray)
	return supplyCurve

def join(netLCOE, dispatch):
	joinedArray = []

	#pprint(netLCOE)

	for name in netLCOE.keys():
		if name in dispatch[0]:
			indexOfResource = dispatch[0].index(name)
			hour = 0
			for row in dispatch[1:]:
				# print name
				# print name[hour]
				# print row[indexOfResource]
				joinedArray.append([name, netLCOE[name][hour], row[indexOfResource]])
				hour += 1



	# for name in dispatch:
	# 	if name in netLCOE.keys():
	# 		for hour in netLCOE:
	# 			joinedArray.append([name, netLCOE[name][hour], dispatch[name][hour]])

	return joinedArray



def getNetLCOE(LCOE, avoidedCosts):
	netLCOE = {}

	for name in LCOE.keys():
		netLCOE[name] = []
		for avoidedCost in avoidedCosts:
			netLCOE[name].append(LCOE[name] - avoidedCost)

	return netLCOE


def calculateLCOE(resourceName, WACC, lifetime, capacity, capitalCost, fixedOM, varOMPerMWh, dispatch, startYear, endYear):
	indexOfResourceLoad = dispatch[0].index(resourceName)

	totalAnnualMWh = 0
	for row in dispatch[(startYear-2014)*8760+1:(endYear-2014)*8760+1]:
		totalAnnualMWh += float(row[indexOfResourceLoad])


	CRF = (WACC*(1+WACC)**lifetime)/((1+WACC)**lifetime-1)
	fixedCap = capitalCost * CRF
	totalAnnualFixedCostPerMW = (fixedCap + fixedOM)*1000
	totalAnnualFixedCosts = totalAnnualFixedCostPerMW * capacity
			
	annualVarOMCosts = totalAnnualMWh*varOMPerMWh
	
	totalAnnualCosts = annualVarOMCosts + totalAnnualFixedCosts


	LCOE = totalAnnualCosts/totalAnnualMWh
	
	return LCOE


def addGen(sortedArray):
	# sortedArray is 8760x2 matrix with LCOE in col 0 and generated each hour in 1
	addedArray = []
	sumMWh = 0
	for i in sortedArray:
		sumMWh += float(i[2])
		addedArray.append([i[0], i[1], sumMWh])
	return addedArray

def outputToExcel(supplyCurve):
	importing.writeArrayToCSV('Supply_Curve',supplyCurve)


def sort(joinedArray):
	i = 0

	sorted_array = sorted(joinedArray, key=lambda interval: interval[1])
	return sorted_array


def getDispatch(dispatchFilename, startYear, endYear):
	dispatch = importing.importTo2DArray(dispatchFilename)
	return dispatch[(startYear-2014)*8760:(endYear-2014)*8760]

def getResources(resourcesFilename):
	return importing.importToDictArray(resourcesFilename)


def getAvoidedCosts(dispatchFilename, startYear, endYear):
	# dispatch = importing.importTo2DArray(dispatchFilename)
	# resources = importing.importToDictArray(resourcesFilename)

	# indexOfResourceLoad = dispatch[0].index(resourceName)
	# toReturn = []

	# for row in dispatch[(startYear-2014)*8760+1:(endYear-2014)*8760+1]:
	# 	toReturn.append(row[indexOfResourceLoad])

	# return toReturn


	toReturn = []
	for i in range(0,(endYear-startYear)*8759):
		#toReturn.append(math.floor(10*random.random()))
		toReturn.append(1)
	return toReturn



if __name__ == "__main__":
    main()
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
	# To run old stuff
	# resourcesFilename = 'PGE_Baseline1.xlsx'
	# dispatchFilename = '8760_DispatchByName1.xlsx'
	# startYear = 2014
	# endYear = 2015

	# # Baseline_Will in 2014
	# resourcesFilename = 'PGE_Baseline.xlsx'
	# dispatchFilename = '8760_Baseline_Will.xlsx'
	# outputFilename = '2014_Baseline_Will_Supply_Curve'
	# startYear = 2014
	# endYear = 2015
	# Baseline_Will in 2033
	resourcesFilename = 'PGE_Baseline.xlsx'
	dispatchFilename = '8760_Baseline_Will.xlsx'
	outputFilename = '2033_Baseline_Will_Supply_Curve'
	startYear = 2033
	endYear = 2034


	# # Baseline_No_Coal in 2014
	# resourcesFilename = 'PGE_Baseline_No_Coal.xlsx'
	# dispatchFilename = '8760_No_Coal.xlsx'
	# outputFilename = '2014_No_Coal_Supply_Curve'
	# startYear = 2014
	# endYear = 2015
	# Baseline_Will in 2033
	# resourcesFilename = 'PGE_Baseline_No_Coal.xlsx'
	# dispatchFilename = '8760_No_Coal.xlsx'
	# outputFilename = '2033_No_Coal_Supply_Curve'
	# startYear = 2033
	# endYear = 2034

	# # Baseline_No_Coal_200Wind in 2014
	# resourcesFilename = 'PGE_Baseline_No_Coal_2000Wind.xlsx'
	# dispatchFilename = '8760_Baseline_No_Coal_2000Wind.xlsx'
	# outputFilename = '2014_Baseline_No_Coal_2000Wind_Supply_Curve'
	# startYear = 2014
	# endYear = 2015
	# # Baseline_Will in 2033
	# resourcesFilename = 'PGE_Baseline_No_Coal_2000Wind.xlsx'
	# dispatchFilename = '8760_Baseline_No_Coal_2000Wind.xlsx'
	# outputFilename = '2033_Baseline_No_Coal_2000Wind_Supply_Curve'
	# startYear = 2033
	# endYear = 2034


	# pprint(getAvoidedCosts(dispatchFilename, startYear, endYear))
	supplyCurve = generateSupplyCurve(resourcesFilename, dispatchFilename, startYear, endYear)
	outputToExcel(supplyCurve, outputFilename)

def generateSupplyCurve(resourcesFilename, dispatchFilename, startYear, endYear):
	entireDispatch = getDispatch(dispatchFilename, startYear, endYear)
	dispatch = []
	dispatch.append(entireDispatch[0])
	dispatch.extend(entireDispatch[(startYear-2014)*8760+1:(endYear-2014)*8760])


	resources = getResources(resourcesFilename)
	LCOE = {}

	#pprint(resources)
	typemap = {}
	for resource in resources:
		###### ONLY DO IF IN SERVICE!!!!!!!
		if resource['Economic Life (Years)'] != '' and float(resource['In-service date']) <= startYear and float(resource['Retirement year']) >= endYear:
			LCOE[resource['Name']] = calculateLCOE(resource['Name'], float(resource['WACC (%)']), float(resource['Economic Life (Years)']), float(resource['Rated Capacity (MW)']), float(resource['Overnight Capital Cost ($/kW)']), float(resource['Fixed O&M ($/kW)']), float(resource['Var O&M ($/MWh)']), dispatch, startYear, endYear)
			typemap[resource['Name']] = resource['Type']

	# print 'Length of LCOE:'
	# print len(LCOE) # how many keys in dict
	avoidedCosts = getAvoidedCosts(dispatch, startYear, endYear)
	# print 'Length of Avoided Costs:'
	# print len(avoidedCosts[0]) # how many hours computed for

	netLCOE = getNetLCOE(LCOE, avoidedCosts) # returns dictionary of {'Name' = netLCOE}
	# print 'Length of netLCOE:'
	# print len(netLCOE) # # names computed for
	
	# in netLCOE, 'Name' points to [netLCOE] for each hour of the year
	# in dispatch, 'Name' is in dispatch[0][something] and production each hour is below that
	joinedArray = join(netLCOE, dispatch, typemap)
	# print 'Length of joinedArray:'
	# print len(joinedArray[0])
	sortedArray = sort(joinedArray) # sorts in order of increasing net LCOE
	# print 'Length of sortedArray:'
	# print len(sortedArray[0])
	supplyCurve = addGen(sortedArray)
	# print 'Length of supplyCurve:'
	# print len(supplyCurve[0])
	return supplyCurve

def join(netLCOE, dispatch, typemap):
	joinedArray = []

	for name in netLCOE.keys():
		if name in dispatch[0]:
			indexOfResource = dispatch[0].index(name)
			# print indexOfResource
			hour = 0
			for row in dispatch[1:]:
				# print hour
				joinedArray.append([name, netLCOE[name][hour], row[indexOfResource],typemap[name]])
				hour += 1

	return joinedArray



def getNetLCOE(LCOE, avoidedCosts):
	netLCOE = {}

	for name in LCOE.keys():
		netLCOE[name] = []
		for avoidedCost in avoidedCosts:
			# print name
			# print LCOE[name]
			# print avoidedCost
			# print LCOE[name]-avoidedCost
			netLCOE[name].append(LCOE[name] - avoidedCost)

	return netLCOE


def calculateLCOE(resourceName, WACC, lifetime, capacity, capitalCost, fixedOM, varOMPerMWh, dispatch, startYear, endYear):
	indexOfResourceLoad = dispatch[0].index(resourceName)

	# print resourceName
	# pprint(dispatch[0:10])
	# pprint(indexOfResourceLoad)

	totalAnnualMWh = 0
	for row in dispatch[1:]:
		totalAnnualMWh += float(row[indexOfResourceLoad])


	CRF = (WACC*(1+WACC)**lifetime)/((1+WACC)**lifetime-1)
	fixedCap = capitalCost * CRF
	totalAnnualFixedCostPerMW = (fixedCap + fixedOM)*1000
	totalAnnualFixedCosts = totalAnnualFixedCostPerMW * capacity
			
	annualVarOMCosts = totalAnnualMWh*varOMPerMWh
	
	totalAnnualCosts = annualVarOMCosts + totalAnnualFixedCosts

	if totalAnnualMWh != 0:
		LCOE = totalAnnualCosts/totalAnnualMWh
	else:
		LCOE = 0
	
	return LCOE


def addGen(sortedArray):
	addedArray = []
	sumMWh = 0
	for i in sortedArray:
		sumMWh += float(i[2])
		addedArray.append([i[0], i[1], sumMWh,i[3]])
	return addedArray

def outputToExcel(supplyCurve, outputFilename):
	importing.writeArrayToCSV(outputFilename,supplyCurve)


def sort(joinedArray):
	i = 0

	sorted_array = sorted(joinedArray, key=lambda interval: interval[1])
	return sorted_array


def getDispatch(dispatchFilename, startYear, endYear):
	dispatch = importing.importTo2DArray(dispatchFilename)
	return dispatch

def getResources(resourcesFilename):
	return importing.importToDictArray(resourcesFilename)


def getAvoidedCosts(dispatch, startYear, endYear):
	indexOfAvoidedCost = dispatch[0].index('AvoidedCost')
	toReturn = []

	for row in dispatch[1:]:
		toReturn.append(float(row[indexOfAvoidedCost]))

	return toReturn


	# toReturn = []
	# for i in range(0,(endYear-startYear)*8759):
	# 	#toReturn.append(math.floor(10*random.random()))
	# 	toReturn.append(1)
	# return toReturn



if __name__ == "__main__":
    main()
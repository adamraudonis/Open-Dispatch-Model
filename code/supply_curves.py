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
	resourceName = 'Beaver1-6'
	resourcesFilename = 'PGE_Baseline.xlsx'
	dispatchFilename = '8760_DispatchByName.xlsx'
	startYear = 2014
	endYear = 2015
	supplyCurve = generateSupplyCurve(resourceName, resourcesFilename, dispatchFilename, startYear, endYear)
	outputToExcel(supplyCurve)

def generateSupplyCurve(resourceName, resourcesFilename, dispatchFilename, startYear, endYear):
	LCOE = calculateLCOE(resourceName, resourcesFilename, dispatchFilename, startYear, endYear)
	avoidedCosts = getAvoidedCosts(startYear, endYear)
	netLCOE = getNetLCOE(LCOE, avoidedCosts)
	dispatch = getDispatch(resourceName, dispatchFilename, startYear, endYear)
	sortedArray = sort(netLCOE, dispatch)
	supplyCurve = addGen(sortedArray)
	return supplyCurve

def addGen(sortedArray):
	# sortedArray is 8760x2 matrix with LCOE in col 0 and generated each hour in 1
	addedArray = []
	sumMWh = 0
	for i in sortedArray:
		sumMWh += float(i[1])
		addedArray.append([i[0], sumMWh])
	return addedArray

def outputToExcel(supplyCurve):
	importing.writeArrayToCSV('Supply_Curve',supplyCurve)


def sort(netLCOE, dispatch):
	i = 0
	unsortedArray = []


	for LCOE in netLCOE:
		unsortedArray.append([LCOE, dispatch[i]])
		i += 1

	sorted_array = sorted(unsortedArray, key=lambda interval: interval[0])
	return sorted_array


def getDispatch(resourceName, dispatchFilename, startYear, endYear):
	dispatch = importing.importTo2DArray(dispatchFilename)

	indexOfResourceLoad = dispatch[0].index(resourceName)
	toReturn = []

	for row in dispatch[(startYear-2014)*8760+1:(endYear-2014)*8760+1]:
		toReturn.append(row[indexOfResourceLoad])

	return toReturn


def calculateLCOE(resourceName, resourcesFilename, dispatchFilename, startYear, endYear):
	resources = importing.importToDictArray(resourcesFilename)
	dispatch = getDispatch(resourceName, dispatchFilename, startYear, endYear)

	totalAnnualMWh = 0.0
	for row in dispatch:
		totalAnnualMWh += float(row)


	WACC = 0# Read in
	lifetime = 0# read in
	capacity = 0# read in from resources file
	capitalCost = 0# read in from resources file
	fixedOM = 0# Read in from somewhere?
	varOMPerMWh = 0# Read in from resources file

	totalAnnualCosts = 0

	for resource in resources:
		annualVarOMCosts = 0
		totalAnnualFixedCosts = 0
		
		if resource['Name'] == resourceName:
			WACC = float(resource['WACC (%)'])
			lifetime = float(resource['Economic Life (Years)'])
			capacity = float(resource['Rated Capacity (MW)'])
			capitalCost = float(resource['Overnight Capital Cost ($/kW)'])
			fixedOM = float(resource['Fixed O&M ($/kW)'])
			varOMPerMWh = float(resource['Var O&M ($/MWh)'])


	CRF = (WACC*(1+WACC)**lifetime)/((1+WACC)**lifetime-1)
	fixedCap = capitalCost * CRF
	totalAnnualFixedCostPerMW = (fixedCap + fixedOM)*1000
	totalAnnualFixedCosts = totalAnnualFixedCostPerMW * capacity
			
	annualVarOMCosts = totalAnnualMWh*varOMPerMWh
	
	totalAnnualCosts += annualVarOMCosts + totalAnnualFixedCosts



	totalAnnualCosts = annualVarOMCosts + totalAnnualFixedCosts
	LCOE = totalAnnualCosts/totalAnnualMWh

	# print capacity
	# print capitalCost
	# print WACC
	# print lifetime
	# print CRF
	# print fixedCap
	# print fixedOM
	# print totalAnnualFixedCostPerMW
	# print totalAnnualFixedCosts
	# print varOMPerMWh
	# print totalAnnualMWh
	# print annualVarOMCosts
	# print totalAnnualCosts
	# print totalAnnualMWh
	# print LCOE
	
	return LCOE



def getAvoidedCosts(startYear, endYear):
	# return [0.1]*((endYear-startYear)*8759)
	toReturn = []
	for i in range(0,(endYear-startYear)*8759):
		toReturn.append(math.floor(10*random.random()))
	return toReturn




def getNetLCOE(LCOE, avoidedCosts):
	netLCOE = []

	for avoidedCost in avoidedCosts:
		netLCOE.append(LCOE - avoidedCost)

	return netLCOE



if __name__ == "__main__":
    main()
import importing
import os
import os.path
import xlrd
from xlrd import XLRDError
from xlrd import open_workbook
from pprint import pprint
import database

def main():
	resourceType = 'Gas'
	resourcesFilename = 'PGE_Resources.xlsx'
	dispatchFilename = '8760_dispatch.xlsx'
	a = generateSupplyCurve(resourceType, resourcesFilename, dispatchFilename)


def generateSupplyCurve(resourceType, resourcesFilename, dispatchFilename):
	LCOE = calculateLCOE(resourceType, resourcesFilename, dispatchFilename)
	return 1.0


def calculateLCOE(resourceType, resourcesFilename, dispatchFilename):
	resources = importing.importToDictArray(resourcesFilename)
	dispatch = importing.importTo2DArray(dispatchFilename)

	
	WACC = 1.0# Read in
	lifetime = 1.0# read in
	capacity = 1.0# read in from resources file
	capitalCost = 1.0# read in from resources file
	fixedOM = 1.0# Read in from somewhere?
	varOMPerMWh = 1.0# Read in from resources file

	for resource in resources:
		if resource['Type'] == resourceType: # Ensure parallel structure here!
			WACC = float(resource['WACC (%)'])
			lifetime = float(resource['Economic Life (Years)'])
			capacity = float(resource['Rated Capacity (MW)'])
			capitalCost = float(resource['Overnight Capital Cost ($/kW)'])
			fixedOM = float(resource['Fixed O&M ($/kW)'])
			varOMPerMWh = float(resource['Var O&M ($/MWh)'])
			break

	indexOfResourceLoad = dispatch[0].index(resourceType)
	totalAnnualMWh = 0.0
	for row in dispatch[1:]:
		totalAnnualMWh += float(row[indexOfResourceLoad])


	CRF = (WACC*(1+WACC)**lifetime)/((1+WACC)**lifetime-1)


	fixedCap = capitalCost * CRF
	totalAnnualFixedCostPerMW = (fixedCap + fixedOM)*1000
	totalAnnualFixedCosts = totalAnnualFixedCostPerMW * capacity

	
	annualVarOMCosts = totalAnnualMWh*varOMPerMWh
	totalAnnualCosts = annualVarOMCosts + totalAnnualFixedCosts
	LCOE = totalAnnualCosts/totalAnnualMWh

	print capacity
	print capitalCost
	print WACC
	print lifetime
	print CRF
	print fixedCap
	print fixedOM
	print totalAnnualFixedCostPerMW
	print totalAnnualFixedCosts
	print varOMPerMWh
	print totalAnnualMWh
	print annualVarOMCosts
	print totalAnnualCosts
	print totalAnnualMWh
	print LCOE
	return LCOE








if __name__ == "__main__":
    main()
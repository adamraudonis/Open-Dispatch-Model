import importing
import os
import os.path
import xlrd
from xlrd import XLRDError
from xlrd import open_workbook
from pprint import pprint
import database

def main():
	# d = loadDictionary()
	# pprint(d)
	print peakJanCapacity('wind_prod','26797_onshore')

def loadDictionary():
	filename = 'PGE_Resources.xlsx'
	parentdir = importing.lvl_down(os.path.dirname(os.path.realpath(__file__)))
	inputdir = importing.lvl_up(parentdir,'inputs')
	fullfilepath = os.path.join(inputdir, filename)
	return excelToArray(fullfilepath)

def excelToArray(infilePath):
	wb = open_workbook(infilePath)
	sheet1 = wb.sheets()[0]
	s = wb.sheets()[0]
	outputArray = []
	categories = []
	for col in range(0,s.ncols):
		categories.append(importing.stringAtCell(s,0,col))
	print categories
	for row in range(1,s.nrows):
		valuesDict = {}
		for col in range(0,s.ncols):
			if s.cell(row,col).ctype == xlrd.XL_CELL_DATE:
				#try:
					date_value = xlrd.xldate_as_tuple(s.cell_value(row,col),wb.datemode)
					valuesDict.append(categories[col],datetime(*date_value).strftime('%d-%b-%Y %H:%M:%S'))
				#except:
				#	raise Exception('A dumb Excel date error occurred. Please convert to CSV')
			else:
				valuesDict[categories[col]] = importing.stringAtCell(s,row,col)
		outputArray.append(valuesDict)

	return outputArray

def peakJanCapacity(tableName, siteName):
	output = database.loadVariableSite(tableName, siteName)
	janStart = 0
	janFinish = 24 * 31
	hour = janStart
	janMax = 0
	pprint(output) # OUTPUT CURRENTLY EMPTY
	while hour < janFinish:
		if output[hour][2] >= janMax:
			janMax = output[hour][2]
		hour = hour + 1
	return janMax


if __name__ == "__main__":
	main()
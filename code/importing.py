import xlrd
from xlrd import open_workbook
from xlrd import XLRDError
import argparse
import os
import os.path
import csv

# Takes a file name and returns its data
def inputFileArrayForName(filename):
	#infilePath = 
	print os.getcwd()

	# Gets the directory of this file (regardles of how executed)
	print os.path.dirname(os.path.realpath(__file__))

# http://stackoverflow.com/questions/13194489/python-change-given-directory-one-level-above-or-below
def lvl_down(path):
    return os.path.split(path)[0]

def lvl_up(path, up_dir):
    return os.path.join(path, updir)

def importFile():

	parser = argparse.ArgumentParser(description='Opens an excel file to perform operations on it')
	parser.add_argument('-f','--infile', type=argparse.FileType('r'),required=True, help='The excel file to open')
	args = parser.parse_args()
	filePath = args.infile.name
	array = []
	if os.path.isfile(filePath):
		if filePath.endswith('.xls') or filePath.endswith('.xlsx'):
			array = excelToArray(filePath)
		elif filePath.endswith('.csv') or filePath.endswith('.txt'):
			array = csvToArray(filePath)
		else:
			print 'Can\'t handle that filetype'

	useArray(array)



def useArray(array):
	print "DO SOMETHING HERE"

def csvToArray(infilePath):
	# http://stackoverflow.com/questions/2999373/python-split-files-using-mutliple-split-delimiters
	csvfile = open(infilePath,'rb')
	reader = '';
	try: # If the auto-detect csv format fails, default to comma. Error if that doesn't work!
		dialect = csv.Sniffer().sniff(csvfile.read(1024))
		csvfile.seek(0)
		reader = csv.reader(csvfile, dialect)
	except Exception, e:
		try:
			csvfile.seek(0)
			reader = csv.reader(csvfile)
		except Exception, e:
			print e
			print 'CSV Format curropted! Please try exporting to windows csv format in excel.'
			raise e

	rawArray = []
	for row in reader:
		rawArray.append(row)
	return rawArray

def excelToArray(infilePath):
	wb = open_workbook(infilePath)
	sheet1 = wb.sheets()[0]
	s = wb.sheets()[0]
	outputArray = []
	for row in range(0,s.nrows):
		valuesArray = []
		for col in range(0,s.ncols):
			if s.cell(row,col).ctype == xlrd.XL_CELL_DATE:
				try:
					date_value = xlrd.xldate_as_tuple(s.cell_value(row,col),wb.datemode)
					valuesArray.append(datetime(*date_value).strftime('%d-%b-%Y %H:%M:%S'))
				except:
					raise Exception('A dumb Excel date error occurred. Please convert to CSV')
			else:
				valuesArray.append(stringAtCell(s,row,col))
		outputArray.append(valuesArray)

	return outputArray

def stringAtCell(sheet,row,col):
	try:
		valueStr = ''
		if isinstance(sheet.cell(row,col).value, (str,unicode)):
			valueStr = sheet.cell(row,col).value.encode('utf-8','ignore')
		else:
			valueStr = str(sheet.cell(row,col).value).encode('utf-8','ignore')
		return valueStr.strip()
	except:
		print 'Cell '+str(row)+', '+ str(col)+' has value:'+valueStr+' is type: ' + str(sheet.cell(row,col).ctype)
		raise Exception('String at Cell Failed!')

def printExcelArray(array):
	for row in array:
		print row

if __name__ == "__main__":
    main()
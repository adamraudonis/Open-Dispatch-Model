import resource_import
import xlwt
import database
import importing
# Note should be the same as winter peak?
#
def getYearlyLoads():
 	#importing.forecastsToDatabase('Hourly_Load_Forecasts.xlsx', 'loads')
	loads = database.loadTableAll('loads'); # date, power (MW))

	yearMap = {}
	for interval in loads:
		year = interval[0].year
		if year in yearMap:
			yearMap[year].append(interval[1])
		else:
			yearMap[year] = [interval[1]]
	yearlyLoads = []
	for year in yearMap:
		peakLoad = max(yearMap[year])
		yearlyLoads.append([year,peakLoad])

	return sorted(yearlyLoads,key=lambda interval: interval[0])


def outputLoadResourceTable():
	resources = importing.importToDictArray('PGE_Baseline_No_Coal_2000Wind.xlsx')

	yearlyLoads = getYearlyLoads()

	normalS = makeNormalStyle()
	boldS = makeBoldStyle()

	wb = xlwt.Workbook()
	ws = wb.add_sheet('Load & Resource Table')

	reservesPercentage = .12

	ws.write(0, 0, 'Year', boldS)
	index = 1
	for interval in yearlyLoads:
		ws.write(0, index, interval[0], boldS)
		index += 1

	ws.write(1, 0, 'Peak (MW)', boldS)
	index = 1
	for interval in yearlyLoads:
		ws.write(1, index, interval[1], normalS)
		index += 1

	ws.write(2, 0, 'Reserves (%s%%)' % int(reservesPercentage*100), boldS)
	index = 1
	for interval in yearlyLoads:
		ws.write(2, index, int(interval[1]*reservesPercentage), normalS)
		index += 1

	ws.write(3, 0, 'Peak w/Reserves', boldS)
	index = 1
	for interval in yearlyLoads:
		ws.write(3, index, int(interval[1]*reservesPercentage+interval[1]), normalS)
		index += 1

	rindex = 5
	for resource in resources:
		if len(resource['In-service date']) > 0 and len(resource['Retirement year']) > 0:
			newname = resource['Type'] + '-' + resource['Name']
			ws.write(rindex, 0, newname, normalS)
			cindex = 1
			for interval in yearlyLoads:
				year = interval[0]
				if year >= sToi(resource['In-service date']) and year < sToi(resource['Retirement year']):
					ws.write(rindex, cindex, sToi(resource['Rated Capacity (MW)']), normalS)
				else:
					ws.write(rindex, cindex, 0, normalS)
				cindex += 1
			rindex += 1
		print resource

	# Set Widths
	ws.col(0).width = 4900
	for i in xrange(1,len(yearlyLoads)+1):
		ws.col(i).width = 1500

	wb.save('L&R_Table_2000W.xls')

def sToi(string):
	if len(string) > 0:
		return int(float(string))
	else:
		return 0;

def makeNormalStyle():
	font = xlwt.Font()
	#font.name = 'Times New Roman'
	#font.colour_index = 2
	font.bold = False

	style = xlwt.XFStyle()
	style.font = font
	return style

def makeBoldStyle():
	font = xlwt.Font()
	#font.name = 'Times New Roman'
	#font.colour_index = 2
	font.bold = True

	style = xlwt.XFStyle()
	style.font = font
	return style

def main():
	outputLoadResourceTable()

if __name__ == "__main__":
	main()
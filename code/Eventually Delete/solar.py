import urllib2
import urllib
from pprint import pprint
import json
from datetime import date, datetime, time, timedelta
import csv

# PV Watts API Key
pv_api_key = '2cd7ea74f17f05b19936c539af22014b3c3018a9'
from_date_time = '2013-01-01'
to_date_time = '2014-01-01'

# Solar Parameters
system_size = 1 #kW
timeframe = 'hourly'
zip_code = '97720' # Zip code approximately in middle of PGE territory
derate = 0.8
tilt = 45
azimuth = 180

pv_params = {'api_key':pv_api_key,'system_size':system_size,'tilt':tilt,'timeframe':timeframe,'derate':derate,'azimuth':azimuth,'address':zip_code}
print('...Pinging PV Watts for annual AC output...')
pv_url = 'http://developer.nrel.gov/api/pvwatts/v4.json?'
# print pv_url + urllib.urlencode(pv_params)
pv_request = urllib2.urlopen(pv_url + urllib.urlencode(pv_params))
#pprint(json.loads(pv_request.read()))

read_pv = json.loads(pv_request.read())
hourly_pv = read_pv['outputs']['df']

time = datetime.strptime(from_date_time + 'T00:00:00', '%Y-%m-%dT%H:%M:%S')
toReturn = {}
toReturnArray = []
for pv_output in hourly_pv:
	toReturn[time] = pv_output
	toReturnArray.append([time,pv_output])
	time = time + timedelta(hours=1)

# pprint(toReturn)

f = open("solar"+zip_code+".csv","wb")
# newArray = []
# for interval in array:
# 	newArray.append([interval[0].strftime('%Y-%m-%d %H:%M:%S'),interval[1]])
# json.dump(newArray,f)
writer = csv.writer(f, delimiter=',',quotechar='"', quoting=csv.QUOTE_MINIMAL)
for row in toReturnArray:
	writer.writerow(row)
f.close()


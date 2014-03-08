import csv # for testing only!!!
import importing

def main():

	# tryToShavePeak([40,30,20,10,5],20,20)
	# tryToShavePeak([40,30,20,10,5],10,20)
	# tryToShavePeak([40,30,20,10,5],5,20)
	# tryToShavePeak([40,30,20,10,5],12,20)
	# tryToShavePeak([40,35,35,10,5],20,20)
	# tryToShavePeak([50,5,5,0,0],20,20)

	#print inputarray
	#shavePeakArray(inputarray,200,600)
	#return
	#shavePeakArray(inputarray,200,600)
	# fillValleyArray(inputarray,200,600)

	# Window shifting makes the assumption peak will not occur at midnight.
	# Could change that pretty easily by searching between daily min to min.

	inputarray = importing.inputFileArrayForName('Hourly_Load_Forecasts.xlsx')

	numdays = len(inputarray) / 24
	print 'Num days %s' % numdays

	intervalMap = {}

	battery_power_cap = 500
	battery_energy_cap = 1000

	for i in xrange(0,numdays-1):
		print ' DAY %s' % i
		#day = inputarray[i*24:(i+1)*24]

		# So inefficienct! TODO: Only calculate daily max once.
		dailyMaxIndex = indexOfDailyMax(inputarray,i)
		print 'Daily max %s' % dailyMaxIndex
		# for interval in day:
		# 	print interval
		#nextday = inputarray[(i+1)*24:(i+2)*24]
		nextDailyMax = indexOfDailyMax(inputarray,i+1)
		print 'Next Daily max %s' % nextDailyMax

		peakSearchRange = inputarray[i*24:(i+1)*24]
		valleySearchRange = inputarray[dailyMaxIndex:nextDailyMax]

		sdarr = shavePeakArray(peakSearchRange,battery_power_cap,battery_energy_cap)
		energyused = 0
		for interval in sdarr:
			energyused -= interval[2] #minus cuz we were discharging

		# Assuming 90% efficiency of the batteries
		fsarr = fillValleyArray(valleySearchRange,battery_power_cap,energyused * 1.10)

		for interval in sdarr:
			if interval[0] in intervalMap:
				if not interval[2] == 0:
					intervalMap[interval[0]] = interval
			else:
				intervalMap[interval[0]] = interval

		for interval in fsarr:
			if interval[0] in intervalMap:
				if not interval[2] == 0:
					intervalMap[interval[0]] = interval
			else:
				intervalMap[interval[0]] = interval

	intervalArray = []
	for key in intervalMap:
		interval = intervalMap[key]
		#print interval
		intervalArray.append([interval[0],interval[1],interval[2] + interval[1],interval[2]])

	sorted_array = sorted(intervalArray, key=lambda interval: interval[0])


	f = open("test_%sMW_%sMWh.csv" % (battery_power_cap, battery_energy_cap),"wb")
	writer = csv.writer(f, delimiter=',',quotechar='"', quoting=csv.QUOTE_MINIMAL)
	writer.writerow(['date','load','new_load','battery'])
	for row in sorted_array:
		writer.writerow(row)
	f.close()

	# electric boats

	#fillValleys([0,10,15,30,40],10,20)

#	fillValleys([0,10,15,25,30],20,20)

	#fillValleys([0,10,15,25,30],10,20)
	#fillValleys([-5,0,15,25,30],10,20)

def indexOfDailyMax(inputarray,i):
	# day = inputarray[i*24:(i+1)*24]
	maximum = 0
	max_index = 0
	for j in xrange(i*24,(i+1)*24):
		testMax = inputarray[j][1]
		# print 'Test Max %s %s' % (inputarray[j][0],inputarray[j][1])
		if testMax > maximum:
			maximum = testMax
			max_index = j
	return max_index

def getDateTimeOfDailyMax(dayArray):
	maximum = ['',0]
	for interval in dayArray:
		if interval[1] > maximum[1]:
			maximum = interval
	return maximum[0]

def fillValleyArray(inputarray, battery_power_cap, battery_energy_cap):

	sorted_array = sorted(inputarray, key=lambda interval: interval[1])
	dischargeResults = fillValleys(sorted_array,battery_power_cap,battery_energy_cap)
	newArray = []
	for i in xrange(0,len(sorted_array)-1):
		result = 0
		if i < len(dischargeResults):
			result = dischargeResults[i]
		newArray.append([sorted_array[i][0],sorted_array[i][1],result])
	#newArray = sorted(newArray, reverse=True, key=lambda interval: interval[0])
	return newArray

	f = open("test_shave1.csv","wb")
	writer = csv.writer(f, delimiter=',',quotechar='"', quoting=csv.QUOTE_MINIMAL)
	writer.writerow(['date','load','new_load','battery'])
	for row in newArray:
		writer.writerow([row[0],row[1],row[1]+row[2],row[2]])
	f.close()

# Goal is to fill all energy while minimally increasing and staying under power requirement
# For example, if we max out power during one hour
# then we must use other hours to get all energy
#
def fillValleys(sorted_array, battery_power_cap, battery_energy_req):
	# Note: I need to return information about how much peak and energy was used.
	power_deltas = []
	cumulative_powers = []
	cumulative_energies = []
	battery_discharges = []

	for time in sorted_array:
		battery_discharges.append(0)

	#energy_discharged = 0

	# Maybe later use the cumulative power as a secondary check to make sure
	# you're not creaking a peak by charging the battery.
	# Have an argument like: optional_allowed_power_peak

	#print " -- Battery kW: " + str(battery_power_cap) + " kWh: " + str(battery_energy_req)
	#print sorted_array

	for i in xrange(1,len(sorted_array)-1): # When length -1 ???
		#print '-- i %s' % i

		energy_used = sum(battery_discharges)
		if energy_used >= battery_energy_req: # should in practice never be significantly greater. Maybe .00001 ok
			#print "ENERGY MAXED outside of can reduce further???"
			#print energy_used
			break

		prev_highest = sorted_array[i - 1][1]
		power_delta = sorted_array[i][1] - prev_highest # CHANGE FOR Production!!!

		# print "Prev highest %s" % prev_highest
		# print "Current Highest %s" % sorted_array[i][1]
		# print "Power Delta %s" % power_delta
		# print "Energy Used %s" % energy_used


		if power_delta > battery_power_cap:
			power_delta = battery_power_cap

		#print '-'

		# while some have available capacity below next highest threshold
		index = 0 # DEBUG
		while canReduceFurther(sorted_array, i, battery_power_cap, battery_energy_req, battery_discharges, index):

			#print 'loop index %s' % index

			# Get number of previous available powers
			total_available_for_divide = 0 # maybe change to 1
			for j in xrange(0,i):
				if battery_discharges[j] < battery_power_cap:
					total_available_for_divide += 1

			#print 'available for dicharge %s' % total_available_for_divide

			difference = battery_energy_req - sum(battery_discharges)
			#print 'Difference %s' % difference
			if difference <= 0:
				#print "ENERGY MAXED PROBLEM!!!???"
				break

			perhourdivide = difference / float(total_available_for_divide)
			if perhourdivide > power_delta:
				perhourdivide = power_delta

			#print "Per hour divide %s" % perhourdivide

			numOfBelowHourDivideDischarges = 0
			for j in xrange(0,i):
				#print 'J %s' % j
				availCapacity = battery_power_cap - battery_discharges[j]
				# print 'battery cap %s' % battery_power_cap
				# print 'discharge at j %s' % battery_discharges[j]
				# print 'avil cap %s' % availCapacity

				if availCapacity > 0 and availCapacity <= perhourdivide:
					#print 'inside'
					battery_discharges[j] += availCapacity
					numOfBelowHourDivideDischarges += 1

			if numOfBelowHourDivideDischarges == 0:
				for j in xrange(0,i):
					availCapacity = battery_power_cap - battery_discharges[j]
					if availCapacity >= perhourdivide:
						battery_discharges[j] += perhourdivide

			#print battery_discharges

			index += 1
	return battery_discharges

# Is there still reduction potential in the tier?
#
def canReduceFurther(sorted_array, i, battery_power_cap, battery_energy_req, battery_discharges, index):
	if index == 15:
		print Exception("WHILE LOOP INFINTY")
		return False # DEBUG. Prevent while loop looping forever

	energy_used = sum(battery_discharges)
	if energy_used >= battery_energy_req: # should in practice never be significantly greater. Maybe .00001 ok
		#print "ENERGY MAXED"
		#print energy_used
		return False

	for j in xrange(0,i):
		capacityAvail = battery_power_cap - battery_discharges[j]
		#print 'highest %s' % sorted_array[i][1]
		#print 'sum %s' % (battery_discharges[j] + sorted_array[j][1])
		if capacityAvail > 0 and battery_discharges[j] + sorted_array[j][1] < sorted_array[i][1]:
			#print 'Can reduce further TRUE!'
			return True
	#print 'Can reduce further FALSE!'
	return False

def shavePeakArray(inputarray, battery_power_cap, battery_energy_cap):

	sorted_array = sorted(inputarray, reverse=True, key=lambda interval: interval[1])
	dischargeResults = tryToShavePeak(sorted_array,battery_power_cap,battery_energy_cap)
	leftovere = sum(dischargeResults)
	print 'Leftover e %s' % leftovere
	newArray = []
	for i in xrange(0,len(sorted_array)-1):
		result = 0
		if i < len(dischargeResults):
			result = dischargeResults[i]
		newArray.append([sorted_array[i][0],sorted_array[i][1],result * -1])
	# newArray = sorted(newArray, reverse=True, key=lambda interval: interval[0])
	return newArray

	f = open("test_shave.csv","wb")
	writer = csv.writer(f, delimiter=',',quotechar='"', quoting=csv.QUOTE_MINIMAL)
	writer.writerow(['date','load','new_load','battery'])
	for row in newArray:
		writer.writerow([row[0],row[1],row[1]-row[2],row[2]])
	f.close()

# Goal is to reduce as much power as possible from peak
# If we have left over energy we don't care
#
def tryToShavePeak(sorted_array, battery_power_cap, battery_energy_cap):

	#print sorted_array

	if battery_energy_cap < battery_power_cap:
		raise Exception("I'm not sure how to handle this situation of battery kWh < kW")

	# Note: I need to return information about how much peak and energy was used.
	power_deltas = []
	cumulative_powers = []
	cumulative_energies = []
	battery_discharges = []

	#print " -- Battery kW: " + str(battery_power_cap) + " kWh: " + str(battery_energy_cap)

	for i in xrange(0,len(sorted_array)-1): # When length -1 ???
		power_delta = sorted_array[i][1] - sorted_array[i + 1][1] # CHANGE FOR TESTS!!!
		#print "%s %s-%s" % (int(power_delta), int(sorted_array[i][1]),int(sorted_array[i + 1][1]))
		if power_delta > battery_power_cap:
			power_delta = battery_power_cap
		power_deltas.append(power_delta)
		energy_delta = power_delta * (i+1)

		cumulative_power = power_delta
		if i > 0:
			cumulative_power = power_delta + cumulative_powers[-1]
		cumulative_powers.append(cumulative_power)

		cumulative_energy = power_delta
		if i > 0:
			cumulative_energy = energy_delta + cumulative_energies[-1]
		cumulative_energies.append(cumulative_energy)

		# print 'power deltas'
		# print power_deltas
		# print cumulative_powers
		# print cumulative_energies

		if cumulative_energy >= battery_energy_cap:
			#print "ENERGY MAXED"

			# The energy available to reduce the tier
			# cumulative_energies[-3] is the previous cumulative energy
			energyAvailInTier = battery_energy_cap
			if len(cumulative_energies) > 1:
				energyAvailInTier = battery_energy_cap - cumulative_energies[-2]
			#print energyAvailInTier
			netpower = float(energyAvailInTier / float(i+1))
			#print cumulative_powers

			cumulative_power = 0
			if len(cumulative_powers) > 1:
				cumulative_power = cumulative_powers[-2]

			if netpower + cumulative_power > battery_power_cap:
				netpower = (battery_power_cap - cumulative_power) / float(i+1)

			#print 'New net power: ' + str(netpower)

			power_deltas[-1] = netpower

			battery_discharges = getDischargeArray(i,power_deltas)
			break

		if cumulative_power >= battery_power_cap:
			#print "POWER MAXED"
			netpower = battery_power_cap
			if len(cumulative_powers) > 1:
				netpower = battery_power_cap - cumulative_powers[-2]

			power_deltas[-1] = netpower

			battery_discharges = getDischargeArray(i,power_deltas)
			break

		if i == len(sorted_array)-2: # We reached the last i
			#print "NO CONSTRAINT MAXED"
			battery_discharges = getDischargeArray(i,power_deltas)

	thesum = 0 # Sanity Check
	if not int(sum(battery_discharges)) == int(battery_energy_cap):
		Exception("Discharges do not add up!!!")

	#print battery_discharges
	return battery_discharges

def getDischargeArray(i,power_deltas):
	battery_discharges = []
	for j in reversed(xrange(0,i + 1)):
		discharge = power_deltas[j]
		if len(battery_discharges) > 0: # inefficient
			discharge += battery_discharges[-1]
		battery_discharges.append(discharge)
	return battery_discharges[::-1] # Reverse the array

if __name__ == "__main__":
	main()
import csv # for testing only!!!

def main():

	# tryToShavePeak([40,30,20,10,5],20,20)
	# tryToShavePeak([40,30,20,10,5],10,20)
	# tryToShavePeak([40,30,20,10,5],5,20)
	# tryToShavePeak([40,30,20,10,5],12,20)
	# tryToShavePeak([40,35,35,10,5],20,20)
	# tryToShavePeak([50,5,5,0,0],20,20)

	inputarray = [["2012-4-01 01:30:00",5200],
	["2012-4-01 02:30:00",5300],
	["2012-4-01 03:30:00",5400],
	["2012-4-01 04:30:00",5500],
	["2012-4-01 05:30:00",5400],
	["2012-4-01 06:30:00",5300],
	["2012-4-01 06:30:00",5200],
	["2012-4-01 06:30:00",5100]]

	inputarray = [["1/1/10 1:00 AM",	2593.161747],
	["1/1/10 2:00 AM",	2534.203542],
	["1/1/10 3:00 AM",	2497.229752],
	["1/1/10 4:00 AM",	2512.219126],
	["1/1/10 5:00 AM",	2606.152538],
	["1/1/10 6:00 AM",	2721.071074],
	["1/1/10 7:00 AM",	2816.003778],
	["1/1/10 8:00 AM",	2838.987485],
	["1/1/10 9:00 AM",	2846.981818],
	["1/1/10 10:00 AM",	2802.013695],
	["1/1/10 11:00 AM",	2767.038489],
	["1/1/10 12:00 PM",	2699.086659],
	["1/1/10 1:00 PM",	2652.119953],
	["1/1/10 2:00 PM",	2623.140496],
	["1/1/10 3:00 PM",	2625.139079],
	["1/1/10 4:00 PM",	2716.074616],
	["1/1/10 5:00 PM",	2994.876978],
	["1/1/10 6:00 PM",	3230.709799],
	["1/1/10 7:00 PM",	3190.738135],
	["1/1/10 8:00 PM",	3117.789847],
	["1/1/10 9:00 PM",	3002.871311],
	["1/1/10 10:00 PM",	2828.994569],
	["1/1/10 11:00 PM",	2617.144746]]

	#print inputarray
	shavePeakArray(inputarray,200,600)
	#shavePeakArray(inputarray,200,600) # FAILS!!!


	#fillValleys([0,10,15,30,40],10,20)

#	fillValleys([0,10,15,25,30],20,20)

	#fillValleys([0,10,15,25,30],10,20)
	#fillValleys([-5,0,15,25,30],10,20)

# Goal is to fill all energy while minimally increasing and staying under power requirement
# For example, if we max out power during one hour
# then we must use other hours to get all energy
#
def fillValleys(sorted_array, battery_power_cap, battery_energy_req):
	# Note: I need to return information about how much peak and energy was used.
	power_deltas = []
	cumulative_powers = []
	cumulative_energies = []
	battery_discharges = [0,0,0,0,0]

	#energy_discharged = 0

	# Maybe later use the cumulative power as a secondary check to make sure
	# you're not creaking a peak by charging the battery.
	# Have an argument like: optional_allowed_power_peak

	print " -- Battery kW: " + str(battery_power_cap) + " kWh: " + str(battery_energy_req)
	print sorted_array

	for i in xrange(1,len(sorted_array)-1): # When length -1 ???
		print '-- i %s' % i

		energy_used = sum(battery_discharges)
		if energy_used >= battery_energy_req: # should in practice never be significantly greater. Maybe .00001 ok
			print "ENERGY MAXED outside of can reduce further???"
			print energy_used
			break

		prev_highest = sorted_array[i - 1]
		power_delta = sorted_array[i] - prev_highest # CHANGE FOR Production!!!

		print "Prev highest %s" % prev_highest
		print "Current Highest %s" % sorted_array[i]
		print "Power Delta %s" % power_delta
		print "Energy Used %s" % energy_used


		if power_delta > battery_power_cap:
			power_delta = battery_power_cap

		print '-'

		# while some have available capacity below next highest threshold
		index = 0 # DEBUG
		while canReduceFurther(sorted_array, i, battery_power_cap, battery_energy_req, battery_discharges, index):

			print 'loop index %s' % index

			# Get number of previous available powers
			total_available_for_divide = 0 # maybe change to 1
			for j in xrange(0,i):
				if battery_discharges[j] < battery_power_cap:
					total_available_for_divide += 1

			print 'available for dicharge %s' % total_available_for_divide

			difference = battery_energy_req - sum(battery_discharges)
			print 'Difference %s' % difference
			if difference <= 0:
				print "ENERGY MAXED PROBLEM!!!???"
				break

			perhourdivide = difference / float(total_available_for_divide)
			if perhourdivide > power_delta:
				perhourdivide = power_delta

			print "Per hour divide %s" % perhourdivide

			numOfBelowHourDivideDischarges = 0
			for j in xrange(0,i):
				print 'J %s' % j
				availCapacity = battery_power_cap - battery_discharges[j]
				print 'battery cap %s' % battery_power_cap
				print 'discharge at j %s' % battery_discharges[j]
				print 'avil cap %s' % availCapacity

				if availCapacity > 0 and availCapacity <= perhourdivide:
					print 'inside'
					battery_discharges[j] += availCapacity
					numOfBelowHourDivideDischarges += 1

			if numOfBelowHourDivideDischarges == 0:
				for j in xrange(0,i):
					availCapacity = battery_power_cap - battery_discharges[j]
					if availCapacity >= perhourdivide:
						battery_discharges[j] += perhourdivide

			print battery_discharges

			index += 1
	return battery_discharges

# Is there still reduction potential in the tier?
#
def canReduceFurther(sorted_array, i, battery_power_cap, battery_energy_req, battery_discharges, index):
	if index == 5:
		print Exception("WHILE LOOP INFINTY")
		return False # DEBUG. Prevent while loop looping forever

	energy_used = sum(battery_discharges)
	if energy_used >= battery_energy_req: # should in practice never be significantly greater. Maybe .00001 ok
		print "ENERGY MAXED"
		print energy_used
		return False

	for j in xrange(0,i):
		capacityAvail = battery_power_cap - battery_discharges[j]
		print 'highest %s' % sorted_array[i]
		print 'sum %s' % (battery_discharges[j] + sorted_array[j])
		if capacityAvail > 0 and battery_discharges[j] + sorted_array[j] < sorted_array[i]:
			print 'Can reduce further TRUE!'
			return True
	print 'Can reduce further FALSE!'
	return False

def shavePeakArray(inputarray, battery_power_cap, battery_energy_cap):

	sorted_array = sorted(inputarray, reverse=True, key=lambda interval: interval[1])
	dischargeResults = tryToShavePeak(sorted_array,battery_power_cap,battery_energy_cap)
	leftoverenergy = battery_energy_cap - sum(dischargeResults)
	print 'Leftover Energy %s kWh' % int(leftoverenergy)
	newArray = []
	for i in xrange(0,len(sorted_array)-1):
		result = 0
		if i < len(dischargeResults):
			result = dischargeResults[i]
		newArray.append([sorted_array[i][0],sorted_array[i][1],result])
	newArray = sorted(newArray, reverse=True, key=lambda interval: interval[0])

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

	print " -- Battery kW: " + str(battery_power_cap) + " kWh: " + str(battery_energy_cap)

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
			print "ENERGY MAXED"

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
			print "POWER MAXED"
			netpower = battery_power_cap
			if len(cumulative_powers) > 1:
				netpower = battery_power_cap - cumulative_powers[-2]

			power_deltas[-1] = netpower

			battery_discharges = getDischargeArray(i,power_deltas)
			break

		if i == len(sorted_array)-2: # We reached the last i
			print "NO CONSTRAINT MAXED"
			battery_discharges = getDischargeArray(i,power_deltas)

	thesum = 0 # Sanity Check
	if not int(sum(battery_discharges)) == int(battery_energy_cap):
		Exception("Discharges do not add up!!!")

	print battery_discharges
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
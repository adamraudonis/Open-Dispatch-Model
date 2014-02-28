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

	print inputarray
	shavePeakArray(inputarray)

def shavePeakArray(inputarray):

	sorted_array = sorted(inputarray, reverse=True, key=lambda interval: interval[1])
	dischargeResults = tryToShavePeak(sorted_array,200,200)
	newArray = []
	for i in xrange(0,len(sorted_array)-1):
		result = 0
		if i < len(dischargeResults):
			result = dischargeResults[i]
		newArray.append([sorted_array[i][0],sorted_array[i][1],result])
	newArray = sorted(newArray, reverse=True, key=lambda interval: interval[0])

	print newArray

def tryToShavePeak(sorted_array,battery_power_cap,battery_energy_cap):

	# Note: I need to return information about how much peak and energy was used.
	power_deltas = []
	cumulative_powers = []
	cumulative_energies = []
	battery_discharges = []

	print " -- Battery kW: " + str(battery_power_cap) + " kWh: " + str(battery_energy_cap)

	for i in xrange(0,len(sorted_array)-1): # When length -1 ???
		power_delta = sorted_array[i][1] - sorted_array[i + 1][1] # CHANGE FOR TESTS!!!
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
				netpower = battery_power_cap - cumulative_powers[-1]

			power_deltas[-1] = netpower

			battery_discharges = getDischargeArray(i,power_deltas)
			break

		if i == len(sorted_array)-2: # We reached the last i
			print "NO CONSTRAINT MAXED"
			battery_discharges = getDischargeArray(i,power_deltas)

	thesum = 0 # Sanity Check
	if not int(sum(battery_discharges)) == int(battery_energy_cap):
		Exception("Discharges do not add up!!!")

	#print array
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
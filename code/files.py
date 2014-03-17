import os
import csv

def inputFilePath(filename):
	parentdir = lvl_down(os.path.dirname(os.path.realpath(__file__)))
	inputdir = lvl_up(parentdir,'inputs')
	return os.path.join(inputdir, filename)

def outputFilePath(foldername, filename):
	parentdir = lvl_down(os.path.dirname(os.path.realpath(__file__)))
	inputdir = lvl_up(parentdir,'outputs')
	scenario_folder = os.path.join(inputdir, foldername)
	if not os.path.exists(scenario_folder):
		os.makedirs(scenario_folder)
	return os.path.join(scenario_folder, filename)

def writeArrayToCSV(filename, array):
	f = open(filename+".csv","wb")
	writer = csv.writer(f, delimiter=',',quotechar='"', quoting=csv.QUOTE_MINIMAL)
	for row in array:
		writer.writerow(row)
	f.close()

# http://stackoverflow.com/questions/13194489/python-change-given-directory-one-level-above-or-below
def lvl_down(path):
    return os.path.split(path)[0]

def lvl_up(path, up_dir):
    return os.path.join(path, up_dir)
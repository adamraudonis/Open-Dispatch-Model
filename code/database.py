import sqlite3 as lite
import sys

databasePath = 'database.db'

def createForecastTable(tableName,datePowerArray):
	try:
		con = lite.connect(databasePath, detect_types = lite.PARSE_COLNAMES)
		cur = con.cursor()
		cur.execute("DROP TABLE IF EXISTS %s" % tableName)
		cur.execute('CREATE TABLE %s(thedate timestamp, power REAL)' % tableName)
		for interval in datePowerArray:
			cur.execute("INSERT INTO %s VALUES('%s', %s)" % (tableName,interval[0],interval[1]))
	 	con.commit()
	except lite.Error, e:
	    if con:
	        con.rollback()
	    print "Error %s:" % e.args[0]
	    sys.exit(1)
	finally:
	    if con:
	        con.close() 

def createVariableProdTable(tableName,dateSitePowerArray):
	try:
		con = lite.connect(databasePath, detect_types = lite.PARSE_COLNAMES)
		cur = con.cursor()
		cur.execute("DROP TABLE IF EXISTS %s" % tableName)
		cur.execute('CREATE TABLE %s(hour INT, site TEXT, power REAL)' % tableName)
		for interval in dateSitePowerArray:
			cur.execute("INSERT INTO %s VALUES(%s,'%s', %s)" % (tableName,interval[0],interval[1],interval[2]))
	 	con.commit()
	except lite.Error, e:
	    if con:
	        con.rollback()
	    print "Error %s:" % e.args[0]
	    sys.exit(1)
	finally:
	    if con:
	        con.close() 


def loadTableAll(tableName):
	return loadTable(tableName,'SELECT thedate as "ts [timestamp]", power  FROM %s' % tableName)

def loadVariableSite(tableName,siteName):
	return loadTable(tableName,"SELECT * FROM %s WHERE site = '%s'" % (tableName,siteName))

def loadTable(tableName,query):
	try:
		con = lite.connect(databasePath, detect_types = lite.PARSE_COLNAMES)
		cur = con.cursor()
		cur.execute(query)
	 	con.commit()

		data = cur.fetchall()
		# http://stackoverflow.com/questions/14831830/convert-a-list-of-tuples-to-a-list-of-lists
		# Convert from list of tuples to list of lists
		return [list(elem) for elem in data]

	except lite.Error, e:
	    if con:
	        con.rollback()
	        
	    print "Error %s:" % e.args[0]
	    sys.exit(1)
	finally:
	    if con:
	        con.close() 




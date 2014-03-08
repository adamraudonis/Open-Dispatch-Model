import sqlite3 as lite
import sys

def createTable(tableName,datePowerArray):
	try:
		con = lite.connect('database.db')
		cur = con.cursor()
		cur.execute("DROP TABLE IF EXISTS %s" % tableName)
		cur.execute('CREATE TABLE loads(theDate DATETIME, power REAL)')
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

def loadTable(tableName):
	try:
		con = lite.connect('database.db')
		cur = con.cursor()
		cur.execute("SELECT * FROM %s" % tableName)
	 	con.commit()

		data = cur.fetchall()
		return data

	except lite.Error, e:
	    if con:
	        con.rollback()
	        
	    print "Error %s:" % e.args[0]
	    sys.exit(1)
	finally:
	    if con:
	        con.close() 



from distutils.command.config import config
import re
import string
from flask import Flask,jsonify, session, redirect, render_template , url_for, request, send_from_directory
import mysql.connector
from datetime import datetime, timedelta
import os
app = Flask(__name__)
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

def MysqlConfig():
        mysqlconfig = {
                'host':'plowmantelemetrydb.clsmeutacd1v.eu-west-2.rds.amazonaws.com',
                'user':'admin',
                'password':'bR0m3lIad2021!!',
                'database':'plowmantelemetryschema'
                }
        return mysqlconfig

def InsertSQL(value,table):
        config = MysqlConfig()
        mydb = mysql.connector.connect(**config)
        mycursor = mydb.cursor()
        #'\'PBL v0.4.2', '2021-10-06 08:03:29', '54.08095', '-1.1727', '13'
        #sql = "INSERT INTO `plowmantelemetryschema`.`PBL_Telemetry` (`Box Number`, `DateTime`, `Longitude`, `Latitude`, `Temperature 1`) VALUES ('\'PBL v0.4.2', '2021-10-06 08:03:29', '54.08095', '-1.1727', '13')"
        sql = "INSERT INTO plowmantelemetryschema." + table + " (`Box Number`, `DateTime`, `Latitude`, `Longitude`, `T1`,`T2`,`T3`,`T4`,`T5`,`T6`,`T7`,`T8`) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        #examples = ('PBL v0.4.1','2021-10-06 08:03:29','54.08095','-1.1727','-127.000')
        #print(value)
        value = value.lstrip('\"')
        value = value.rstrip('\"')
        value = eval(value)
        #print(value)    
        mycursor.execute(sql,value)
        mydb.commit()

#trying to post all data to the same table. 
def InsertSQLModified(value):
        config = MysqlConfig()
        mydb = mysql.connector.connect(**config)
        mycursor = mydb.cursor()
        sql = "INSERT INTO PBL_Uploaded_Data (`Box Number`, `DateTime`, `Latitude`, `Longitude`, `T1`,`T2`,`T3`,`T4`,`T5`,`T6`,`T7`,`T8`) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        value = value.lstrip('\"')
        value = value.rstrip('\"')
        value = eval(value)   
        mycursor.execute(sql,value)
        mydb.commit()

def SelectSQL(boxNumber):
        config = MysqlConfig()
        mydb = mysql.connector.connect(**config)
        mycursor = mydb.cursor()
        try:
            mycursor.execute("SELECT * FROM PBL_Uploaded_Data WHERE `Box Number` = '" + boxNumber + "' ORDER BY ID DESC LIMIT 100;")
            myresult = mycursor.fetchall()
            data = []
            for x in myresult:
                    data.append(x)
            return (data)
        except:
            return "Error - Likely table does not exist"


# Converts datetime into more readable format
# '%Y-%m-%d %H:%M:%S' to '%d/%m/%Y %H:%M:%S'
# dateTime = date time in format of YYYY-MM-DD HH/MM/SS (e.g. datetime from sql server)
# returns readableDate
def ConvertToReadableTime(dateTime):
    readableDate = datetime.strftime(dateTime, "%d/%m/%Y %H:%M:%S")
    return readableDate

# compares date (in a datetime format of '%Y-%m-%d %H:%M:%S') against current server time.
# timeMinutes = integer time in minutes
# dateTime = time to evaluate (e.g. last packet from sql server)
# returns true or false based upon defined allowable range in minutes.
def PacketAge(timeMinutes, dateTime):
    difference = (datetime.utcnow() - dateTime) - timedelta(minutes=timeMinutes)
    # print(difference)
    if difference < timedelta(0):
        return True
    else:
        return False

# Queries SQL database and finds last row for specified box number. Converts to date or checks if online/offline
# boxNumber = string that is specific to livestock box. e.g. 'PBL v0.4.9' no checks if this is wrong!
# **kwargs:
#          - dateformat. if set as true, will return last packet in format of DD/MM/YYYY HH:MM:SS
#          - status.     if set as true, will return last packet in readable format AND ONLINE/OFFLINE (used on html)
# returns datetime in format of '%Y-%m-%d %H:%M:%S' as standard.
def LastPacketTime(boxNumber, **kwargs):
    config = MysqlConfig()
    mydb = mysql.connector.connect(**config)
    cursor = mydb.cursor()  # define cursor
    query = "SELECT DateTime, Latitude, Longitude FROM PBL_Uploaded_Data WHERE  `Box Number` = %s ORDER BY DateTime DESC LIMIT 1  ;"  # construct query
    cursor.execute(query, (boxNumber,))
    for result in cursor:
        result = list(result)
        if kwargs.get("dateformat"):  # probably will be unused
            readableDate = ConvertToReadableTime((result[0]))
            return readableDate
        if kwargs.get("status"):  # if we want to check ONLINE/OFFLINE
            readableDate = ConvertToReadableTime((result[0]))
            if PacketAge(
                5, result[0]
            ):  # Pass in 20 minutes, we can expose and change this later
                result = readableDate + " || ONLINE "
            else:
                result = readableDate + " || OFFLINE "
            return result
        else:
            return result

    return "No Data in db"

def serverTime():
        serverTime = ConvertToReadableTime(datetime.utcnow())
        return serverTime

@app.route('/')
def index():
    JMWStatus = LastPacketTime('PBL003', status = True)
    RedPathSatus = LastPacketTime('PBL004', status = True)
    templateData = {
        "textLine0" : "upload.plowmantelemetry.com",
        "textLine1" : "The server is running. All times displayed in UCT.",
        "textLine2" : "The server time is: " + serverTime(),
        "textLine3" : "JMW: " + JMWStatus,
        "textLine4" : "RedPath: " + RedPathSatus
    }
    
    return render_template("empty.html",**templateData)
    
#Endpoint for JMW Farms Box #001    
@app.route('/post/tplowman',methods=['GET','POST'])
def sqlTPlowman():
    table = "PBL003"
    if request.method == 'POST':
        input_json = request.get_json(force=True)
        #print('data:',input_json)
        value = input_json['value']
        InsertSQLModified(value) #changing route for JMW to Uploaded Data. 
        #InsertSQL(value,table)
        #Save to sql
        return value
    if request.method == 'GET':
        values = SelectSQL(table)
        return jsonify(values)    

#Endpoint for Redpath Box #001    
@app.route('/post/<string:boxNumber>',methods=['GET','POST'])
def sqlRedpath(boxNumber):
    table = boxNumber  #table name 
    if request.method == 'POST':
        input_json = request.get_json(force=True)
        value = input_json['value']
        #InsertSQL(value,table) # Removed 010522 for modified, see below. 
        InsertSQLModified(value)
        #Save to sql
        return value
    if request.method == 'GET':
        values = SelectSQL(table)
        return jsonify(values)   



from werkzeug.debug import DebuggedApplication
app.wsgi_app = DebuggedApplication(app.wsgi_app, True)

app.debug = True


if __name__ == "__main__":
        app.run(host='0.0.0.0', port=8080) #Port 8080 is for Debugging. This must be changed when using nginx service. 






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


def SelectSQL(table):
        config = MysqlConfig()
        mydb = mysql.connector.connect(**config)
        mycursor = mydb.cursor()
        try:
            mycursor.execute("SELECT * FROM `plowmantelemetryschema`." + table + " ORDER BY ID DESC;")
            myresult = mycursor.fetchall()
            data = []
            for x in myresult:
                    data.append(x)
            return (data)
        except:
            return "Error - Likely table does not exist"


@app.route('/')
def index():
    text = "This service is purely for posting data to the server"
    return render_template("empty.html",text = text)
    
#Endpoint for JMW Farms Box #001    
@app.route('/post/tplowman',methods=['GET','POST'])
def sqlTPlowman():
    table = "PBL_Telemetry_JMW"
    if request.method == 'POST':
        input_json = request.get_json(force=True)
        #print('data:',input_json)
        value = input_json['value']
        
        InsertSQL(value,table)
        #Save to sql
        return value
    if request.method == 'GET':
        values = SelectSQL(table)
        return jsonify(values)    

#Endpoint for Redpath Box #001    
@app.route('/post/<string:boxNumber>',methods=['GET','POST'])
def sqlRedpath(boxNumber):
    table = "PBL_Telemetry_" + boxNumber  #table name 
    if request.method == 'POST':
        input_json = request.get_json(force=True)
        value = input_json['value']
        InsertSQL(value,table)
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






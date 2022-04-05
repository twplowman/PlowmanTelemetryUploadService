from flask import Flask, session, redirect, url_for, escape, request, render_template, jsonify
import csv
import mysql.connector
import mplleaflet
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import os
from datetime import datetime, timedelta

def GetSQLPassword():
    password = "bR0m3lIad2021!!"
    #password = ""
    return password


def InsertSQL(value):
    mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password=GetSQLPassword(),
    database="mysql_test"
    )
    
    mycursor = mydb.cursor()
    #sql = "INSERT INTO `mysql_test`.`PBL_Telemetry` (`Box Number`, `DateTime`, `Longitude`, `Latitude`, `Temperature 1`) VALUES ('\'PBL v0.4.2', '2021-10-06 08:03:29', '54.08095', '-1.1727', '13')"
    sql = "INSERT INTO `mysql_test`.`PBL_Telemetry_2` (`Box Number`, `DateTime`, `Latitude`, `Longitude`, `Temperature`) VALUES (%s, %s, %s, %s, %s)"
    examples = ('PBL v0.4.1','2021-10-06 08:03:29','54.08095','-1.1727','-127.000')
    #print(value)
    value = value.lstrip('\"')
    value = value.rstrip('\"')
    value = eval(value)
    #print(value)
    #print(examples)
    #print(type(value))
    #print(type(examples))
    mycursor.execute(sql,value)
    mydb.commit()
    #print("1 record inserted, ID:", mycursor.lastrowid)


def InsertSQLv0_5_3(value):
    mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password=GetSQLPassword(),
    database="mysql_test"
    )
    
    mycursor = mydb.cursor()
    sql = "INSERT INTO `mysql_test`.`PBL_Telemetry_0_5_3` (`Box Number`, `DateTime`, `Latitude`, `Longitude`, `T1`, `T2`, `T3`, `T4`, `T5`, `T6`, `T7`, `T8`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    examples = ('PBL v0.4.1','2021-10-06 08:03:29','54.08095','-1.1727','-127.000','-127.000','-127.000','-127.000','-127.000','-127.000','-127.000','-127.000')
    value = value.lstrip('\"')
    value = value.rstrip('\"')
    value = eval(value)
    print(value)
    print(examples)
    print(type(value))
    print(type(examples))
    mycursor.execute(sql,value)
    mydb.commit()

def SelectSQL():
    mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password=GetSQLPassword(),
    database="mysql_test"
    )    
    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM `mysql_test`.`PBL_Telemetry_2`")
    myresult = mycursor.fetchall()
    
    data = []
    for x in myresult:
      data.append(x)
    return (data)

# Creates a Map based upon dateTime and boxNumber from SQL database
# Uses SQL database: mysql_test.PBL_Telemetry_2
# Finds latitude and longitude in range and plots these on a map
# TODO - add a few days before? or all day ranges.
# Saves file to same place this code executes then file is moved to correct folder
#
# dateTime = datetime in format of YYYY-MM-DD HH/MM/SS 
# boxNumber = string that is specific to livestock box. e.g. 'PBL v0.4.9' no checks if this is wrong!
# filename = name to save map (usually same as box number)
def sqlOneDayMap(dateTime, boxNumber,filename,table):
    
    ccnx = mysql.connector.connect(host="localhost",
                                   user="root",
                                   password=GetSQLPassword(),
                                   database="mysql_test") #connect to database
    cursor = ccnx.cursor() #define cursor
    query = ("SELECT latitude, longitude FROM %s WHERE DateTime > %s AND `Box Number` = %s;") #construct query
    cursor.execute(query,(table,dateTime,boxNumber)) #execute query using time range and box number
    
    #define arrays
    latitudeRange = []
    longitudeRange = []
    for (latitude, longitude) in cursor: #loop through each row and store longitude and latitude under cursor
        latitudeRange.append(latitude)
        longitudeRange.append(longitude)
    if not latitudeRange:
        return
    #print(latitudeRange, longitudeRange)    
    plt.plot(longitudeRange,latitudeRange,color = '#0e4a99',lw=4) #plot graph - wants to be in own function.
    mplleaflet.save_html(fileobj=filename) #save map to same place as this function
    os.system("mv "+ filename+" ~/flaskapp/static/maps/") #move to correct folder so server can find the file
    plt.clf()




# Creates a Temperature graph based upon dateTime and boxNumber from SQL database
# Uses SQL database: mysql_test.PBL_Telemetry_2
# Finds temperature and ID in range and plots these on a graph
# TODO - add a few days before? or all day ranges.
# Saves file to same place this code executes then file is moved to correct folder
#
# dateTime = datetime in format of YYYY-MM-DD HH/MM/SS 
# boxNumber = string that is specific to livestock box. e.g. 'PBL v0.4.9' no checks if this is wrong!
# filename = name to save temperature (usually same as box number)
def sqlGenerateTempGraph(dateTime, boxNumber,filename):
    ccnx = mysql.connector.connect(host="localhost",
                                   user="root",
                                   password=GetSQLPassword(),
                                   database="mysql_test") #connect to database
    cursor = ccnx.cursor() #define cursor
    query = ("SELECT ID, temperature FROM mysql_test.PBL_Telemetry_2 WHERE DateTime > %s AND `Box Number` = %s;") #construct query
    cursor.execute(query,(dateTime,boxNumber)) #execute query using time range and box number
    #define array
    datetimeRange = []
    temperatureRange = []
    for (ID, temperature) in cursor: #loop through each row and store longitude and latitude under cursor
        temperatureRange.append(temperature)
        datetimeRange.append(ID)
    if not temperature:
        return
    
    plt.plot(datetimeRange,temperatureRange,color = '#0e4a99',lw=4) #plot graph - wants to be in own function.
    plt.savefig(filename)
    os.system("mv "+ filename+" ~/flaskapp/static/maps/") #move to correct folder so server can find the file
    plt.clf() 
    

# Queries SQL database and finds last row for specified box number. Converts to date or checks if online/offline 
# boxNumber = string that is specific to livestock box. e.g. 'PBL v0.4.9' no checks if this is wrong!
# **kwargs:
#          - dateformat. if set as true, will return last packet in format of DD/MM/YYYY HH:MM:SS
#          - status.     if set as true, will return last packet in readable format AND ONLINE/OFFLINE (used on html)
# returns datetime in format of '%Y-%m-%d %H:%M:%S' as standard. 
def LastPacketTime(boxNumber,**kwargs):
    ccnx = mysql.connector.connect(host="localhost", user="root", password=GetSQLPassword(), database="mysql_test") #connect to database
    cursor = ccnx.cursor() #define cursor
    query = ("SELECT DateTime FROM mysql_test.PBL_Telemetry_2  WHERE  `Box Number` = %s ORDER BY DateTime DESC LIMIT 1  ;") #construct query
    cursor.execute(query,(boxNumber,))
    for datetime in cursor:
        if kwargs.get('dateformat'): #probably will be unused
            readableDate = ConvertToReadableTime((datetime[0]))
            return readableDate
        if kwargs.get('status'): #if we want to check ONLINE/OFFLINE
            readableDate = ConvertToReadableTime((datetime[0]))
            if PacketAge(20,datetime[0]): #Pass in 20 minutes, we can expose and change this later
                readableDate = readableDate + " || ONLINE "
            else:
                readableDate = readableDate + " || OFFLINE "
            return readableDate
        else:
            return datetime[0]


#TODO - fix
def LastPacket(boxNumber):
    ccnx = mysql.connector.connect(host="localhost", user="root", password=GetSQLPassword(), database="mysql_test") #connect to database
    cursor = ccnx.cursor() #define cursor
    query = ("SELECT * FROM mysql_test.PBL_Telemetry_2  WHERE  `Box Number` = %s ORDER BY DateTime DESC LIMIT 1  ;") #construct query
    myresult = cursor.fetchall()
    data = [] #this is the array
    for x in cursor: #should only be one row related to that specific box. 
        data.append(x)
    return data

# compares date (in a datetime format of '%Y-%m-%d %H:%M:%S') against current server time.
# timeMinutes = integer time in minutes 
# dateTime = time to evaluate (e.g. last packet from sql server)
# returns true or false based upon defined allowable range in minutes.
def PacketAge(timeMinutes,dateTime): 
    difference = (datetime.now() - dateTime) - timedelta(minutes = timeMinutes)
    #print(difference)
    if difference < timedelta(0):
        return True
    else:
        return False
    
# Converts readable format into datetime type.
# '%d/%m/%Y %H:%M:%S' to '%Y-%m-%d %H:%M:%S'
# readableDate = date time in format of DD/MM/YYYY HH:MM:SS (e.g. time from picos)
# returns dateTime = datetime in format of YYYY-MM-DD HH/MM/SS (e.g. datetime from sql server)
def ConvertToDateTime(readableDate):
    dateTime = datetime.strptime(readableDate, '%Y-%m-%d %H:%M:%S')
    return dateTime

# Converts datetime into more readable format
# '%Y-%m-%d %H:%M:%S' to '%d/%m/%Y %H:%M:%S'
# dateTime = date time in format of YYYY-MM-DD HH/MM/SS (e.g. datetime from sql server)
# returns readableDate
def ConvertToReadableTime(dateTime):
    readableDate = datetime.strftime(dateTime, '%d/%m/%Y %H:%M:%S')
    return readableDate


#TODO - fix
def LiveLocation():
    data1 = LastPacket('PBL002')
    data2 = LastPacket('PBL003')







def createCsvGraph():
    import csv
    import numpy as np
    import pandas
    import os
    from matplotlib.collections import LineCollection
    from matplotlib.colors import ListedColormap, BoundaryNorm
    global lastUpdated, lastPacket

    path = "~/flaskapp/"
    csvfile = "PostData.csv"
    processedcsv = "ProcessedData.csv"
    with open(csvfile, 'r') as f, open(processedcsv, 'w') as fo: 
        for line in f:
            fo.write(line.replace('"', '').replace("'", ""))

    colnames = ['Box Number', 'Date', 'Time', 'Latitude', 'Longitude', 'Temperature']
    data = pandas.read_csv(path+processedcsv,names=colnames,quotechar='"')
    temperature = data.Temperature.tolist()
    latitude = (data.Latitude.tolist())
    longitude = (data.Longitude.tolist())
    date = (data.Date.tolist())
    time = (data.Time.tolist())

    lastPacket = date[-1] + " || " + time[-1]
    #print(lastPacket)

    s = ' Latitude'
    matched_indexes = []
    i = 0
    length = len(latitude)
    #print(length)
    while i < length:
        if s == latitude[i]:
            matched_indexes.append(i)
        i += 1

    #print(matched_indexes)
    i = 0
    a = 0
    del latitude[matched_indexes[i]]
    del longitude[matched_indexes[i]]
    del temperature[matched_indexes[i]]
    del date[matched_indexes[i]]
    del time[matched_indexes[i]]

    for i in reversed(range(len(matched_indexes))):
        #print(i)
        a = 0
        while a < 3:
            #print(matched_indexes)
            #print(a)
            matched_indexes[i] = matched_indexes[i] - 1
            #print(matched_indexes[i])
            del latitude[matched_indexes[i]]
            del longitude[matched_indexes[i]]
            del temperature[matched_indexes[i]]
            del date[matched_indexes[i]]
            del time[matched_indexes[i]]
            a = a + 1

    from datetime import datetime, timedelta
    today = datetime.today()
    dateToday = today.strftime("%d/%m/%Y")
    now = datetime.now()
    timeTodayHr = int(now.strftime("%H"))
    timeTodayMin = int(now.strftime("%M"))
    global timeSearch
    timeRange = timeTodayHr - int(timeSearch)
    if timeRange < 0:
        #Get date from the previous day!?!?!
        yesterday = datetime.today() - timedelta(days=1)
        dateToday = yesterday.strftime("%d/%m/%Y")
        timeRange = 2
    latitudeRange = []
    longitudeRange = []
    temperatureRange = []
    temperatureTime = []
    i = 0
#    print(timeRange)
    while i < len(date):
#        print("looping: " + str(i) + "   " + str(len(date)))
        if dateToday == date[i]:
            if timeRange < int((time[i])[0]+(time[i])[1]):
                latitudeRange.append(latitude[i])
                longitudeRange.append(longitude[i])
                temperatureRange.append(temperature[i])
                temperatureTime.append(time[i])
        i += 1

#check if we have sent data in the last 10 minutes??
    
    if dateToday == date[-1]:
        if timeTodayHr == int((time[-1])[0]+(time[-1])[1]):
            if (timeTodayMin - int((time[-1])[3]+(time[-1])[4])) < 15:
                lastPacket = lastPacket + " || ONLINE "

    lastPacket = lastPacket + " || OFFLINE "


    latitude = list(map(float,latitude))
    longitude = list(map(float,longitude))
    temperature = list(map(float,temperature))

    x = np.array(latitude)
    y = np.array(longitude)
    t = np.array(temperature)

#    print(xRange)
#    print(yRange)

    plt.plot(y,x,color = '#8a8a8a',lw=4,alpha=0.9)

    if len(latitudeRange) < 1:
        xRange = np.array(latitude[-1])
        yRange = np.array(longitude[-1])
        currentLocationColour = 'r'

    else:
        latitudeRange = list(map(float,latitudeRange))
        longitudeRange = list(map(float,longitudeRange))
        temperatureRange = list(map(float,temperatureRange))
        temperatureTime = list(temperatureTime)
        xRange = np.array(latitudeRange)
        yRange = np.array(longitudeRange)
        tRange = np.array(temperatureRange)
        tTime = np.array(temperatureTime)
        plt.plot(yRange,xRange,color = '#0e4a99',lw=8)
        plt.plot(yRange,xRange,color = '#1a73e8',lw=4)
        currentLocationColour = 'g'

    plt.scatter(y[-1],x[-1],s=200,alpha=0.8,c=currentLocationColour)

    filename = "PostData.html"
    mplleaflet.save_html(fileobj=filename)
    os.system("mv PostData.html ~/flaskapp/static/maps/")
    lastUpdated = now.strftime("%d/%m/%Y || %H:%M:%S")
    
    if len(latitudeRange) > 1:
        plt.clf()
        plt.plot(tTime,tRange,color = '#0e4a99',lw=8)  
        plt.savefig('temperature.png')
        os.system("mv temperature.png ~/flaskapp/static/maps/")
        plt.clf()    
    

def readData():
    with open("PostData.csv", "r") as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter=',')
        values = []
        for lines in csv_reader:
            #print(lines)
            values.append(lines['Box Number'])
            #print(values)
        return values


def writeData(value):
    destname = "PostData.csv"
    destfile = open(destname, 'a')
    mywriter = csv.writer(destfile)
    mywriter.writerow([value])
    destfile.close()



      
    












app = Flask(__name__)
global lastUpdated, timeSearch, lastPacket
lastUpdated = "Before Server Restart"
timeSearch = 5
lastPacket = lastUpdated











@app.route('/')
def index():
    if 'username' in session:
        link = '_map_002'
        return render_template('home.html',mapHTML=link,username = escape(session['username']))
    return redirect(url_for('login'))

@app.route('/post',methods=['GET','POST'])
def post():
    if request.method == 'POST':
        input_json = request.get_json(force=True)
        #print('data:', input_json)
        value = input_json['value']
        writeData(value)
        #createCsvGraph()
        return value
    if request.method == 'GET':
        values = readData()
        return jsonify(values)



@app.route('/post/sql',methods=['GET','POST'])
def sql():
    if request.method == 'POST':
        input_json = request.get_json(force=True)
        #print('data:',input_json)
        value = input_json['value']
        InsertSQL(value)
        #Save to sql
        return value
    if request.method == 'GET':
        values = SelectSQL()
        return jsonify(values)
    
    
@app.route('/post/sql/v0_5_3',methods=['POST'])
def sqlv_0_5_3():
    if request.method == 'POST':
        input_json = request.get_json(force=True)
        #print('data:',input_json)
        value = input_json['value']
        InsertSQLv0_5_3(value)
        #Save to sql
        return value   

@app.route('/get/sql',methods=['GET', 'POST'])
def getSqlMap():
    now = datetime.now()
    lastUpdated = now.strftime("%d/%m/%Y || %H:%M:%S")
    delay = True
    if request.method == 'POST':
        input_json = request.get_json(force=True)
        boxNumber = input_json['boxNumber']
        dateTime = input_json['dateTime']
        link = 'getMap'
        #print(boxNumber)
        #print(dateTime)
    if request.method == 'GET':
        if 'username' not in session:
            return redirect(url_for('login'))
        link = 'sqlMap'
        boxNumber = 'PBL v0.4.9'
        dateTime = datetime.now() - timedelta(days = 10)
        dateTime = dateTime.strftime('%Y-%m-%d %H:%M:%S')
        #print(dateTime)
    lastPacket = LastPacketTime(boxNumber,status = True)    
    sqlOneDayMap(dateTime,boxNumber,link+".html","PBL_Telemetry_2")    
    return render_template('home.html',mapHTML=link, delay=delay,lastUpdated=lastUpdated, lastPacket = lastPacket)


@app.route('/<name>/<timeRange>/',methods=['GET', 'POST'])
def getSqlMapAction(name,timeRange):
    now = datetime.now()
    lastUpdated = now.strftime("%d/%m/%Y || %H:%M:%S")
    delay = False
    if request.method == 'POST':
        input_json = request.get_json(force=True)
        boxNumber = input_json['boxNumber']
        dateTime = input_json['dateTime']
        link = 'getMap'
        #print(boxNumber)
        #print(dateTime)
    if request.method == 'GET':
        if 'username' not in session:
            return redirect(url_for('login'))
        link = 'sqlMap'
        boxNumber = name
        dateTime = datetime.now() - timedelta(days = int(timeRange))
        dateTime = dateTime.strftime('%Y-%m-%d %H:%M:%S')
        #print(dateTime)
    lastPacket = LastPacketTime(boxNumber,status = True)    
    sqlOneDayMap(dateTime,boxNumber,link+".html","PBL_Telemetry_2")    
    return render_template('home.html',mapHTML=link, delay=delay,lastUpdated=lastUpdated, lastPacket = lastPacket)


@app.route('/formtest',methods=['GET','POST'])
def formtest():
    if request.method == 'POST':
        print('here')
        link = 'formtest'
        boxNumber = request.form.get('Box_Number')
        dateTime = request.form.get('datetime') + (" 00:00:00")
        table = request.form.get('table') #e.g. PBL_Telemetry_2
        print(table)
        sqlOneDayMap(dateTime,boxNumber,link+".html",table)
        sqlGenerateTempGraph(dateTime,boxNumber,link+".png")
        print(boxNumber,dateTime)
    
        #Save to sql
        return render_template('Form_input.html',mapHTML = link)
    if request.method == 'GET':
        if 'username' not in session:
            return redirect(url_for('login'))
        link = 'formtest'
        
        return render_template('Form_input.html', mapHTML = link)
    





@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['username'] = request.form['username']
        return redirect(url_for('postmap'))
    if 'username' in session:
        session.pop('username',None)
        username = 'Logged Out'
    else:
        username = 'Not Logged In'
    return render_template('login_page.html',username=username)

@app.route("/mapmain/")
def mapmain():
    if 'username' in session:
        link = '_mapmain'
        return render_template('home.html',mapHTML=link,username = escape(session['username']))
    return redirect(url_for('login'))

@app.route('/setrange',methods=['GET','POST'])
def setrange():
    global timeSearch
    if request.method == 'POST':
        timeSearch = request.values['username']
        return redirect(url_for('generatemap'))
    info = 'enter time range in hrs'
    return render_template('login_page.html', username = info)


@app.route("/postmap/")
def postmap():
    global lastUpdated, lastPacket
    if 'username' in session:
        link = 'PostData'
        #return redirect(url_for('generatemap'))
        return render_template('home.html',mapHTML=link,username = escape(session['username']),lastUpdated=lastUpdated, lastPacket = lastPacket)
    return redirect(url_for('login'))

@app.route("/generatemap/")
def generatemap():
    global lastUpdated, lastPacket
    if 'username' in session:
        createCsvGraph()
        link = 'PostData'
        delay = True
#        return redirect(url_for('postmap'))
        return render_template('home.html',mapHTML=link,username = escape(session['username']), delay=delay,lastUpdated=lastUpdated, lastPacket = lastPacket)
    return redirect(url_for('login'))


@app.route("/map001/")
def map001():
    if 'username' in session:
        link = '_map_001'
        return render_template('home.html',mapHTML=link,username = escape(session['username']))
    return redirect(url_for('login'))

@app.route("/map002/")
def map002():
    if 'username' in session:
        link = '_map_002'
        return render_template('home.html',mapHTML=link,username = escape(session['username']))
    return redirect(url_for('login'))

@app.route("/map003/")
def map003():
    if 'username' in session:
        link = '_map_003'
        return render_template('home.html',mapHTML=link,username = escape(session['username']))
    return redirect(url_for('login'))

app.route("/map004/")
def map004():
    if 'username' in session:
        link = '_map_004'
        return render_template('home.html',mapHTML=link,username = escape(session['username']))
    return redirect(url_for('login'))


@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.pop('username', None)
    return redirect(url_for('index'))

# set the secret key.  keep this really secret:
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

 #Date range,Box Number,Map Name.
#PacketAge(10,LastPacketTime('PBL v0.4.9'))

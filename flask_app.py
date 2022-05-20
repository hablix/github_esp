
# A very simple Flask Hello World app for you to get started with...

from flask import Flask, redirect, render_template, request, url_for, send_from_directory
from datetime import datetime, timedelta
import matplotlib as mpl
import numpy as np
import matplotlib.pyplot as plt
import requests
from config import ACCESS_TOKEN_KEY

from io import StringIO

app = Flask(__name__)
app.config["DEBUG"] = True
comments = []
filename="/home/ha123blix/mysite/history/logfile.txt"
filename_timestamp="/home/ha123blix/mysite/history/logfile_timestamp.txt"


@app.route('/hw')
def hello_world():
    return 'Hello World in Python with Flask'

@app.route('/api1/history', methods=["GET","POST","DELETE"])
def api():
    if request.method == "GET":
        f = open(filename, "r")
        text = f.read()
        f.close()
        return text
    if request.method == "POST":
        f = open(filename, "a")
        f.write("\n\r")
        f.write(request.data.decode('UTF-8'))
        f.close()
        writeTimestamp()
        return Flask.Response(status=200)
    if request.method == "DELETE":
        f = open(filename, "w")
        f.write("temp; light1; light2; soil\n1;0;0;1")
        f.close()
        return 'deleted'

@app.route('/api1/history_generateimg', methods=["GET"])
def generateimg():
    if request.method == "GET":
        generateimggraph()
        #crimg.generateimg()
        return 'img generated, go back and reload'


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        comments=[]
        f = open(filename, "r")
        for x in f:
            comments.append(x)
        f.close()
        val = getLastValues()
        time = getTimestamp()
        res = getWetterComTemperature()
        temp_out = res[0]
        val_feel = res[1]
        hum = res[2]
        return render_template("main_page.html",
        comments=comments,
        val_temp = val[0] if len(val)>0 else ' ',
        val_light1 = val[1]if len(val)>1 else ' ',
        val_light2 = val[2]if len(val)>2 else ' ',
        val_soil = val[3]if len(val)>3 else ' ',
        val_lastupdate = time,
        val_temp_out = temp_out,
        val_feel=val_feel,
        val_hum = hum)

    if request.method == "POST":
        if request.form['submit_button'] =='Bild neu erzeugen':
            generateimggraph()
            return redirect(url_for('index'))
        else:
            f = open(filename, "a")
            f.write("\n\r")
            f.write(request.form["contents"])
            f.close()
            writeTimestamp()
            return redirect(url_for('index'))

    if request.method == "PUT":
        generateimggraph()
        return redirect(url_for('index'))
# necessary for image!
@app.route('/history/<path:path>')
def send_js(path):
    return send_from_directory('history', path)


def getLastValues():
    with open(filename, "rb") as f:
        last = readlastline(f).decode('UTF-8')
        return last.replace('\r','').split(';')

def getTimestamp():
    f = open(filename_timestamp, "r")
    text = f.read()
    f.close()
    return text

def writeTimestamp():
    now = datetime.now()
    now = now + timedelta(hours=1)
    dt_string = now.strftime("%d %B, %H:%M:%S")
    f = open(filename_timestamp, "w")
    f.write(dt_string)
    f.close()


def readlastline(f):        # https://stackoverflow.com/questions/3346430/what-is-the-most-efficient-way-to-get-first-and-last-line-of-a-text-file
    f.seek(-2, 2)              # Jump to the second last byte.
    while f.read(1) != b"\n":  # Until EOL is found ...
        f.seek(-2, 1)
    f.seek(-2, 1)
    while f.read(1) != b"\n":
        f.seek(-2, 1)
    return f.read()            # Read all data from this point on.
# *******************************************************************

def getWetterComTemperature():
  resp =requests.get(ACCESS_TOKEN_KEY) # for security reasons load from config.py
  jsn = resp.json()
  k = jsn['main']['temp']
  c = KelvinToCelsius(k)
  c_feel = KelvinToCelsius(jsn['main']['feels_like'])
  hum = jsn['main']['humidity']

  return round(c,2), round(c_feel,2), hum

def KelvinToCelsius(kelvin):
    celsius = kelvin - 273.15;
    return celsius


# *******************************************************************
# GENERATE IMAGE

def generateimggraph():
  print('paste values or pass empty field to request from web server: http://ha123blix.eu.pythonanywhere.com/')
  val = \
  '''123;56;658
  234;675;878
  56;76;0
  48;990;0;45
  '''

  f = open(filename, "r")
  val = f.read()
  f.close()

  val = val.replace(' ', '\n')
  data = np.genfromtxt(StringIO(val), delimiter=";", skip_header=1, skip_footer=0, names=['x', 'y', 'z', 'a'], invalid_raise = False)
  print (data)

  x_=[]
  i = 0;
  for k in data:
    x_.append(i)
    i = i +1

  temp_1 = 0

  # filter

  for index, temp in enumerate(data['x']):
    if(temp == 85):
      data['x'][index] = temp_1;
    else:
      temp_1 = temp
    if(temp <= -1):
      data['x'][index] =-1;
      temp_1 = -1;
    if(temp >= 50):
      data['x'][index] =-1
      temp_1 = -1


  for index, y in enumerate(data['y']):
    rep = 5
    if(index >=rep ):
      sum=0
      for k in range(rep):
        sum =sum + data['y'][index-k]
      data['y'][index] = sum/rep

  for index, z in enumerate(data['z']):
    rep = 5
    if(index >=rep ):
      sum=0
      for k in range(rep):
        sum =sum + data['z'][index-k]
      data['z'][index] = sum/rep


  plt.rcParams["figure.figsize"] = (24, 6)
  fig = plt.figure()
  ax1 = fig.add_subplot(111)
  ax1.set_title("Zeitreihe")
  ax1.set_xlabel('time')
  ax1.set_ylabel('value')

  ax1.plot(x_, data['x']*10, color='r', label='temp')
  ax1.plot(x_, data['y'], color='y', label='light 1' )
  ax1.plot(x_, data['z'], color='g', label='light 2' )
  ax1.plot(x_, data['a']/20, color='b', label='soil' )
  plt.savefig("/home/ha123blix/mysite/history/graph.png")




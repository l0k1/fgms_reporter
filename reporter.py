import pickle
import configparser
import telnetlib
import math
import csv
from time import time
from time import sleep
from pathlib import Path
from datetime import datetime

delay = 15

debug = 2   # use this to turn a bunch of print statements on or off.
            # 2 prints a lot, 1 prints logging stuff.
            
runs = 0

home = str(Path.home()) +  '/fgms_reporter/'

print(str(datetime.now()) +" // Starting FGMS Reporter!")

# make sure the config file exists.
try:
    _ = open(home + "config.ini","rt")
except FileNotFoundError as e:
    _ = open(home + "config.ini","xt")
    print("[general]\ncallsigns=pinto|PINTO|Leto|USAF001\naircraft=JA37-Viggen|AJ37-Viggen|AJS37-Viggen|F-15C\nservers=mpserver01.flightgear.org\nports=5001",file=_)
    if debug >= 1:
        print(str(datetime.now()) +" // config.ini not found, creating default config.ini...")
finally:
    _.close()
    
# make sure the csv file exists
try:
    _ = open(home + "output.csv","rt")
except FileNotFoundError as e:
    _ = open(home + "output.csv","xt")
    # parr[cs] = {'active':0,'lastmodel':"",'x':0,'y':0,'z':0,'lat':0,'lon':0,'time':0,'model':{}}
    print("callsign,model,eft",file=_)
    if debug >= 1:
        print(str(datetime.now()) +" // output.csv not found, creating default output.csv...")
finally:
    _.close

# make sure the pickle database exists
try:
    _ = open(home + "db.pickle","rb")
except FileNotFoundError as e:
    _ = open(home + "db.pickle","xb")
    pickle.dump({},_)
    if debug >= 1:
        print(str(datetime.now()) +" // db.pickle not found, creating default db.pickle...")
finally:
    _.close()

# main loop
while True:
    if debug == 2:
        print(str(datetime.now()) +" // beginning main loop")
    #config stuff
    conf = configparser.ConfigParser()
    conf.read(home + 'config.ini')
    callsigns = str(conf.get('general','callsigns')).split('|')
    aircraft = str(conf.get('general','aircraft')).split('|')
    servers = str(conf.get('general','servers')).split('|')
    ports = str(conf.get('general','ports')).split('|')
    if debug == 2:
        print(str(datetime.now()) +" // config file has been read.")
    
    #database stuff
    pickle_file = open(home + 'db.pickle','rb')
    parr = pickle.load(pickle_file)
    pickle_file.close()
    if parr == None:
        parr = {}
    if debug == 2:
        print(str(datetime.now()) + " // database successfully loaded.")
        
    #telnet stuff - aggregate our data.
    data = ""
    for server in servers:
        try:
            tn = telnetlib.Telnet(server,int(ports[servers.index(server)]))
            data = data + str(tn.read_all())
            tn.close()
            if debug == 2:
                print(str(datetime.now()) + " // pulled data from " + str(server))
        except:
            print(str(datetime.now()) + " // Unable to establish a connection with " + str(server))
    data = data.split('\\n')
    
    runs = runs + 1
    
    # make sure we have everybody in parr.
    for cs in callsigns:
        if not cs in parr:
            parr[cs] = {'active':0,'lastmodel':"",'x':0,'y':0,'z':0,'time':0,'model':{}}
        for ac in aircraft:
            if not ac in parr[cs]['model']:
                parr[cs]['model'][ac] = 0
        found = 0
        for d in data:
            if d.find('@') != -1 and d.split('@')[0] == cs:
                found = 1
                extract = d.split('@')[1].split(' ')
                model = extract[10].split('/')[-1].split('.xml')[0]
                if debug >= 1 and parr[cs]['active'] == 0:
                    print(str(datetime.now()) + " // runs: " + str(runs) + " // Detected " + cs + " online using model " + model + ".")
                if model in parr[cs]['model']:
                    if ( parr[cs]['active'] == 0 ) or ( parr[cs]['active'] == 1 and parr[cs]['lastmodel'] != model ) :
                        if debug == 2:
                            print(str(datetime.now()) +" // " + cs + " has been detected online as newly active or the model has changed.")
                        parr[cs]['lastmodel'] = model
                        parr[cs]['time'] = time()
                        parr[cs]['x'] = float(extract[1])
                        parr[cs]['y'] = float(extract[2])
                        parr[cs]['z'] = float(extract[3])
                    elif parr[cs]['active'] == 1 and parr[cs]['lastmodel'] == model:
                        # active - we need to calculate speed to see if we should add to eft.
                        x1 = float(extract[1])
                        y1 = float(extract[2])
                        z1 = float(extract[3])
                        x2 = parr[cs]['x']
                        y2 = parr[cs]['y']
                        z2 = parr[cs]['z']
                        distance = math.sqrt( (z2 - z1) ** 2 + (x2 - x1) ** 2 + (y2 - y1) ** 2)
                        update_time = time() - parr[cs]['time']
                        speed = distance / update_time # in meters/second
                        if speed > 2.57: #i.e. 5 knots
                            parr[cs]['model'][model] = parr[cs]['model'][model] + update_time
                            if debug == 2:
                                print(str(datetime.now()) +" // " + cs + " is moving at " + str(speed) + " m/s, adding " + str(update_time) + " to " + model)
                        elif debug == 2:
                            print(str(datetime.now()) +" // " + cs + " has not moved more than 5kts.")
                        parr[cs]['time'] = time()
                        parr[cs]['x'] = x1
                        parr[cs]['y'] = y1
                        parr[cs]['z'] = z1
                else:
                    parr[cs]['lastmodel'] = "none"
        if debug >= 1 and parr[cs]['active'] == 1 and found == 0:
            print(str(datetime.now()) + " // runs: " + str(runs) + " // " + cs + " is no longer online.")
        parr[cs]['active'] = found

    # now need to export parr to csv and to pickle DB.
    pickle_file = open(home + 'db.pickle','wb')
    pickle.dump(parr,pickle_file)
    pickle_file.close()
    
    csv_file = open(home + 'output.csv','wt')
    try:
        writer = csv.writer(csv_file)
        writer.writerow(('callsign','model','eft','last update time: ' + str(datetime.now())))
        for cs in parr:
            for model in parr[cs]['model']:
                writer.writerow((cs,model,parr[cs]['model'][model],str(parr[cs]['time'])))
    finally:
        csv_file.close()
    
    # wait -delay- seconds and run 'er again!
    sleep(delay)
    

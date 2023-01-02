#Copyright 2022-2023 Hugh Garner
#Permission is hereby granted, free of charge, to any person obtaining a copy 
#of this software and associated documentation files (the "Software"), to deal 
#in the Software without restriction, including without limitation the rights 
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
#copies of the Software, and to permit persons to whom the Software is 
#furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in 
#all copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL 
#THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR 
#OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, 
#ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR 
#OTHER DEALINGS IN THE SOFTWARE.  

#v2.00 01/01/2023 Compatible with FoosOBSPlus v2.00 and above

import network
import secretsHP
import secretsHome
import config
import time
import sys
import socket
import select
import machine
from machine import Pin
from machine import Timer

FORMAT = 'utf-8'
LED = Pin("LED",Pin.OUT)
isConnected = False
CONFIGFILE = "config.py"
REQUIREDCONFIGNAMES = ["PORT","SENSOR1","SENSOR2","SENSOR3","LED1","LED2","DELAY_TIME"]
REQUIREDCONFIGTESTS = ["PORT","PIN","PIN","PIN","PIN","PIN","TIME"]
VALIDPINS = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,26,27,28]

def blink(blinks, duration):
        while blinks > 0:
                LED.value(True)
                time.sleep(duration)
                LED.value(False)
                time.sleep(duration)
                blinks = blinks - 1

def pinId(pin):
    return int(str(pin)[4:6].rstrip(","))

def timerDone(Source):
    global isBlocked
    isBlocked = False
    team1LED.value(0)
    team2LED.value(0)

def sensorInterrupt(pin):
    global sensorStates
    global blockingTimer
    global isBlocked
    global teamScored
    global sensorPinNbr
    global delayTime
    
    id = pinId(pin)
    idx = pins.index(id)
    sensorState = sensorStates[idx]
    led = leds[idx]
    team = teams[idx]-1

    for sensor in sensors:
        sensor.irq(handler=None)

    sensor = sensors[idx]

    if (sensor.value() == onState) and (sensorStates[idx] == 0):
        if not(isBlocked):
            sensorStates[idx] = 1
            isBlocked = True
            led.value(1)
            teamScored[team] = True
            sensorPinNbr = id

    elif (sensor.value() == offState) and (sensorStates[idx] == 1):
        blockingTimer = Timer(period = delayTime, mode = Timer.ONE_SHOT, callback = timerDone)
        sensorStates[idx] = 0

    for sensor in sensors:
        sensor.irq(handler=sensorInterrupt)

def sendMessage(c, message):
    global isConnected
    try:
        displayMessage = message.replace("\r","\\r")
        displayMessage = displayMessage.replace("\n","\\n")
        print("Sending: [" + displayMessage + "]")
        c.send(message.encode(FORMAT))
    except Exception as ex:
        if(type(ex).__name__=="OSError"):
            print(type(ex).__name__,"exception in [sendMessage] function: ",ex.args)
            print("Socket disconnected.")
        else:
            print(type(ex).__name__,"exception in [sendMessage] function: ",ex.args)
        print("Closing socket.")
        c.close()
        isConnected = False

def sendScore(c,teamAndPin):
    msg = "Team:"+teamAndPin+"\r\n"
    sendMessage(c,msg)

def readConfigFile():
    config = ""
    with open(CONFIGFILE,"r") as file:
        config = file.readlines()
    return config

def sendConfigFile():
    config = readConfigFile()
    sendMessage(c,"Read:\r\n")
    for line in config:
        line = "Line:" + line.rstrip()
        if line != "Line:":
            line = line + "\r\n"
            sendMessage(c,line)
        
def writeConfigFile(config,filename):
    with open(filename,"w") as file:
        for line in config:
            file.write(line)
    print("Config written to " + filename + ".")

def validateConfig(config):
    print("Validating...")
    validated = True
    lines = config.rsplit("\r\n")
    configNames = REQUIREDCONFIGNAMES.copy()
    configTests = REQUIREDCONFIGTESTS.copy()
    for line in lines:
        if line != "":
            line = line.replace(" ","")
            name,value = line.rsplit("=")
            if name in configNames:
                pos = configNames.index(name)
                if pos >= 0:
                    test = configTests[pos]
                    del configNames[pos]
                    del configTests[pos]
                    if test == "PORT":
                        if value.isdigit():
                            value = int(value)
                            if value < 0 or value > 65535:
                                validated = False
                        else:
                            validated = False
                    elif test == "PIN":
                        if value.isdigit():
                            value = int(value)
                            if value not in VALIDPINS:
                                validated = False
                        else:
                            validated = False
                    elif test == "TIME":
                        if value.isdigit():
                            value = int(value)
                            if value < 1 or value > 60000:
                                validated = False
                        else:
                            validated = False
    if len(configNames) != 0:
        validated = False
        print("Missing parameters: ")
        print(*configNames, sep = ", ")
    return validated

def parseSave():
    writeDone = False
    dateStamp = ""
    config = ""
    text = cmd[1].rsplit("\n")
    for t in text:
        if t != "":
            if t[0:3] == "End":
                print("Got End")
                if validateConfig(config):
                    if dateStamp != "":
                        oldConfig = readConfigFile()
                        if oldConfig == config:
                            print("New config same as old config - write aborted.")
                        else:
                            writeConfigFile(oldConfig,CONFIGFILE + dateStamp)
                            print("Old config backed up as " + CONFIGFILE + dateStamp + ".")
                            print("writing config...")
                            writeConfigFile(config,CONFIGFILE)
                    else:
                        print("No dateStamp found - write aborted.")
                else:
                    print("Invalid config - write aborted.")
            elif t[0:4] == "date":
                dateStamp = t[7:21]
            else:
                config = config + t + "\r\n"
    
port       = config.PORT
SENSOR1    = config.SENSOR1
SENSOR2    = config.SENSOR2
SENSOR3    = config.SENSOR3
LED1       = config.LED1
LED2       = config.LED2
delayTime  = config.DELAY_TIME

print("Configuration:")
print("PORT:    ",port)
print("SENSOR1: ",SENSOR1)
print("SENSOR2: ",SENSOR2)
print("SENSOR3: ",SENSOR3)
print("LED1:    ",LED1)
print("LED2:    ",LED2)
print("DELAY:   ",delayTime)

if SENSOR1 + SENSOR2 + SENSOR3 < 1:
    print("Not enough sensors configured in " + CONFIGFILE + ".  Aborting.")
    sys.exit()
if ((SENSOR1 == SENSOR2) or (SENSOR2 == SENSOR3) or (LED1 == LED2)):
    print("ERROR: Two Pins are the same in " + CONFIGFILE + ".  Aborting.")
    sys.exit()
if ((SENSOR1 == LED1) or (SENSOR2 == LED1) or (SENSOR3 == LED1)):
    print("ERROR: Sensor and LED1 have same pin in " + CONFIGFILE + ".  Aborting.")
    sys.exit()
if ((SENSOR1 == LED2) or (SENSOR2 == LED2) or (SENSOR3 == LED2)):
    print("ERROR: Sensor and LED2 have same pin in " + CONFIGFILE + ".  Aborting.")
    sys.exit()

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
while (wlan.isconnected()==False):
    print("Trying wifi connection with: ",secretsHP.SSID)
    wlan.connect(secretsHP.SSID, secretsHP.PASSWORD)
    blink(6,.25)
    time.sleep(2)
    if(wlan.isconnected()==False):
        print("Trying wifi connection with: ",secretsHome.SSID)
        wlan.connect(secretsHome.SSID, secretsHome.PASSWORD)
        blink(6,.25)
        time.sleep(2)

blink(2,.25)
host = wlan.ifconfig()[0]
print("Connected. Host ip = " + host + ".")
print()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

try:
    s.bind((host, port))
except:
    s.close()
    try:
        s.bind((host, port))
    except:
        print("Could not bind " + host + ":" + port + ".")
        sys.exit()
print("Socket bound.")
s.listen(1)

blink(4,.15)

team1LED = Pin(LED1,Pin.OUT)
team2LED = Pin(LED2,Pin.OUT)
blockingTimer = Timer(period = 1, mode = Timer.ONE_SHOT, callback = timerDone)
onState = False
offState = True
x = 0
sensorStates = [0,0,0]
pins = [SENSOR1, SENSOR2, SENSOR3]
sensors = [Pin(p, Pin.IN) for p in pins]
for sensor in sensors:
    sensorStates[x] = not(sensor.value())
    sensor.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=sensorInterrupt)
    x+=1
isBlocked = False
teamScored = [0 , 0]
teams = [1, 2, 2]
x=0
leds = [team1LED, team2LED, team2LED]
for team in teams:
    if (team == 1):
        leds[x] = team1LED
    else:
        leds[x] = team2LED
    x+=1

def allBlink(blinks, duration):
        while blinks > 0:
                team1LED.value(True)
                team2LED.value(True)
                LED.value(True)
                time.sleep(duration)
                team1LED.value(False)
                team2LED.value(False)
                LED.value(False)
                time.sleep(duration)
                blinks = blinks - 1

allBlink(3,.3)
isConnected = False

print("Sensors Active.")

connectCount = 0

while True:
    if teamScored[0]:
        teamScored[0] = False
        print("Team 1 Scored - Pin: " + str(sensorPinNbr))
        if(isConnected):
            sendScore(c,"1,"+str(sensorPinNbr))
    elif teamScored[1]:
        teamScored[1] = False
        print("Team 2 Scored - Pin: " + str(sensorPinNbr))
        if(isConnected):
            sendScore(c,"2,"+str(sensorPinNbr))
    time.sleep(.1)
    if(isConnected):
        data = False
        try:
            data = c.recv(255)
        except Exception as TimeoutException:
            pass
        if data:
            raw = data.decode(FORMAT)
            print("Read from socket:", raw)
            cmd = raw.rsplit(":")
            print("Command: [" + cmd[0] + "]")
            if cmd[0]=="reset":
                print("Resetting...")
                machine.reset()
            if cmd[0]=="read":
                sendConfigFile()
            if cmd[0]=="save":
                parseSave()
       
    try:
        r, w, err = select.select((s,), (), (), .001)
    except select.error:
        s.close()
        isConnected = False
        print("connection error.  Aborting..")
        sys.exit()
    if r:
        for readable in r:
            c, addr = s.accept()
            connectCount += 1
            timeoutCount = 0
            recvCount = 0
            print("Connected to :", addr[0], ':', addr[1])
            print("Connection number: ", connectCount)
            c.settimeout(.01)
            blink(3,.15)
            isConnected = True

s.close()

team1LED.value(0)
team2LED.value(0)
blockingTimer.deinit()
for sensor in sensors:
    sensor.irq(handler=None)

print("Sensors Deactivated.")

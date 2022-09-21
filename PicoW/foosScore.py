#Copyright 2022 Hugh Garner
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

#v1.0 09/20/2022

import network
import secretsHP
import secretsHome
import config
import time
import sys
import socket
import select
from machine import Pin
from machine import Timer

FORMAT = 'utf-8'
LED = Pin("LED",Pin.OUT)
isConnected = False

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
        blockingTimer = Timer(period = DELAY_TIME, mode = Timer.ONE_SHOT, callback = timerDone)
        sensorStates[idx] = 0

    for sensor in sensors:
        sensor.irq(handler=sensorInterrupt)

def sendScore(c,teamAndPin):
    global isConnected
    msg = "Team"+teamAndPin+"\r\n"
    try:
        c.send(msg.encode(FORMAT))
    except Exception as ex:
        if(type(ex).__name__=="OSError"):
            print("Socket disconnected.")
        else:
            print(type(ex).__name__,"exception in [sendScore] function: ",ex.args)
        print("Closing socket.")
        c.close()
        isConnected = False

host       = config.HOST
port       = config.PORT
SENSOR1    = config.SENSOR1
SENSOR2    = config.SENSOR2
SENSOR3    = config.SENSOR3
LED1       = config.LED1
LED2       = config.LED2
DELAY_TIME = config.DELAY_TIME

print("Configuration:")
print("HOST:    ",host)
print("PORT:    ",port)
print("SENSOR1: ",SENSOR1)
print("SENSOR2: ",SENSOR2)
print("SENSOR3: ",SENSOR3)
print("LED1:    ",LED1)
print("LED2:    ",LED2)

if SENSOR1 + SENSOR2 + SENSOR3 < 1:
    print("Not enough sensors configured in config.py.  Aborting.")
    sys.exit()
if ((SENSOR1 == SENSOR2) or (SENSOR2 == SENSOR3) or (LED1 == LED2)):
    print("ERROR: Two Pins are the same in config.py.  Aborting.")
    sys.exit()
if ((SENSOR1 == LED1) or (SENSOR2 == LED1) or (SENSOR3 == LED1)):
    print("ERROR: Sensor and LED1 have same pin in config.py. Aborting.")
    sys.exit()
if ((SENSOR1 == LED2) or (SENSOR2 == LED2) or (SENSOR3 == LED2)):
    print("ERROR: Sensor and LED2 have same pin in config.py. Aborting.")
    sys.exit()

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
while (wlan.isconnected()==False):
    print("Establishing wifi connection with: ",secretsHP.SSID)
    wlan.connect(secretsHP.SSID, secretsHP.PASSWORD)
    blink(10,.25)
    time.sleep(3)
    if(wlan.isconnected()==False):
        print("Trying wifi connection with: ",secretsHome.SSID)
        wlan.connect(secretsHome.SSID, secretsHome.PASSWORD)
        blink(10,.25)
        time.sleep(3)

blink(2,.5)
host = wlan.ifconfig()[0]
print("host ip = ",host)
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
        print("Could not bind "+host+":"+port)
        sys.exit()
print("Socket bound")
s.listen(1)

blinks=5
duration=.25
blink(blinks,duration)

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

blinks=3
duration=.5
allBlink(blinks,duration)
isConnected = False

print("Sensors Active.")

connectCount = 0

while True:
    if teamScored[0]:
        teamScored[0] = False
        print("Team 1 Scored so send to live stream - Pin: " + str(sensorPinNbr))
        if(isConnected):
            sendScore(c,"1,"+str(sensorPinNbr))
    elif teamScored[1]:
        teamScored[1] = False
        print("Team 2 Scored so send to live stream - Pin: " + str(sensorPinNbr))
        if(isConnected):
            sendScore(c,"2,"+str(sensorPinNbr))
    time.sleep(.1)

    try:
        r, w, err = select.select((s,), (), (), .001)
    except select.error:
        s.close()
        print("connection error.  Aborting..")
        sys.exit()
    if r:
        for readable in r:
            c, addr = s.accept()
            connectCount += 1
            print("Connected to :", addr[0], ':', addr[1])
            print("Connection number: ",connectCount)
            blink(3,.25)
            isConnected = True

s.close()

team1LED.value(0)
team2LED.value(0)
blockingTimer.deinit()
for sensor in sensors:
    sensor.irq(handler=None)

print("Sensors Deactivated.")

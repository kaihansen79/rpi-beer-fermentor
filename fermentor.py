#!/usr/bin/python3

import time, os, json
import RPi.GPIO as GPIO
import requests
import uuid
from datetime import datetime

# gpio vars
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(18, GPIO.OUT)
GPIO.output(18, GPIO.LOW)

# TODO: make contents of this file a dict and start storing ES IP there
with open('settings.json', 'r') as lf:
    settings = json.load(lf)
    print('settings: ' + str(settings))

    desiredTemperature = settings['desiredTemp']
    esIp = settings['elasticDbIp']
    print('desiredTemp: ' + str(desiredTemperature) + ' | esIp: ' + esIp)

headers = { 'Content-Type': 'application/json' }
relayState = 0
lastTemp = 0

while True:
    tempfile = open("/sys/bus/w1/devices/28-051680360fff/w1_slave")
    thetext = tempfile.read()
    tempfile.close()
    tempdata = thetext.split("\n")[1].split(" ")[9]
    temperature = float(tempdata[2:])
    temperature = (temperature/1000)*1.8+32
   
    if temperature > desiredTemperature+0.05 and relayState == 1:
        # turn off relay
        print ('relay off')
        GPIO.output(18, GPIO.LOW)
        relayState = 0
            
    elif temperature < desiredTemperature-0.05 and relayState == 0:
        # turn on relay
        print ('relay on')
        GPIO.output(18, GPIO.HIGH)
        relayState = 1

    log_uuid = str(uuid.uuid1())
    date_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    data = { 'currentTemp': temperature, 'relayState': relayState, 'date_time': date_time }
    json_data = json.dumps(data)

    try:
        r = requests.put('http://' + esIp + ':9200/fermentor-' + str(datetime.now().year) + '/_doc/' + log_uuid, data=json_data, headers=headers)
        print(str(r.status_code))
    except Exception as e:
        print('error in try: ' + str(e))

    time.sleep(30)

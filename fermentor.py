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

with open('settings.json', 'r') as lf:
    settings = json.load(lf)
    desiredTemperature = settings['desiredTemp']
    esIp = settings['elasticDbIp']
    relayState = settings['relayState']

headers = { 'Content-Type': 'application/json' }
def sendToEs(ct, rs):
    log_uuid = str(uuid.uuid1())
    date_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    data = { 'currentTemp': ct, 'relayState': rs, 'date_time': date_time }
    json_data = json.dumps(data)
    try:
        r = requests.put('http://' + esIp + ':9200/fermentor-' + str(datetime.now().year) + '/_doc/' + log_uuid, data=json_data, headers=headers)
    except Exception as e:
        print('error in try: ' + str(e))
    print('currentTemp: ' + str(ct) + ' | relayState: ' + str(rs))

while True:
    tempfile = open("/sys/bus/w1/devices/28-051680360fff/w1_slave")
    thetext = tempfile.read()
    tempfile.close()
    tempdata = thetext.split("\n")[1].split(" ")[9]
    temperature = float(tempdata[2:])
    temperature = (temperature/1000)*1.8+32

    if temperature > desiredTemperature+0.025:
        # turn off relay
        print ('relay off')
        GPIO.output(18, GPIO.LOW)
        relayState = 0

    elif temperature < desiredTemperature-0.025:
        # turn on relay
        print ('relay on')
        GPIO.output(18, GPIO.HIGH)
        relayState = 1

    with open('settings.json', 'w') as lf:
        settings['relayState'] = relayState
        json.dump(settings, lf)

    sendToEs(temperature, relayState)
    time.sleep(15)

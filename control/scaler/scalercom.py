#!/usr/bin/env python3
# coding: utf-8
#

import RPi.GPIO as GPIO
import datetime
import time

from bottle import route, run
from bottle import get, post, request
from bottle import template


#gStart = 2
#gStop  = 22
#gReset = 5
gStart = 3
gStop  = 23
gReset = 6
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(gStart, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(gStop,  GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(gReset, GPIO.OUT, initial=GPIO.LOW)

@route('/')
def index():

    act = request.query.action
    
    if act=="start":
        GPIO.output(gStart, 1)
        time.sleep(0.01)
        GPIO.output(gStart, 0)

    if act=="stop":
        GPIO.output(gStop, 1)
        time.sleep(0.01)
        GPIO.output(gStop, 0)

    if act=="reset":
        GPIO.output(gReset, 1)
        time.sleep(0.01)
        GPIO.output(gReset,0)
        
    now = str(datetime.datetime.today())[:19]
    return template('index',now=now)

run(host='0.0.0.0', port=8080, debug=True)


#!/usr/bin/env python3
# coding: utf-8
#

# ============ HEADERS ==============
# basic
import datetime
import json
import time

# for bottle
from bottle import route, run
from bottle import get, post, request
from bottle import template
from bottle import static_file

# Static file
@get("/static/<filepath:re:.*\.css>")
def css(filepath):
    return static_file(filepath, root="static/")

# ============ FUNCTIONS ==============
def set_value(ser,com,val):
    command = "d" + com + " " + val + "\r\n"
    ser.write(command.encode())
    c = ser.readline()
    print(c)
    c = ser.readline()
    print(c)
    ser.write(("abs"+com+"\r\n").encode())
    c = ser.readline()
    print(c)

def read_value(ser,com):
    ser.write(("r"+com+"\r\n").encode())
    while True :
        c = ser.readline().decode().rstrip("\r\n")
        print(c)
        if c.find("PC"+com) > 0 :
            line = c.find('=')+1
            return int(c[line:])

def save_data():
    file = open("tgt_position.json","w")
    json.dump(cc,file)
    file.close()

def read_data():
    file = open("tgt_position.json","r")
    cc = json.load(file)
    file.close()
    return cc

# ============ SERIAL SETUP ==============
import serial

ser0 = serial.Serial("/dev/ttyUSB0",timeout=3)
ser0.flushInput()
ser0.write("v 100\r\n".encode())
time.sleep(0.02)
print(ser0.readline().decode().rstrip("\r\n"))
print(ser0.readline().decode().rstrip("\r\n"))
time.sleep(0.02)
ser0.write("vs 100\r\n".encode())
time.sleep(0.02)
print(ser0.readline().decode().rstrip("\r\n"))
print(ser0.readline().decode().rstrip("\r\n"))
time.sleep(0.02)
ser0.write("v2 100\r\n".encode())
time.sleep(0.02)
print(ser0.readline().decode().rstrip("\r\n"))
print(ser0.readline().decode().rstrip("\r\n"))
time.sleep(0.02)
ser0.write("vs2 100\r\n".encode())
time.sleep(0.02)
print(ser0.readline().decode().rstrip("\r\n"))
print(ser0.readline().decode().rstrip("\r\n"))
time.sleep(0.02)

ser1 = serial.Serial("/dev/ttyUSB1",timeout=3)
ser0.flushInput()
ser1.write("v 100\r\n".encode())
time.sleep(0.02)
print(ser1.readline().decode().rstrip("\r\n"))
print(ser1.readline().decode().rstrip("\r\n"))
time.sleep(0.02)
ser1.write("vs 100\r\n".encode())
time.sleep(0.02)
print(ser1.readline().decode().rstrip("\r\n"))
print(ser1.readline().decode().rstrip("\r\n"))
time.sleep(0.02)

cc = {}

cc["pos_ge"] = read_value(ser1,"")
cc["pos_si"] = read_value(ser0,"2")

cc["set_ge"]  = cc["pos_ge"] 
cc["set_si"]  = cc["pos_si"]

ang = read_value(ser0,"1")
sang = ""
if float(ang) > 0:
    sang ="+"
cc["pos_rot"] = sang + str(float(ang)/20.)
cc["set_rot"] = str(float(ang)/20.)

# ============ BOTTLE.py ==============
tgt_pos = read_data()
cc.update(tgt_pos)

# ============ BOTTLE.py ==============

# --- main page
@route('/')
def index():

    cc["now"] = str(datetime.datetime.today())[:19]
    return template('index.html',**cc)

# --- post
@post('/')
def post_index():
    
    a = request.forms.get("action")
    print(a)

    # ===== Si Rotation =====
    # --- move
    if a == "move_rot" :
        angle = request.forms.get("rot")
        cc["set_rot"] = angle
        
        sign = ""
        if angle[0:1] == "-":
            sign = "-"
            angle = angle[1:]
        elif angle[0:1] == "+":
            sign = "+"
            angle = angle[1:]

        angle = sign + str(int(float(angle)*20.))
        set_value(ser0,"1",angle)
        
    # --- read
    if a == "read_rot":
        ang = read_value(ser0,"1")
        sang = ""
        if float(ang) > 0:
            sang = "+"
        cc["pos_rot"] = sang + str(float(ang)/20.)

    # --- stop
    if a == "stop_rot":
        ser0.write("s\r\n".encode())
        print(ser0.readline().decode().rstrip("\r\n"))
        
    # ===== Target =====
    # --- Si Target
    if a == "tSir" :
        cc["pos_si"] = read_value(ser0,"2")
    if a == "tSi0" :
        set_value(ser0,"2",cc["tSi0"])
    if a == "tSi1" :
        set_value(ser0,"2",cc["tSi1"])
    if a == "tSi2" :
        set_value(ser0,"2",cc["tSi2"])
    if a == "tSi3" :
        set_value(ser0,"2",cc["tSi3"])
        
    # --- Ge Target
    if a == "tGer" :
        cc["pos_ge"] = read_value(ser1,"")
    if a == "tGe0" :
        set_value(ser1,"",cc["tGe0"])
    if a == "tGe1" :
        set_value(ser1,"",cc["tGe1"])
    if a == "tGe2" :
        set_value(ser1,"",cc["tGe2"])
    if a == "tGe3" :
        set_value(ser1,"",cc["tGe3"])
    if a == "tGe4" :
        set_value(ser1,"",cc["tGe4"])
        
    
        
    # ===== return =====
    cc["now"] = str(datetime.datetime.today())[:19]
    return template('index.html',**cc)



run(host='0.0.0.0', port=8008, debug=True)


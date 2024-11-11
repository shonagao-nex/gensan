import serial
import time
import re

def ReadPosition(ser):
    while True:
        status = 1
        position = -99999
        ser.write(b'r1\r\n')
        time.sleep(0.02)
        while True:
            response = ser.readline().decode().rstrip("\r\n")
            match_moving   = re.search(r'Move = (\d)', response)
            match_position = re.search(r'PC  = (\d+)', response)
            if response == '':
                print("Success")
                break
            if "Syntax error" in response:
                print("Syntax Error")
                break

            if match_moving:
                status = int(match_moving.group(1))
                if status == 1:
                    print("Moving", end=', ')
                elif status == 0:
                    pass
            if match_position:
                position = int(match_position.group(1))
                print("Position = {}".format(position))
        if status == 0:
            break
        elif status == 1:
            time.sleep(1)

def GoPosition(ser, num):
    command = "d1 {}\r\n".format(num)
    ser.write(command.encode())
    ReadLine(ser)
    ser.write(b'abs1\r\n')
    ReadLine(ser)
    ReadPosition(ser)

def ReadLine(ser):
    time.sleep(0.02)
    while True:
        response = ser.readline().decode().rstrip("\r\n")
        if response == '':
            print("Success")
            break
        if "Syntax error" in response:
            print("Syntax Error")
            break

def ReadOutput(ser):
    time.sleep(0.02)
    while True:
        response = ser.readline().decode().rstrip("\r\n")
        if response == '':
            break
        print(response)


try:
    ser = serial.Serial('/dev/ttyUSB1', 9600, timeout=0.02)
    ser.flushInput()
    print("************************************")
    print("* Welcome to target controller for *")
    print("* ---------  Ge  Ge  Ge  --------- *")
    print("************************************")
    ser.write(b'v1 100\r\n')
    ReadLine(ser)
    ser.write(b'vs1 100\r\n')
    ReadLine(ser)
    ReadPosition(ser)

except serial.SerialException as e:
    print(f"Connection Error: {e}")
    ser.close()
    exit()

while True:
    command = input("Command (or type help): ")
    if command == 'exit':
        ser.close()
        break
    elif command == 'pos':
        ReadPosition(ser)
    elif command == 'goEmpty':
        GoPosition(ser,0)
    elif command == 'goScreen':
        GoPosition(ser,690)
    elif command == 'goSm':
        GoPosition(ser,1010)
    elif command == 'goW':
        GoPosition(ser,1340)
    elif command == 'goAl':
        GoPosition(ser,1150)
    elif command.startswith('goPos'):
        parts = command.split()
        if len(parts) == 2 and parts[1].isdigit():
            GoPosition(ser, int(parts[1]))
        else:
            print("Error: Invalid command format. Use 'goPos <number>'.")
    elif command == 'help':
        print("pos       :  Read current position")
        print("goEmpty   :  Go to an empty target")
        print("goScreen  :  Go to the BaS screen target")
        print("goSm      :  Go to the Samarium target")
        print("goW       :  Go to the Tungsten target")
        print("goAl      :  Go to the Aluminum target")
        print("goPos num :  Go to a certain position")
#        print("resetPos  :  Reset position to 0")
        print("help      :  This help")
        print("exit      :  Exit this script")
    else:
        print("unknown command, see help")


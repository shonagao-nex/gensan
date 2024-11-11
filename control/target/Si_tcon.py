import serial
import time
import re

def ReadPosition(ser):
    while True:
        status = 1
        position = -99999
        ser.write(b'r2\r\n')
        time.sleep(0.02)
        while True:
            response = ser.readline().decode().rstrip("\r\n")
            match_moving   = re.search(r'Move = (\d)', response)
            match_position = re.search(r'PC2 = (\d+)', response)
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

def ReadAngle(ser):
    while True:
        status = 1
        position = -99999
        ser.write(b'r1\r\n')
        time.sleep(0.02)
        while True:
            response = ser.readline().decode().rstrip("\r\n")
            match_moving   = re.search(r'Move = (\d)', response)
            match_position = re.search(r'PC1 = (\d+)', response)
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
                position = int(match_position.group(1)) / 20
                print("Angle = {:.1f} degrees".format(position))
        if status == 0:
            break
        elif status == 1:
            time.sleep(1)
    return position

def GoPosition(ser, num):
    command = "d2 {}\r\n".format(num)
    ser.write(command.encode())
    ReadLine(ser)
    ser.write(b'abs2\r\n')
    ReadLine(ser)
    ReadPosition(ser)

def GoAngle(ser, num):
    current_angle = ReadAngle(ser)
    if (current_angle < 0 and num > 0) or (current_angle > 0 and num < 0):
        response = input("Warning: You are attempting to move to an angle with a different sign. Continue? Y/n: ")
        if response.lower() != 'y':
            print("Operation cancelled.")
            return
    if abs(num) < 300:
        response = input("Warning: The angle is less than 15 deg. This may be too small. Continue? Y/n: ")
        if response.lower() != 'y':
            print("Operation cancelled.")
            return
    command = "d1 {}\r\n".format(num)
    ser.write(command.encode())
    ReadLine(ser)
    ser.write(b'abs1\r\n')
    ReadLine(ser)
    angle = ReadAngle(ser)

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
    time.sleep(0.01)

def ReadOutput(ser):
    time.sleep(0.02)
    while True:
        response = ser.readline().decode().rstrip("\r\n")
        if response == '':
            break
        print(response)


try:
    ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=0.02)
    ser.flushInput()
    print("************************************")
    print("* Welcome to target controller for *")
    print("* ---------  Si  Si  Si  --------- *")
    print("************************************")
    ser.write(b'v1 100\r\n')
    ReadLine(ser)
    ser.write(b'vs1 100\r\n')
    ReadLine(ser)
    ser.write(b'v2 100\r\n')
    ReadLine(ser)
    ser.write(b'vs2 100\r\n')
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
    elif command == 'ang':
        angle = ReadAngle(ser)
    elif command == 'goEmpty':
        GoPosition(ser,0)
    elif command == 'goScreen':
        GoPosition(ser,500)
    elif command == 'goAu1':
        GoPosition(ser,830)
    elif command == 'goAu2':
        GoPosition(ser,1150)
    elif command.startswith('goPos'):
        parts = command.split()
        if len(parts) == 2 and parts[1].isdigit():
            GoPosition(ser, int(parts[1]))
        else:
            print("Error: Invalid command format. Use 'goPos <number>'.")
    elif command.startswith('goAng'):
        parts = command.split()
        angle = int(parts[1]) * 20
        GoAngle(ser, angle)
#        if len(parts) == 2 and parts[1].isdigit():
#            angle = int(parts[1]) * 20
#            GoAngle(ser, angle)
#        else:
#            print("Error2: Invalid command format. Use 'goAng <number>'.")
    elif command == 'help':
        print("pos       :  Read current position")
        print("ang       :  Read current angle")
        print("goEmpty   :  Go to an empty target")
        print("goScreen  :  Go to the BaS screen target")
        print("goAu1     :  Go to the Upper Au target")
        print("goAu2     :  Go to the Lower Au target")
        print("goPos num :  Go to a certain position")
        print("goAng num :  Go to certain angles, 0.2deg unit in minimum")
#        print("resetPos  :  Reset position to 0")
        print("help      :  This help")
        print("exit      :  Exit this script")
    else:
        print("unknown command, see help")


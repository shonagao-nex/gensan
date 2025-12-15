import serial
import time
import re
import os
import atexit
import datetime

try:
    import readline
except Exception:
    readline = None

HISTORY_FILE = os.path.expanduser("~/.Si_tcon.history")
LOG_FILE     = os.path.expanduser("~/.Si_tcon.log")

def setup_history():
    if readline is None:
        return
    try:
        readline.read_history_file(HISTORY_FILE)
    except FileNotFoundError:
        pass
    except Exception:
        pass

    try:
        readline.set_history_length(1000)
    except Exception:
        pass

    def save_history():
        try:
            readline.write_history_file(HISTORY_FILE)
        except Exception:
            pass

    atexit.register(save_history)

def log_command(cmd: str):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{ts}\t{cmd}\n")
    except Exception:
        pass

setup_history()



def ReadPosition(ser):
    while True:
        status = 1
        position = -99999
        ser.write(b'r2\r\n')
        time.sleep(0.02)
        while True:
            response = ser.readline().decode().rstrip("\r\n")
            match_moving   = re.search(r'Move = (\d)', response)
            match_position = re.search(r'PC2 = (-?\d+)', response)
            if response == '':
                print("Position Readout Success")
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
                print("Position = {} step, {:.1f} mm".format(position, float(position) / 10))
        if status == 0:
            break
        elif status == 1:
            time.sleep(1)
    return position



def ReadAngle(ser):
    while True:
        status = 1
        position = -99999
        ser.write(b'r1\r\n')
        time.sleep(0.02)
        while True:
            response = ser.readline().decode().rstrip("\r\n")
            match_moving   = re.search(r'Move = (\d)', response)
            match_position = re.search(r'PC1 = (-?\d+)', response)
            if response == '':
                print("Angle Readout Success")
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
                print("Angle = {} step, {:.1f} deg".format(position, float(position) / 20))
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
    position = ReadPosition(ser)



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
    if num > 0:
        command = "d1 +{}\r\n".format(num)
    else:
        command = "d1 {}\r\n".format(num)
    ser.write(command.encode())
    ReadLine(ser)
    ser.write(b'abs1\r\n')
    ReadLine(ser)
    angle = ReadAngle(ser)



def ResetPos(ser):
    command = "rtncr2\r\n"
    ser.write(command.encode())
    ReadLine(ser)
    position = ReadPosition(ser)



def ResetAng(ser):
    command = "rtncr1\r\n"
    ser.write(command.encode())
    ReadLine(ser)
    angle = ReadAngle(ser)



def ReadLine(ser):
    time.sleep(0.02)
    while True:
        response = ser.readline().decode().rstrip("\r\n")
        if response == '':
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
    position = ReadPosition(ser)
    angle    = ReadAngle(ser)

    while True:
        command = input("Command (or type help): ")
        log_command(command)
        if command == 'exit':
            ser.close()
            break
        elif command == 'pos':
            position = ReadPosition(ser)
        elif command == 'ang':
            angle = ReadAngle(ser)
        elif command == 'goEmpty':
            GoPosition(ser, 0)
        elif command == 'goScreen':
            GoPosition(ser, 520)
        elif command == 'goAu1':
            GoPosition(ser, 850)
        elif command == 'goAu2':
            GoPosition(ser, 1170)
        elif command.startswith('goPos'):
            parts = command.split()
            if len(parts) == 2:
                try:
                    position = int(parts[1])
                    GoPosition(ser, position)
                except ValueError:
                    print("Error: arg[1] must be an integer value.")
            else:
                print("Error: Invalid command format. Use 'goPos <number>'.")
        elif command.startswith('goAng'):
            parts = command.split()
            if len(parts) == 2:
                try:
                    angle = int(float(parts[1]) * 20)
                    GoAngle(ser, angle)
                except ValueError:
                    print("Error: arg[1] must be a numeric value.")
            else:
                print("Error: Invalid command format. Use 'goAng <number>'.")
        elif command == 'resetPos':
            ResetPos(ser)
        elif command == 'resetAng':
            ResetAng(ser)
        elif command == 'help':
            print("pos        :  Read current position")
            print("ang        :  Read current angle")
            print("goEmpty    :  Go to an empty target")
            print("goScreen   :  Go to the BaS screen target")
            print("goAu1      :  Go to the Upper Au target")
            print("goAu2      :  Go to the Lower Au target")
            print("goPos step :  Go to a certain position (1 step = 0.1 mm)")
            print("goAng deg  :  Go to certain angles, 0.05 deg unit in minimum")
            # print("resetPos  :  Reset position to 0")
            print("help      :  This help")
            print("exit      :  Exit this script")
        else:
            print("unknown command, see help")

except serial.SerialException as e:
    print(f"Connection Error: {e}")
    exit()

except KeyboardInterrupt:
    print("\nKeyboard Interrupt detected. Closing serial connection.")
    ser.close()
    print("Serial connection closed. Exiting program.")
    exit()

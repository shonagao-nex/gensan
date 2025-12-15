import serial
import time
import re
import os
import atexit
import datetime

import sys
import fcntl
import termios

try:
    import readline
except Exception:
    readline = None

HISTORY_FILE = os.path.expanduser("~/.Si_tcon.history")
LOG_FILE     = os.path.expanduser("~/.Si_tcon.log")

# ロックファイル（同一ユーザー運用）
LOCK_FILE    = os.path.expanduser("~/Si_tcon.lock")

# ソフトリミット
POS_MIN, POS_MAX = 0, 1300
ANG_MIN, ANG_MAX = -2000, 2000  # step

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

# ----- single instance lock -----
_lock_fp = None  # keep reference

def ensure_single_instance():
    """
    既に同スクリプトが動いていたら警告して終了。
    flockはプロセス終了で自動解放されるので、異常終了にも強い。
    """
    global _lock_fp
    _lock_fp = open(LOCK_FILE, "a+")
    try:
        fcntl.flock(_lock_fp.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        pid_txt = ""
        try:
            _lock_fp.seek(0)
            pid_txt = _lock_fp.read().strip()
        except Exception:
            pass

        msg = "WARNING: Si_tcon.py is already running"
        if pid_txt:
            msg += f" (PID={pid_txt})"
        print(msg + ". Exit.")
        sys.exit(1)

    # ロック取得できたのでPIDを書いておく（表示用）
    try:
        _lock_fp.seek(0)
        _lock_fp.truncate()
        _lock_fp.write(str(os.getpid()))
        _lock_fp.flush()
        os.fsync(_lock_fp.fileno())
    except Exception:
        pass

def ask_yes_no(prompt: str) -> bool:
    ans = input(prompt).strip().lower()
    return ans == "y"

def read_lines_until_blank(ser, overall_timeout_s: float = 2.0, max_empty_reads: int = 80):
    """
    デバイスからの応答を「空行で終端」と仮定して読み切る。
    - 全体タイムアウト
    - 連続空読み(b'')が続く場合も異常として扱う
    """
    t0 = time.time()
    empty_reads = 0
    lines = []
    while True:
        if time.time() - t0 > overall_timeout_s:
            raise TimeoutError("Serial read timed out (no response termination).")

        raw = ser.readline()  # bytes
        if raw == b'':
            empty_reads += 1
            if empty_reads >= max_empty_reads:
                raise TimeoutError("Serial read timed out (device not responding).")
            continue

        empty_reads = 0
        s = raw.decode(errors="replace").rstrip("\r\n")
        if s == "":
            return lines
        lines.append(s)

def ReadLine(ser):
    time.sleep(0.02)
    try:
        lines = read_lines_until_blank(ser, overall_timeout_s=2.0)
    except TimeoutError as e:
        print(f"WARNING: {e}")
        return
    for response in lines:
        if "Syntax error" in response:
            print("Syntax Error")
            break
    time.sleep(0.01)

def ReadOutput(ser):
    time.sleep(0.02)
    try:
        lines = read_lines_until_blank(ser, overall_timeout_s=2.0)
    except TimeoutError as e:
        print(f"WARNING: {e}")
        return
    for response in lines:
        print(response)

def ReadPosition(ser):
    while True:
        status = 1
        position = -99999
        ser.write(b'r2\r\n')
        time.sleep(0.02)

        try:
            lines = read_lines_until_blank(ser, overall_timeout_s=3.0)
        except TimeoutError as e:
            raise TimeoutError(f"ReadPosition failed: {e}")

        for response in lines:
            match_moving   = re.search(r'Move = (\d)', response)
            match_position = re.search(r'PC2 = (-?\d+)', response)

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

        print("Position Readout Success")

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

        try:
            lines = read_lines_until_blank(ser, overall_timeout_s=3.0)
        except TimeoutError as e:
            raise TimeoutError(f"ReadAngle failed: {e}")

        for response in lines:
            match_moving   = re.search(r'Move = (\d)', response)
            match_position = re.search(r'PC1 = (-?\d+)', response)

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

        print("Angle Readout Success")

        if status == 0:
            break
        elif status == 1:
            time.sleep(1)

    return position

def GoPosition(ser, num):
    # 3) ソフトリミット（警告→Y/N）
    if not (POS_MIN <= num <= POS_MAX):
        if not ask_yes_no(f"Warning: Position {num} is outside [{POS_MIN}, {POS_MAX}]. Continue? Y/n: "):
            print("Operation cancelled.")
            return

    command = "d2 {}\r\n".format(num)
    ser.write(command.encode())
    ReadLine(ser)
    ser.write(b'abs2\r\n')
    ReadLine(ser)
    _ = ReadPosition(ser)

def GoAngle(ser, num):
    # 3) ソフトリミット（警告→Y/N）
    if not (ANG_MIN <= num <= ANG_MAX):
        if not ask_yes_no(f"Warning: Angle(step) {num} is outside [{ANG_MIN}, {ANG_MAX}]. Continue? Y/n: "):
            print("Operation cancelled.")
            return

    current_angle = ReadAngle(ser)
    if (current_angle < 0 and num > 0) or (current_angle > 0 and num < 0):
        if not ask_yes_no("Warning: You are attempting to move to an angle with a different sign. Continue? Y/n: "):
            print("Operation cancelled.")
            return
    if abs(num) < 300:
        if not ask_yes_no("Warning: The angle is less than 15 deg. This may be too small. Continue? Y/n: "):
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
    _ = ReadAngle(ser)

def ResetPos(ser):
    command = "rtncr2\r\n"
    ser.write(command.encode())
    ReadLine(ser)
    _ = ReadPosition(ser)

def ResetAng(ser):
    command = "rtncr1\r\n"
    ser.write(command.encode())
    ReadLine(ser)
    _ = ReadAngle(ser)

# ---------------- main ----------------
ser = None
try:
    # 多重起動禁止
    ensure_single_instance()

    # デバイス占有チェック（OSの排他で掴む）
    DEV = "/dev/ttyUSB0"
    try:
        # pyserial 3.5+ の場合
        ser = serial.Serial(DEV, 9600, timeout=0.02, exclusive=True)
    except TypeError:
        # 古いpyserial向けフォールバック
        ser = serial.Serial(DEV, 9600, timeout=0.02)
        try:
            fcntl.ioctl(ser.fileno(), termios.TIOCEXCL)
        except OSError as e:
            ser.close()
            ser = None
            print(f"WARNING: {DEV} is already in use by another process. Exit. ({e})")
            sys.exit(1)

    # 5) flushInput() -> reset_input_buffer()
    ser.reset_input_buffer()

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
                    # 入力はdeg → step(0.05deg=1step)換算
                    angle_step = int(float(parts[1]) * 20)
                    GoAngle(ser, angle_step)
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
            print("resetPos  :  Reset position to 0")
            print("resetAng  :  Reset angle to 0")
            print("help      :  This help")
            print("exit      :  Exit this script")
            print(f"[Soft limits] Position: {POS_MIN}..{POS_MAX} step, Angle: {ANG_MIN}..{ANG_MAX} step")
        else:
            print("unknown command, see help")

except serial.SerialException as e:
    print(f"WARNING: Connection Error (device busy / cannot open): {e}")
    sys.exit(1)

except KeyboardInterrupt:
    print("\nKeyboard Interrupt detected. Exiting program.")
    sys.exit(0)

except TimeoutError as e:
    print(f"ERROR: {e}")
    sys.exit(1)

except Exception as e:
    # 1) 予期せぬ例外でも落ちる前にメッセージを出す
    print(f"ERROR: Unexpected exception: {e}")
    sys.exit(1)

finally:
    # 1) どんな場合でも確実に close
    if ser is not None:
        try:
            ser.close()
            print("Serial connection closed.")
        except Exception:
            pass

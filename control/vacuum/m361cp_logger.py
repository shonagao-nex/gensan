import serial
import time
import sys
import os

# ---------------- 設定 ----------------
PORT = '/dev/ttyUSB0'
BAUDRATE = 19200
INTERVAL = 1.0     # 測定間隔 [秒]
# --------------------------------------

# --- 引数チェック ---
if len(sys.argv) != 2:
    print("Usage: python3 m361cp_logger.py logfile.csv")
    sys.exit(1)

logfile = sys.argv[1]

# --- シリアル初期化 ---
ser = serial.Serial(
    port=PORT,
    baudrate=BAUDRATE,
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    timeout=1.0
)

def send(cmd):
    ser.write((cmd + "\r").encode("ascii"))
    ser.flush()
    return ser.readline().decode("ascii", errors="ignore").strip()

# ==============================
# 初期チェック処理
# ==============================

print("Checking communication...")

# --- 通信確認 ---
test = send("#00RD")
if not test:
    print("ERROR: No response from gauge (#00RD). Check wiring and settings.")
    ser.close()
    sys.exit(1)

print("Communication OK. Response:", test)

# --- HV状態確認 ---
hv = send("#00IG")
if hv == "1":
    print("Cold Cathode already ON.")
elif hv == "0":
    print("Cold Cathode is OFF -> Trying to turn ON...")
    send("#00IG1")
    time.sleep(1.0)

    hv = send("#00IG")
    if hv != "1":
        print("ERROR: Failed to turn ON Cold Cathode.")
        ser.close()
        sys.exit(1)
    print("Cold Cathode turned ON successfully.")
else:
    print("ERROR: Unknown Cold Cathode status:", hv)
    ser.close()
    sys.exit(1)

# --- ログファイル生成（なければ） ---
if not os.path.exists(logfile):
    with open(logfile, "w") as f:
        f.write("Timestamp,Pressure(Pa),ColdCathode\n")

# ==============================
# ログ本体
# ==============================

try:
    while True:
        now = time.strftime("%Y-%m-%d %H:%M:%S")

        rd = send("#00RD")
        pressure = "NaN"
        if rd:
            try:
                pressure = f"{float(rd):.3e}"
            except ValueError:
                pressure = rd

        ig = send("#00IG")
        if ig == "1":
            cc = "ON"
        elif ig == "0":
            cc = "OFF"
        else:
            cc = ig if ig else "UNKNOWN"

        with open(logfile, "a") as f:
            f.write(f"{now}, {pressure}, {cc}\n")

        time.sleep(INTERVAL)

except KeyboardInterrupt:
    print("\nLogging stopped.")

finally:
    ser.close()

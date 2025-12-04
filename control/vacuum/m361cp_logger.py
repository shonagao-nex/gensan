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

def send(cmd: str) -> str:
    """RS-485コマンド送信 + 応答取得"""
    ser.write((cmd + "\r").encode("ascii"))
    ser.flush()
    resp = ser.readline().decode("ascii", errors="ignore").strip()
    return resp

def parse_pressure(resp: str):
    """
    応答例: '*00 1.00E+-2'
    → 値部分を抽出して float に変換
    """
    if not resp:
        return None, "NaN"

    parts = resp.split()
    if len(parts) < 2:
        return None, resp

    raw = parts[-1].strip()
    raw = raw.replace("E+-", "E-")  # Canon形式補正

    try:
        val = float(raw)
        return val, f"{val:.3e}"
    except ValueError:
        return None, raw

def parse_hv_status(resp: str) -> str:
    """
    応答例: '*00 HV1'
    → Cold Cathode ON/OFF 判定
    """
    if not resp:
        return "UNKNOWN"

    parts = resp.split()
    if len(parts) < 2:
        return resp

    token = parts[-1]  # 'HV1' / 'HV0'

    if token.startswith("HV"):
        code = token[2:]
    else:
        return resp

    if code == "1":
        return "ON"
    elif code == "0":
        return "OFF"
    else:
        return "UNKNOWN"

# ==============================
# 起動時チェック
# ==============================

print("Checking M-361CP communication ...")

# --- 通信確認 ---
resp = send("#00RD")
p_val, p_text = parse_pressure(resp)

if not resp:
    print("ERROR: No response from gauge (#00RD).")
    ser.close()
    sys.exit(1)

print(f"Pressure response OK: {resp} -> {p_text} Pa")

# --- HV確認 ---
hv_resp = send("#00HV")
hv_status = parse_hv_status(hv_resp)
print(f"Initial HV status: {hv_resp} -> {hv_status}")

# HVがOFFならONを試みる
if hv_status == "OFF":
    print("Trying to set Cold Cathode HV ON (#00HV1)...")
    send("#00HV1")
    time.sleep(1.0)

    hv_resp2 = send("#00HV")
    hv_status2 = parse_hv_status(hv_resp2)
    print(f"After HV ON

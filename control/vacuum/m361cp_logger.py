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
    """RS485コマンド送信 + 1行受信"""
    ser.write((cmd + "\r").encode("ascii"))
    ser.flush()
    resp = ser.readline().decode("ascii", errors="ignore").strip()
    return resp

def parse_pressure(resp: str):
    """
    応答例: '*00 1.00E+-2'
    → 2番目のトークンを取り出して float に変換
    """
    if not resp:
        return None, "NaN"

    tokens = resp.split()
    if len(tokens) < 2:
        return None, resp

    raw = tokens[-1].strip()  # '1.00E+-2' など
    # 'E+-2' のような表記を 'E-2' に補正
    raw = raw.replace("E+-", "E-")

    try:
        val = float(raw)
        return val, f"{val:.3e}"
    except ValueError:
        return None, raw

def parse_hv_status(resp: str) -> str:
    """
    応答例: '*00 HV1' / '*00 HV0'
     → 'HV1' を見て ON/OFF に変換
    """
    if not resp:
        return "UNKNOWN"

    tokens = resp.split()
    if len(tokens) < 2:
        return resp

    hv_token = tokens[-1]  # 'HV1' の想定
    if hv_token.startswith("HV"):
        code = hv_token[2:]
    else:
        code = hv_token

    if code == "1":
        return "ON"
    elif code == "0":
        return "OFF"
    else:
        return resp

# ==============================
# 初期チェック処理
# ==============================

print("Checking communication with M-361CP...")

# --- 通信確認 (00RD) ---
test_resp = send("00RD")
p_val, p_text = parse_pressure(test_resp)

if p_val is None and p_text in ("NaN", ""):
    print("ERROR: No valid response from gauge (00RD).")
    print("  Raw response:", repr(test_resp))
    ser.close()
    sys.exit(1)

print(f"Communication OK. First pressure response: {test_resp}  ->  {p_text} Pa")

# --- HV状態確認 (00HV) ---
hv_resp = send("00HV")
hv_status = parse_hv_status(hv_resp)
print(f"Initial Cold Cathode HV status: {hv_resp}  ->  {hv_status}")

# OFFなら一度だけONを試みる（圧力が高いと自動的にOFFになる点に注意）
if hv_status == "OFF":
    print("Trying to turn Cold Cathode HV ON (00HV1)...")
    send("00HV1")
    time.sleep(1.0)
    hv_resp2 = send("00HV")
    hv_status2 = parse_hv_status(hv_resp2)
    print(f"After 00HV1: {hv_resp2}  ->  {hv_status2}")
    # 圧力が高くてONにならない場合もあるので、ここでは終了せずログは続行する

# --- ログファイルが無ければ作成し、ヘッダを書く ---
if not os.path.exists(logfile):
    with open(logfile, "w") as f:
        f.write("Timestamp,Pressure(Pa),ColdCathode\n")

# ==============================
# ログ本体
# ==============================

try:
    while True:
        now = time.strftime("%Y-%m-%d %H:%M:%S")

        # --- 圧力取得 ---
        rd_resp = send("00RD")
        p_val, p_text = parse_pressure(rd_resp)

        # --- HV状態取得 ---
        hv_resp = send("00HV")
        hv_status = parse_hv_status(hv_resp)

        # --- ログ1行作成 ---
        # 例: 2025-12-04 12:00:00, 1.000e-03, ON
        line = f"{now}, {p_text}, {hv_status}\n"
        with open(logfile, "a") as f:
            f.write(line)

        time.sleep(INTERVAL)

except KeyboardInterrupt:
    print("\nLogging stopped by user.")

finally:
    ser.close()

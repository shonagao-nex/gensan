import sys
import os
import csv
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.animation import FuncAnimation

# ---------------- 設定 ----------------
UPDATE_INTERVAL_MS = 1000   # 更新間隔 [ms]
# --------------------------------------

if len(sys.argv) != 2:
    print("Usage: python3 m361cp_plotter.py logfile.csv")
    sys.exit(1)

LOGFILE = sys.argv[1]

if not os.path.exists(LOGFILE):
    print(f"ERROR: Log file not found: {LOGFILE}")
    sys.exit(1)

last_mtime = 0.0
cached_times = []
cached_pressures = []
cached_cc_status = "UNKNOWN"
cached_latest_pressure = None

def read_log(logfile):
    times = []
    pressures = []
    cc_status = "UNKNOWN"
    latest_p = None

    with open(logfile, newline="") as f:
        reader = csv.reader(f)
        header = next(reader, None)

        for row in reader:
            if len(row) < 3:
                continue

            t_str = row[0].strip()
            p_str = row[1].strip()
            cc_str = row[2].strip()

            try:
                t = dt.datetime.strptime(t_str, "%Y-%m-%d %H:%M:%S")
                p = float(p_str)
            except ValueError:
                continue

            times.append(t)
            pressures.append(p)
            cc_status = cc_str
            latest_p = p

    return times, pressures, cc_status, latest_p

# ---------- グラフ設定 ----------
plt.ion()
fig, ax = plt.subplots()
ax.set_xlabel("Time")
ax.set_ylabel("Pressure [Pa]")
ax.set_yscale("log")
ax.grid(True, which="both", linestyle="--", alpha=0.5)

ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
fig.autofmt_xdate()

line, = ax.plot([], [], marker="o", linestyle="-")

status_text = ax.text(
    0.99, 0.99, "",
    transform=ax.transAxes,
    ha="right", va="top",
    fontsize=10,
    bbox=dict(facecolor="white", alpha=0.7, edgecolor="none")
)

def init():
    line.set_data([], [])
    status_text.set_text("")
    return line, status_text

def update(frame):
    global last_mtime, cached_times, cached_pressures, cached_cc_status, cached_latest_pressure

    try:
        mtime = os.path.getmtime(LOGFILE)
    except FileNotFoundError:
        return line, status_text

    if mtime == last_mtime and cached_times:
        return line, status_text

    times, pressures, cc_status, latest_p = read_log(LOGFILE)
    if not times:
        return line, status_text

    last_mtime = mtime
    cached_times = times
    cached_pressures = pressures
    cached_cc_status = cc_status
    cached_latest_pressure = latest_p

    x = mdates.date2num(times)
    y = pressures
    line.set_data(x, y)

    ax.relim()
    ax.autoscale_view()
    ax.set_ylim(1e-4, 1e3)

    # 右上テキスト更新
    if cached_latest_pressure is not None:
        p_text = f"{cached_latest_pressure:.3e} Pa"
    else:
        p_text = "UNKNOWN"

    status_text.set_text(
        f"Pressure : {p_text}\n"
        f"ColdCathode : {cached_cc_status}"
    )

    return line, status_text

ani = FuncAnimation(fig, update, init_func=init, interval=UPDATE_INTERVAL_MS, blit=False)
plt.show(block=True)

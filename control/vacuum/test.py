import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime
import sys
import os, time
from matplotlib.animation import FuncAnimation
from matplotlib.ticker import ScalarFormatter, FormatStrFormatter

# データをグローバル変数で保持
global_times = []
global_pressures = []

def read_data(filename):
    if not os.path.exists(filename):
        print(f"Error: The file '{filename}' does not exist.")
        sys.exit(1)

    times = []
    pressures = []
    with open(filename, 'r') as file:
        for line in file:
            if line.strip():
                parts = line.split()
                date_time_str = parts[0] + ' ' + parts[1]
                pressure = float(parts[2])

                time_obj = datetime.datetime.strptime(date_time_str, '%Y/%m/%d %H:%M:%S')

                times.append(time_obj)
                pressures.append(pressure)

    return times, pressures

def init():
    ln.set_data(global_times, global_pressures)
    adjust_axes(global_times, global_pressures)
    return ln,

def update(frame):
    # データ更新ロジック（この場合は既に読み込まれているデータを使用）
    ln.set_data(global_times, global_pressures)
    adjust_axes(global_times, global_pressures)
    return ln,

def adjust_axes(times, pressures):
    margin_x = 0.02 * (max(times) - min(times))
    margin_y = 0.1 * (max(pressures) - min(pressures))
    ax.set_xlim(min(times) - margin_x, max(times) + margin_x)
    ax.set_ylim(min(pressures) - margin_y, max(pressures) + margin_y)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <filename>")
        sys.exit(1)

    filename = sys.argv[1]
    global_times, global_pressures = read_data(filename)  # データをグローバル変数に読み込む

    fig, ax = plt.subplots()
    ln, = ax.plot([], [], 'ro', animated=True)

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M:%S'))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.xticks(rotation=30, ha='right')

    plt.title(filename)
    plt.xlabel('Date and Time')
    plt.ylabel('Pressure (Pa)')

    plt.tight_layout()

    ani = FuncAnimation(fig, update, init_func=init, blit=True, interval=5000)
    plt.show()


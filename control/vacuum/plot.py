import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime
import sys
import os, time
from matplotlib.animation import FuncAnimation
from matplotlib.ticker import ScalarFormatter, FormatStrFormatter, LogFormatter

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
    times, pressures = read_data(filename)
    ln.set_data(times, pressures)
    set_scale(pressures)
    return ln,

def update(frame):
    times, pressures = read_data(filename)
    ln.set_data(times, pressures)
    set_scale(pressures)
    adjust_axes(times, pressures)
    return ln,

def set_scale(pressures):
#    ax.set_yscale('linear')
#    ax.yaxis.set_major_formatter(FormatStrFormatter('%.3e'))
    ax.set_yscale('log')
#    ax.yaxis.set_major_formatter(ScalarFormatter())
    ax.yaxis.set_major_formatter(LogFormatter())

def adjust_axes(times, pressures):
#    if times:
#        xmax = times[-1]
#        xmin = xmax - datetime.timedelta(hours=12)
#    else:
    xmin = times[0]
    xmax = datetime.datetime.now()

    if max(pressures) > 0.1:
        ymin = min(pressures) / 2
        ymax = 0.1
    else:
        ymin = min(pressures) / 2
        ymax = max(pressures) * 2

    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)

if __name__ == "__main__":
    try:
        if len(sys.argv) != 2:
            print("Usage: python script.py <filename>")
            sys.exit(1)

        filename = sys.argv[1]
        times, pressures = read_data(filename)

        fig, ax = plt.subplots()
        ln, = ax.plot(times, pressures, 'ro', animated=True)

        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M:%S'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.xticks(rotation=30, ha='right')

        plt.title(filename)
        plt.xlabel('Date and Time')
        plt.ylabel('Pressure (Pa)')

#        plt.grid(True)
        plt.tight_layout()
#        time.sleep(1)

        ani = FuncAnimation(fig, update, init_func=init, blit=True, interval=5000)
        plt.show()
    except KeyboardInterrupt:
        print("Program interrupted by user. Exiting...")
        try:
            plt.close(fig)  # Try to close the matplotlib figure to clean up resources
        except Exception as e:
            print(f"Failed to close the figure: {e}")
        sys.exit(0)


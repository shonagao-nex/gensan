import time
import threading
import datetime
import serial
import sys

READ_INTERVAL = 30   # seconds

def main(filename):
    vac = [0]
    running = [True]  # Running flag

    # Start the vacuum reading thread
    thread_vac_read = threading.Thread(target=read_vacuum, args=(vac, filename, running))
    thread_vac_read.start()

    try:
        while thread_vac_read.is_alive():
            thread_vac_read.join(timeout=1)
    except KeyboardInterrupt:
        print("Program interrupted by user, shutting down...")
        running[0] = False  # Set running flag to False
        thread_vac_read.join()  # Wait for the thread to finish

def read_vacuum(vac, filename, running):
    ser = serial.Serial("/dev/ttyUSB2", timeout=0.5)
    with open(filename, "a") as f:
        while running[0]:
            ser.write("$PRD\r".encode())
            line = ser.readline().decode()
            if line:  # Check if line is not empty
                try:
                    vac[0] = float(line[3:-1])
                    t = datetime.datetime.now()
                    output = f'{t:%Y/%m/%d %H:%M:%S}  {vac[0]:.2e} Pa'
                    print(output)
                    f.write(output + '\n')
                    f.flush()
                except ValueError:
                    print("Error processing line:", line)
            time.sleep(READ_INTERVAL)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <filename>")
        sys.exit(1)
    main(sys.argv[1])


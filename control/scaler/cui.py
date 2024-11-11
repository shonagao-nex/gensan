import RPi.GPIO as GPIO
import time
from threading import Thread, Event
import sys

# GPIOピンの設定
input_pin = 5  # GPIOピン5

# GPIOのセットアップ
GPIO.setmode(GPIO.BCM)
GPIO.setup(input_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# グローバル変数
counter = 0
start_time = None
stop_event = Event()

# エッジ検出を行うスレッド関数
def edge_detection():
    global counter, start_time
    while not stop_event.is_set():
        GPIO.wait_for_edge(input_pin, GPIO.RISING)
        if not stop_event.is_set():
            counter += 1
            elapsed_time = time.time() - start_time
            frequency = counter / elapsed_time / 10
            # カウンターと時間を上書きして表示
            sys.stdout.write(f"\rCount: {counter} /0.1nQ, Time: {elapsed_time:.3f} s, Current: {frequency:.3f} nQ/s  ")
            sys.stdout.flush()

# メイン関数
def main():
    global start_time
    start_time = time.time()
    print("Monitoring started... Press Ctrl+C to stop.")
    
    # エッジ検出スレッドを開始
    detection_thread = Thread(target=edge_detection)
    detection_thread.start()

    try:
        # Ctrl+Cが押されるまでメインスレッドはここで待機
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        # ストップイベントをセットしてスレッドを終了
        stop_event.set()
        detection_thread.join()
        print("\nMonitoring stopped.")
        GPIO.cleanup()

if __name__ == "__main__":
    main()


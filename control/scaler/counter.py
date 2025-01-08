import RPi.GPIO as GPIO
import tkinter as tk
from tkinter import font
import time

# GPIOピンの設定
input_pin = 5  # GPIOピン5

# GPIOのセットアップ
GPIO.setmode(GPIO.BCM)
GPIO.setup(input_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# GUIのセットアップ
root = tk.Tk()
root.title("GPIO Signal Counter")
root.configure(bg='white')  # 背景色を白に設定
root.geometry("400x500")  # ウィンドウの初期サイズを幅500ピクセル、高さ300ピクセルに設定
root.resizable(False, False)  # ウィンドウのサイズ変更を無効にする

# フォントの設定
app_font = font.Font(family='Arial', size=28)

# カウンターラベル
label = tk.Label(root, text="Count: 0 / 0.1nQ", font=app_font, bg='white', anchor='w')
label.pack(pady=20, fill=tk.X, padx=20)

# タイマーラベル
timer_label = tk.Label(root, text="Time: 0.000 s", font=app_font, bg='white', anchor='w')
timer_label.pack(pady=20, fill=tk.X, padx=20)

# フリクエンシーラベル
frequency_label = tk.Label(root, text="Current: 0.000 nQ/s", font=app_font, bg='white', anchor='w')
frequency_label.pack(pady=20, fill=tk.X, padx=20)

# グローバル変数
counter = 0
monitoring = False  # 監視状態
start_time = None  # スタート時間
stop_time = None  # ストップ時間
elapsed_time = 0  # 経過時間

# コールバック関数
def callback(pin):
    if monitoring:
        global counter
        counter += 1

# タイマー更新関数
def update_timer():
    global elapsed_time
    if monitoring:
        current_time = time.time()
        elapsed_time = current_time - start_time
        formatted_time = f"{elapsed_time:.3f} sec"
        timer_label.config(text=f"Time: {formatted_time}")
        update_counter()
        update_frequency()
        root.after(280, update_timer)

# フリクエンシー更新関数
def update_frequency():
    if elapsed_time > 0:
        frequency = counter / elapsed_time / 10
        frequency_label.config(text=f"Current: {frequency:.3f} nQ/s")

def update_counter():
    if elapsed_time > 0:
        label.config(text=f"Count: {counter} / 0.1nQ")

# ボタンの状態設定関数
def set_button_state(start_enabled, stop_enabled, reset_enabled):
    start_button['state'] = 'normal' if start_enabled else 'disabled'
    stop_button['state'] = 'normal' if stop_enabled else 'disabled'
    reset_button['state'] = 'normal' if reset_enabled else 'disabled'

# イベント検出の設定（デフォルトでは無効）
def start_monitoring():
    global monitoring, start_time, elapsed_time
    monitoring = True
    start_time = time.time() - elapsed_time
    update_timer()
    set_button_state(False, True, False)

def stop_monitoring():
    global monitoring, stop_time, elapsed_time
    stop_time = time.time()
    monitoring = False
    elapsed_time = stop_time - start_time  # 更新停止時の経過時間を固定
    formatted_time = f"{elapsed_time:.3f} sec"
    timer_label.config(text=f"Time: {formatted_time}")
    update_counter()
    update_frequency()
    set_button_state(True, False, True)

def reset_counters():
    global counter, start_time, stop_time, elapsed_time
    counter = 0
    start_time = None
    stop_time = None
    elapsed_time = 0
    label.config(text="Count: 0 / 0.1nQ")
    timer_label.config(text="Time: 0.000 s")
    frequency_label.config(text="Current: 0.000 nQ/s")
    set_button_state(True, False, False)

# GPIOイベント検出の設定
GPIO.remove_event_detect(input_pin)
GPIO.add_event_detect(input_pin, GPIO.RISING, callback=callback)

# ボタンの追加、色とサイズの設定
button_width = 10  # ボタンの横幅を統一
start_button = tk.Button(root, text="Start", command=start_monitoring, font=app_font, bg='#ADD8E6', width=button_width)
start_button.pack(pady=10)

stop_button = tk.Button(root, text="Stop", command=stop_monitoring, font=app_font, bg='#FFFFE0', width=button_width)
stop_button.pack(pady=10)

reset_button = tk.Button(root, text="Reset", command=reset_counters, font=app_font, bg='#FFA07A', width=button_width)
reset_button.pack(pady=10)

# 初期状態の設定
set_button_state(True, False, False)  # Start enabled, Stop and Reset disabled

# GPIOのクリーンアップ処理を行う関数
def on_closing():
    GPIO.cleanup()
    root.destroy()

# ウィンドウを閉じるイベントハンドラの設定
root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()


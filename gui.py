import tkinter as tk
from tkinter import ttk
from main import main
import threading
import matplotlib.pyplot as plt

def plot_bollinger_bands(data):
    plt.figure(figsize=(12, 6))
    plt.plot(data['time'], data['close'], label='Price', color='blue')
    plt.plot(data['time'], data['Middle Band'], label='Middle Band', color='black')
    plt.plot(data['time'], data['Upper Band'], label='Upper Band', color='red', linestyle='--')
    plt.plot(data['time'], data['Lower Band'], label='Lower Band', color='green', linestyle='--')
    plt.title('Bollinger Bands')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend()
    plt.show()

def update_progress(progress):
    progress_var.set(progress)  
    progress_bar['value'] = progress  
    win.update_idletasks()
    
def reset_progress_bar():
    progress_var.set(0)
    progress_bar['value'] = 0
    win.update_idletasks()

def run_main():
    cbb_value = cbb.get()
    def progress_callback(current_progress):
        update_progress(current_progress * 100 / 20) 
    def plot_callback(data):
        win.after(0, plot_bollinger_bands, data) 
    portfolio = main(cbb_value, update_progress=progress_callback, plot_callback=plot_callback)
    if portfolio is None or portfolio.empty:
        status_label.config(text="未抓取到數據。")  
    else:
        status_label.config(text=str(portfolio.tail(5)))
    win.after(0, reset_progress_bar)
    btn.config(state=tk.NORMAL)  

def btn_command():
    btn.config(state=tk.DISABLED)  
    status_label.config(text="數據請求中(20Day)")
    threading.Thread(target=run_main, daemon=True).start()

win = tk.Tk()
win.title("Bollinger bands simulated trading")
win.geometry("600x400")
win.maxsize(1024, 768)
win.minsize(400, 200)

win.iconbitmap("app.ico")

center_frame = tk.Frame(win)
center_frame.pack(pady=20)

lb = tk.Label(center_frame, text="BTC_USDT")
lb.pack(side="left", padx=5)

cbb = ttk.Combobox(center_frame, values=["1M","5M","15M","30M","60M","4H","8H","12H","1D"], state="readonly", width=10)
cbb.pack(side="left", padx=5)
cbb.set("15M")  

progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(win, orient='horizontal', length=286, mode='determinate', variable=progress_var)
progress_bar.pack(pady=20)

btn = tk.Button(win, text="Start", command=btn_command)
btn.pack(pady=10)

status_label = tk.Label(win, text="請選擇K線週期，並按下按鈕開始模擬布林帶策略", anchor='center')
status_label.pack(pady=5, fill='x')

win.mainloop()
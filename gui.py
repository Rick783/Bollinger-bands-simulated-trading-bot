import tkinter as tk
from tkinter import ttk
from main import main
import threading
import matplotlib.pyplot as plt

def plot_bollinger_bands(data):
    # 繪製布林帶圖表
    plt.figure(figsize=(12, 6))
    plt.plot(data['time'], data['close'], label='Price', color='blue')  # 繪製收盤價
    plt.plot(data['time'], data['Middle Band'], label='Middle Band', color='black')  # 中線
    plt.plot(data['time'], data['Upper Band'], label='Upper Band', color='red', linestyle='--')  # 上線
    plt.plot(data['time'], data['Lower Band'], label='Lower Band', color='green', linestyle='--')  # 下線
    plt.title('Bollinger Bands')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend()
    plt.show()

def update_progress(progress):
    # 更新進度條
    progress_var.set(progress)  
    progress_bar['value'] = progress  
    win.update_idletasks()  # 更新GUI
    
def reset_progress_bar():
    # 重置進度條
    progress_var.set(0)
    progress_bar['value'] = 0
    win.update_idletasks()

def run_main():
    # 執行主程序
    cbb_value = cbb.get()  # 獲取下拉選單中選擇的值
    def progress_callback(current_progress):
        update_progress(current_progress * 100 / 20)  # 計算進度百分比
    def plot_callback(data):
        win.after(0, plot_bollinger_bands, data)  # 異步繪製布林帶圖表
    portfolio = main(cbb_value, update_progress=progress_callback, plot_callback=plot_callback)
    if portfolio is None or portfolio.empty:
        status_label.config(text="未抓取到數據。")
    else:
        status_label.config(text=str(portfolio.tail(5)))  # 顯示最後五條數據
    win.after(0, reset_progress_bar)
    btn.config(state=tk.NORMAL)  # 按鈕恢復可用

def btn_command():
    # 按鈕命令函數
    btn.config(state=tk.DISABLED)  # 按鈕設為不可用
    status_label.config(text="數據請求中(20Day)")
    threading.Thread(target=run_main, daemon=True).start()  # 在新線程中運行主程序

win = tk.Tk()
win.title("Bollinger bands simulated trading")
win.geometry("600x400")
win.maxsize(1024, 768)
win.minsize(400, 200)

win.iconbitmap("app.ico")  # 設定視窗圖標
icon = tk.PhotoImage(file='app.png')  # 設定視窗圖標
win.tk.call('wm', 'iconphoto', win._w, icon)

center_frame = tk.Frame(win)  # 創建一個框架容器
center_frame.pack(pady=20)

lb = tk.Label(center_frame, text="BTC_USDT")  # 標籤顯示交易對
lb.pack(side="left", padx=5)

cbb = ttk.Combobox(center_frame, values=["1M","5M","15M","30M","60M","4H","8H","12H","1D"], state="readonly", width=10)
cbb.pack(side="left", padx=5)
cbb.set("15M")  # 預設選項

progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(win, orient='horizontal', length=286, mode='determinate', variable=progress_var)
progress_bar.pack(pady=20)

btn = tk.Button(win, text="Start", command=btn_command)
btn.pack(pady=10)

status_label = tk.Label(win, text="請選擇K線週期，並按下按鈕開始模擬布林帶策略", anchor='center')
status_label.pack(pady=5, fill='x')

win.mainloop()  # 開始事件循環

import requests
import time
from dotenv import load_dotenv
import os
import pandas as pd
import matplotlib.pyplot as plt  # 確保在這裡導入 matplotlib.pyplot
from datetime import datetime, timedelta

# 載入環境變數
load_dotenv()

# 獲取 API 金鑰和 API 密鑰
api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")

# 定義生成 PIONEX-SIGNATURE 的函數
def generate_signature(api_secret, method, path, timestamp, params=None, data=None):
    # 將查詢參數設置為鍵值對：key=value
    if params is None:
        params = {}
    params['timestamp'] = timestamp
    query_string = urlencode(sorted(params.items()))

    # 將查詢參數與 PATH 連接起來
    path_url = f"{path}?{query_string}"

    # 將 METHOD 和 PATH_URL 連接起來
    message = f"{method.upper()}{path_url}"

    # 如果有數據，將其 JSON 格式化並連接到消息中
    if data is not None:
        message += json.dumps(data, separators=(',', ':'))

    # 使用 API 密鑰和上述結果生成 HMAC SHA256 編碼，然後將其轉換為十六進制
    signature = hmac.new(api_secret.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).hexdigest()

    return signature

# 定義發送私有請求的函數
def make_private_request(method, endpoint, params=None, data=None):
    url = f"https://api.pionex.com{endpoint}"

    # 獲取當前毫秒級時間戳
    timestamp = str(int(time.time() * 1000))

    # 在參數中設置時間戳
    if params is None:
        params = {}
    params['timestamp'] = timestamp

    # 設置標頭
    headers = {
        'PIONEX-KEY': api_key,
        'PIONEX-SIGNATURE': generate_signature(api_secret, method, endpoint, timestamp, params=params, data=data),
        'Content-Type': 'application/json',
    }

    # 發送請求
    if method == 'GET':
        response = requests.get(url, headers=headers, params=params)
    elif method == 'POST':
        headers['Content-Type'] = 'application/json'
        response = requests.post(url, headers=headers, json=data, params=params)
    elif method == 'DELETE':
        response = requests.delete(url, headers=headers, json=data, params=params)
    else:
        raise ValueError(f"不支援的 HTTP 方法: {method}")

    return response.json()

# 計算布林帶
def calculate_bollinger_bands(data, window=20, num_std=2):
    """
    計算布林帶指標

    參數:
    - data: 包含 'Date' 和 'close' 欄位的 DataFrame。
    - window: 移動平均和標準差計算的窗口大小。
    - num_std: 上下軌道的標準差數量。

    返回值:
    - 添加了 'Middle Band', 'Upper Band', 和 'Lower Band' 欄位的 DataFrame。
    """
    data['close'] = pd.to_numeric(data['close'])

    # 計算中軌
    data['Middle Band'] = data['close'].rolling(window=window).mean()

    # 計算標準差
    data['Std Dev'] = data['close'].rolling(window=window).std()

    # 計算上下軌道
    data['Upper Band'] = data['Middle Band'] + (num_std * data['Std Dev'])
    data['Lower Band'] = data['Middle Band'] - (num_std * data['Std Dev'])

    return data

#獲取K線數據
def get_recent_klines(symbol, interval):
    # 計算現在的時間和 30 天前的時間
    end_time = datetime.now()
    start_time = end_time - timedelta(days=30)

    # 將時間轉換為毫秒級的時間戳
    start_time_ms = int(start_time.timestamp() * 1000)
    end_time_ms = int(end_time.timestamp() * 1000)


    endpoint = 'https://api.pionex.com/api/v1/market/klines'
    params = {
        'symbol': symbol,
        'interval': interval,
        'startTime': start_time_ms,
        'endTime': end_time_ms
    }
    # 發送 GET 請求
    response = requests.get(endpoint, params=params)
    # 檢查響應狀態碼
    if response.status_code == 200:
        # 解析 JSON 響應
        data = response.json()
        # 獲取 K 線數據
        klines = data.get('data', {}).get('klines', [])
        # 將 K 線數據轉換為 DataFrame
        df = pd.DataFrame(klines, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
        df['time'] = pd.to_datetime(df['time'], unit='ms')
        return df

# 繪製布林帶圖表
def plot_bollinger_bands(data):
    """
    繪製布林帶圖表

    參數:
    - data: 包含 'Date', 'Close', 'Middle Band', 'Upper Band', 'Lower Band' 欄位的 DataFrame。
    """
    plt.figure(figsize=(12, 6))
    plt.plot(data['time'], data['close'], label='Bitcoin Price', color='blue')
    plt.plot(data['time'], data['Middle Band'], label='Middle Band', color='black')
    plt.plot(data['time'], data['Upper Band'], label='Upper Band', color='red', linestyle='--')
    plt.plot(data['time'], data['Lower Band'], label='Lower Band', color='green', linestyle='--')
    plt.title('Bitcoin Bollinger Bands')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend()
    plt.show()
    print(data['close'].describe())
    print(data.isnull().sum())
    print(data.describe())

# 獲取最近 30 天的比特幣 K 線數據，計算布林帶，並繪製圖表
def main():
    symbol = 'BTC_USDT'  # 比特幣/美元交易對
    interval = '1D'  # 日K線

    # 獲取 K 線數據
    klines_df = get_recent_klines(symbol, interval)

    # 計算布林帶
    bollinger_bands_df = calculate_bollinger_bands(klines_df)

    # 繪製布林帶圖表
    plot_bollinger_bands(bollinger_bands_df)

if __name__ == "__main__":
    main()
    
import requests
import time
import json
import hashlib
import hmac
from urllib.parse import urlencode
from dotenv import load_dotenv
import os

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
        response = requests.post(url, headers=headers, json=data, params=params )
    elif method == 'DELETE':
        response = requests.delete(url, headers=headers, json=data, params=params)
    else:
        raise ValueError(f"不支援的 HTTP 方法: {method}")

    # 打印生成的簽名、消息和服務器時間戳
    # print(f"生成的簽名: {headers['PIONEX-SIGNATURE']}")
    # print(f"生成的消息: {method.upper()}{url}?{urlencode(sorted(params.items()))}")
    # print(f"服務器時間戳: {response.json().get('timestamp')}")

    return response.json()

# 定義發送公共請求的函數
endpoint = "/api/v1/trade/order"

# 發送 POST 請求
response = make_private_request('GET', '/api/v1/trade/allOrders', params={'symbol': 'BTC_USDT', 'limit': 1})

# 打印請求結果
# print(response)

# 定義獲取當前價格的函數
def get_current_price(symbol):
    endpoint = 'https://api.pionex.com/api/v1/market/tickers'
    params = {'symbol': symbol}
    response = requests.get(endpoint, params=params)
    if response.status_code == 200:
        data = response.json()
        tickers = data.get('data', {}).get('tickers', [])
        for ticker in tickers:
            if ticker['symbol'] == symbol:
                return ticker.get('close')
    return None

current_price = get_current_price('BTC_USDT')
print(f"BTC:{current_price}")
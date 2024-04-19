import requests
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta

def get_recent_klines(symbol, interval):
    # 初始化儲存K線數據的列表
    all_klines = []
    # 設置查詢的結束時間為當前時間
    end_time = datetime.now()
    # 設置開始時間為20天前
    start_time = end_time - timedelta(days=20)
    # 轉換時間為毫秒單位，以符合API要求
    end_time_ms = int(end_time.timestamp() * 1000)
    start_time_ms = int(start_time.timestamp() * 1000)
    # API端點URL
    endpoint = 'https://api.pionex.com/api/v1/market/klines'
    # 使用迴圈來逐步抓取所有所需的K線數據
    while True:
        params = {
            'symbol': symbol,
            'interval': interval,
            'endTime': end_time_ms
        }
        response = requests.get(endpoint, params=params, timeout=300)
        if response.status_code == 200:
            data = response.json()
            klines = data.get('data', {}).get('klines', [])
            if not klines:
                print("未抓取到更多數據。")
                break
            all_klines.extend(klines)
            last_time_ms = int(klines[-1]['time'])
            end_time_ms = last_time_ms - 1
            if last_time_ms <= start_time_ms:
                break
        else:
            print(f"請求失敗，狀態碼：{response.status_code}")
            break
    if all_klines:
        df = pd.DataFrame(all_klines)
        df = df.iloc[::-1].reset_index(drop=True)
        df['time'] = pd.to_datetime(df['time'], unit='ms')
        df = df[df['time'] >= pd.to_datetime(start_time_ms, unit='ms')]
        for column in ['open', 'close', 'high', 'low', 'volume']:
            df[column] = pd.to_numeric(df[column].str.replace(',', ''), errors='coerce')
        return df
    else:
        return pd.DataFrame()

def validate_data(df):
    # 檢查缺失值
    missing_values = df.isnull().sum()
    print("檢查缺失值:\n", missing_values)
    print("\n檢查數據類型:")
    print(df.dtypes)
    df['time'] = pd.to_datetime(df['time'])
    df = df.sort_values(by='time')
    time_diff = df['time'].diff().dropna()
    unexpected_gaps = time_diff[time_diff > pd.Timedelta(days=1)]
    if not unexpected_gaps.empty:
        print("\n時間連續性問題：存在超過一天的空隙。")
    else:
        print("\n時間連續性檢查：通過。")
    print("\n基本統計數據：")
    print(df[['open', 'high', 'low', 'close', 'volume']].describe())

def calculate_bollinger_bands(data, window=20, num_std=2):
    # 計算布林帶
    data['close'] = pd.to_numeric(data['close'], errors='coerce')
    data['Middle Band'] = data['close'].rolling(window=window).mean()
    data['Std Dev'] = data['close'].rolling(window=window).std()
    data['Upper Band'] = data['Middle Band'] + (data['Std Dev'] * num_std)
    data['Lower Band'] = data['Middle Band'] - (data['Std Dev'] * num_std)
    return data

def plot_bollinger_bands(data):
    # 繪製布林帶圖表
    plt.figure(figsize=(12, 6))
    plt.plot(data['time'], data['close'], label='price', color='blue')
    plt.plot(data['time'], data['Middle Band'], label='mid', color='black')
    plt.plot(data['time'], data['Upper Band'], label='up', color='red', linestyle='--')
    plt.plot(data['time'], data['Lower Band'], label='low', color='green', linestyle='--')
    plt.title('bollinger bands')
    plt.xlabel('date')
    plt.ylabel('price')
    plt.legend()
    plt.show()

def bollinger_strategy(bollinger_bands_df):
    # 布林帶交易策略
    signals = pd.DataFrame(index=bollinger_bands_df.index)
    signals['signals'] = 0
    state = 0
    for i in range(len(bollinger_bands_df)):
        if bollinger_bands_df.loc[i, 'close'] < bollinger_bands_df.loc[i, 'Lower Band'] and state != 1:
            signals.loc[i, 'signals'] = 1
            state = 1
        elif bollinger_bands_df.loc[i, 'close'] > bollinger_bands_df.loc[i, 'Upper Band'] and state == 1:
            signals.loc[i, 'signals'] = -1
            state = 0
    signals['positions'] = signals['signals'].diff()
    return signals

def simulate_bollinger_strategy(bollinger_bands_df, signals, initial_capital=10000.0):
    # 模擬布林帶策略交易
    portfolio = pd.DataFrame(index=bollinger_bands_df.index)
    portfolio['holdings'] = 0.0
    portfolio['cash'] = initial_capital
    portfolio['total'] = initial_capital
    position = 0
    cash = initial_capital
    for index, row in bollinger_bands_df.iterrows():
        if index not in signals.index:
            continue
        signal = signals.loc[index, 'signals']
        price = row['close']
        transaction_cost_percent = 0.001
        if signal == 1 and cash > 0:
            units_bought = (cash / (1 + transaction_cost_percent)) / price
            transaction_cost = cash - (units_bought * price)
            cash -= (units_bought * price + transaction_cost)
            position += units_bought
        elif signal == -1 and position > 0:
            sell_revenue = position * price
            transaction_cost = sell_revenue * transaction_cost_percent
            net_revenue = sell_revenue - transaction_cost
            cash += net_revenue
            position = 0
        portfolio.loc[index, 'cash'] = cash
        portfolio.loc[index, 'holdings'] = position * price
        portfolio.loc[index, 'total'] = portfolio.loc[index, 'cash'] + portfolio.loc[index, 'holdings']
    return portfolio

def main():
    # 主函數
    symbol = 'BTC_USDT'
    interval = '15M'
    klines_df = get_recent_klines(symbol, interval)
    if klines_df.empty:
        print("未抓取到數據。")
        return
    bollinger_bands_df = calculate_bollinger_bands(klines_df)
    bollinger_bands_df = bollinger_bands_df.reset_index(drop=True)
    plot_bollinger_bands(bollinger_bands_df)
    signals = bollinger_strategy(bollinger_bands_df)
    portfolio = simulate_bollinger_strategy(bollinger_bands_df, signals)
    print(portfolio.tail(5))

if __name__ == "__main__":
    main()

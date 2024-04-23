import requests
import pandas as pd
from datetime import datetime, timedelta
from requests.exceptions import RequestException

def get_recent_klines(symbol, interval, update_progress, total_requests):
    all_klines = []
    end_time = datetime.now()
    start_time = end_time - timedelta(days=20)
    end_time_ms = int(end_time.timestamp() * 1000)
    start_time_ms = int(start_time.timestamp() * 1000)
    endpoint = 'https://api.pionex.com/api/v1/market/klines'
    params = {
        'symbol': symbol,
        'interval': interval,
        'endTime': end_time_ms
    }

    for request_count in range(total_requests):
        try:
            response = requests.get(endpoint, params=params, timeout=300)
            if response.status_code == 200:
                data = response.json()
                klines = data.get('data', {}).get('klines', [])
                if not klines:
                    print(f"No more data available after {request_count} requests.")
                    break
                all_klines.extend(klines)
                last_time_ms = int(klines[-1]['time'])
                end_time_ms = last_time_ms - 1
                params['endTime'] = end_time_ms
                update_progress(request_count + 1)
            else:
                print(f"Request failed with status code {response.status_code}: {response.text}")
                break

            if last_time_ms <= start_time_ms:
                print("Reached the start of the data range.")
                break

        except RequestException as e:
            print(f"An error occurred: {e}")
            break

    if all_klines:
        df = pd.DataFrame(all_klines)
        df = df.iloc[::-1].reset_index(drop=True)
        df['time'] = pd.to_datetime(df['time'], unit='ms')
        df = df[df['time'] >= pd.to_datetime(start_time_ms, unit='ms')]
        for column in ['open', 'close', 'high', 'low', 'volume']:
            df[column] = pd.to_numeric(df[column], errors='coerce')
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

def main(cbb_value, update_progress=None, plot_callback=None):
    if cbb_value not in ["1M","5M","15M","30M","60M","4H","8H","12H","1D"]:
        cbb_value = '15M'
    symbol = 'BTC_USDT'
    interval = cbb_value
    total_requests = 20
    klines_df = get_recent_klines(symbol, interval, update_progress, total_requests)

    if klines_df.empty:
        print("未抓取到數據。")
        return
    bollinger_bands_df = calculate_bollinger_bands(klines_df)
    bollinger_bands_df = bollinger_bands_df.reset_index(drop=True)
    if plot_callback:
        plot_callback(bollinger_bands_df) #通過回調函數傳遞繪製圖表數據
    signals = bollinger_strategy(bollinger_bands_df)
    portfolio = simulate_bollinger_strategy(bollinger_bands_df, signals)
    
    return portfolio
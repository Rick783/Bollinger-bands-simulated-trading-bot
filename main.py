import requests
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta

def get_recent_klines(symbol, interval):
    all_klines = []
    end_time = datetime.now()
    start_time = end_time - timedelta(days=20)
    end_time_ms = int(end_time.timestamp() * 1000)
    start_time_ms = int(start_time.timestamp() * 1000)
    endpoint = 'https://api.pionex.com/api/v1/market/klines'
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
                print("No more data fetched.")
                break
            all_klines.extend(klines)
            last_time_ms = int(klines[-1]['time'])
            end_time_ms = last_time_ms - 1
            if last_time_ms <= start_time_ms:
                break
        else:
            print(f"Request failed, status code: {response.status_code}")
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
    missing_values = df.isnull().sum()
    print("Missing values check:\n", missing_values)
    print("\nData type check:")
    print(df.dtypes)
    df['time'] = pd.to_datetime(df['time'])
    df = df.sort_values(by='time')
    time_diff = df['time'].diff().dropna()
    unexpected_gaps = time_diff[time_diff > pd.Timedelta(days=1)]
    if not unexpected_gaps.empty:
        print("\nTime continuity issue: There are gaps more than 1 day.")
    else:
        print("\nTime continuity check: Passed.")
    print("\nBasic statistics:")
    print(df[['open', 'high', 'low', 'close', 'volume']].describe())

def calculate_bollinger_bands(data, window=20, num_std=2):
    data['close'] = pd.to_numeric(data['close'], errors='coerce')
    data['Middle Band'] = data['close'].rolling(window=window).mean()
    data['Std Dev'] = data['close'].rolling(window=window).std()
    data['Upper Band'] = data['Middle Band'] + (data['Std Dev'] * num_std)
    data['Lower Band'] = data['Middle Band'] - (data['Std Dev'] * num_std)
    return data

def plot_bollinger_bands(data):
    plt.figure(figsize=(12, 6))
    plt.plot(data['time'], data['close'], label='Price', color='blue')
    plt.plot(data['time'], data['Middle Band'], label='Mid', color='black')
    plt.plot(data['time'], data['Upper Band'], label='Up', color='red', linestyle='--')
    plt.plot(data['time'], data['Lower Band'], label='Low', color='green', linestyle='--')
    plt.title('Bollinger Bands')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend()
    plt.show()

def bollinger_strategy(bollinger_bands_df):
    signals = pd.DataFrame(index=bollinger_bands_df.index)
    signals['signals'] = 0
    state = 0  # 0: no position, 1: bought, -1: sold

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
    portfolio = pd.DataFrame(index=bollinger_bands_df.index)
    portfolio['holdings'] = 0.0  # 持仓价值
    portfolio['cash'] = initial_capital  # 可用现金
    portfolio['total'] = initial_capital  # 总资产价值
    position = 0  # 当前持仓数量
    cash = initial_capital  # 现金

    for index, row in bollinger_bands_df.iterrows():
        if index not in signals.index:
            continue  # 如无信号则跳过此行

        signal = signals.loc[index, 'signals']  # 更正列名为'signals'
        price = row['close']
        transaction_cost_percent = 0.001  # 交易成本比例

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
    symbol = 'BTC_USDT'
    interval = '15M'
    klines_df = get_recent_klines(symbol, interval)
    if klines_df.empty:
        print("No data fetched.")
        return
    bollinger_bands_df = calculate_bollinger_bands(klines_df)
    bollinger_bands_df = bollinger_bands_df.reset_index(drop=True)
    plot_bollinger_bands(bollinger_bands_df)
    signals = bollinger_strategy(bollinger_bands_df)
    portfolio = simulate_bollinger_strategy(bollinger_bands_df, signals)
    print(portfolio.tail(1000))

if __name__ == "__main__":
    main()

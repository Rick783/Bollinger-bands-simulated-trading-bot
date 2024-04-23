# 加密貨幣市場分析工具

此工具用於從Pionex API獲取近期加密貨幣數據，並應用布林帶（Bollinger Bands）交易策略來分析市場趨勢，從而進行視覺化顯示和生成交易信號。

## 功能

- 從Pionex API獲取近20天的K線數據。
- 計算並繪製布林帶。
- 基於布林帶數據模擬交易策略。

## 安裝步驟

執行此工具前，您需要安裝所需的Python庫。您可以使用pip進行安裝：

```bash
pip install requirements.txt
```
## 使用方法

1. 確認Python環境已安裝上述庫。
2. 請運行 `gui.py` 文件。
3. 在命令行中運行該腳本：

```bash
python gui.py
```
## 主要功能介紹

- `get_recent_klines`: 此函數用於從API獲取指定交易對的K線數據。
- `validate_data`: 檢查數據中的缺失值和時間連續性。
- `calculate_bollinger_bands`: 計算布林帶。
- `plot_bollinger_bands`: 繪製布林帶圖表。
- `bollinger_strategy`: 執行基於布林帶的交易策略。
- `simulate_bollinger_strategy`: 模擬布林帶交易策略的執行情況，並計算可能的盈虧。

## 注意事項

確保您有權訪問 [Pionex API](https://api.pionex.com/api/v1/market/klines)，並且API在您的地區是可用的。

## 開發者信息

此工具由[Rick783]開發，用於學術和研究目的。對於因使用此工具造成的任何直接或間接損失，開發者不承擔責任。
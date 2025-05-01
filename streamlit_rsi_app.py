# 📦 安裝所需套件
!pip install yfinance ta --quiet

# 📊 匯入套件
import yfinance as yf
import pandas as pd
import ta

# ⏱ 下載最近 3 個月的黃金歷史資料（每天）
data = yf.download("GC=F", period="3mo", interval="1d")

# ✅ 檢查資料是否抓取成功
if data.empty:
    print("❌ 無法取得黃金資料，請稍後再試")
else:
    # 計算 RSI（14日）
    close_prices = data["Close"]
    rsi = ta.momentum.RSIIndicator(close_prices, window=14).rsi()
    
    # 顯示最近一筆 RSI 值
    latest_rsi = rsi.dropna().iloc[-1]
    print(f"✅ 最新黃金 RSI（14日）為：{latest_rsi:.2f}")

import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import matplotlib.pyplot as plt
from datetime import date, timedelta

# 設定中文/英文標籤對照與替代商品清單
asset_map = {
    "Gold (GC=F)": ["GC=F", "GLD", "IAU"],
    "Silver (SI=F)": ["SI=F", "SLV"],
    "Oil (CL=F)": ["CL=F", "USO"],
    "Bitcoin (BTC-USD)": ["BTC-USD"],
    "Apple (AAPL)": ["AAPL"]
}

# 自動修正日期與資料下載函式
def safe_download(ticker_list, start_date, end_date):
    max_date = date.today() - timedelta(days=2)
    if end_date > max_date:
        end_date = max_date

    for code in ticker_list:
        try:
            df = yf.download(code, start=start_date, end=end_date)
            if not df.empty:
                df["symbol_used"] = code
                return df
        except Exception as e:
            print(f"⚠ Error downloading {code}: {e}")
    return None

# RSI 策略信號產生
def apply_rsi_strategy(df, rsi_period=14, lower=30, upper=70):
    df["RSI"] = ta.momentum.RSIIndicator(df["Close"], window=rsi_period).rsi()
    df["Signal"] = 0
    df.loc[df["RSI"] < lower, "Signal"] = 1
    df.loc[df["RSI"] > upper, "Signal"] = -1
    df["Strategy Return"] = df["Signal"].shift(1) * df["Close"].pct_change()
    df["Cumulative Return"] = (1 + df["Strategy Return"]).cumprod()
    return df

# UI 部分
st.title("📈 Multi-Asset RSI Strategy Dashboard")
asset_label = st.selectbox("Select Asset", list(asset_map.keys()))
start_date = st.date_input("Start Date", value=date(2023, 1, 1))
end_date = st.date_input("End Date", value=date(2025, 4, 30))

# 資料下載
df = safe_download(asset_map[asset_label], start_date, end_date)

if df is None:
    st.error("Unable to retrieve data. Try different dates or assets.")
else:
    actual_symbol = df["symbol_used"].iloc[0]
    st.success(f"Data loaded: {actual_symbol} — from {df.index.min().date()} to {df.index.max().date()}")

    df = apply_rsi_strategy(df)

    # 顯示 RSI 圖
    st.subheader("🔍 RSI Signal")
    fig1, ax1 = plt.subplots(figsize=(10, 4))
    ax1.plot(df.index, df["RSI"], label="RSI", color="blue")
    ax1.axhline(70, color="red", linestyle="--")
    ax1.axhline(30, color="green", linestyle="--")
    ax1.set_title("RSI Indicator")
    st.pyplot(fig1)

    # 顯示績效報酬圖
    st.subheader("💰 Strategy Backtest Performance")
    fig2, ax2 = plt.subplots(figsize=(10, 4))
    ax2.plot(df.index, df["Cumulative Return"], label="Strategy Return", color="orange")
    ax2.set_title("Cumulative Strategy Return")
    st.pyplot(fig2)

    # 顯示策略統計
    st.subheader("📊 Strategy Summary")
    final_return = df["Cumulative Return"].iloc[-1]
    win_rate = (df["Strategy Return"] > 0).sum() / df["Strategy Return"].count()
    st.markdown(f"""
    - **Final cumulative return**: `{final_return:.2f}x`
    - **Win rate**: `{win_rate:.2%}`
    """)


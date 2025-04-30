import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import matplotlib.pyplot as plt
from datetime import date, timedelta

# 商品映射表與備援代碼
asset_map = {
    "Gold (GC=F)": ["GC=F", "GLD", "IAU"],
    "Silver (SI=F)": ["SI=F", "SLV"],
    "Oil (CL=F)": ["CL=F", "USO"],
    "Bitcoin (BTC-USD)": ["BTC-USD"],
    "Apple (AAPL)": ["AAPL"]
}

# 自動回補資料函數：最多往前追溯 lookback_days
def safe_download_v2(ticker_list, start_date, end_date, lookback_days=7):
    max_allowed = date.today() - timedelta(days=2)
    end_date = min(end_date, max_allowed)

    for offset in range(lookback_days):
        try_end = end_date - timedelta(days=offset)
        for symbol in ticker_list:
            try:
                df = yf.download(symbol, start=start_date, end=try_end)
                if not df.empty:
                    df["symbol_used"] = symbol
                    return df, try_end
            except Exception as e:
                print(f"⚠ Error downloading {symbol} on {try_end}: {e}")
    return None, None

# RSI 策略邏輯
def apply_rsi_strategy(df, rsi_period=14, lower=30, upper=70):
    df["RSI"] = ta.momentum.RSIIndicator(df["Close"], window=rsi_period).rsi()
    df["Signal"] = 0
    df.loc[df["RSI"] < lower, "Signal"] = 1
    df.loc[df["RSI"] > upper, "Signal"] = -1
    df["Strategy Return"] = df["Signal"].shift(1) * df["Close"].pct_change()
    df["Cumulative Return"] = (1 + df["Strategy Return"]).cumprod()
    return df

# 📊 UI 部分
st.title("📊 Multi-Asset RSI Strategy Dashboard")
asset_label = st.selectbox("Select Asset", list(asset_map.keys()))
start_date = st.date_input("Start Date", value=date(2023, 1, 1))
end_date = st.date_input("End Date", value=date(2025, 4, 30))

# 資料下載（最多往前補 7 天）
df, adjusted_end = safe_download_v2(asset_map[asset_label], start_date, end_date, lookback_days=7)

if df is None:
    st.error("❌ No valid data available. Please adjust asset or date range.")
else:
    actual_symbol = df["symbol_used"].iloc[0]
    st.success(f"✅ Loaded data from `{actual_symbol}` up to `{adjusted_end}`")

    # RSI 策略與報酬計算
    df = apply_rsi_strategy(df)

    # RSI 指標圖
    st.subheader("🔍 RSI Indicator")
    fig1, ax1 = plt.subplots(figsize=(10, 4))
    ax1.plot(df.index, df["RSI"], label="RSI", color="blue")
    ax1.axhline(70, color="red", linestyle="--")
    ax1.axhline(30, color="green", linestyle="--")
    ax1.set_title("RSI Values")
    st.pyplot(fig1)

    # 策略報酬圖
    st.subheader("💰 Strategy Cumulative Return")
    fig2, ax2 = plt.subplots(figsize=(10, 4))
    ax2.plot(df.index, df["Cumulative Return"], label="Strategy Return", color="orange")
    ax2.set_title("Backtest Performance")
    st.pyplot(fig2)

    # 策略統計摘要
    st.subheader("📈 Strategy Summary")
    final_return = df["Cumulative Return"].iloc[-1]
    win_rate = (df["Strategy Return"] > 0).sum() / df["Strategy Return"].count()
    st.markdown(f"""
    - **Final cumulative return**: `{final_return:.2f}x`
    - **Win rate**: `{win_rate:.2%}`
    """)

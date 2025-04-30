import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import matplotlib.pyplot as plt
from datetime import date, timedelta

# 商品與備援代碼表
asset_map = {
    "Gold (GC=F)": ["GC=F", "GLD", "IAU"],
    "Silver (SI=F)": ["SI=F", "SLV"],
    "Oil (CL=F)": ["CL=F", "USO"],
    "Bitcoin (BTC-USD)": ["BTC-USD"],
    "Apple (AAPL)": ["AAPL"]
}

# 智慧資料下載函數：最多往前 N 天補資料，並回傳嘗試日誌
def safe_download_v3(ticker_list, start_date, end_date, lookback_days=7):
    max_allowed = date.today() - timedelta(days=2)
    end_date = min(end_date, max_allowed)

    attempt_log = []

    for offset in range(lookback_days):
        try_end = end_date - timedelta(days=offset)
        for symbol in ticker_list:
            try:
                df = yf.download(symbol, start=start_date, end=try_end)
                attempt_log.append((symbol, try_end, not df.empty))
                if not df.empty:
                    df["symbol_used"] = symbol
                    return df, try_end, attempt_log
            except Exception as e:
                attempt_log.append((symbol, try_end, False))
    return None, None, attempt_log

# RSI 策略
def apply_rsi_strategy(df, rsi_period=14, lower=30, upper=70):
    df["RSI"] = ta.momentum.RSIIndicator(df["Close"], window=rsi_period).rsi()
    df["Signal"] = 0
    df.loc[df["RSI"] < lower, "Signal"] = 1
    df.loc[df["RSI"] > upper, "Signal"] = -1
    df["Strategy Return"] = df["Signal"].shift(1) * df["Close"].pct_change()
    df["Cumulative Return"] = (1 + df["Strategy Return"]).cumprod()
    return df

# Streamlit UI
st.title("📊 Multi-Asset RSI Strategy Dashboard")
asset_label = st.selectbox("Select Asset", list(asset_map.keys()))
start_date = st.date_input("Start Date", value=date(2023, 1, 1))
end_date = st.date_input("End Date", value=date(2025, 4, 30))

# 資料讀取 + 錯誤日誌
df, adjusted_end, attempt_log = safe_download_v3(asset_map[asset_label], start_date, end_date)

if df is None:
    st.error("❌ No valid data found after checking all fallback symbols and dates.")
    with st.expander("📋 Debug Log: Download Attempts"):
        for sym, d, success in attempt_log:
            st.text(f"→ {sym} on {d}: {'✅ Success' if success else '❌ Empty'}")
else:
    actual_symbol = df["symbol_used"].iloc[0]
    st.success(f"✅ Data loaded from `{actual_symbol}`, up to `{adjusted_end}`")

    # RSI 策略分析
    df = apply_rsi_strategy(df)

    st.subheader("🔍 RSI Indicator")
    fig1, ax1 = plt.subplots(figsize=(10, 4))
    ax1.plot(df.index, df["RSI"], label="RSI", color="blue")
    ax1.axhline(70, color="red", linestyle="--")
    ax1.axhline(30, color="green", linestyle="--")
    ax1.set_title("RSI Values")
    st.pyplot(fig1)

    st.subheader("💰 Strategy Cumulative Return")
    fig2, ax2 = plt.subplots(figsize=(10, 4))
    ax2.plot(df.index, df["Cumulative Return"], label="Strategy Return", color="orange")
    ax2.set_title("Backtest Performance")
    st.pyplot(fig2)

    st.subheader("📈 Strategy Summary")
    final_return = df["Cumulative Return"].iloc[-1]
    win_rate = (df["Strategy Return"] > 0).sum() / df["Strategy Return"].count()
    st.markdown(f"""
    - **Final cumulative return**: `{final_return:.2f}x`
    - **Win rate**: `{win_rate:.2%}`
    """)

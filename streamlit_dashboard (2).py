import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import matplotlib.pyplot as plt
from datetime import date, timedelta

# 商品映射表與替代代碼列表
asset_map = {
    "Gold (GC=F)": ["GC=F", "GLD", "IAU"],
    "Silver (SI=F)": ["SI=F", "SLV"],
    "Oil (CL=F)": ["CL=F", "USO"],
    "Bitcoin (BTC-USD)": ["BTC-USD"],
    "Apple (AAPL)": ["AAPL"]
}

# 自動安全資料下載函數：避免未來日期，支援備援代碼
def safe_download(ticker_list, start_date, end_date, safety_days=2):
    max_end = date.today() - timedelta(days=safety_days)
    if end_date > max_end:
        end_date = max_end

    for symbol in ticker_list:
        try:
            df = yf.download(symbol, start=start_date, end=end_date)
            if not df.empty:
                df["symbol_used"] = symbol
                return df, end_date
        except Exception as e:
            print(f"⚠ Error fetching {symbol}: {e}")
    return None, None

# RSI 策略計算
def apply_rsi_strategy(df, rsi_period=14, lower=30, upper=70):
    df["RSI"] = ta.momentum.RSIIndicator(df["Close"], window=rsi_period).rsi()
    df["Signal"] = 0
    df.loc[df["RSI"] < lower, "Signal"] = 1
    df.loc[df["RSI"] > upper, "Signal"] = -1
    df["Strategy Return"] = df["Signal"].shift(1) * df["Close"].pct_change()
    df["Cumulative Return"] = (1 + df["Strategy Return"]).cumprod()
    return df

# 🖥️ Streamlit 介面
st.title("📊 Multi-Asset RSI Strategy Dashboard")
asset_label = st.selectbox("Select Asset", list(asset_map.keys()))
start_date = st.date_input("Start Date", value=date(2023, 1, 1))
end_date = st.date_input("End Date", value=date(2025, 4, 30))

# 📥 下載資料（含自動日期修正與備援代碼）
df, adjusted_end = safe_download(asset_map[asset_label], start_date, end_date)

# ❌ 無法取得資料處理
if df is None:
    st.error("❌ Unable to retrieve data. Try adjusting the date range or choosing a different asset.")
else:
    actual_symbol = df["symbol_used"].iloc[0]
    st.success(f"✅ Data loaded from `{actual_symbol}`, up to `{adjusted_end}`")

    # 🧠 RSI 策略計算
    df = apply_rsi_strategy(df)

    # RSI 指標圖
    st.subheader("🔍 RSI Signal")
    fig1, ax1 = plt.subplots(figsize=(10, 4))
    ax1.plot(df.index, df["RSI"], label="RSI", color="blue")
    ax1.axhline(70, color="red", linestyle="--")
    ax1.axhline(30, color="green", linestyle="--")
    ax1.set_title("RSI Indicator")
    st.pyplot(fig1)

    # 策略報酬圖
    st.subheader("💰 Strategy Backtest Performance")
    fig2, ax2 = plt.subplots(figsize=(10, 4))
    ax2.plot(df.index, df["Cumulative Return"], label="Strategy Return", color="orange")
    ax2.set_title("Cumulative Strategy Return")
    st.pyplot(fig2)

    # 報酬統計
    st.subheader("📈 Strategy Summary")
    final_return = df["Cumulative Return"].iloc[-1]
    win_rate = (df["Strategy Return"] > 0).sum() / df["Strategy Return"].count()
    st.markdown(f"""
    - **Final cumulative return**: `{final_return:.2f}x`
    - **Win rate**: `{win_rate:.2%}`
    """)

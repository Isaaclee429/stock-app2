# streamlit_dashboard.py
import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import ta
from datetime import datetime

st.set_page_config(page_title="多商品 RSI 策略分析儀表板", layout="wide")
st.title("📊 多商品 RSI 策略分析儀表板")

symbols = {
    "黃金 (GC=F)": "GC=F",
    "天然氣 (NG=F)": "NG=F",
    "比特幣 (BTC-USD)": "BTC-USD",
    "Apple (AAPL)": "AAPL",
    "Tesla (TSLA)": "TSLA",
    "QQQ (納指ETF)": "QQQ"
}

symbol_name = st.sidebar.selectbox("選擇商品：", list(symbols.keys()))
symbol = symbols[symbol_name]

@st.cache_data
def load_data(symbol):
    df = yf.download(symbol, start="2023-01-01", end=datetime.today().strftime('%Y-%m-%d'))
    if df.empty or "Close" not in df.columns:
        return pd.DataFrame()
    df.dropna(subset=["Close"], inplace=True)
    df["rsi"] = ta.momentum.RSIIndicator(close=df["Close"]).rsi()
    df["signal"] = "HOLD"
    df.loc[df["rsi"] < 30, "signal"] = "BUY"
    df.loc[df["rsi"] > 70, "signal"] = "SELL"
    return df

data = load_data(symbol)
if data.empty:
    st.warning("⚠ 此商品資料無效或不可用，請稍後再試或更換商品。")
    st.stop()

st.subheader(f"📈 {symbol_name} 價格與 RSI")
st.line_chart(data[["Close", "rsi"]])

latest_price = data["Close"].iloc[-1]
latest_rsi = data["rsi"].iloc[-1]
latest_signal = data["signal"].iloc[-1]

st.metric("最新價格", f"${latest_price:.2f}")
st.metric("RSI 值", f"{latest_rsi:.2f}")
st.metric("建議操作", latest_signal)

# RSI 策略模擬績效
initial_cash = 10000
cash = initial_cash
position = 0.0
portfolio = []

for i in range(1, len(data)):
    signal = data["signal"].iloc[i]
    price = data["Close"].iloc[i]
    if signal == "BUY" and cash > 0:
        position = cash / price
        cash = 0
    elif signal == "SELL" and position > 0:
        cash = position * price
        position = 0
    total_value = cash + position * price
    portfolio.append(total_value)

data = data.iloc[1:]
data["portfolio"] = portfolio

total_return = (portfolio[-1] - initial_cash) / initial_cash * 100
st.subheader("💰 RSI 策略模擬資產變化")
fig, ax = plt.subplots()
ax.plot(data.index, data["portfolio"], label="資產價值")
ax.set_title(f"{symbol_name} RSI 策略模擬績效")
ax.set_ylabel("資產 (USD)")
ax.grid(True)
st.pyplot(fig)

st.success(f"策略總報酬：{total_return:.2f}%")

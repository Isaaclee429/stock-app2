# streamlit_dashboard.py
import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import ta
from datetime import datetime
from fpdf import FPDF

st.set_page_config(page_title="多商品 RSI 策略分析儀表板", layout="wide")
st.title("📊 多商品 RSI 策略分析儀表板（更新日期：2025/04/02）")

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
    today = datetime.today()
    df = yf.download(symbol, start="2023-01-01", end=today.strftime('%Y-%m-%d'))
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
    df.dropna(inplace=True)
    if df.empty:
        return df, None
    close_series = df["Close"].squeeze()
    df["rsi"] = ta.momentum.RSIIndicator(close=close_series).rsi()
    df["signal"] = "HOLD"
    df.loc[df["rsi"] < 30, "signal"] = "BUY"
    df.loc[df["rsi"] > 70, "signal"] = "SELL"
    last_date = df.index[-1].strftime('%Y-%m-%d')
    return df, last_date

# 讀取資料
data, last_date = load_data(symbol)

st.subheader(f"📈 {symbol_name} 價格與 RSI")

if data.empty:
    st.warning("⚠ 無法取得該商品的最新資料，請選擇其他商品或稍後再試。")
    st.info(f"最後可用資料日期：{last_date if last_date else '無'}")
    st.stop()

try:
    if "Close" in data.columns and "rsi" in data.columns:
        st.line_chart(data[["Close", "rsi"]])
    else:
        st.warning("⚠ 資料中缺少 'Close' 或 'rsi' 欄位，請稍後再試或選擇其他商品。")
except Exception as e:
    st.error(f"❌ 畫圖失敗：{e}")

latest_price = data["Close"].iloc[-1]
latest_rsi = data["rsi"].iloc[-1] if "rsi" in data.columns else None
latest_signal = data["signal"].iloc[-1] if "signal" in data.columns else "HOLD"

st.metric("最新價格", f"${latest_price:.2f}")
if latest_rsi:
    st.metric("RSI 值", f"{latest_rsi:.2f}")
st.metric("建議操作", latest_signal)

initial_cash = 10000
cash = initial_cash
position = 0.0
portfolio = []

for i in range(1, len(data)):
    signal = data["signal"].iloc[i] if "signal" in data.columns else "HOLD"
    price = data["Close"].iloc[i]
    if signal == "BUY" and cash > 0:
        position = cash / price
        cash = 0
    elif signal == "SELL" and position > 0:
        cash = position * price
        position = 0
    total_value = cash + position * price
    portfolio.append(total_value)

if portfolio:
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

    if st.button("📄 下載 PDF 報告"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="RSI 策略分析報告", ln=True, align='C')
        pdf.cell(200, 10, txt=f"商品：{symbol_name}", ln=True)
        pdf.cell(200, 10, txt=f"價格：${latest_price:.2f}", ln=True)
        pdf.cell(200, 10, txt=f"RSI：{latest_rsi:.2f}", ln=True)
        pdf.cell(200, 10, txt=f"建議操作：{latest_signal}", ln=True)
        pdf.cell(200, 10, txt=f"策略總報酬：{total_return:.2f}%", ln=True)
        filename = f"report_{symbol}.pdf"
        pdf.output(filename)
        with open(filename, "rb") as f:
            st.download_button("⬇️ 點此下載報告", f, file_name=filename)# streamlit_dashboard.py
import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import ta
from datetime import datetime, timedelta
from fpdf import FPDF

st.set_page_config(page_title="多商品 RSI 策略分析儀表板", layout="wide")
st.title("📊 多商品 RSI 策略分析儀表板（更新日期：2025/04/02）")

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
    today = datetime.today()
    df = yf.download(symbol, start="2023-01-01", end=today.strftime('%Y-%m-%d'))
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
    df.dropna(inplace=True)
    close_series = df["Close"].squeeze()
    df["rsi"] = ta.momentum.RSIIndicator(close=close_series).rsi()
    df["signal"] = "HOLD"
    df.loc[df["rsi"] < 30, "signal"] = "BUY"
    df.loc[df["rsi"] > 70, "signal"] = "SELL"
    return df

data = load_data(symbol)

st.subheader(f"📈 {symbol_name} 價格與 RSI")
try:
    if "Close" in data.columns and "rsi" in data.columns:
        st.line_chart(data[["Close", "rsi"]])
    else:
        st.warning("⚠ 資料中缺少 'Close' 或 'rsi' 欄位，請稍後再試或選擇其他商品。")
except Exception as e:
    st.error(f"❌ 畫圖失敗：{e}")

if not data.empty and "Close" in data.columns:
    latest_price = data["Close"].iloc[-1]
    latest_rsi = data["rsi"].iloc[-1] if "rsi" in data.columns else None
    latest_signal = data["signal"].iloc[-1] if "signal" in data.columns else "HOLD"

    st.metric("最新價格", f"${latest_price:.2f}")
    if latest_rsi is not None:
        st.metric("RSI 值", f"{latest_rsi:.2f}")
    st.metric("建議操作", latest_signal)

    # 🟢 RSI 策略模擬與報酬繼續處理（可放這裡）

else:
    st.warning("⚠ 無法取得該商品的最新資料，請選擇其他商品或稍後再試。")
    st.stop()  # ❗這一行讓程式到這裡就停止，不再執行後面報表區

st.metric("最新價格", f"${latest_price:.2f}")
if latest_rsi:
    st.metric("RSI 值", f"{latest_rsi:.2f}")
st.metric("建議操作", latest_signal)

initial_cash = 10000
cash = initial_cash
position = 0.0
portfolio = []

for i in range(1, len(data)):
    signal = data["signal"].iloc[i] if "signal" in data.columns else "HOLD"
    price = data["Close"].iloc[i]
    if signal == "BUY" and cash > 0:
        position = cash / price
        cash = 0
    elif signal == "SELL" and position > 0:
        cash = position * price
        position = 0
    total_value = cash + position * price
    portfolio.append(total_value)

if portfolio:
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

    if st.button("📄 下載 PDF 報告"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="RSI 策略分析報告", ln=True, align='C')
        pdf.cell(200, 10, txt=f"商品：{symbol_name}", ln=True)
        pdf.cell(200, 10, txt=f"價格：${latest_price:.2f}", ln=True)
        pdf.cell(200, 10, txt=f"RSI：{latest_rsi:.2f}", ln=True)
        pdf.cell(200, 10, txt=f"建議操作：{latest_signal}", ln=True)
        pdf.cell(200, 10, txt=f"策略總報酬：{total_return:.2f}%", ln=True)
        filename = f"report_{symbol}.pdf"
        pdf.output(filename)
        with open(filename, "rb") as f:
            st.download_button("⬇️ 點此下載報告", f, file_name=filename)

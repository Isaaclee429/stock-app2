# 多商品 RSI 策略分析儀表板 - 強化版（含錯誤處理）

import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# 商品代碼對照表（可擴充）
symbols = {
    "黃金 (GC=F)": "GC=F",
    "白銀 (SI=F)": "SI=F",
    "原油 (CL=F)": "CL=F",
    "天然氣 (NG=F)": "NG=F",
    "比特幣 (BTC-USD)": "BTC-USD",
    "SPDR黃金ETF (GLD)": "GLD",
    "Tesla (TSLA)": "TSLA",
    "Apple (AAPL)": "AAPL",
    "Amazon (AMZN)": "AMZN",
    "Netflix (NFLX)": "NFLX",
    "愛奇藝 (IQ)": "IQ"
}

# Streamlit 介面
st.title("📊 多商品 RSI 策略分析儀表板")
st.markdown("更新日期：2025/04/29")

# 選擇商品
product = st.selectbox("請選擇商品：", list(symbols.keys()))
symbol = symbols[product]

# 設定期間
start_date = st.date_input("起始日期", pd.to_datetime("2023-01-01"))
end_date = st.date_input("結束日期", pd.to_datetime("today"))

# 嘗試抓資料
try:
    df = yf.download(symbol, start=start_date, end=end_date)
    if df.empty:
        st.warning(f"⚠️ 無法取得「{product}」的歷史資料，請稍後再試，或選擇其他商品。")
        st.info(f"📅 最後可用資料日期：尚無資料記錄（可能為資料來源暫時中斷）")
    else:
        # 計算 RSI
        delta = df['Close'].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        df['RSI'] = rsi

        # 畫圖
        fig, ax = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
        ax[0].plot(df['Close'], label='收盤價')
        ax[0].set_title(f"{product} 價格走勢")
        ax[0].legend()
        ax[1].plot(df['RSI'], label='RSI (14)', color='orange')
        ax[1].axhline(70, linestyle='--', color='red', alpha=0.5)
        ax[1].axhline(30, linestyle='--', color='green', alpha=0.5)
        ax[1].set_title("RSI 指標")
        ax[1].legend()
        st.pyplot(fig)

except Exception as e:
    st.error(f"資料擷取時發生錯誤：{e}")

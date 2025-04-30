# 多商品 RSI 策略分析儀表板 - 修正 Finnhub 403 錯誤，只對支援資產使用 Finnhub

import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import traceback
from datetime import timedelta
import finnhub
import time

# 初始化 Finnhub（請填入你自己的 API 金鑰）
FINNHUB_API_KEY = "YOUR_API_KEY_HERE"
finnhub_client = finnhub.Client(api_key=FINNHUB_API_KEY)

def get_finnhub_price_data(symbol, start_date, end_date):
    try:
        start_unix = int(time.mktime(start_date.timetuple()))
        end_unix = int(time.mktime(end_date.timetuple()))
        res = finnhub_client.stock_candles(symbol, 'D', start_unix, end_unix)
        if res and res['s'] == 'ok':
            df = pd.DataFrame({
                'Date': pd.to_datetime(res['t'], unit='s'),
                'Open': res['o'],
                'High': res['h'],
                'Low': res['l'],
                'Close': res['c'],
                'Volume': res['v']
            })
            df.set_index('Date', inplace=True)
            return df
        else:
            return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

symbols = {
    "黃金 (GC=F)": "GC=F",
    "白銀 (SI=F)": "SI=F",
    "原油 (CL=F)": "CL=F",
    "天然氣 (NG=F)": "NG=F",
    "比特幣 (BTC-USD)": "BINANCE:BTCUSDT",
    "SPDR黃金ETF (GLD)": "GLD",
    "Tesla (TSLA)": "TSLA",
    "Apple (AAPL)": "AAPL",
    "Amazon (AMZN)": "AMZN",
    "Netflix (NFLX)": "NFLX",
    "愛奇藝 (IQ)": "IQ"
}

# 只有以下資產才使用 Finnhub，其餘一律使用 yfinance（避免 403 錯誤）
finnhub_assets = {"AAPL", "TSLA", "AMZN", "NFLX", "IQ", "BINANCE:BTCUSDT"}

fallback_map = {
    "GC=F": "GLD",
    "SI=F": "SLV",
    "NG=F": "UNG"
}

st.title("📊 多商品 RSI 策略分析儀表板")
st.markdown("更新日期：2025/04/29")

product = st.selectbox("請選擇商品：", list(symbols.keys()))
symbol = symbols[product]

start_date = st.date_input("起始日期", pd.to_datetime("2023-01-01"))
end_date = st.date_input("結束日期", pd.to_datetime("today"))

debug_logs = []
df = pd.DataFrame()
success = False

try:
    debug_logs.append(f"原始代碼查詢：{symbol}")

    def attempt_download(sym):
        for i in range(8):
            adjusted_end = end_date - timedelta(days=i)
            debug_logs.append(f"嘗試下載資料：{sym}, 結束日期：{adjusted_end}")
            if sym in finnhub_assets:
                data = get_finnhub_price_data(sym, start_date, adjusted_end)
            else:
                data = yf.download(sym, start=start_date, end=adjusted_end)
            if not data.empty:
                debug_logs.append(f"✅ 成功取得資料，使用結束日期：{adjusted_end}")
                return data, adjusted_end
        return pd.DataFrame(), None

    df, final_end = attempt_download(symbol)

    if df.empty and symbol in fallback_map:
        fallback = fallback_map[symbol]
        st.warning(f"⚠️ 無法取得 {symbol} 資料，自動改用替代商品：{fallback}")
        debug_logs.append(f"原始資料為空，改用替代商品：{fallback}")
        df, final_end = attempt_download(fallback)
        symbol = fallback
        product += f"（改為 {fallback}）"

    if df.empty:
        st.warning(f"⚠️ 無法取得「{product}」的歷史資料，請稍後再試，或選擇其他商品。")
        st.info(f"📅 最後可用資料日期：尚無資料記錄（可能為資料來源暫時中斷）")
        debug_logs.append("最終資料仍為空，未能成功下載任何可用資料。")
    else:
        st.info(f"✅ 資料來自：{symbol}，結束日期：{final_end}")
        delta = df['Close'].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        df['RSI'] = rsi

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
    err = traceback.format_exc()
    debug_logs.append("⚠️ 發生例外錯誤：\n" + err)
    st.error(f"資料擷取時發生錯誤：{e}")

with st.expander("🧾 錯誤追蹤報表與 Debug 日誌", expanded=True):
    for log in debug_logs:
        st.code(log)
    if not df.empty:
        st.write("✅ 下載資料範例：")
        st.dataframe(df.head())

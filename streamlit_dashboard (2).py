import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import matplotlib.pyplot as plt
from fpdf import FPDF
from datetime import date, timedelta
import io

# 多商品備援代碼表
asset_map = {
    "Gold (GC=F)": ["GC=F", "GLD", "IAU"],
    "Silver (SI=F)": ["SI=F", "SLV"],
    "Oil (CL=F)": ["CL=F", "USO"],
    "Bitcoin (BTC-USD)": ["BTC-USD"],
    "Apple (AAPL)": ["AAPL"]
}

# 自動回補資料下載函數（帶錯誤紀錄）
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

# RSI 策略應用
def apply_rsi_strategy(df, rsi_period=14, lower=30, upper=70):
    df["RSI"] = ta.momentum.RSIIndicator(df["Close"], window=rsi_period).rsi()
    df["Signal"] = 0
    df.loc[df["RSI"] < lower, "Signal"] = 1
    df.loc[df["RSI"] > upper, "Signal"] = -1
    df["Strategy Return"] = df["Signal"].shift(1) * df["Close"].pct_change()
    df["Cumulative Return"] = (1 + df["Strategy Return"]).cumprod()
    return df

# 建立 PDF 報告
def generate_pdf_report(final_return, win_rate, asset_label, symbol_used):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="RSI Strategy Report", ln=True, align="C")
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Asset: {asset_label} ({symbol_used})", ln=True)
    pdf.cell(200, 10, txt=f"Final cumulative return: {final_return:.2f}x", ln=True)
    pdf.cell(200, 10, txt=f"Win rate: {win_rate:.2%}", ln=True)
    pdf_output = io.BytesIO()
    pdf.output(pdf_output)
    return pdf_output.getvalue()

# UI
st.title("📊 Multi-Asset RSI Strategy Assistant")
asset_label = st.selectbox("Select Asset", list(asset_map.keys()))
start_date = st.date_input("Start Date", value=date(2023, 1, 1))
end_date = st.date_input("End Date", value=date(2025, 4, 30))

df, adjusted_end, attempt_log = safe_download_v3(asset_map[asset_label], start_date, end_date)

if df is None:
    st.error("❌ No valid data found.")
    with st.expander("📋 Debug Log"):
        for sym, d, success in attempt_log:
            st.text(f"{sym} on {d}: {'✅ Success' if success else '❌ Empty'}")
else:
    symbol_used = df["symbol_used"].iloc[0]
    st.success(f"✅ Data loaded from `{symbol_used}` up to `{adjusted_end}`")
    df = apply_rsi_strategy(df)

    # 圖：RSI
    st.subheader("🔍 RSI Indicator")
    fig1, ax1 = plt.subplots(figsize=(10, 4))
    ax1.plot(df.index, df["RSI"], color="blue")
    ax1.axhline(70, color="red", linestyle="--")
    ax1.axhline(30, color="green", linestyle="--")
    ax1.set_title("RSI Indicator")
    st.pyplot(fig1)

    # 圖：策略報酬
    st.subheader("💰 Strategy Performance")
    fig2, ax2 = plt.subplots(figsize=(10, 4))
    ax2.plot(df.index, df["Cumulative Return"], color="orange")
    ax2.set_title("Cumulative Strategy Return")
    st.pyplot(fig2)

    # 報酬統計
    final_return = df["Cumulative Return"].iloc[-1]
    win_rate = (df["Strategy Return"] > 0).sum() / df["Strategy Return"].count()
    st.subheader("📈 Strategy Summary")
    st.markdown(f"""
    - **Final cumulative return**: `{final_return:.2f}x`
    - **Win rate**: `{win_rate:.2%}`
    """)

    # 匯出 CSV
    st.download_button("⬇ Download CSV", df.to_csv().encode(), file_name=f"{symbol_used}_RSI_strategy.csv", mime="text/csv")

    # 匯出 PDF
    pdf_data = generate_pdf_report(final_return, win_rate, asset_label, symbol_used)
    st.download_button("⬇ Download PDF Report", pdf_data, file_name=f"{symbol_used}_RSI_report.pdf", mime="application/pdf")

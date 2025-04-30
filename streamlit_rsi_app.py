import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import matplotlib.pyplot as plt
from fpdf import FPDF
from datetime import date, timedelta
import io
import os

# 商品與備援代碼
asset_map = {
    "Gold (GC=F)": ["GC=F", "GLD", "IAU"],
    "Silver (SI=F)": ["SI=F", "SLV"],
    "Oil (CL=F)": ["CL=F", "USO"],
    "Bitcoin (BTC-USD)": ["BTC-USD"],
    "Apple (AAPL)": ["AAPL"]
}

# 強化下載 + 區間回溯 + 錯誤日誌
def safe_download_v4(ticker_list, start_date, end_date, max_lookback_days=30):
    max_allowed = date.today() - timedelta(days=2)
    end_date = min(end_date, max_allowed)
    attempt_log = []

    for back_offset in range(max_lookback_days):
        try_start = start_date - timedelta(days=back_offset)
        try_end = end_date - timedelta(days=back_offset)
        for symbol in ticker_list:
            try:
                df = yf.download(symbol, start=try_start, end=try_end)
                attempt_log.append((symbol, try_start, try_end, not df.empty))
                if not df.empty:
                    df["symbol_used"] = symbol
                    return df, try_start, try_end, attempt_log
            except Exception as e:
                attempt_log.append((symbol, try_start, try_end, False))
    return None, None, None, attempt_log

# RSI 策略
def apply_rsi_strategy(df, rsi_period=14, lower=30, upper=70):
    df["RSI"] = ta.momentum.RSIIndicator(df["Close"], window=rsi_period).rsi()
    df["Signal"] = 0
    df.loc[df["RSI"] < lower, "Signal"] = 1
    df.loc[df["RSI"] > upper, "Signal"] = -1
    df["Strategy Return"] = df["Signal"].shift(1) * df["Close"].pct_change()
    df["Cumulative Return"] = (1 + df["Strategy Return"]).cumprod()
    return df

# 匯出 PDF 報告
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

# 主頁 UI
st.title("📊 Multi-Asset RSI Strategy Assistant (Stable + Offline Fallback)")
asset_label = st.selectbox("Select Asset", list(asset_map.keys()))
start_date = st.date_input("Start Date", value=date(2023, 1, 1))
end_date = st.date_input("End Date", value=date(2025, 4, 30))

# 嘗試從網路抓資料
df, used_start, used_end, attempt_log = safe_download_v4(asset_map[asset_label], start_date, end_date)

# 若網路資料失敗 → 改用本地 CSV 備援
if df is None:
    st.warning("⚠️ Online data not available, trying local CSV backup...")
    for sym in asset_map[asset_label]:
        csv_path = f"local_backup_{sym.replace('=','')}.csv"
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
            df["symbol_used"] = sym
            used_start = df.index.min().date()
            used_end = df.index.max().date()
            st.success(f"✅ Loaded local CSV backup: `{csv_path}`")
            break

# 如果還是無資料 → 報錯並顯示日誌
if df is None or df.empty:
    st.error("❌ No valid data found even with local backup.")
    with st.expander("🧾 Download Attempts"):
        for sym, s, e, success in attempt_log:
            st.text(f"{sym} | {s} → {e}: {'✅ Success' if success else '❌ Empty'}")
else:
    symbol_used = df["symbol_used"].iloc[0]
    st.success(f"✅ Data loaded from `{symbol_used}` ({used_start} ~ {used_end})")
    df = apply_rsi_strategy(df)

    # RSI 圖
    st.subheader("🔍 RSI Indicator")
    fig1, ax1 = plt.subplots(figsize=(10, 4))
    ax1.plot(df.index, df["RSI"], color="blue")
    ax1.axhline(70, color="red", linestyle="--")
    ax1.axhline(30, color="green", linestyle="--")
    ax1.set_title("RSI Indicator")
    st.pyplot(fig1)

    # 策略績效圖
    st.subheader("💰 Strategy Performance")
    fig2, ax2 = plt.subplots(figsize=(10, 4))
    ax2.plot(df.index, df["Cumulative Return"], color="orange")
    ax2.set_title("Cumulative Return")
    st.pyplot(fig2)

    # 回測統計
    final_return = df["Cumulative Return"].iloc[-1]
    win_rate = (df["Strategy Return"] > 0).sum() / df["Strategy Return"].count()
    st.subheader("📈 Summary")
    st.markdown(f"- **Final Return**: `{final_return:.2f}x`\n- **Win Rate**: `{win_rate:.2%}`")

    # 匯出按鈕
    st.download_button("⬇ Download CSV", df.to_csv().encode(), file_name=f"{symbol_used}_RSI.csv", mime="text/csv")
    pdf_bytes = generate_pdf_report(final_return, win_rate, asset_label, symbol_used)
    st.download_button("⬇ Download PDF Report", pdf_bytes, file_name=f"{symbol_used}_RSI_Report.pdf", mime="application/pdf")

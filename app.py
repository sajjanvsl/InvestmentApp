import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np

st.set_page_config(page_title="AI Investment Dashboard", layout="wide")

st.title("📊 AI Smart Investment Dashboard")

# -----------------------------
# Initialize Session State
# -----------------------------
if "portfolio" not in st.session_state:
    st.session_state.portfolio = pd.DataFrame(
        columns=["Stock", "Quantity", "Buy Price"]
    )

# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.header("📥 Portfolio Input")

# Manual Entry
stock = st.sidebar.text_input("Stock Symbol (e.g. TCS.NS)")
qty = st.sidebar.number_input("Quantity", min_value=1)
buy_price = st.sidebar.number_input("Buy Price", min_value=0.0)

if st.sidebar.button("Add Stock"):
    if stock:
        new_row = pd.DataFrame([[stock.upper(), qty, buy_price]],
                               columns=["Stock", "Quantity", "Buy Price"])
        st.session_state.portfolio = pd.concat(
            [st.session_state.portfolio, new_row], ignore_index=True
        )

# CSV Upload
uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])

if uploaded_file:
    df_csv = pd.read_csv(uploaded_file)
    st.session_state.portfolio = df_csv
    st.sidebar.success("CSV Uploaded!")

# -----------------------------
# Functions
# -----------------------------
def get_data(symbol):
    try:
        data = yf.Ticker(symbol)
        hist = data.history(period="6mo")
        price = hist["Close"].iloc[-1]
        return hist, price
    except:
        return None, None

def calculate_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def fair_value(eps, growth):
    return eps * growth * 1.5

# -----------------------------
# Portfolio Processing
# -----------------------------
st.subheader("📋 Portfolio Overview")

if not st.session_state.portfolio.empty:

    df = st.session_state.portfolio.copy()

    results = []

    for i, row in df.iterrows():
        hist, price = get_data(row["Stock"])

        if price:
            invested = row["Buy Price"] * row["Quantity"]
            value = price * row["Quantity"]
            pnl = value - invested

            # RSI
            rsi = calculate_rsi(hist["Close"]).iloc[-1]

            # Dummy EPS & growth (you can replace with API)
            eps = 50
            growth = 15

            fv = fair_value(eps, growth)

            # Recommendation
            if price < fv * 0.8:
                signal = "BUY"
            elif price > fv * 1.2:
                signal = "SELL"
            else:
                signal = "HOLD"

        else:
            invested = value = pnl = rsi = fv = 0
            signal = "N/A"

        results.append([
            row["Stock"], row["Quantity"], row["Buy Price"],
            price, invested, value, pnl, rsi, fv, signal
        ])

    df_final = pd.DataFrame(results, columns=[
        "Stock", "Qty", "Buy Price", "Current Price",
        "Invested", "Value", "P/L", "RSI", "Fair Value", "Signal"
    ])

    st.dataframe(df_final, use_container_width=True)

    # -----------------------------
    # Metrics
    # -----------------------------
    total_invested = df_final["Invested"].sum()
    total_value = df_final["Value"].sum()
    total_pnl = total_value - total_invested

    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Invested", f"₹{total_invested:,.0f}")
    col2.metric("📈 Value", f"₹{total_value:,.0f}")
    col3.metric("🔥 P/L", f"₹{total_pnl:,.0f}")

    # -----------------------------
    # Allocation Chart
    # -----------------------------
    st.subheader("📊 Allocation")

    chart = df_final.set_index("Stock")["Value"]
    st.bar_chart(chart)

    # -----------------------------
    # Download Report
    # -----------------------------
    csv = df_final.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Report", csv, "portfolio_report.csv")

    # -----------------------------
    # Stock Chart
    # -----------------------------
    st.subheader("📉 Stock Chart")

    selected = st.selectbox("Select Stock", df_final["Stock"])

    hist, _ = get_data(selected)

    if hist is not None:
        st.line_chart(hist["Close"])

else:
    st.info("Add stocks or upload CSV")

# -----------------------------
# Clear Portfolio
# -----------------------------
if st.button("🧹 Clear Portfolio"):
    st.session_state.portfolio = pd.DataFrame(
        columns=["Stock", "Quantity", "Buy Price"]
    )
    st.warning("Portfolio Cleared")

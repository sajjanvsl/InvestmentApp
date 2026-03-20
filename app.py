import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np

st.set_page_config(page_title="Pro Investment Dashboard", layout="wide")

st.title("🚀 Pro AI Investment Dashboard")

# -----------------------------
# Session State
# -----------------------------
if "portfolio" not in st.session_state:
    st.session_state.portfolio = pd.DataFrame(
        columns=["Stock", "Quantity", "Buy Price"]
    )

# -----------------------------
# Sidebar Input
# -----------------------------
st.sidebar.header("📥 Add Stock")

stock = st.sidebar.text_input("Stock Symbol (e.g. TCS.NS)")
qty = st.sidebar.number_input("Quantity", min_value=1)
buy_price = st.sidebar.number_input("Buy Price", min_value=0.0)

if st.sidebar.button("Add"):
    if stock:
        new_row = pd.DataFrame([[stock.upper(), qty, buy_price]],
                               columns=["Stock", "Quantity", "Buy Price"])
        st.session_state.portfolio = pd.concat(
            [st.session_state.portfolio, new_row],
            ignore_index=True
        )

# -----------------------------
# Functions
# -----------------------------
def get_stock_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1y")
        info = ticker.info

        price = hist["Close"].iloc[-1]
        eps = info.get("trailingEps", None)
        pe = info.get("trailingPE", None)

        return hist, price, eps, pe
    except:
        return None, None, None, None


def calculate_rsi(series, window=14):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(window).mean()
    loss = (-delta.clip(upper=0)).rolling(window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def fair_value(eps, growth=15):
    if eps:
        return eps * growth * 1.5
    return None


def signal_logic(price, fv, rsi):
    if fv is None:
        return "N/A"

    if price < fv * 0.8 and rsi < 40:
        return "STRONG BUY"
    elif price < fv:
        return "BUY"
    elif price > fv * 1.3:
        return "SELL"
    else:
        return "HOLD"


# -----------------------------
# Portfolio Processing
# -----------------------------
st.subheader("📊 Portfolio Dashboard")

if not st.session_state.portfolio.empty:

    df = st.session_state.portfolio.copy()
    results = []

    for _, row in df.iterrows():
        hist, price, eps, pe = get_stock_data(row["Stock"])

        if hist is not None:
            invested = row["Buy Price"] * row["Quantity"]
            value = price * row["Quantity"]
            pnl = value - invested

            rsi = calculate_rsi(hist["Close"]).iloc[-1]
            ma50 = hist["Close"].rolling(50).mean().iloc[-1]
            ma200 = hist["Close"].rolling(200).mean().iloc[-1]

            fv = fair_value(eps)

            signal = signal_logic(price, fv, rsi)

        else:
            invested = value = pnl = rsi = ma50 = ma200 = fv = 0
            signal = "N/A"

        results.append([
            row["Stock"], row["Quantity"], row["Buy Price"],
            price, invested, value, pnl, rsi, ma50, ma200, fv, signal
        ])

    df_final = pd.DataFrame(results, columns=[
        "Stock", "Qty", "Buy Price", "Current Price",
        "Invested", "Value", "P/L",
        "RSI", "MA50", "MA200",
        "Fair Value", "Signal"
    ])

    st.dataframe(df_final, use_container_width=True)

    # -----------------------------
    # Metrics
    # -----------------------------
    total_inv = df_final["Invested"].sum()
    total_val = df_final["Value"].sum()
    total_pnl = total_val - total_inv

    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Invested", f"₹{total_inv:,.0f}")
    c2.metric("📈 Value", f"₹{total_val:,.0f}")
    c3.metric("🔥 Profit/Loss", f"₹{total_pnl:,.0f}")

    # -----------------------------
    # Allocation %
    # -----------------------------
    st.subheader("📊 Allocation %")

    df_final["Allocation %"] = (df_final["Value"] / total_val) * 100
    st.bar_chart(df_final.set_index("Stock")["Allocation %"])

    # -----------------------------
    # Stock Chart
    # -----------------------------
    st.subheader("📉 Technical Chart")

    selected = st.selectbox("Select Stock", df_final["Stock"])
    hist, _, _, _ = get_stock_data(selected)

    if hist is not None:
        chart_df = pd.DataFrame({
            "Close": hist["Close"],
            "MA50": hist["Close"].rolling(50).mean(),
            "MA200": hist["Close"].rolling(200).mean()
        })
        st.line_chart(chart_df)

    # -----------------------------
    # Multibagger Screener Logic
    # -----------------------------
    st.subheader("🚀 Multibagger Candidates")

    multi = df_final[
        (df_final["RSI"] < 50) &
        (df_final["Current Price"] < df_final["Fair Value"])
    ]

    if not multi.empty:
        st.success("Potential Multibaggers Found")
        st.dataframe(multi)
    else:
        st.info("No strong candidates now")

    # -----------------------------
    # Download
    # -----------------------------
    csv = df_final.to_csv(index=False).encode()
    st.download_button("📥 Download Report", csv, "portfolio.csv")

else:
    st.info("Add stocks to begin")

# -----------------------------
# Clear
# -----------------------------
if st.button("🧹 Clear Portfolio"):
    st.session_state.portfolio = pd.DataFrame(
        columns=["Stock", "Quantity", "Buy Price"]
    )

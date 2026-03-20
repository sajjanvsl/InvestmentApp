import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np

st.set_page_config(page_title="Ultimate AI Portfolio", layout="wide")

st.title("🚀 Ultimate AI Investment System")

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

stock = st.sidebar.text_input("Stock (e.g. TCS.NS)")
qty = st.sidebar.number_input("Quantity", min_value=1)
buy = st.sidebar.number_input("Buy Price", min_value=0.0)

if st.sidebar.button("Add Stock"):
    new = pd.DataFrame([[stock.upper(), qty, buy]],
                       columns=["Stock", "Quantity", "Buy Price"])
    st.session_state.portfolio = pd.concat(
        [st.session_state.portfolio, new], ignore_index=True
    )

# -----------------------------
# FUNCTIONS
# -----------------------------
def fetch_data(symbol):
    try:
        t = yf.Ticker(symbol)
        hist = t.history(period="1y")
        info = t.info

        price = hist["Close"].iloc[-1]
        eps = info.get("trailingEps", None)
        pe = info.get("trailingPE", None)
        sector = info.get("sector", "Unknown")

        return hist, price, eps, pe, sector
    except:
        return None, None, None, None, "Unknown"


def RSI(series, n=14):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(n).mean()
    loss = (-delta.clip(upper=0)).rolling(n).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def fair_value(eps, growth=15):
    return eps * growth * 1.5 if eps else None


def ai_score(price, fv, rsi, ma50, ma200):
    score = 0

    if fv and price < fv:
        score += 30
    if rsi < 40:
        score += 20
    if price > ma50:
        score += 20
    if price > ma200:
        score += 20
    if fv and price < fv * 0.8:
        score += 10

    return score


def decision(score):
    if score >= 70:
        return "STRONG BUY"
    elif score >= 50:
        return "BUY"
    elif score >= 30:
        return "HOLD"
    else:
        return "SELL"


# -----------------------------
# MAIN DASHBOARD
# -----------------------------
st.subheader("📊 Portfolio Analysis")

if not st.session_state.portfolio.empty:

    df = st.session_state.portfolio.copy()
    results = []

    for _, row in df.iterrows():
        hist, price, eps, pe, sector = fetch_data(row["Stock"])

        if hist is not None:
            invested = row["Buy Price"] * row["Quantity"]
            value = price * row["Quantity"]
            pnl = value - invested

            rsi = RSI(hist["Close"]).iloc[-1]
            ma50 = hist["Close"].rolling(50).mean().iloc[-1]
            ma200 = hist["Close"].rolling(200).mean().iloc[-1]

            fv = fair_value(eps)
            score = ai_score(price, fv, rsi, ma50, ma200)
            signal = decision(score)

            stop_loss = price * 0.85
            target = price * 1.4

        else:
            invested = value = pnl = rsi = ma50 = ma200 = fv = score = 0
            signal = "N/A"
            sector = "Unknown"
            stop_loss = target = 0

        results.append([
            row["Stock"], sector, row["Quantity"], row["Buy Price"],
            price, invested, value, pnl,
            rsi, ma50, ma200, fv, score, signal,
            stop_loss, target
        ])

    df_final = pd.DataFrame(results, columns=[
        "Stock", "Sector", "Qty", "Buy Price", "Current Price",
        "Invested", "Value", "P/L",
        "RSI", "MA50", "MA200",
        "Fair Value", "AI Score", "Signal",
        "Stop Loss", "Target"
    ])

    st.dataframe(df_final, use_container_width=True)

    # -----------------------------
    # METRICS
    # -----------------------------
    total_inv = df_final["Invested"].sum()
    total_val = df_final["Value"].sum()

    st.metric("💰 Invested", f"₹{total_inv:,.0f}")
    st.metric("📈 Value", f"₹{total_val:,.0f}")
    st.metric("🔥 Profit", f"₹{total_val-total_inv:,.0f}")

    # -----------------------------
    # PORTFOLIO HEALTH
    # -----------------------------
    st.subheader("🧠 Portfolio Health Score")

    avg_score = df_final["AI Score"].mean()

    if avg_score > 65:
        st.success(f"Strong Portfolio ({avg_score:.0f}/100)")
    elif avg_score > 45:
        st.warning(f"Moderate Portfolio ({avg_score:.0f}/100)")
    else:
        st.error(f"Weak Portfolio ({avg_score:.0f}/100)")

    # -----------------------------
    # RISK (ALLOCATION)
    # -----------------------------
    st.subheader("⚠️ Risk Analysis")

    df_final["Allocation %"] = (df_final["Value"] / total_val) * 100
    st.bar_chart(df_final.set_index("Stock")["Allocation %"])

    # -----------------------------
    # SECTOR DIVERSIFICATION
    # -----------------------------
    st.subheader("🏭 Sector Distribution")

    sector_dist = df_final.groupby("Sector")["Value"].sum()
    st.bar_chart(sector_dist)

    # -----------------------------
    # MULTIBAGGER FILTER
    # -----------------------------
    st.subheader("🚀 Multibagger Picks")

    multi = df_final[
        (df_final["AI Score"] > 70) &
        (df_final["RSI"] < 50)
    ]

    st.dataframe(multi)

    # -----------------------------
    # REBALANCING SUGGESTION
    # -----------------------------
    st.subheader("⚖️ Rebalancing Suggestions")

    over_alloc = df_final[df_final["Allocation %"] > 25]
    if not over_alloc.empty:
        st.warning("Reduce exposure in:")
        st.write(over_alloc[["Stock", "Allocation %"]])
    else:
        st.success("Well balanced portfolio")

    # -----------------------------
    # DOWNLOAD
    # -----------------------------
    csv = df_final.to_csv(index=False).encode()
    st.download_button("📥 Download Report", csv, "ultimate_portfolio.csv")

else:
    st.info("Add stocks to start")

# -----------------------------
# CLEAR
# -----------------------------
if st.button("🧹 Reset Portfolio"):
    st.session_state.portfolio = pd.DataFrame(
        columns=["Stock", "Quantity", "Buy Price"]
    )

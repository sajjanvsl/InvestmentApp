import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from ta.momentum import RSIIndicator
from datetime import datetime

st.set_page_config(page_title="Quant Fund Manager", layout="wide")

# ------------------------------
# CUSTOM CSS – Professional Dashboard
# ------------------------------
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background-color: #f0f2f6;
    }
    /* Headers */
    h1, h2, h3 {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        color: #0f172a;
    }
    /* Metric cards */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 20px;
        box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1);
        border: 1px solid #e9eef2;
        transition: all 0.2s;
        height: 100%;
    }
    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 20px 30px -10px rgba(0,0,0,0.15);
    }
    .metric-label {
        font-size: 0.85rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.25rem;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #0f172a;
        line-height: 1.2;
    }
    .metric-delta {
        font-size: 0.9rem;
        font-weight: 500;
    }
    .buy-tag {
        background: #dcfce7;
        color: #166534;
        padding: 0.25rem 0.8rem;
        border-radius: 30px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
    }
    .hold-tag {
        background: #fff3cd;
        color: #856404;
        padding: 0.25rem 0.8rem;
        border-radius: 30px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
    }
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: white;
        padding: 0.5rem 1.5rem;
        border-radius: 50px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 30px;
        padding: 0.6rem 1.5rem;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1e293b;
        color: white !important;
    }
    /* Dataframes */
    .stDataFrame {
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    hr {
        margin: 2rem 0;
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, #cbd5e1, transparent);
    }
    /* Sidebar (removed) but we keep main area clean */
    .main-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 2rem;
    }
    .logo {
        font-size: 1.8rem;
        font-weight: 700;
        background: linear-gradient(135deg, #1e293b, #0f172a);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------
# MASTER STOCK LIST (all NSE stocks you provided)
# ------------------------------
ALL_STOCKS = {
    "CIPLA": "CIPLA.NS",
    "ICICIAMC": "ICICIAMC.NS",
    "GANESHHOU": "GANESHHOU.NS",
    "TCS": "TCS.NS",
    "MON100": "MON100.NS",
    "BSE": "BSE.NS",
    "TMCV": "TMCV.NS",
    "IRCTC": "IRCTC.NS",
    "SILVERBEES": "SILVERBEES.NS",
    "HDFCBANK": "HDFCBANK.NS",
    "HAL": "HAL.NS",
    "VBL": "VBL.NS",
    "MAZDOCK": "MAZDOCK.NS",
    "ADANIPORTS": "ADANIPORTS.NS",
    "TRENT": "TRENT.NS",
    "GOLDBEES": "GOLDBEES.NS",
    "LIQUIDBEES": "LIQUIDBEES.NS",
    "SMALL250": "SMALL250.NS",
    "ASTRAL": "ASTRAL.NS",
    "TRUALT": "TRUALT.NS",
    "TMPV": "TMPV.NS",
    "IREDA": "IREDA.NS",
    "ANANTRAJ": "ANANTRAJ.NS",
    "WAAREEENER": "WAAREEENER.NS",
    "BAJAJHFL": "BAJAJHFL.NS",
    "JIOFIN": "JIOFIN.NS",
    "NHPC": "NHPC.NS",
    "AWHCL": "AWHCL.NS",
    "ECORECO": "ECORECO.NS",
    "EPACKPEB": "EPACKPEB.NS",
    "NATPLASTI": "NATPLASTI.NS",
    "SETL": "SETL.NS",
    "TDPOWERSYS": "TDPOWERSYS.NS"
}

# ------------------------------
# DATA FETCHING FUNCTIONS (cached)
# ------------------------------
@st.cache_data(ttl=3600)
def get_price_data(ticker):
    try:
        df = yf.download(ticker, period="6mo", interval="1d", auto_adjust=True, progress=False)
        if df.empty:
            return pd.DataFrame()
        df.dropna(inplace=True)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=86400)
def get_fundamental_data(ticker):
    try:
        t = yf.Ticker(ticker)
        info = t.info
        financials = t.financials
        balance_sheet = t.balance_sheet
        cashflow = t.cashflow

        def get_latest(df, key):
            if df is not None and key in df.index:
                vals = df.loc[key]
                if isinstance(vals, pd.Series):
                    vals = vals[vals.notna()]
                    if len(vals) > 0:
                        return vals.iloc[0]
            return np.nan

        sales_growth = info.get('revenueGrowth', np.nan)
        if not pd.isna(sales_growth):
            sales_growth = sales_growth * 100

        profit_growth = info.get('earningsGrowth', np.nan)
        if not pd.isna(profit_growth):
            profit_growth = profit_growth * 100

        market_cap = info.get('marketCap', 0) / 1e7  # in Crores

        ebit = get_latest(financials, 'EBIT')
        total_assets = get_latest(balance_sheet, 'Total Assets')
        current_liab = get_latest(balance_sheet, 'Total Current Liabilities')
        capital_employed = total_assets - current_liab
        roce = (ebit / capital_employed) * 100 if capital_employed and capital_employed != 0 else np.nan

        total_debt = get_latest(balance_sheet, 'Total Debt')
        if pd.isna(total_debt):
            ltd = get_latest(balance_sheet, 'Long Term Debt')
            std = get_latest(balance_sheet, 'Short Term Debt')
            total_debt = (ltd if not pd.isna(ltd) else 0) + (std if not pd.isna(std) else 0)
        equity = get_latest(balance_sheet, 'Stockholders Equity')
        de_ratio = total_debt / equity if equity and equity != 0 else np.nan

        interest = get_latest(financials, 'Interest Expense')
        icr = ebit / interest if interest and interest != 0 else np.nan

        current_price = info.get('regularMarketPrice', info.get('currentPrice', np.nan))
        high_52w = info.get('fiftyTwoWeekHigh', np.nan)
        down_from_high = ((high_52w - current_price) / high_52w) * 100 if high_52w and current_price else np.nan

        fcf = get_latest(cashflow, 'Free Cash Flow')
        fcf_positive = fcf > 0 if not pd.isna(fcf) else False

        promoter = np.nan

        return {
            'sales_growth': sales_growth,
            'profit_growth': profit_growth,
            'market_cap': market_cap,
            'roce': roce,
            'de_ratio': de_ratio,
            'icr': icr,
            'down_from_high': down_from_high,
            'fcf_positive': fcf_positive,
            'promoter': promoter,
            'current_price': current_price,
            'info': info
        }
    except Exception:
        return None

# ------------------------------
# STRICT SCREENING (all 9 conditions)
# ------------------------------
def screen_stock(fund):
    if fund is None:
        return "HOLD", {}
    criteria = {
        'Sales growth >15%': fund['sales_growth'] > 15 if not pd.isna(fund['sales_growth']) else False,
        'Profit growth >15%': fund['profit_growth'] > 15 if not pd.isna(fund['profit_growth']) else False,
        'Mkt Cap >1000 Cr': fund['market_cap'] > 1000 if not pd.isna(fund['market_cap']) else False,
        'ROCE >15%': fund['roce'] > 15 if not pd.isna(fund['roce']) else False,
        'Debt/Equity <0.5': fund['de_ratio'] < 0.5 if not pd.isna(fund['de_ratio']) else False,
        'ICR >3': fund['icr'] > 3 if not pd.isna(fund['icr']) else False,
        'Down from 52W high >30%': fund['down_from_high'] > 30 if not pd.isna(fund['down_from_high']) else False,
        'FCF positive': fund['fcf_positive'],
        'Promoter >50%': fund['promoter'] > 50 if not pd.isna(fund['promoter']) else False
    }
    if all(criteria.values()):
        rec = "BUY"
    else:
        rec = "HOLD"
    return rec, criteria

# ------------------------------
# SWING SIGNAL GENERATION
# ------------------------------
def swing_signal(df, name):
    if df.empty or len(df) < 50:
        return None
    try:
        close = df['Close'].astype(float)
        high = df['High'].astype(float)
        low = df['Low'].astype(float)

        rsi = RSIIndicator(close).rsi()
        current_rsi = rsi.iloc[-1]

        ma20 = close.rolling(20).mean()
        ma50 = close.rolling(50).mean()

        recent_high = high[-20:].max()
        recent_low = low[-20:].min()
        current_price = close.iloc[-1]

        if current_rsi < 40 and ma20.iloc[-1] > ma50.iloc[-1] and current_price > recent_low * 1.02:
            signal = "SWING BUY"
            entry = current_price
            target = recent_high
            stop_loss = recent_low * 0.98
            holding_days = 15
        elif current_rsi > 70:
            signal = "BOOK PROFIT"
            entry = target = stop_loss = holding_days = np.nan
        else:
            signal = "WAIT"
            entry = target = stop_loss = holding_days = np.nan

        return {
            'Stock': name,
            'Signal': signal,
            'RSI': round(current_rsi, 1),
            'Entry': round(entry, 2) if not pd.isna(entry) else '-',
            'Target': round(target, 2) if not pd.isna(target) else '-',
            'Stop Loss': round(stop_loss, 2) if not pd.isna(stop_loss) else '-',
            'Holding (days)': int(holding_days) if not pd.isna(holding_days) else '-'
        }
    except Exception:
        return None

# ------------------------------
# INITIALIZE SESSION STATE
# ------------------------------
if 'holdings_df' not in st.session_state:
    st.session_state.holdings_df = None
if 'portfolio_df' not in st.session_state:
    st.session_state.portfolio_df = None
if 'total_value' not in st.session_state:
    st.session_state.total_value = 0
if 'total_cost' not in st.session_state:
    st.session_state.total_cost = 0
if 'buy_count' not in st.session_state:
    st.session_state.buy_count = 0

# ------------------------------
# HEADER
# ------------------------------
st.markdown('<div class="main-header"><span class="logo">📈 Quant Fund Manager</span><span style="color:#64748b;">Professional Edition</span></div>', unsafe_allow_html=True)
st.markdown("#### Institutional‑grade analytics for your long‑term and swing portfolios")

# Input row
col1, col2 = st.columns([2, 1])
with col1:
    uploaded_file = st.file_uploader("Upload Holdings CSV", type=['csv'], key="file_uploader")
with col2:
    single_stock = st.text_input("Or add a single stock", placeholder="e.g., CIPLA").strip().upper()

# Process uploaded file (only if new file uploaded)
if uploaded_file is not None:
    try:
        raw_df = pd.read_csv(uploaded_file, skipinitialspace=True, engine='python')
        raw_df = raw_df.loc[:, ~raw_df.columns.str.contains('^Unnamed')]
        
        if raw_df.shape[1] < 8:
            st.error(f"CSV has only {raw_df.shape[1]} columns. Expected at least 8.")
        else:
            df_hold = raw_df.iloc[:, :8].copy()
            df_hold.columns = ['Instrument', 'Qty', 'Avg Price', 'LTP', 'Cur Value', 'P&L', 'Net Chg %', 'Day Chg %']
            
            df_hold['Instrument'] = df_hold['Instrument'].astype(str).str.strip().str.upper()
            df_hold = df_hold[df_hold['Instrument'].notna() & (df_hold['Instrument'] != '') & (df_hold['Instrument'] != 'NAN')]
            
            for col in ['Qty', 'Avg Price', 'LTP', 'Cur Value', 'P&L', 'Net Chg %', 'Day Chg %']:
                df_hold[col] = pd.to_numeric(df_hold[col], errors='coerce')
            
            # Filter to master list
            original_len = len(df_hold)
            df_hold = df_hold[df_hold['Instrument'].isin(ALL_STOCKS.keys())]
            if len(df_hold) == 0:
                st.error("No stocks from your CSV are in the master list.")
            else:
                st.session_state.holdings_df = df_hold
                st.success(f"Loaded {len(df_hold)} stocks from CSV.")
    except Exception as e:
        st.error(f"Error reading CSV: {e}")

# Add single stock
if single_stock:
    if single_stock in ALL_STOCKS:
        new_row = pd.DataFrame({
            'Instrument': [single_stock],
            'Qty': [1],
            'Avg Price': [np.nan],
            'LTP': [np.nan],
            'Cur Value': [np.nan],
            'P&L': [np.nan],
            'Net Chg %': [np.nan],
            'Day Chg %': [np.nan]
        })
        if st.session_state.holdings_df is not None:
            if single_stock not in st.session_state.holdings_df['Instrument'].values:
                st.session_state.holdings_df = pd.concat([st.session_state.holdings_df, new_row], ignore_index=True)
                st.success(f"Added {single_stock}.")
            else:
                st.warning(f"{single_stock} already in holdings.")
        else:
            st.session_state.holdings_df = new_row
            st.success(f"Added {single_stock}.")
    else:
        st.error(f"{single_stock} not found in master list.")

# If no data, stop
if st.session_state.holdings_df is None or st.session_state.holdings_df.empty:
    st.info("👆 Please upload a CSV or add a stock to begin.")
    st.stop()

# ------------------------------
# PROCESS HOLDINGS (only if not already processed or data changed)
# ------------------------------
# We'll process each time (fast due to caching) but could add a flag.
portfolio_data = []
total_value = 0
total_cost = 0
buy_count = 0

progress_bar = st.progress(0, text="Analyzing holdings...")
for idx, row in st.session_state.holdings_df.iterrows():
    name = row['Instrument']
    ticker = ALL_STOCKS.get(name)

    price_df = get_price_data(ticker)
    if price_df.empty:
        st.warning(f"No price data for {name}. Skipping.")
        continue

    current_price = price_df['Close'].iloc[-1]
    cur_value = row['Qty'] * current_price
    if not pd.isna(row['Avg Price']):
        pnl = row['Qty'] * (current_price - row['Avg Price'])
        pnl_pct = (current_price - row['Avg Price']) / row['Avg Price'] * 100
    else:
        pnl = np.nan
        pnl_pct = np.nan

    fund = get_fundamental_data(ticker)
    rec, _ = screen_stock(fund)
    if rec == "BUY":
        buy_count += 1

    portfolio_data.append({
        'Stock': name,
        'Qty': row['Qty'],
        'Avg Price': row['Avg Price'],
        'LTP (CSV)': row['LTP'],
        'Current Price': current_price,
        'Cur Value': cur_value,
        'P&L': pnl,
        'P&L %': pnl_pct,
        'Recommendation': rec,
    })

    total_value += cur_value
    if not pd.isna(row['Avg Price']):
        total_cost += row['Qty'] * row['Avg Price']

    progress_bar.progress((idx+1)/len(st.session_state.holdings_df))
progress_bar.empty()

st.session_state.portfolio_df = pd.DataFrame(portfolio_data)
st.session_state.total_value = total_value
st.session_state.total_cost = total_cost
st.session_state.buy_count = buy_count

# ------------------------------
# DASHBOARD METRICS CARDS
# ------------------------------
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Total Portfolio Value</div>
        <div class="metric-value">₹{total_value:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)
with col2:
    if total_cost > 0:
        total_pnl = total_value - total_cost
        total_pnl_pct = (total_pnl / total_cost) * 100
        delta_color = "green" if total_pnl >= 0 else "red"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total P&L</div>
            <div class="metric-value">₹{total_pnl:+,.0f}</div>
            <div class="metric-delta" style="color:{delta_color};">{total_pnl_pct:+.2f}%</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total P&L</div>
            <div class="metric-value">N/A</div>
        </div>
        """, unsafe_allow_html=True)
with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Stocks Meeting All Criteria</div>
        <div class="metric-value">{buy_count}</div>
    </div>
    """, unsafe_allow_html=True)
with col4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Portfolio Size</div>
        <div class="metric-value">{len(st.session_state.portfolio_df)}</div>
    </div>
    """, unsafe_allow_html=True)

# ------------------------------
# ALLOCATION PIE CHART
# ------------------------------
st.markdown("---")
col1, col2 = st.columns([1, 1])
with col1:
    st.subheader("Portfolio Allocation by Value")
    if not st.session_state.portfolio_df.empty:
        fig = px.pie(st.session_state.portfolio_df, values='Cur Value', names='Stock', title='Current Allocation')
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data for pie chart.")

with col2:
    st.subheader("Performance Sparkline (Last Month)")
    # Show mini line chart of total portfolio value over last 30 days
    # We need to fetch historical prices for all holdings and aggregate.
    # For simplicity, we'll just show a placeholder or compute if possible.
    st.info("Historical portfolio performance will appear here (requires multi‑stock history).")
    # You could implement by fetching 1mo daily prices for each stock and computing weighted sum.

# ------------------------------
# TABS
# ------------------------------
tab1, tab2, tab3 = st.tabs(["📊 Holdings & Recommendations", "⚡ Swing Trading Signals", "📈 Charts"])

with tab1:
    st.subheader("Your Holdings – Long‑Term Analysis")
    st.caption("BUY = meets all 9 fundamental criteria. HOLD = fails at least one.")
    st.dataframe(
        st.session_state.portfolio_df.style.format({
            'Avg Price': '₹{:.2f}',
            'LTP (CSV)': '₹{:.2f}',
            'Current Price': '₹{:.2f}',
            'Cur Value': '₹{:.2f}',
            'P&L': '₹{:.2f}',
            'P&L %': '{:+.2f}%'
        }, na_rep='-').applymap(
            lambda x: 'background-color: #d4edda' if x == 'BUY' else ('background-color: #fff3cd' if x == 'HOLD' else ''),
            subset=['Recommendation']
        ),
        use_container_width=True
    )

with tab2:
    st.subheader("Daily Swing Trading Opportunities")
    st.caption("Scanning all stocks in master list. Entry, target, SL based on recent swings.")
    swing_data = []
    for name, ticker in ALL_STOCKS.items():
        df = get_price_data(ticker)
        sig = swing_signal(df, name)
        if sig:
            swing_data.append(sig)
    if swing_data:
        swing_df = pd.DataFrame(swing_data)
        def highlight_buy(row):
            if row['Signal'] == 'SWING BUY':
                return ['background-color: #d4edda'] * len(row)
            return [''] * len(row)
        st.dataframe(swing_df.style.apply(highlight_buy, axis=1), use_container_width=True)
    else:
        st.info("No swing signals today.")

with tab3:
    st.subheader("Price Chart")
    if not st.session_state.portfolio_df.empty:
        selected = st.selectbox("Select stock", st.session_state.portfolio_df['Stock'].tolist())
        ticker = ALL_STOCKS[selected]
        df = get_price_data(ticker)
        if not df.empty:
            fig = go.Figure(data=[go.Candlestick(
                x=df.index,
                open=df['Open'], high=df['High'],
                low=df['Low'], close=df['Close'],
                name='Price'
            )])
            fig.update_layout(title=f"{selected} – 6 Months", height=450)
            st.plotly_chart(fig, use_container_width=True)

            close = df['Close'].astype(float)
            rsi = RSIIndicator(close).rsi()
            fig2 = px.line(y=rsi, title="RSI (14)")
            fig2.add_hline(y=70, line_dash="dash", line_color="red")
            fig2.add_hline(y=30, line_dash="dash", line_color="green")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.warning("No chart data.")
    else:
        st.info("No stocks to display.")

st.markdown("---")
st.caption("Data sourced from Yahoo Finance. For educational purposes only. Always do your own research.")
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from ta.momentum import RSIIndicator
from datetime import datetime, timedelta
import json
import os
import time

# Attempt to import sklearn – fallback if not available
try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

st.set_page_config(page_title="Quant Fund Manager", layout="wide")

# ------------------------------
# CLEAN WHITE BACKGROUND WITH DARK RED HEADER
# ------------------------------
st.markdown("""
<style>
    /* Clean white background */
    html, body, [data-testid="stAppViewContainer"] {
        background: #ffffff !important;
    }
    .stApp {
        background: transparent !important;
    }
    /* Headers with dark red */
    h1, h2, h3, h4, h5, h6 {
        color: #8B0000 !important;  /* dark red */
        font-weight: 600;
    }
    .main-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 2rem;
        background: #f8f9fa;
        padding: 1rem 2rem;
        border-radius: 40px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .logo {
        font-size: 1.8rem;
        font-weight: 700;
        color: #8B0000 !important;  /* dark red */
    }
    /* Metric cards – subtle white cards */
    .metric-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 24px;
        padding: 1.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        color: #333;
        transition: all 0.2s ease;
        height: 100%;
    }
    .metric-card:hover {
        box-shadow: 0 8px 24px rgba(0,0,0,0.1);
    }
    .metric-label {
        color: #666;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-value {
        color: #1e3a8a;  /* dark blue */
        font-size: 2rem;
        font-weight: 700;
    }
    .metric-delta {
        color: #333;
    }
    /* Tags */
    .buy-tag {
        background: #d4edda;
        color: #155724;
        padding: 0.25rem 0.8rem;
        border-radius: 30px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
    }
    .sell-tag {
        background: #f8d7da;
        color: #721c24;
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
    .fresh-tag {
        background: #cffafe;
        color: #0e7490;
        padding: 0.25rem 0.8rem;
        border-radius: 30px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
        margin-left: 0.5rem;
    }
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background: #f8f9fa;
        padding: 0.5rem 1.5rem;
        border-radius: 50px;
        border: 1px solid #e0e0e0;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 30px;
        padding: 0.6rem 1.5rem;
        font-weight: 500;
        color: #333;
    }
    .stTabs [aria-selected="true"] {
        background-color: #8B0000 !important;
        color: white !important;
    }
    /* DataFrames */
    .stDataFrame {
        border-radius: 20px;
        overflow: hidden;
        border: 1px solid #e0e0e0;
    }
    .stDataFrame th {
        background: #f8f9fa !important;
        color: #333 !important;
        font-weight: 600;
    }
    .stDataFrame td {
        color: #333 !important;
    }
    /* Dividers */
    hr {
        margin: 2rem 0;
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, #ccc, transparent);
    }
    /* Input section */
    .input-section {
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 30px;
        border: 1px solid #e0e0e0;
        margin-top: 2rem;
    }
    .stTextInput input, .stFileUploader {
        background: white;
        border: 1px solid #ccc;
        border-radius: 30px;
    }
    /* Priority box */
    .priority-box {
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 30px;
        border-left: 6px solid #8B0000;
        border: 1px solid #e0e0e0;
        margin-bottom: 2rem;
        color: #333;
    }
    /* Debug box */
    .debug-box {
        background: #f1f3f5;
        border: 1px dashed #8B0000;
        padding: 1rem;
        border-radius: 16px;
    }
    /* Info/warning messages */
    .stAlert {
        background: #f8f9fa;
        border: 1px solid #ccc;
        color: #333;
        border-radius: 16px;
    }
    /* Buttons */
    .stButton button {
        background: white;
        border: 1px solid #8B0000;
        color: #8B0000;
        border-radius: 30px;
        transition: all 0.2s;
    }
    .stButton button:hover {
        background: #8B0000;
        color: white;
    }
    /* Delete button (small trash can) */
    .delete-btn {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        border-radius: 20px;
        padding: 0.2rem 0.8rem;
    }
    .delete-btn:hover {
        background: #f5c6cb;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------
# MASTER STOCK LIST (all NSE stocks)
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
# DATA FETCHING WITH BETTER ERROR HANDLING
# ------------------------------
@st.cache_data(ttl=1800)  # 30 minutes
def get_price_data(ticker):
    """Fetch price data with retry logic."""
    max_retries = 2
    for attempt in range(max_retries):
        try:
            df = yf.download(ticker, period="6mo", interval="1d", auto_adjust=True, progress=False)
            if df.empty:
                return pd.DataFrame()
            df.dropna(inplace=True)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            return df
        except Exception as e:
            if attempt == max_retries - 1:
                return pd.DataFrame()
            time.sleep(1)  # wait before retry
    return pd.DataFrame()

# ------------------------------
# DATA PERSISTENCE
# ------------------------------
HOLDINGS_FILE = "holdings_data.json"
SOLD_FILE = "sold_history.json"

def load_holdings():
    if os.path.exists(HOLDINGS_FILE):
        try:
            with open(HOLDINGS_FILE, 'r') as f:
                data = json.load(f)
            if data:
                return pd.DataFrame(data)
        except:
            pass
    return None

def save_holdings(df):
    if df is not None and not df.empty:
        records = df.to_dict(orient='records')
        with open(HOLDINGS_FILE, 'w') as f:
            json.dump(records, f, indent=2)
    else:
        if os.path.exists(HOLDINGS_FILE):
            os.remove(HOLDINGS_FILE)

def load_sold():
    if os.path.exists(SOLD_FILE):
        try:
            with open(SOLD_FILE, 'r') as f:
                data = json.load(f)
            if data:
                return pd.DataFrame(data)
        except:
            pass
    return pd.DataFrame(columns=['Stock', 'Qty', 'Avg Price', 'Sell Price', 'Sell Date', 'P&L'])

def save_sold(df):
    if df is not None and not df.empty:
        records = df.to_dict(orient='records')
        with open(SOLD_FILE, 'w') as f:
            json.dump(records, f, indent=2)
    else:
        if os.path.exists(SOLD_FILE):
            os.remove(SOLD_FILE)

# ------------------------------
# IMPROVED FUNDAMENTAL FETCHING (3‑year averages)
# ------------------------------
def safe_get_series(df, key):
    if df is not None and key in df.index:
        vals = df.loc[key]
        if isinstance(vals, pd.Series):
            vals = vals[vals.notna()]
            if len(vals) > 0:
                return vals
    return pd.Series(dtype=float)

def cagr(series, years=3):
    """CAGR over the last `years` (requires at least 2 points)."""
    if len(series) < 2:
        return np.nan
    idx = min(years, len(series)-1)
    latest = series.iloc[0]
    past = series.iloc[idx]
    if past == 0 or np.isnan(past):
        return np.nan
    return ((latest / past) ** (1/idx) - 1) * 100

@st.cache_data(ttl=86400)
def get_fundamental_data(ticker):
    try:
        t = yf.Ticker(ticker)
        info = t.info
        financials = t.financials
        balance_sheet = t.balance_sheet
        cashflow = t.cashflow

        revenue = safe_get_series(financials, 'Total Revenue')
        sales_growth = cagr(revenue, years=3)

        profit = safe_get_series(financials, 'Net Income')
        profit_growth = cagr(profit, years=3)

        market_cap = info.get('marketCap', 0) / 1e7

        ebit_series = safe_get_series(financials, 'EBIT')
        ta_series = safe_get_series(balance_sheet, 'Total Assets')
        cl_series = safe_get_series(balance_sheet, 'Total Current Liabilities')
        roce_values = []
        for i in range(min(len(ebit_series), len(ta_series), len(cl_series))):
            ebit = ebit_series.iloc[i]
            ta = ta_series.iloc[i]
            cl = cl_series.iloc[i]
            capital = ta - cl
            if capital != 0 and not np.isnan(capital) and not np.isnan(ebit):
                roce_values.append((ebit / capital) * 100)
        avg_roce = np.mean(roce_values) if roce_values else np.nan

        total_debt = safe_get_series(balance_sheet, 'Total Debt')
        if len(total_debt) > 0:
            total_debt = total_debt.iloc[0]
        else:
            ltd = safe_get_series(balance_sheet, 'Long Term Debt')
            std = safe_get_series(balance_sheet, 'Short Term Debt')
            total_debt = (ltd.iloc[0] if len(ltd) > 0 else 0) + (std.iloc[0] if len(std) > 0 else 0)
        equity = safe_get_series(balance_sheet, 'Stockholders Equity')
        equity = equity.iloc[0] if len(equity) > 0 else np.nan
        de_ratio = total_debt / equity if equity and equity != 0 else np.nan

        ebit_latest = ebit_series.iloc[0] if len(ebit_series) > 0 else np.nan
        interest = safe_get_series(financials, 'Interest Expense')
        interest = interest.iloc[0] if len(interest) > 0 else np.nan
        icr = ebit_latest / interest if interest and interest != 0 else np.nan

        current_price = info.get('regularMarketPrice', info.get('currentPrice', np.nan))
        high_52w = info.get('fiftyTwoWeekHigh', np.nan)
        down_from_high = ((high_52w - current_price) / high_52w) * 100 if high_52w and current_price else np.nan

        fcf_series = safe_get_series(cashflow, 'Free Cash Flow')
        fcf_cr = fcf_series / 1e7
        avg_fcf = fcf_cr.iloc[:3].mean() if len(fcf_cr) > 0 else np.nan

        promoter = info.get('heldPercentInsiders', np.nan)
        if not pd.isna(promoter):
            promoter = promoter * 100

        cash = info.get('totalCash', 0)
        ev = market_cap * 1e7 + (total_debt if not pd.isna(total_debt) else 0) - cash
        ey = (ebit_latest / ev) * 100 if ev and ev != 0 else np.nan

        return {
            'sales_growth': sales_growth,
            'profit_growth': profit_growth,
            'market_cap': market_cap,
            'roce': avg_roce,
            'de_ratio': de_ratio,
            'icr': icr,
            'down_from_high': down_from_high,
            'avg_fcf': avg_fcf,
            'promoter': promoter,
            'current_price': current_price,
            'info': info,
            'ebit': ebit_latest,
            'ev': ev,
            'ey': ey
        }
    except Exception:
        return None

def screen_stock(fund):
    """Return recommendation based on number of criteria met."""
    if fund is None:
        return "SELL", {}, 0, {}
    criteria = {
        'Sales growth >15%': fund['sales_growth'] > 15 if not pd.isna(fund['sales_growth']) else False,
        'Profit growth >15%': fund['profit_growth'] > 15 if not pd.isna(fund['profit_growth']) else False,
        'Mkt Cap >1000 Cr': fund['market_cap'] > 1000 if not pd.isna(fund['market_cap']) else False,
        'ROCE >15%': fund['roce'] > 15 if not pd.isna(fund['roce']) else False,
        'Debt/Equity <0.5': fund['de_ratio'] < 0.5 if not pd.isna(fund['de_ratio']) else False,
        'ICR >3': fund['icr'] > 3 if not pd.isna(fund['icr']) else False,
        'Down from 52W high >30%': fund['down_from_high'] > 30 if not pd.isna(fund['down_from_high']) else False,
        'Avg FCF >1 Cr': fund['avg_fcf'] > 1 if not pd.isna(fund['avg_fcf']) else False,
        'Promoter >50%': fund['promoter'] > 50 if not pd.isna(fund['promoter']) else False
    }
    criteria_met = sum(criteria.values())
    values = {
        'Sales growth': fund['sales_growth'],
        'Profit growth': fund['profit_growth'],
        'Market Cap': fund['market_cap'],
        'ROCE': fund['roce'],
        'D/E': fund['de_ratio'],
        'ICR': fund['icr'],
        'Down from high': fund['down_from_high'],
        'Avg FCF (Cr)': fund['avg_fcf'],
        'Promoter': fund['promoter']
    }
    # Recommendation logic
    if criteria_met >= 9:
        rec = "BUY"
    elif criteria_met >= 4:
        rec = "HOLD"
    else:
        rec = "SELL"
    return rec, criteria, criteria_met, values

# ------------------------------
# AI SWING SCANNER (unchanged)
# ------------------------------
def train_simple_model(df):
    if not SKLEARN_AVAILABLE or df.empty or len(df) < 60:
        return None, None
    try:
        close = df['Close'].astype(float)
        df_model = df.copy()
        df_model['RSI'] = RSIIndicator(close).rsi()
        df_model['MA20'] = close.rolling(20).mean()
        df_model['Close_MA20'] = close / df_model['MA20']
        df_model['High_Low'] = (df_model['High'] - df_model['Low']) / close
        df_model['Volume_Change'] = df_model['Volume'].pct_change()
        df_model['Target'] = (close.shift(-5) > close * 1.05).astype(int)
        df_model.dropna(inplace=True)
        if len(df_model) < 50:
            return None, None
        features = ['RSI', 'Close_MA20', 'High_Low', 'Volume_Change']
        X = df_model[features]
        y = df_model['Target']
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        model = RandomForestClassifier(n_estimators=30, max_depth=4, random_state=42)
        model.fit(X_scaled, y)
        return model, scaler
    except Exception:
        return None, None

def ai_swing_signal(df, name):
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

        rule_buy = (current_rsi < 45 and ma20.iloc[-1] > ma50.iloc[-1] and current_price > recent_low * 1.02)

        ai_confidence = 0.0
        if SKLEARN_AVAILABLE:
            model, scaler = train_simple_model(df)
            if model is not None and scaler is not None:
                last_rsi = current_rsi
                last_ma20 = ma20.iloc[-1]
                last_close_ma20 = current_price / last_ma20 if last_ma20 != 0 else 1
                last_high_low = (high.iloc[-1] - low.iloc[-1]) / current_price
                last_vol_change = df['Volume'].pct_change().iloc[-1] if len(df) > 1 else 0
                features = np.array([[last_rsi, last_close_ma20, last_high_low, last_vol_change]])
                features_scaled = scaler.transform(features)
                pred_proba = model.predict_proba(features_scaled)[0]
                ai_confidence = pred_proba[1] if len(pred_proba) > 1 else 0

        if rule_buy or ai_confidence > 0.6:
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
            'AI Conf': f"{ai_confidence*100:.0f}%" if ai_confidence > 0 else '-',
            'Entry': round(entry, 2) if not pd.isna(entry) else '-',
            'Target': round(target, 2) if not pd.isna(target) else '-',
            'Stop Loss': round(stop_loss, 2) if not pd.isna(stop_loss) else '-',
            'Holding': int(holding_days) if not pd.isna(holding_days) else '-'
        }
    except Exception:
        return None

# ------------------------------
# INTRADAY PICKS (scans all stocks)
# ------------------------------
def intraday_picks():
    picks = []
    for name, ticker in ALL_STOCKS.items():
        df = get_price_data(ticker)
        if df.empty or len(df) < 20:
            continue
        close = df['Close'].astype(float)
        volume = df['Volume']
        avg_vol = volume.rolling(20).mean().iloc[-1]
        if avg_vol == 0:
            continue
        vol_ratio = volume.iloc[-1] / avg_vol
        ma20 = close.rolling(20).mean().iloc[-1]
        if vol_ratio > 1.2 or close.iloc[-1] > ma20:
            entry = close.iloc[-1]
            target = entry * 1.02
            stop = entry * 0.98
            picks.append({
                'Stock': name,
                'Entry': round(entry, 2),
                'Target': round(target, 2),
                'Stop Loss': round(stop, 2),
                'Volume Surge': f"{vol_ratio:.1f}x",
                'Price vs 20MA': 'Above' if close.iloc[-1] > ma20 else 'Below'
            })
    return picks

# ------------------------------
# SESSION STATE
# ------------------------------
if 'holdings_df' not in st.session_state:
    st.session_state.holdings_df = load_holdings()
if 'portfolio_df' not in st.session_state:
    st.session_state.portfolio_df = None
if 'total_value' not in st.session_state:
    st.session_state.total_value = 0
if 'total_cost' not in st.session_state:
    st.session_state.total_cost = 0
if 'buy_count' not in st.session_state:
    st.session_state.buy_count = 0
if 'swing_history' not in st.session_state:
    st.session_state.swing_history = {}
if 'sold_history' not in st.session_state:
    st.session_state.sold_history = load_sold()

# ------------------------------
# HEADER
# ------------------------------
st.markdown('<div class="main-header"><span class="logo">📈 Quant Fund Manager</span><span style="color:#666;">Professional Edition</span></div>', unsafe_allow_html=True)
st.markdown("#### Institutional‑grade analytics with AI swing scanner, Magic Formula, and intraday picks")

# ------------------------------
# MANUAL REFRESH BUTTON
# ------------------------------
if st.button("🔄 Refresh Data (clear cache)"):
    st.cache_data.clear()
    st.rerun()

# ------------------------------
# SWING TRADING SECTION (scans all stocks)
# ------------------------------
st.markdown("## 🤖 AI Swing Trading Scanner")
st.caption("Scanning all stocks daily. Signals combine technical rules with RandomForest AI. Green highlight = SWING BUY. 'Fresh' tag = first appearance in 5 days.")

with st.spinner("Fetching swing signals..."):
    swing_data = []
    today = datetime.now().date()
    processed = 0
    total = len(ALL_STOCKS)
    progress_bar = st.progress(0, text="Scanning stocks...")
    for idx, (name, ticker) in enumerate(ALL_STOCKS.items()):
        df = get_price_data(ticker)
        sig = ai_swing_signal(df, name)
        if sig and sig['Signal'] == 'SWING BUY':
            last_seen = st.session_state.swing_history.get(name)
            if last_seen is None or (today - last_seen).days >= 5:
                sig['Fresh'] = '✅ Fresh'
                st.session_state.swing_history[name] = today
            else:
                sig['Fresh'] = ''
            swing_data.append(sig)
        processed += 1
        progress_bar.progress((idx+1)/total, text=f"Scanned {idx+1}/{total} stocks")
    progress_bar.empty()

if swing_data:
    swing_df = pd.DataFrame(swing_data)
    def highlight_fresh(row):
        if row['Fresh'] == '✅ Fresh':
            return ['background-color: #cffafe'] * len(row)
        elif row['Signal'] == 'SWING BUY':
            return ['background-color: #d4edda'] * len(row)
        return [''] * len(row)
    st.dataframe(swing_df.style.apply(highlight_fresh, axis=1), use_container_width=True)
else:
    st.warning("No swing buy signals found. This could be due to market hours, data availability, or API limits. Try the refresh button above.")

# ------------------------------
# INTRADAY PICKS SECTION (scans all stocks)
# ------------------------------
st.markdown("## ⚡ Intraday Stock Picks")
st.caption("Stocks with volume surge >1.2x OR price above 20MA. Targets: +2%, Stop: -2%.")
with st.spinner("Scanning for intraday opportunities..."):
    intraday = intraday_picks()
if intraday:
    intraday_df = pd.DataFrame(intraday)
    st.dataframe(intraday_df, use_container_width=True)
else:
    st.info("No intraday picks at this moment. (Market may be closed or no stocks meet criteria.)")

st.markdown("---")

# ------------------------------
# HOLDINGS PROCESSING (with BUY/HOLD/SELL based on criteria count)
# ------------------------------
if st.session_state.holdings_df is not None and not st.session_state.holdings_df.empty:
    if st.session_state.portfolio_df is None:
        portfolio_data = []
        debug_data = []
        total_value = 0
        total_cost = 0
        buy_count = 0
        hold_count = 0
        sell_count = 0
        progress_bar = st.progress(0, text="Analyzing holdings...")
        for idx, row in st.session_state.holdings_df.iterrows():
            name = row['Instrument']
            ticker = ALL_STOCKS.get(name)
            price_df = get_price_data(ticker)
            if price_df.empty:
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
            rec, criteria, criteria_met, values = screen_stock(fund)
            if rec == "BUY":
                buy_count += 1
            elif rec == "HOLD":
                hold_count += 1
            else:
                sell_count += 1
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
                'Criteria Met': criteria_met,
            })
            debug_data.append({
                'Stock': name,
                **values
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
        st.session_state.hold_count = hold_count
        st.session_state.sell_count = sell_count
        st.session_state.debug_df = pd.DataFrame(debug_data)

    # Priority Ranking (simplified)
    st.markdown("## 📊 Buy / Hold / Sell Priority Ranking")
    st.markdown("Based on your formula (growth + quality + undervaluation). Ranked by criteria fit.")

    # Debug expander
    with st.expander("🔍 Debug: Fundamental Values for Your Holdings"):
        st.write("These are the actual computed values for each stock. Compare with the 9 criteria to see why a stock is not a BUY.")
        if 'debug_df' in st.session_state and not st.session_state.debug_df.empty:
            st.dataframe(st.session_state.debug_df.style.format({
                'Sales growth': '{:.2f}%',
                'Profit growth': '{:.2f}%',
                'Market Cap': '₹{:.2f} Cr',
                'ROCE': '{:.2f}%',
                'D/E': '{:.2f}',
                'ICR': '{:.2f}',
                'Down from high': '{:.2f}%',
                'Avg FCF (Cr)': '₹{:.2f} Cr',
                'Promoter': '{:.2f}%'
            }, na_rep='-'), use_container_width=True)
        else:
            st.info("No debug data available.")

    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Portfolio Value</div>
            <div class="metric-value">₹{st.session_state.total_value:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        if st.session_state.total_cost > 0:
            total_pnl = st.session_state.total_value - st.session_state.total_cost
            total_pnl_pct = (total_pnl / st.session_state.total_cost) * 100
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
            <div class="metric-label">BUY / HOLD / SELL</div>
            <div class="metric-value">{st.session_state.buy_count} / {st.session_state.hold_count} / {st.session_state.sell_count}</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Portfolio Size</div>
            <div class="metric-value">{len(st.session_state.portfolio_df)}</div>
        </div>
        """, unsafe_allow_html=True)

    # Allocation pie
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("Portfolio Allocation by Value")
        if not st.session_state.portfolio_df.empty:
            fig = px.pie(st.session_state.portfolio_df, values='Cur Value', names='Stock')
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.subheader("Performance Sparkline")
        st.info("Coming soon")

    st.markdown("---")

    # TABS
    tab1, tab2, tab3 = st.tabs(["📊 Holdings & Recommendations", "📈 Charts", "🧙 Magic Formula"])

    with tab1:
        st.subheader("Your Holdings – Long‑Term Analysis")
        st.caption("BUY = meets all 9 criteria, HOLD = 4-8 criteria, SELL = 0-3 criteria. Click Delete to sell stock.")

        # Display holdings with delete button
        for idx, row in st.session_state.portfolio_df.iterrows():
            col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([1.5,1,1,1,1,1,1,0.8])
            with col1:
                st.write(row['Stock'])
            with col2:
                st.write(f"{row['Qty']:.0f}")
            with col3:
                st.write(f"₹{row['Avg Price']:.2f}" if not pd.isna(row['Avg Price']) else '-')
            with col4:
                st.write(f"₹{row['Current Price']:.2f}")
            with col5:
                st.write(f"₹{row['Cur Value']:.2f}")
            with col6:
                st.write(f"₹{row['P&L']:+.2f}" if not pd.isna(row['P&L']) else '-')
            with col7:
                # Show recommendation tag
                if row['Recommendation'] == 'BUY':
                    st.markdown('<span class="buy-tag">BUY</span>', unsafe_allow_html=True)
                elif row['Recommendation'] == 'HOLD':
                    st.markdown('<span class="hold-tag">HOLD</span>', unsafe_allow_html=True)
                else:
                    st.markdown('<span class="sell-tag">SELL</span>', unsafe_allow_html=True)
            with col8:
                if st.button("🗑️", key=f"del_{idx}"):
                    sold_entry = {
                        'Stock': row['Stock'],
                        'Qty': row['Qty'],
                        'Avg Price': row['Avg Price'],
                        'Sell Price': row['Current Price'],
                        'Sell Date': today.strftime('%Y-%m-%d'),
                        'P&L': row['P&L'] if not pd.isna(row['P&L']) else 0
                    }
                    st.session_state.sold_history = pd.concat([st.session_state.sold_history, pd.DataFrame([sold_entry])], ignore_index=True)
                    save_sold(st.session_state.sold_history)
                    st.session_state.holdings_df = st.session_state.holdings_df[st.session_state.holdings_df['Instrument'] != row['Stock']].reset_index(drop=True)
                    save_holdings(st.session_state.holdings_df)
                    st.session_state.portfolio_df = None
                    st.rerun()

        st.markdown("#### Sold History")
        if not st.session_state.sold_history.empty:
            st.dataframe(st.session_state.sold_history, use_container_width=True)
        else:
            st.info("No sold stocks yet.")

    with tab2:
        st.subheader("Price Chart")
        if not st.session_state.portfolio_df.empty:
            selected = st.selectbox("Select stock", st.session_state.portfolio_df['Stock'].tolist())
            ticker = ALL_STOCKS[selected]
            df = get_price_data(ticker)
            if not df.empty:
                fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
                fig.update_layout(title=f"{selected} – 6 Months", height=450)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No chart data.")
        else:
            st.info("No stocks to display.")

    with tab3:
        st.subheader("Magic Formula Ranking")
        st.caption("Ranked by Return on Capital (ROC) and Earnings Yield (EY).")
        magic_data = []
        for name, ticker in ALL_STOCKS.items():
            fund = get_fundamental_data(ticker)
            if fund and not pd.isna(fund['roce']) and not pd.isna(fund['ey']):
                magic_data.append({'Stock': name, 'ROC (%)': round(fund['roce'], 2), 'EY (%)': round(fund['ey'], 2)})
        if magic_data:
            magic_df = pd.DataFrame(magic_data)
            magic_df['ROC Rank'] = magic_df['ROC (%)'].rank(ascending=False)
            magic_df['EY Rank'] = magic_df['EY (%)'].rank(ascending=False)
            magic_df['Combined'] = magic_df['ROC Rank'] + magic_df['EY Rank']
            magic_df = magic_df.sort_values('Combined').reset_index(drop=True)
            magic_df['Magic Rank'] = magic_df.index + 1
            st.dataframe(magic_df[['Magic Rank', 'Stock', 'ROC (%)', 'EY (%)']], use_container_width=True)
        else:
            st.info("Insufficient data for Magic Formula.")

else:
    st.info("No holdings data. Please add stocks using the section below.")

# ------------------------------
# INPUT SECTION AT BOTTOM
# ------------------------------
st.markdown('<div class="input-section">', unsafe_allow_html=True)
st.subheader("📁 Add Holdings")
col1, col2 = st.columns([2, 1])
with col1:
    uploaded_file = st.file_uploader("Upload Holdings CSV", type=['csv'], key="file_uploader_bottom")
with col2:
    single_stock = st.text_input("Or add a single stock", placeholder="e.g., CIPLA").strip().upper()

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
            original_len = len(df_hold)
            df_hold = df_hold[df_hold['Instrument'].isin(ALL_STOCKS.keys())]
            if len(df_hold) == 0:
                st.error("No stocks from your CSV are in the master list.")
            else:
                st.session_state.holdings_df = df_hold
                save_holdings(df_hold)
                st.session_state.portfolio_df = None
                st.success(f"Loaded {len(df_hold)} stocks from CSV.")
                st.rerun()
    except Exception as e:
        st.error(f"Error reading CSV: {e}")

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
                save_holdings(st.session_state.holdings_df)
                st.session_state.portfolio_df = None
                st.success(f"Added {single_stock}.")
                st.rerun()
            else:
                st.warning(f"{single_stock} already in holdings.")
        else:
            st.session_state.holdings_df = new_row
            save_holdings(st.session_state.holdings_df)
            st.session_state.portfolio_df = None
            st.success(f"Added {single_stock}.")
            st.rerun()
    else:
        st.error(f"{single_stock} not found in master list.")

st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")
st.caption("Data sourced from Yahoo Finance. Recommendations based on your 9‑factor formula.")

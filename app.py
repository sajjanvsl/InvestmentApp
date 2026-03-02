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
# ELEGANT CSS WITH BLUE BACKGROUND
# ------------------------------
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #e6f0ff 0%, #d4e4ff 100%);
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }
    h1, h2, h3 { font-weight: 600; color: #0a2540; }
    .metric-card {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(10px);
        padding: 1.5rem;
        border-radius: 24px;
        box-shadow: 0 10px 30px rgba(0,20,50,0.1);
        border: 1px solid rgba(255,255,255,0.5);
        transition: all 0.2s;
        height: 100%;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 40px rgba(0,30,70,0.15);
    }
    .metric-label {
        font-size: 0.85rem;
        color: #2c3e50;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.25rem;
        opacity: 0.7;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #0a2540;
        line-height: 1.2;
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
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background: rgba(255,255,255,0.6);
        backdrop-filter: blur(8px);
        padding: 0.5rem 1.5rem;
        border-radius: 50px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 30px;
        padding: 0.6rem 1.5rem;
        font-weight: 500;
        color: #0a2540;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1e3a8a;
        color: white !important;
    }
    .stDataFrame {
        border-radius: 20px;
        border: none;
        overflow: hidden;
        box-shadow: 0 8px 20px rgba(0,20,50,0.1);
    }
    hr {
        margin: 2rem 0;
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, #3b82f6, transparent);
    }
    .main-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 2rem;
        background: rgba(255,255,255,0.3);
        backdrop-filter: blur(8px);
        padding: 1rem 2rem;
        border-radius: 40px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.05);
    }
    .logo {
        font-size: 1.8rem;
        font-weight: 700;
        background: linear-gradient(135deg, #1e3a8a, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .input-section {
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(10px);
        padding: 2rem;
        border-radius: 30px;
        box-shadow: 0 8px 25px rgba(0,30,70,0.1);
        margin-top: 2rem;
        border: 1px solid rgba(255,255,255,0.6);
    }
    .priority-box {
        background: rgba(255,255,255,0.8);
        backdrop-filter: blur(10px);
        padding: 2rem;
        border-radius: 30px;
        border-left: 6px solid #1e3a8a;
        box-shadow: 0 10px 30px rgba(0,20,50,0.1);
        margin-bottom: 2rem;
    }
    .debug-box {
        background: rgba(0,0,0,0.03);
        padding: 1rem;
        border-radius: 16px;
        border: 1px dashed #3b82f6;
    }
    .stAlert {
        border-radius: 16px;
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
# DATA PERSISTENCE (unchanged)
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
# IMPROVED FUNDAMENTAL FETCHING (unchanged)
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
    if fund is None:
        return "HOLD", {}, 0, {}
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
    if all(criteria.values()):
        rec = "BUY"
    else:
        rec = "HOLD"
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
# INTRADAY PICKS (unchanged)
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
st.markdown('<div class="main-header"><span class="logo">📈 Quant Fund Manager</span><span style="color:#1e3a8a;">Debug Edition</span></div>', unsafe_allow_html=True)
st.markdown("#### Institutional‑grade analytics with AI swing scanner, Magic Formula, and intraday picks")

# ------------------------------
# MANUAL REFRESH BUTTON
# ------------------------------
if st.button("🔄 Refresh Data (clear cache)"):
    st.cache_data.clear()
    st.rerun()

# ------------------------------
# SWING TRADING SECTION WITH LOADING SPINNER
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


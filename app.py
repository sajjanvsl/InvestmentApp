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

# Attempt to import sklearn – fallback if not available
try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    st.warning("scikit‑learn not installed – AI swing scanner disabled, using rule‑based only.")

st.set_page_config(page_title="Quant Fund Manager", layout="wide")

# ------------------------------
# CUSTOM CSS (unchanged)
# ------------------------------
st.markdown("""
<style>
    .stApp { background-color: #f0f2f6; }
    h1, h2, h3 { font-family: 'Inter', sans-serif; font-weight: 600; color: #0f172a; }
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
    .input-section {
        background: white;
        padding: 2rem;
        border-radius: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin-top: 2rem;
    }
    .priority-box {
        background: white;
        padding: 2rem;
        border-radius: 20px;
        border-left: 5px solid #1e293b;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin-bottom: 2rem;
    }
    .debug-box {
        background: #f1f5f9;
        padding: 1rem;
        border-radius: 10px;
        font-family: monospace;
        font-size: 0.8rem;
        margin-top: 1rem;
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
# DATA PERSISTENCE (JSON)
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
    # Series is from latest to oldest (index 0 = most recent)
    # Take the value ~years ago if available, else the oldest.
    idx = min(years, len(series)-1)
    latest = series.iloc[0]
    past = series.iloc[idx]
    if past == 0 or np.isnan(past):
        return np.nan
    return ((latest / past) ** (1/idx) - 1) * 100

def mean_series(series, years=3):
    """Average over the last `years` (or all if less)."""
    if len(series) == 0:
        return np.nan
    recent = series.iloc[:min(years, len(series))]
    return recent.mean()

@st.cache_data(ttl=86400)
def get_fundamental_data(ticker):
    try:
        t = yf.Ticker(ticker)
        info = t.info
        financials = t.financials
        balance_sheet = t.balance_sheet
        cashflow = t.cashflow

        # Revenue growth (3‑year CAGR)
        revenue = safe_get_series(financials, 'Total Revenue')
        sales_growth = cagr(revenue, years=3)

        # Profit growth (3‑year CAGR)
        profit = safe_get_series(financials, 'Net Income')
        profit_growth = cagr(profit, years=3)

        # Market Cap (in Crores)
        market_cap = info.get('marketCap', 0) / 1e7

        # ROCE (average over 3 years)
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

        # Debt to Equity (latest)
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

        # Interest Coverage Ratio (latest)
        ebit_latest = ebit_series.iloc[0] if len(ebit_series) > 0 else np.nan
        interest = safe_get_series(financials, 'Interest Expense')
        interest = interest.iloc[0] if len(interest) > 0 else np.nan
        icr = ebit_latest / interest if interest and interest != 0 else np.nan

        # Down from 52W high
        current_price = info.get('regularMarketPrice', info.get('currentPrice', np.nan))
        high_52w = info.get('fiftyTwoWeekHigh', np.nan)
        down_from_high = ((high_52w - current_price) / high_52w) * 100 if high_52w and current_price else np.nan

        # Free Cash Flow – average of last 3 years > 1 (in Crores)
        fcf_series = safe_get_series(cashflow, 'Free Cash Flow')
        # Convert to Crores (1e7)
        fcf_cr = fcf_series / 1e7
        avg_fcf = fcf_cr.iloc[:3].mean() if len(fcf_cr) > 0 else np.nan

        # Promoter holding – from 'heldPercentInsiders' (convert to %)
        promoter = info.get('heldPercentInsiders', np.nan)
        if not pd.isna(promoter):
            promoter = promoter * 100

        # Magic Formula components
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
            'avg_fcf': avg_fcf,          # average FCF in Crores
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
# INTRADAY PICKS (more inclusive)
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
        # Condition: volume surge > 1.2x OR price > 20MA
        if vol_ratio > 1.2 or close.iloc[-1] > ma20:
            entry = close.iloc[-1]
            target = entry * 1.02  # 2% target
            stop = entry * 0.98     # 2% stop
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
# SESSION STATE (load persisted data)
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
st.markdown('<div class="main-header"><span class="logo">📈 Quant Fund Manager</span><span style="color:#64748b;">Debug Edition</span></div>', unsafe_allow_html=True)
st.markdown("#### Institutional‑grade analytics with AI swing scanner, Magic Formula, and intraday picks")

# ------------------------------
# SWING TRADING SECTION
# ------------------------------
st.markdown("## 🤖 AI Swing Trading Scanner")
st.caption("Scanning all stocks daily. Signals combine technical rules with RandomForest AI. Green highlight = SWING BUY. 'Fresh' tag = first appearance in 5 days.")

swing_data = []
today = datetime.now().date()
for name, ticker in ALL_STOCKS.items():
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
    st.info("No swing buy signals today.")

# ------------------------------
# INTRADAY PICKS SECTION
# ------------------------------
st.markdown("## ⚡ Intraday Stock Picks")
st.caption("Stocks with volume surge >1.2x OR price above 20MA. Targets: +2%, Stop: -2%.")
intraday = intraday_picks()
if intraday:
    intraday_df = pd.DataFrame(intraday)
    st.d            capital_employed = ta - cl
            if capital_employed != 0 and not np.isnan(capital_employed) and not np.isnan(ebit):
                roce_values.append((ebit / capital_employed) * 100)
        avg_roce = np.mean(roce_values) if roce_values else np.nan

        # Debt to Equity (latest)
        total_debt = safe_get_latest(balance_sheet, 'Total Debt')
        if pd.isna(total_debt):
            ltd = safe_get_latest(balance_sheet, 'Long Term Debt')
            std = safe_get_latest(balance_sheet, 'Short Term Debt')
            total_debt = (ltd if not pd.isna(ltd) else 0) + (std if not pd.isna(std) else 0)
        equity = safe_get_latest(balance_sheet, 'Stockholders Equity')
        de_ratio = total_debt / equity if equity and equity != 0 else np.nan

        # Interest Coverage Ratio (latest)
        ebit_latest = safe_get_latest(financials, 'EBIT')
        interest = safe_get_latest(financials, 'Interest Expense')
        icr = ebit_latest / interest if interest and interest != 0 else np.nan

        # Down from 52W high
        current_price = info.get('regularMarketPrice', info.get('currentPrice', np.nan))
        high_52w = info.get('fiftyTwoWeekHigh', np.nan)
        down_from_high = ((high_52w - current_price) / high_52w) * 100 if high_52w and current_price else np.nan

        # Free Cash Flow – check if any of the last 3 years are positive
        fcf_series = safe_get_series(cashflow, 'Free Cash Flow')
        fcf_positive_any = (fcf_series > 0).any() if len(fcf_series) > 0 else False

        # Promoter holding – try 'heldPercentInsiders' from info
        promoter = info.get('heldPercentInsiders', np.nan)
        if not pd.isna(promoter):
            promoter = promoter * 100  # convert to percentage

        # Magic Formula components
        cash = info.get('totalCash', np.nan)
        if pd.isna(cash):
            cash = 0
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
            'fcf_positive': fcf_positive_any,
            'promoter': promoter,
            'current_price': current_price,
            'info': info,
            'ebit': ebit_latest,
            'ev': ev,
            'ey': ey
        }
    except Exception as e:
        # Optionally log e for debugging
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
        'FCF positive (any 3y)': fund['fcf_positive'],  # any positive in last 3 years
        'Promoter >50%': fund['promoter'] > 50 if not pd.isna(fund['promoter']) else False
    }
    criteria_met = sum(criteria.values())
    # For debugging, we can also return the raw values
    values = {
        'Sales growth': fund['sales_growth'],
        'Profit growth': fund['profit_growth'],
        'Market Cap': fund['market_cap'],
        'ROCE': fund['roce'],
        'D/E': fund['de_ratio'],
        'ICR': fund['icr'],
        'Down from high': fund['down_from_high'],
        'FCF positive': fund['fcf_positive'],
        'Promoter': fund['promoter']
    }
    if all(criteria.values()):
        rec = "BUY"
    else:
        rec = "HOLD"
    return rec, criteria, criteria_met, values

# ------------------------------
# (Rest of the app unchanged, but in the processing loop we now have `values` for debug)
# ------------------------------


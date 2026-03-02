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
# CUSTOM CSS (unchanged, professional)
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
    .priority-box h3 {
        margin-top: 0;
    }
    .priority-tier1 {
        color: #166534;
        font-weight: 600;
    }
    .priority-tier2 {
        color: #0e7490;
        font-weight: 600;
    }
    .priority-hold {
        color: #b45309;
    }
    .priority-caution {
        color: #92400e;
    }
    .priority-sell {
        color: #b91c1c;
    }
    .delete-btn {
        background-color: #fee2e2;
        color: #991b1b;
        border: none;
        border-radius: 20px;
        padding: 0.2rem 0.8rem;
        font-size: 0.8rem;
        cursor: pointer;
    }
    .delete-btn:hover {
        background-color: #fecaca;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------
# MASTER STOCK LIST
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
# DATA PERSISTENCE (JSON file)
# ------------------------------
HOLDINGS_FILE = "holdings_data.json"

def load_holdings():
    """Load holdings from JSON file. Returns DataFrame or None."""
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
    """Save holdings DataFrame to JSON file."""
    if df is not None and not df.empty:
        # Convert to records for JSON
        records = df.to_dict(orient='records')
        with open(HOLDINGS_FILE, 'w') as f:
            json.dump(records, f, indent=2)
    else:
        # If empty, remove file
        if os.path.exists(HOLDINGS_FILE):
            os.remove(HOLDINGS_FILE)

def load_sold_history():
    """Load sold stocks history from JSON."""
    sold_file = "sold_history.json"
    if os.path.exists(sold_file):
        try:
            with open(sold_file, 'r') as f:
                data = json.load(f)
            if data:
                return pd.DataFrame(data)
        except:
            pass
    return pd.DataFrame(columns=['Stock', 'Qty', 'Avg Price', 'Sell Price', 'Sell Date', 'P&L'])

def save_sold_history(df):
    """Save sold history."""
    sold_file = "sold_history.json"
    if df is not None and not df.empty:
        records = df.to_dict(orient='records')
        with open(sold_file, 'w') as f:
            json.dump(records, f, indent=2)
    else:
        if os.path.exists(sold_file):
            os.remove(sold_file)

# ------------------------------
# DATA FETCHING (cached)
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

        market_cap = info.get('marketCap', 0) / 1e7

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

        # Magic Formula components
        # Enterprise Value = Market Cap + Debt - Cash
        cash = info.get('totalCash', np.nan)
        if pd.isna(cash):
            cash = 0
        ev = market_cap * 1e7 + (total_debt if not pd.isna(total_debt) else 0) - cash
        ey = (ebit / ev) * 100 if ev and ev != 0 else np.nan

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
            'info': info,
            'ebit': ebit,
            'ev': ev,
            'ey': ey
        }
    except Exception:
        return None

def screen_stock(fund):
    if fund is None:
        return "HOLD", {}, 0
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
    criteria_met = sum(criteria.values())
    if all(criteria.values()):
        rec = "BUY"
    else:
        rec = "HOLD"
    return rec, criteria, criteria_met

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
# INTRADAY SELECTION (simple logic)
# ------------------------------
def intraday_picks():
    """Generate simple intraday picks based on volume and price action."""
    picks = []
    for name, ticker in ALL_STOCKS.items():
        df = get_price_data(ticker)
        if df.empty or len(df) < 5:
            continue
        close = df['Close'].astype(float)
        volume = df['Volume']
        # Conditions: volume > 1.5x average(20), price > 20MA, and positive day
        avg_vol = volume.rolling(20).mean().iloc[-1]
        if avg_vol == 0:
            continue
        vol_ratio = volume.iloc[-1] / avg_vol
        ma20 = close.rolling(20).mean().iloc[-1]
        prev_close = close.iloc[-2] if len(close) > 1 else close.iloc[-1]
        day_change = (close.iloc[-1] - prev_close) / prev_close * 100
        if vol_ratio > 1.5 and close.iloc[-1] > ma20 and day_change > 1:
            entry = close.iloc[-1]
            target = entry * 1.03  # 3% target
            stop = entry * 0.98     # 2% stop
            picks.append({
                'Stock': name,
                'Entry': round(entry, 2),
                'Target': round(target, 2),
                'Stop Loss': round(stop, 2),
                'Volume Surge': f"{vol_ratio:.1f}x",
                'Day Change %': f"{day_change:.1f}%"
            })
    return picks

# ------------------------------
# SESSION STATE INIT (load persisted data)
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
    st.session_state.sold_history = load_sold_history()

# ------------------------------
# HEADER
# ------------------------------
st.markdown('<div class="main-header"><span class="logo">📈 Quant Fund Manager</span><span style="color:#64748b;">AI‑Powered Edition</span></div>', unsafe_allow_html=True)
st.markdown("#### Institutional‑grade analytics with AI swing scanner, Magic Formula, and intraday picks")

# ------------------------------
# SWING TRADING SECTION (top)
# ------------------------------
st.markdown("## 🤖 AI Swing Trading Scanner")
st.caption("Scanning all stocks daily. Signals combine technical rules with RandomForest AI (trained on 5‑day forward returns). Green highlight = SWING BUY. 'Fresh' tag = first appearance in 5 days.")

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
# INTRADAY PICKS SECTION (after swing)
# ------------------------------
st.markdown("## ⚡ Intraday Stock Picks")
st.caption("Stocks with volume surge >1.5x average, price above 20MA, and positive day change. Targets: +3%, Stop: -2%.")
intraday = intraday_picks()
if intraday:
    intraday_df = pd.DataFrame(intraday)
    st.dataframe(intraday_df, use_container_width=True)
else:
    st.info("No intraday picks at this moment.")

st.markdown("---")

# ------------------------------
# HOLDINGS PROCESSING (with criteria count)
# ------------------------------
if st.session_state.holdings_df is not None and not st.session_state.holdings_df.empty:
    if st.session_state.portfolio_df is None:
        portfolio_data = []
        total_value = 0
        total_cost = 0
        buy_count = 0
        progress_bar = st.progress(0, text="Analyzing holdings...")
        for idx, row in st.session_state.holdings_df.iterrows():
          

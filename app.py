import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
from datetime import datetime, timedelta
import json
import os
import time
import hashlib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import traceback

# Attempt to import sklearn – fallback if not available
try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

st.set_page_config(page_title="Quant Fund Manager", layout="wide")

# ------------------------------
# ENHANCED CSS (professional, dark red header, white background)
# ------------------------------
st.markdown("""
<style>
    /* Clean white background */
    html, body, [data-testid="stAppViewContainer"] {
        background: #f5f7fa !important;
    }
    .stApp {
        background: transparent !important;
    }
    /* Headers with dark red */
    h1, h2, h3, h4, h5, h6 {
        color: #8B0000 !important;
        font-weight: 700;
        letter-spacing: -0.02em;
    }
    /* Table headers - general */
    .stDataFrame th {
        background: #2c3e50 !important;
        color: white !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        padding: 12px !important;
        text-align: center !important;
    }
    .stDataFrame td {
        font-size: 1rem !important;
        padding: 10px !important;
    }
    /* Holdings table specific header */
    .holdings-table thead tr th {
        background: #1E3A8A !important;  /* dark blue */
        color: white !important;
        font-weight: bold !important;
        font-size: 1.1rem !important;
        text-align: center !important;
    }
    /* Metric cards */
    .metric-card {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 8px 20px rgba(0,0,0,0.06);
        border: 1px solid #e9ecef;
        transition: all 0.2s ease;
        height: 100%;
    }
    .metric-card:hover {
        box-shadow: 0 12px 30px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }
    .metric-label {
        color: #6c757d;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-value {
        color: #1e3a8a;
        font-size: 2rem;
        font-weight: 700;
    }
    /* Tags */
    .super-buy-tag {
        background: #8B0000;
        color: white;
        padding: 0.25rem 0.8rem;
        border-radius: 30px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
        box-shadow: 0 2px 8px rgba(139,0,0,0.3);
    }
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
    .fairvalue-tag {
        background: #cce5ff;
        color: #004085;
        padding: 0.25rem 0.8rem;
        border-radius: 30px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
    }
    .criteria-pass {
        color: #28a745;
        font-weight: 600;
        font-size: 1.2rem;
    }
    .criteria-fail {
        color: #dc3545;
        font-weight: 600;
        font-size: 1.2rem;
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
    .top-pick-badge {
        background: #ffc107;
        color: #000;
        padding: 0.2rem 1rem;
        border-radius: 30px;
        font-weight: 700;
        font-size: 0.9rem;
        display: inline-block;
        margin-bottom: 0.5rem;
        box-shadow: 0 2px 8px rgba(255,193,7,0.4);
    }
    .no-stocks-message {
        background: #f8f9fa;
        border-left: 4px solid #8B0000;
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1rem 0;
        font-size: 1.1rem;
        color: #495057;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background: white;
        padding: 0.5rem 1.5rem;
        border-radius: 50px;
        border: 1px solid #dee2e6;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 30px;
        padding: 0.6rem 1.5rem;
        font-weight: 500;
        color: #495057;
    }
    .stTabs [aria-selected="true"] {
        background-color: #8B0000 !important;
        color: white !important;
    }
    .main-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 2rem;
        background: white;
        padding: 1rem 2rem;
        border-radius: 40px;
        border: 1px solid #dee2e6;
        box-shadow: 0 4px 12px rgba(0,0,0,0.04);
    }
    .logo {
        font-size: 1.8rem;
        font-weight: 700;
        color: #8B0000 !important;
    }
    .input-section {
        background: white;
        padding: 2rem;
        border-radius: 30px;
        border: 1px solid #dee2e6;
        margin-top: 2rem;
        box-shadow: 0 8px 20px rgba(0,0,0,0.04);
    }
    .stButton button {
        background: white;
        border: 1px solid #8B0000;
        color: #8B0000;
        border-radius: 30px;
        font-weight: 500;
        transition: all 0.2s;
    }
    .stButton button:hover {
        background: #8B0000;
        color: white;
    }
    hr {
        margin: 2rem 0;
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, #adb5bd, transparent);
    }
    .criteria-table {
        background: white;
        border-radius: 16px;
        padding: 1rem;
        margin: 1rem 0;
        border: 1px solid #dee2e6;
    }
    .criteria-row {
        display: flex;
        justify-content: space-between;
        padding: 0.5rem;
        border-bottom: 1px solid #f0f0f0;
    }
    .criteria-row:last-child {
        border-bottom: none;
    }
    /* Debug info */
    .debug-info {
        background: #e9ecef;
        padding: 1rem;
        border-radius: 8px;
        font-family: monospace;
        font-size: 0.9rem;
        margin: 1rem 0;
    }
    /* Alert settings section */
    .alert-settings {
        background: #e8f4fd;
        padding: 1.5rem;
        border-radius: 16px;
        margin: 1rem 0;
        border-left: 4px solid #007bff;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------
# ALERT SYSTEM
# ------------------------------
class AlertSystem:
    def __init__(self):
        self.alert_cooldown = {}  # stock -> last alert time
        self.cooldown_minutes = 15
        
    def should_send_alert(self, symbol):
        """Check if enough time has passed since last alert."""
        current_time = time.time()
        if symbol in self.alert_cooldown:
            last_alert = self.alert_cooldown[symbol]
            minutes_passed = (current_time - last_alert) / 60
            if minutes_passed < self.cooldown_minutes:
                return False
        self.alert_cooldown[symbol] = current_time
        return True
    
    def send_email_alert(self, stock_name, current_price, target_price):
        """Send email alert via Gmail SMTP."""
        if not st.session_state.get('email_enabled', False):
            return False
            
        sender_email = st.session_state.get('email_sender', '')
        sender_password = st.session_state.get('email_password', '')
        recipient_email = st.session_state.get('email_recipient', '')
        
        if not all([sender_email, sender_password, recipient_email]):
            return False
            
        subject = f"🚨 BUY ALERT: {stock_name}"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #8B0000;">📈 Buy Alert: {stock_name}</h2>
            <table style="border-collapse: collapse; width: 100%; max-width: 400px;">
                <tr style="background-color: #f2f2f2;">
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Current Price:</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">₹{current_price:.2f}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Your Target Price:</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">₹{target_price:.2f}</td>
                </tr>
                <tr style="background-color: #f2f2f2;">
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Time:</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td>
                </tr>
            </table>
            <p style="margin-top: 20px; color: #666;">
                <small>This is an automated alert from Quant Fund Manager.</small>
            </p>
        </body>
        </html>
        """
        
        try:
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = recipient_email
            msg['Subject'] = subject
            msg.attach(MIMEText(html_body, 'html'))
            
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            server.quit()
            return True
        except Exception as e:
            st.error(f"Email failed: {str(e)}")
            return False
    
    def send_telegram_alert(self, stock_name, current_price, target_price):
        """Send Telegram alert via bot."""
        if not st.session_state.get('telegram_enabled', False):
            return False
            
        bot_token = st.session_state.get('telegram_bot_token', '')
        chat_id = st.session_state.get('telegram_chat_id', '')
        
        if not all([bot_token, chat_id]):
            return False
            
        message = f"""🚨 *BUY ALERT: {stock_name}*
        
📊 *Current Price:* ₹{current_price:.2f}
🎯 *Your Target:* ₹{target_price:.2f}
⏰ *Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

_This is an automated alert from Quant Fund Manager._"""
        
        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            response = requests.post(url, json=payload)
            return response.status_code == 200
        except Exception as e:
            st.error(f"Telegram failed: {str(e)}")
            return False
    
    def check_and_send_alerts(self, stock_name, current_price, target_prices):
        """Check if any alerts should be sent."""
        alerts_sent = []
        
        # Check if current price <= any target price
        for target_price in target_prices:
            if current_price <= target_price and self.should_send_alert(f"{stock_name}_{target_price}"):
                # Send email
                if st.session_state.get('email_enabled', False):
                    if self.send_email_alert(stock_name, current_price, target_price):
                        alerts_sent.append(f"Email at ₹{target_price:.2f}")
                
                # Send Telegram
                if st.session_state.get('telegram_enabled', False):
                    if self.send_telegram_alert(stock_name, current_price, target_price):
                        alerts_sent.append(f"Telegram at ₹{target_price:.2f}")
        
        return alerts_sent

# Initialize alert system in session state
if 'alert_system' not in st.session_state:
    st.session_state.alert_system = AlertSystem()
if 'target_prices' not in st.session_state:
    st.session_state.target_prices = {}  # stock -> list of target prices
if 'price_alerts' not in st.session_state:
    st.session_state.price_alerts = {}   # stock -> list of triggered alerts

# ------------------------------
# AUTHENTICATION FUNCTIONS
# ------------------------------
USERS_FILE = "users.json"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    else:
        default_users = {
            "admin": hash_password("admin123")
        }
        with open(USERS_FILE, 'w') as f:
            json.dump(default_users, f)
        return default_users

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

def check_login(username, password):
    users = load_users()
    if username in users and users[username] == hash_password(password):
        return True
    return False

def reset_password(username, new_password):
    users = load_users()
    if username in users:
        users[username] = hash_password(new_password)
        save_users(users)
        return True
    return False

# Initialize session state for authentication
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = None

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
    "TDPOWERSYS": "TDPOWERSYS.NS",
    "MCX": "MCX.NS"
}

# ------------------------------
# DEBUG DATA FETCHING
# ------------------------------
def debug_data_fetch(ticker):
    try:
        df = yf.download(ticker, period="5d", interval="1d", progress=False)
        if df.empty:
            return "❌ No data"
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        close = df['Close'].squeeze()
        if isinstance(close, pd.Series):
            last_close = close.iloc[-1]
        else:
            last_close = close
        return f"✅ Data shape: {df.shape}, Last close: {last_close:.2f}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

# ------------------------------
# DATA FETCHING WITH RETRIES
# ------------------------------
@st.cache_data(ttl=1800, show_spinner=False)
def get_price_data(ticker):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            df = yf.download(ticker, period="6mo", interval="1d", auto_adjust=True, progress=False)
            if df.empty:
                if attempt == max_retries - 1:
                    return pd.DataFrame()
                time.sleep(2)
                continue
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df.dropna(inplace=True)
            return df
        except Exception:
            if attempt == max_retries - 1:
                return pd.DataFrame()
            time.sleep(2)
    return pd.DataFrame()

@st.cache_data(ttl=300, show_spinner=False)
def get_intraday_data(ticker):
    max_retries = 2
    for attempt in range(max_retries):
        try:
            df = yf.download(ticker, period="1d", interval="5m", auto_adjust=True, progress=False)
            if df.empty:
                return pd.DataFrame()
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df.dropna(inplace=True)
            return df
        except Exception:
            if attempt == max_retries - 1:
                return pd.DataFrame()
            time.sleep(1)
    return pd.DataFrame()

# ------------------------------
# DATA PERSISTENCE
# ------------------------------
HOLDINGS_FILE = "holdings_data.json"
SOLD_FILE = "sold_history.json"
TARGET_PRICES_FILE = "target_prices.json"

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

def load_target_prices():
    """Load target prices from JSON file."""
    if os.path.exists(TARGET_PRICES_FILE):
        try:
            with open(TARGET_PRICES_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}

def save_target_prices(target_dict):
    """Save target prices to JSON file."""
    with open(TARGET_PRICES_FILE, 'w') as f:
        json.dump(target_dict, f, indent=2)

# ------------------------------
# FUNDAMENTAL FETCHING
# ------------------------------
def safe_get_series(df, key):
    if df is not None and key in df.index:
        vals = df.loc[key]
        if isinstance(vals, pd.Series):
            vals = vals[vals.notna()]
            if len(vals) > 0:
                return vals
    return pd.Series(dtype=float)

def cagr(series, years=5):
    if len(series) < 2:
        return np.nan
    idx = min(years, len(series)-1)
    latest = series.iloc[0]
    past = series.iloc[idx]
    if past == 0 or np.isnan(past):
        return np.nan
    return ((latest / past) ** (1/idx) - 1) * 100

@st.cache_data(ttl=86400, show_spinner=False)
def get_fundamental_data(ticker):
    try:
        t = yf.Ticker(ticker)
        info = t.info
        financials = t.financials
        balance_sheet = t.balance_sheet
        cashflow = t.cashflow

        revenue = safe_get_series(financials, 'Total Revenue')
        sales_growth_5y = cagr(revenue, years=5)
        sales_growth_3y = cagr(revenue, years=3)

        profit = safe_get_series(financials, 'Net Income')
        profit_growth_5y = cagr(profit, years=5)
        profit_growth_3y = cagr(profit, years=3)

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
        cash = info.get('totalCash', 0)
        invested_capital = (total_debt if not pd.isna(total_debt) else 0) + (equity if not pd.isna(equity) else 0) - cash
        ebit_latest = ebit_series.iloc[0] if len(ebit_series) > 0 else np.nan
        roic = (ebit_latest / invested_capital) * 100 if invested_capital and invested_capital != 0 else np.nan

        de_ratio = total_debt / equity if equity and equity != 0 else np.nan
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

        book_value = info.get('bookValue', np.nan)
        net_profit = profit.iloc[0] / 1e7 if len(profit) > 0 else np.nan
        pe = info.get('trailingPE', np.nan)
        ey = (1 / pe) * 100 if not pd.isna(pe) and pe > 0 else np.nan

        return {
            'sales_growth_3y': sales_growth_3y,
            'profit_growth_3y': profit_growth_3y,
            'sales_growth_5y': sales_growth_5y,
            'profit_growth_5y': profit_growth_5y,
            'market_cap': market_cap,
            'roce': avg_roce,
            'roic': roic,
            'de_ratio': de_ratio,
            'icr': icr,
            'down_from_high': down_from_high,
            'avg_fcf': avg_fcf,
            'promoter': promoter,
            'book_value': book_value,
            'net_profit': net_profit,
            'ey': ey,
            'current_price': current_price,
            'info': info
        }
    except Exception:
        return None

# ------------------------------
# COMBINED SCREENER (Original 9 + Magic Formula 10)
# ------------------------------
def screen_stock(fund):
    if fund is None:
        return "SELL", {}, 0, {}
    
    criteria_original = {
        'Sales growth 3Y >15%': fund['sales_growth_3y'] > 15 if not pd.isna(fund['sales_growth_3y']) else False,
        'Profit growth 3Y >15%': fund['profit_growth_3y'] > 15 if not pd.isna(fund['profit_growth_3y']) else False,
        'Mkt Cap >1000 Cr': fund['market_cap'] > 1000 if not pd.isna(fund['market_cap']) else False,
        'ROCE >15%': fund['roce'] > 15 if not pd.isna(fund['roce']) else False,
        'Debt/Equity <0.5': fund['de_ratio'] < 0.5 if not pd.isna(fund['de_ratio']) else False,
        'ICR >3': fund['icr'] > 3 if not pd.isna(fund['icr']) else False,
        'Down from 52W high >30%': fund['down_from_high'] > 30 if not pd.isna(fund['down_from_high']) else False,
        'Avg FCF >1 Cr': fund['avg_fcf'] > 1 if not pd.isna(fund['avg_fcf']) else False,
        'Promoter >50%': fund['promoter'] > 50 if not pd.isna(fund['promoter']) else False
    }
    
    criteria_magic = {
        'ROIC >25%': fund['roic'] > 25 if not pd.isna(fund['roic']) else False,
        'Earnings Yield >15%': fund['ey'] > 15 if not pd.isna(fund['ey']) else False,
        'Book Value >0': fund['book_value'] > 0 if not pd.isna(fund['book_value']) else False,
        'Market Cap >15 Cr': fund['market_cap'] > 15 if not pd.isna(fund['market_cap']) else False,
        'ROCE >20%': fund['roce'] > 20 if not pd.isna(fund['roce']) else False,
        'Sales growth 5Y >10%': fund['sales_growth_5y'] > 10 if not pd.isna(fund['sales_growth_5y']) else False,
        'Profit growth 5Y >15%': fund['profit_growth_5y'] > 15 if not pd.isna(fund['profit_growth_5y']) else False,
        'Debt/Equity <0.2': fund['de_ratio'] < 0.2 if not pd.isna(fund['de_ratio']) else False,
        'Promoter >60%': fund['promoter'] > 60 if not pd.isna(fund['promoter']) else False,
        'Net Profit >200 Cr': fund['net_profit'] > 200 if not pd.isna(fund['net_profit']) else False
    }
    
    all_criteria = {**criteria_original, **criteria_magic}
    criteria_met = sum(all_criteria.values())
    total_criteria = len(all_criteria)
    
    values = {
        'Sales Gr 3Y': fund['sales_growth_3y'],
        'Profit Gr 3Y': fund['profit_growth_3y'],
        'Sales Gr 5Y': fund['sales_growth_5y'],
        'Profit Gr 5Y': fund['profit_growth_5y'],
        'Mkt Cap': fund['market_cap'],
        'ROCE': fund['roce'],
        'ROIC': fund['roic'],
        'D/E': fund['de_ratio'],
        'ICR': fund['icr'],
        'Down 52W': fund['down_from_high'],
        'Avg FCF': fund['avg_fcf'],
        'Promoter': fund['promoter'],
        'Book Value': fund['book_value'],
        'Net Profit': fund['net_profit'],
        'EY': fund['ey']
    }
    
    if criteria_met >= total_criteria * 0.8:
        rec = "SUPER BUY"
    elif criteria_met >= total_criteria * 0.6:
        rec = "BUY"
    elif criteria_met >= total_criteria * 0.3:
        rec = "HOLD"
    else:
        rec = "SELL"
        
    return rec, all_criteria, criteria_met, values

# ------------------------------
# TRAIN SIMPLE MODEL (fixed feature names warning)
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
        
        feature_names = ['RSI', 'Close_MA20', 'High_Low', 'Volume_Change']
        X = df_model[feature_names]
        y = df_model['Target']
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        scaler.feature_names_in_ = feature_names
        
        model = RandomForestClassifier(n_estimators=30, max_depth=4, random_state=42)
        model.fit(X_scaled, y)
        
        return model, scaler
    except Exception:
        return None, None

# ------------------------------
# SCREENER FUNCTIONS
# ------------------------------

def calculate_fair_value(fund):
    """Calculate intrinsic value using a simplified DCF model."""
    try:
        if fund is None:
            return None
        
        # Get required data
        fcf = fund.get('avg_fcf')  # Average FCF in Cr
        growth_rate = fund.get('profit_growth_5y')  # 5-year profit growth
        if pd.isna(growth_rate) or growth_rate <= 0:
            growth_rate = 10  # default 10% if no data
        
        # Parameters for DCF
        projection_years = 5
        discount_rate = 12  # 12% required return
        terminal_growth = 4  # 4% perpetual growth
        
        # Project FCF for next 5 years
        projected_fcf = []
        for i in range(1, projection_years + 1):
            projected_fcf.append(fcf * ((1 + growth_rate/100) ** i))
        
        # Calculate present value of projected FCF
        pv_fcf = sum([fcf / ((1 + discount_rate/100) ** (i+1)) for i, fcf in enumerate(projected_fcf)])
        
        # Calculate terminal value
        terminal_fcf = projected_fcf[-1] * (1 + terminal_growth/100)
        terminal_value = terminal_fcf / ((discount_rate/100) - (terminal_growth/100))
        pv_terminal = terminal_value / ((1 + discount_rate/100) ** projection_years)
        
        # Total intrinsic value (in Cr)
        intrinsic_value_cr = pv_fcf + pv_terminal
        
        # Per share value
        shares_outstanding = fund.get('info', {}).get('sharesOutstanding', 0)
        if shares_outstanding > 0:
            intrinsic_value_per_share = (intrinsic_value_cr * 1e7) / shares_outstanding
            return intrinsic_value_per_share
        else:
            return None
    except Exception:
        return None

def fair_value_signal(df, name):
    """Identify stocks trading at least 15% below fair value."""
    if df.empty:
        return None
    try:
        # Fetch fundamental data
        fund = get_fundamental_data(ALL_STOCKS[name])
        if fund is None:
            return None
        
        # Get current price
        close = df['Close'].astype(float)
        current_price = close.iloc[-1]
        
        # Calculate fair value
        fair_value = calculate_fair_value(fund)
        if fair_value is None:
            return None
        
        # Calculate discount
        discount = ((fair_value - current_price) / fair_value) * 100
        
        # Only include if trading at least 15% below fair value
        if discount >= 15:
            return {
                'Stock': name,
                'Current Price': round(current_price, 2),
                'Fair Value': round(fair_value, 2),
                'Discount %': round(discount, 1),
                'Upside': round(discount, 1),
                'Signal': 'BUY ON DIP',
                'FCF (Cr)': round(fund.get('avg_fcf', 0), 2),
                'Growth 5Y %': round(fund.get('profit_growth_5y', 0), 1),
                'ROCE %': round(fund.get('roce', 0), 1)
            }
        return None
    except Exception:
        return None

def swing_breakout_signal(df, name):
    if df.empty or len(df) < 50:
        return None
    try:
        close = df['Close'].astype(float)
        high = df['High'].astype(float)
        volume = df['Volume'].astype(float)
        ema50 = close.ewm(span=50, adjust=False).mean()
        ema200 = close.ewm(span=200, adjust=False).mean()
        rsi = RSIIndicator(close).rsi()
        volume_sma20 = volume.rolling(20).mean()
        highest_high_20 = high.rolling(20).max()
        current_close = close.iloc[-1]
        prev_close = close.iloc[-2] if len(close) > 1 else current_close
        current_ema50 = ema50.iloc[-1]
        current_ema200 = ema200.iloc[-1]
        current_rsi = rsi.iloc[-1]
        current_volume = volume.iloc[-1]
        current_vol_sma = volume_sma20.iloc[-1]
        current_highest_high = highest_high_20.iloc[-1]

        cond1 = current_close > current_highest_high and prev_close <= current_highest_high
        cond2 = current_volume > 1.5 * current_vol_sma if current_vol_sma > 0 else False
        cond3 = current_rsi > 60
        cond4 = current_ema50 > current_ema200
        cond5 = current_close > 100

        if cond1 and cond2 and cond3 and cond4 and cond5:
            return {
                'Stock': name,
                'Close': round(current_close, 2),
                'RSI': round(current_rsi, 1),
                'Vol Ratio': round(current_volume / current_vol_sma, 2) if current_vol_sma > 0 else 0,
                '20d High': round(current_highest_high, 2),
                'Entry': round(current_close, 2),
                'Target': round(current_close * 1.1, 2),
                'Stop Loss': round(current_highest_high * 0.98, 2)
            }
        return None
    except Exception:
        return None

def intraday_breakout_breakdown_signal(name):
    """Intraday Breakout/Breakdown Screener using 5-min data."""
    ticker = ALL_STOCKS[name]
    df = get_intraday_data(ticker)
    if df.empty or len(df) < 20:
        return None
    try:
        close = df['Close'].astype(float)
        high = df['High'].astype(float)
        low = df['Low'].astype(float)
        volume = df['Volume'].astype(float)

        rsi = RSIIndicator(close).rsi()
        volume_sma20 = volume.rolling(20).mean()
        typical_price = (high + low + close) / 3
        vwap = (typical_price * volume).cumsum() / volume.cumsum()

        current_close = close.iloc[-1]
        prev_high = high.iloc[-2] if len(high) > 1 else high.iloc[-1]
        prev_low = low.iloc[-2] if len(low) > 1 else low.iloc[-1]
        current_rsi = rsi.iloc[-1]
        current_volume = volume.iloc[-1]
        current_vol_sma = volume_sma20.iloc[-1]
        current_vwap = vwap.iloc[-1]

        # Conditions for Breakout (up)
        if (current_close > current_vwap and
            current_rsi > 55 and
            (current_volume > 1.5 * current_vol_sma if current_vol_sma > 0 else False) and
            current_close > prev_high):
            return {
                'Stock': name,
                'Type': 'BREAKOUT',
                'Close': round(current_close, 2),
                'RSI': round(current_rsi, 1),
                'Vol Ratio': round(current_volume / current_vol_sma, 2) if current_vol_sma > 0 else 0,
                'VWAP': round(current_vwap, 2),
                'Entry': round(current_close, 2),
                'Target': round(current_close * 1.02, 2),
                'Stop Loss': round(current_vwap * 0.99, 2)
            }
        # Conditions for Breakdown (down)
        elif (current_close < current_vwap and
              current_rsi < 45 and
              (current_volume > 1.5 * current_vol_sma if current_vol_sma > 0 else False) and
              current_close < prev_low):
            return {
                'Stock': name,
                'Type': 'BREAKDOWN',
                'Close': round(current_close, 2),
                'RSI': round(current_rsi, 1),
                'Vol Ratio': round(current_volume / current_vol_sma, 2) if current_vol_sma > 0 else 0,
                'VWAP': round(current_vwap, 2),
                'Entry': round(current_close, 2),
                'Target': round(current_close * 0.98, 2),
                'Stop Loss': round(current_vwap * 1.01, 2)
            }
        return None
    except Exception:
        return None

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
                features_df = pd.DataFrame([[last_rsi, last_close_ma20, last_high_low, last_vol_change]],
                                           columns=['RSI', 'Close_MA20', 'High_Low', 'Volume_Change'])
                features_scaled = scaler.transform(features_df)
                pred_proba = model.predict_proba(features_scaled)[0]
                ai_confidence = pred_proba[1] if len(pred_proba) > 1 else 0

        if rule_buy or ai_confidence > 0.6:
            signal = "SWING BUY"
            entry = current_price
            target = recent_high
            stop_loss = recent_low * 0.98
            holding_days = 15
            return {
                'Stock': name,
                'Signal': signal,
                'RSI': round(current_rsi, 1),
                'AI Conf': f"{ai_confidence*100:.0f}%" if ai_confidence > 0 else '-',
                'Entry': round(entry, 2),
                'Target': round(target, 2),
                'Stop Loss': round(stop_loss, 2),
                'Holding': holding_days
            }
        return None
    except Exception:
        return None

def ai_intraday_buy_signal(df, name):
    if df.empty or len(df) < 20:
        return None
    try:
        close = df['Close'].astype(float)
        volume = df['Volume']
        rsi = RSIIndicator(close).rsi()
        current_rsi = rsi.iloc[-1]
        ma20 = close.rolling(20).mean().iloc[-1]
        avg_vol = volume.rolling(20).mean().iloc[-1]
        if avg_vol == 0:
            return None
        vol_ratio = volume.iloc[-1] / avg_vol
        current_price = close.iloc[-1]

        vol_condition = vol_ratio > 1.2
        price_ma_condition = current_price > ma20
        rsi_condition = 30 < current_rsi < 70

        ai_confidence = 0.0
        if SKLEARN_AVAILABLE and len(df) > 50:
            model, scaler = train_simple_model(df)
            if model is not None and scaler is not None:
                last_rsi = current_rsi
                last_ma20 = ma20
                last_close_ma20 = current_price / last_ma20 if last_ma20 != 0 else 1
                last_high_low = (df['High'].iloc[-1] - df['Low'].iloc[-1]) / current_price
                last_vol_change = df['Volume'].pct_change().iloc[-1] if len(df) > 1 else 0
                features_df = pd.DataFrame([[last_rsi, last_close_ma20, last_high_low, last_vol_change]],
                                           columns=['RSI', 'Close_MA20', 'High_Low', 'Volume_Change'])
                features_scaled = scaler.transform(features_df)
                pred_proba = model.predict_proba(features_scaled)[0]
                ai_confidence = pred_proba[1] if len(pred_proba) > 1 else 0

        rule_score = (2 if vol_ratio > 1.5 else 1 if vol_ratio > 1.2 else 0) + \
                     (1 if price_ma_condition else 0) + \
                     (1 if rsi_condition else 0)
        combined_score = rule_score + (ai_confidence * 3)

        if combined_score >= 3:
            entry = current_price
            target = entry * 1.02
            stop = entry * 0.98
            return {
                'Stock': name,
                'Entry': round(entry, 2),
                'Target': round(target, 2),
                'Stop Loss': round(stop, 2),
                'Volume Surge': f"{vol_ratio:.1f}x",
                'RSI': round(current_rsi, 1),
                'AI Conf': f"{ai_confidence*100:.0f}%" if ai_confidence > 0 else '-',
                'Score': round(combined_score, 1)
            }
        return None
    except Exception:
        return None

def ai_intraday_sell_signal(df, name):
    if df.empty or len(df) < 20:
        return None
    try:
        close = df['Close'].astype(float)
        volume = df['Volume']
        rsi = RSIIndicator(close).rsi()
        current_rsi = rsi.iloc[-1]
        ma20 = close.rolling(20).mean().iloc[-1]
        avg_vol = volume.rolling(20).mean().iloc[-1]
        if avg_vol == 0:
            return None
        vol_ratio = volume.iloc[-1] / avg_vol
        current_price = close.iloc[-1]

        vol_condition = vol_ratio > 1.2
        price_ma_condition = current_price < ma20
        rsi_condition = current_rsi > 70

        ai_confidence = 0.0
        if SKLEARN_AVAILABLE and len(df) > 50:
            model, scaler = train_simple_model(df)
            if model is not None and scaler is not None:
                last_rsi = current_rsi
                last_ma20 = ma20
                last_close_ma20 = current_price / last_ma20 if last_ma20 != 0 else 1
                last_high_low = (df['High'].iloc[-1] - df['Low'].iloc[-1]) / current_price
                last_vol_change = df['Volume'].pct_change().iloc[-1] if len(df) > 1 else 0
                features_df = pd.DataFrame([[last_rsi, last_close_ma20, last_high_low, last_vol_change]],
                                           columns=['RSI', 'Close_MA20', 'High_Low', 'Volume_Change'])
                features_scaled = scaler.transform(features_df)
                pred_proba = model.predict_proba(features_scaled)[0]
                ai_confidence = pred_proba[0] if len(pred_proba) > 1 else 0

        rule_score = (2 if vol_ratio > 1.5 else 1 if vol_ratio > 1.2 else 0) + \
                     (1 if price_ma_condition else 0) + \
                     (1 if rsi_condition else 0)
        combined_score = rule_score + (ai_confidence * 3)

        if combined_score >= 3:
            entry = current_price
            target = entry * 0.98
            stop = entry * 1.02
            return {
                'Stock': name,
                'Entry': round(entry, 2),
                'Target': round(target, 2),
                'Stop Loss': round(stop, 2),
                'Volume Surge': f"{vol_ratio:.1f}x",
                'RSI': round(current_rsi, 1),
                'AI Conf': f"{ai_confidence*100:.0f}%" if ai_confidence > 0 else '-',
                'Score': round(combined_score, 1)
            }
        return None
    except Exception:
        return None

def intraday_picks():
    picks = []
    stock_signals = {}
    for name, ticker in ALL_STOCKS.items():
        df = get_price_data(ticker)
        buy_sig = ai_intraday_buy_signal(df, name)
        if buy_sig:
            buy_sig['Signal'] = 'BUY'
            stock_signals[name] = buy_sig
        sell_sig = ai_intraday_sell_signal(df, name)
        if sell_sig:
            sell_sig['Signal'] = 'SELL'
            if name in stock_signals:
                if sell_sig['Score'] > stock_signals[name]['Score']:
                    stock_signals[name] = sell_sig
            else:
                stock_signals[name] = sell_sig
    picks = list(stock_signals.values())
    return sorted(picks, key=lambda x: x['Score'], reverse=True)

# ------------------------------
# LOGIN PAGE
# ------------------------------
def show_login():
    st.markdown("<h1 style='text-align: center; color: #8B0000;'>📈 Quant Fund Manager</h1>", unsafe_allow_html=True)
    st.markdown("---")
    tab1, tab2 = st.tabs(["Login", "Forgot Password"])
    with tab1:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            if submitted:
                if check_login(username, password):
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("Invalid username or password")
    with tab2:
        with st.form("reset_form"):
            reset_user = st.text_input("Username")
            new_pass = st.text_input("New Password", type="password")
            confirm_pass = st.text_input("Confirm Password", type="password")
            reset_submitted = st.form_submit_button("Reset Password")
            if reset_submitted:
                if new_pass != confirm_pass:
                    st.error("Passwords do not match")
                elif reset_password(reset_user, new_pass):
                    st.success("Password reset successfully. Please login.")
                else:
                    st.error("Username not found")

def no_stocks_message(screener_name, criteria_description):
    st.markdown(f"""
    <div class="no-stocks-message">
        <strong>📊 {screener_name}</strong><br><br>
        No stocks match the criteria today.<br><br>
        <strong>Criteria applied:</strong> {criteria_description}<br><br>
        This could be due to:<br>
        • Market being closed<br>
        • Strict screening criteria<br>
        • No stocks currently meeting all conditions<br><br>
        Try the refresh button above or check back later.
    </div>
    """, unsafe_allow_html=True)

# ------------------------------
# MAIN APP
# ------------------------------
def main_app():
    # Session state initialization
    if 'holdings_df' not in st.session_state:
        st.session_state.holdings_df = load_holdings()
    if 'portfolio_df' not in st.session_state:
        st.session_state.portfolio_df = None
    if 'total_value' not in st.session_state:
        st.session_state.total_value = 0.0
    if 'total_cost' not in st.session_state:
        st.session_state.total_cost = 0.0
    if 'super_buy_count' not in st.session_state:
        st.session_state.super_buy_count = 0
    if 'buy_count' not in st.session_state:
        st.session_state.buy_count = 0
    if 'hold_count' not in st.session_state:
        st.session_state.hold_count = 0
    if 'sell_count' not in st.session_state:
        st.session_state.sell_count = 0
    if 'swing_history' not in st.session_state:
        st.session_state.swing_history = {}
    if 'sold_history' not in st.session_state:
        st.session_state.sold_history = load_sold()
    if 'debug_df' not in st.session_state:
        st.session_state.debug_df = None
    if 'criteria_data' not in st.session_state:
        st.session_state.criteria_data = {}
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = datetime.now()
    
    # Load target prices
    if 'target_prices' not in st.session_state:
        st.session_state.target_prices = load_target_prices()

    # Header
    col1, col2 = st.columns([6, 1])
    with col1:
        st.markdown('<div class="main-header"><span class="logo">📈 Quant Fund Manager</span><span style="color:#666;">Super Screener Edition</span></div>', unsafe_allow_html=True)
    with col2:
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.rerun()

    st.markdown("#### Combined screener: Original 9‑factor + Magic Formula (19 criteria total)")

    # Alert Settings Section
    with st.expander("📧 Alert Settings (Email / Telegram)"):
        st.markdown('<div class="alert-settings">', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📧 Email Settings")
            st.checkbox("Enable Email Alerts", key="email_enabled", value=False)
            st.text_input("Sender Email (Gmail)", key="email_sender", placeholder="your@gmail.com")
            st.text_input("App Password", key="email_password", type="password", 
                         help="Use Gmail App Password (not your regular password)")
            st.text_input("Recipient Email", key="email_recipient", value="sajjanvsl@gmail.com")
        
        with col2:
            st.subheader("📱 Telegram Settings")
            st.checkbox("Enable Telegram Alerts", key="telegram_enabled", value=False)
            st.text_input("Bot Token", key="telegram_bot_token", 
                         help="Get from @BotFather on Telegram")
            st.text_input("Chat ID", key="telegram_chat_id", value="@sajjanvsl",
                         help="Your Telegram username or chat ID")
        
        st.info("⚠️ For Gmail, you need to enable 2FA and create an App Password. For Telegram, create a bot with @BotFather and get your chat ID from @userinfobot.")
        st.markdown('</div>', unsafe_allow_html=True)

    # Manual refresh button
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.session_state.last_refresh = datetime.now()
        st.rerun()

    # Debug expander
    with st.expander("🔧 Debug Data Fetching"):
        st.write("Testing data fetch for CIPLA.NS:")
        debug_result = debug_data_fetch("CIPLA.NS")
        st.write(debug_result)
        if "❌" in debug_result:
            st.error("Data fetch failed. Please check your internet connection or try again later.")
        else:
            st.success("Data fetch successful. If screeners show no stocks, criteria may be too strict.")
        st.write("---")
        st.write("If data fetch fails, try running this command in your terminal:")
        st.code("pip install --upgrade yfinance")

    # Tabs
    screener_tab1, screener_tab2, screener_tab3, screener_tab4, screener_tab5 = st.tabs([
        "🤖 AI Swing Scanner", 
        "💰 Fair Value (Buy on Dip)",   # renamed tab
        "📈 Fundamental Breakout",
        "⚡ Intraday Breakout & Breakdown (5-min)",
        "🤖 AI Intraday Picks"
    ])

    # ----- Tab 1: AI Swing Scanner -----
    with screener_tab1:
        st.markdown("## 🤖 AI Swing Trading Scanner")
        st.caption("AI-powered swing signals combining technical rules with RandomForest.")
        with st.spinner("Fetching swing signals..."):
            swing_data = []
            today = datetime.now().date()
            total_stocks = len(ALL_STOCKS)
            progress_bar = st.progress(0, text="Scanning stocks...")
            for idx, (name, ticker) in enumerate(ALL_STOCKS.items()):
                df = get_price_data(ticker)
                sig = ai_swing_signal(df, name)
                if sig:
                    last_seen = st.session_state.swing_history.get(name)
                    if last_seen is None or (today - last_seen).days >= 5:
                        sig['Fresh'] = '✅ Fresh'
                        st.session_state.swing_history[name] = today
                    else:
                        sig['Fresh'] = ''
                    swing_data.append(sig)
                progress_bar.progress((idx+1)/total_stocks)
            progress_bar.empty()
        if swing_data:
            swing_df = pd.DataFrame(swing_data)
            display_cols = ['Stock', 'Signal', 'RSI', 'Entry', 'Target', 'Stop Loss', 'Holding', 'AI Conf', 'Fresh']
            swing_df = swing_df[[col for col in display_cols if col in swing_df.columns]]
            st.markdown('<span class="top-pick-badge">⭐ TOP SWING PICK</span>', unsafe_allow_html=True)
            st.dataframe(swing_df, width='stretch')
        else:
            no_stocks_message("AI Swing Scanner", "• RSI < 45<br>• 20 EMA > 50 EMA<br>• Price > recent low +2%<br>• AI confidence > 60%")

    # ----- Tab 2: Fair Value Screener with Editable Buy Price -----
    with screener_tab2:
        st.markdown("## 💰 Fair Value Screener")
        st.caption("Stocks trading at least 15% below estimated fair value. Set your target buy price and get alerts when price hits it.")

        with st.spinner("Scanning for undervalued stocks..."):
            fair_value_data = []
            total_stocks = len(ALL_STOCKS)
            progress_bar = st.progress(0, text="Scanning stocks...")
            for idx, (name, ticker) in enumerate(ALL_STOCKS.items()):
                df = get_price_data(ticker)
                sig = fair_value_signal(df, name)
                if sig:
                    # Add target price column (default to fair value * 0.8 for 20% margin of safety)
                    sig['Target Price'] = sig['Fair Value'] * 0.8
                    fair_value_data.append(sig)
                progress_bar.progress((idx+1)/total_stocks)
            progress_bar.empty()
            
        if fair_value_data:
            # Create DataFrame
            fair_value_df = pd.DataFrame(fair_value_data)
            fair_value_df = fair_value_df.sort_values('Discount %', ascending=False)
            
            # Create editable table with Target Price
            st.markdown('<span class="top-pick-badge">⭐ BEST VALUE</span>', unsafe_allow_html=True)
            
            # Prepare columns for editing
            display_cols = ['Stock', 'Current Price', 'Fair Value', 'Discount %', 'Target Price', 'Signal', 'FCF (Cr)', 'Growth 5Y %', 'ROCE %']
            edit_df = fair_value_df[display_cols].copy()
            
            # Column configuration
            column_config = {
                'Stock': st.column_config.TextColumn('Stock', disabled=True),
                'Current Price': st.column_config.NumberColumn('Current Price', disabled=True, format="₹%.2f"),
                'Fair Value': st.column_config.NumberColumn('Fair Value', disabled=True, format="₹%.2f"),
                'Discount %': st.column_config.NumberColumn('Discount %', disabled=True, format="%.1f%%"),
                'Target Price': st.column_config.NumberColumn('Target Price', min_value=0.0, format="₹%.2f"),
                'Signal': st.column_config.TextColumn('Signal', disabled=True),
                'FCF (Cr)': st.column_config.NumberColumn('FCF (Cr)', disabled=True, format="₹%.2f"),
                'Growth 5Y %': st.column_config.NumberColumn('Growth 5Y %', disabled=True, format="%.1f%%"),
                'ROCE %': st.column_config.NumberColumn('ROCE %', disabled=True, format="%.1f%%')
            }
            
            edited_df = st.data_editor(
                edit_df,
                column_config=column_config,
                use_container_width=True,
                hide_index=True,
                num_rows="fixed"
            )
            
            # Check for changes in Target Price
            target_prices_updated = False
            for idx, row in edited_df.iterrows():
                stock = row['Stock']
                new_target = row['Target Price']
                old_target = st.session_state.target_prices.get(stock, [])
                
                # Convert to list if not already
                if not isinstance(old_target, list):
                    old_target = [old_target] if old_target else []
                
                # Update if changed
                if new_target not in old_target:
                    if new_target > 0:
                        st.session_state.target_prices[stock] = [new_target]
                        target_prices_updated = True
            
            if target_prices_updated:
                save_target_prices(st.session_state.target_prices)
                st.success("Target prices updated!")
            
            # Check for alerts
            alerts_triggered = []
            for idx, row in edited_df.iterrows():
                stock = row['Stock']
                current_price = row['Current Price']
                
                if stock in st.session_state.target_prices:
                    target_list = st.session_state.target_prices[stock]
                    if isinstance(target_list, list):
                        alerts_sent = st.session_state.alert_system.check_and_send_alerts(
                            stock, current_price, target_list
                        )
                        if alerts_sent:
                            alerts_triggered.append(f"{stock}: {', '.join(alerts_sent)}")
            
            if alerts_triggered:
                st.success("✅ Alerts sent: " + "; ".join(alerts_triggered))
            
            # Show current target prices
            if st.session_state.target_prices:
                with st.expander("📋 Current Target Prices"):
                    target_df = pd.DataFrame([
                        {'Stock': k, 'Target Price(s)': v} 
                        for k, v in st.session_state.target_prices.items()
                    ])
                    st.dataframe(target_df, width='stretch')
        else:
            no_stocks_message(
                "Fair Value Screener",
                "• Simplified DCF model<br>• 5‑year FCF projections<br>• 12% discount rate<br>• 4% terminal growth<br>• Requires at least 15% discount"
            )

    # ----- Tab 3: Fundamental Breakout -----
    with screener_tab3:
        st.markdown("## 📈 Fundamental Breakout Screener")
        st.caption("Stocks meeting: Price >500, Mkt Cap >500 Cr, Sales & Profit growth >20%, ROCE >10%, P/E > 15.")
        with st.spinner("Scanning for fundamental breakouts..."):
            breakout_data = []
            total_stocks = len(ALL_STOCKS)
            progress_bar = st.progress(0, text="Scanning stocks...")
            for idx, (name, ticker) in enumerate(ALL_STOCKS.items()):
                price_df = get_price_data(ticker)
                if price_df.empty:
                    progress_bar.progress((idx+1)/total_stocks)
                    continue
                close_series = price_df['Close'].squeeze()
                current_price = close_series.iloc[-1] if isinstance(close_series, pd.Series) else close_series
                fund = get_fundamental_data(ticker)
                if fund is None:
                    progress_bar.progress((idx+1)/total_stocks)
                    continue
                market_cap = fund.get('market_cap')
                sales_growth = fund.get('sales_growth_3y')
                profit_growth = fund.get('profit_growth_3y')
                roce = fund.get('roce')
                pe = fund.get('info', {}).get('trailingPE')
                cond1 = current_price > 500
                cond2 = market_cap > 500 if not pd.isna(market_cap) else False
                cond3 = sales_growth > 20 if not pd.isna(sales_growth) else False
                cond4 = profit_growth > 20 if not pd.isna(profit_growth) else False
                cond5 = roce > 10 if not pd.isna(roce) else False
                cond6 = pe > 15 if not pd.isna(pe) else False
                if cond1 and cond2 and cond3 and cond4 and cond5 and cond6:
                    breakout_data.append({
                        'Stock': name,
                        'Price (₹)': round(current_price, 2),
                        'Mkt Cap (Cr)': round(market_cap, 2) if not pd.isna(market_cap) else 'N/A',
                        'Sales Gr 3Y (%)': round(sales_growth, 2) if not pd.isna(sales_growth) else 'N/A',
                        'Profit Gr 3Y (%)': round(profit_growth, 2) if not pd.isna(profit_growth) else 'N/A',
                        'ROCE (%)': round(roce, 2) if not pd.isna(roce) else 'N/A',
                        'P/E': round(pe, 2) if not pd.isna(pe) else 'N/A'
                    })
                progress_bar.progress((idx+1)/total_stocks)
            progress_bar.empty()
        if breakout_data:
            breakout_df = pd.DataFrame(breakout_data)
            st.markdown('<span class="top-pick-badge">⭐ TOP BREAKOUT</span>', unsafe_allow_html=True)
            st.dataframe(breakout_df.style.format({
                'Price (₹)': '₹{:.2f}',
                'Mkt Cap (Cr)': '₹{:.2f}',
                'Sales Gr 3Y (%)': '{:.2f}%',
                'Profit Gr 3Y (%)': '{:.2f}%',
                'ROCE (%)': '{:.2f}%'
            }, na_rep='-'), width='stretch')
        else:
            no_stocks_message("Fundamental Breakout Screener", "• Price > 500<br>• Mkt Cap > 500 Cr<br>• Sales growth > 20%<br>• Profit growth > 20%<br>• ROCE > 10%<br>• P/E > 15")

    # ----- Tab 4: Intraday Breakout & Breakdown -----
    with screener_tab4:
        st.markdown("## ⚡ Intraday Breakout & Breakdown Screener (5-min)")
        st.caption("Real‑time 5‑minute signals: Breakout (up) and Breakdown (down).")

        with st.spinner("Scanning for intraday opportunities..."):
            intraday_signals = []
            total_stocks = len(ALL_STOCKS)
            progress_bar = st.progress(0, text="Scanning stocks...")
            for idx, (name, ticker) in enumerate(ALL_STOCKS.items()):
                sig = intraday_breakout_breakdown_signal(name)
                if sig:
                    intraday_signals.append(sig)
                progress_bar.progress((idx+1)/total_stocks)
            progress_bar.empty()

        if intraday_signals:
            intraday_df = pd.DataFrame(intraday_signals)
            cols = ['Stock', 'Type', 'Close', 'RSI', 'Vol Ratio', 'VWAP', 'Entry', 'Target', 'Stop Loss']
            intraday_df = intraday_df[[c for c in cols if c in intraday_df.columns]]
            st.markdown('<span class="top-pick-badge">⭐ TOP INTRADAY SIGNAL</span>', unsafe_allow_html=True)
            st.dataframe(intraday_df, width='stretch')
        else:
            no_stocks_message(
                "Intraday Breakout & Breakdown Screener",
                "• Breakout: Close > VWAP, RSI > 55, Volume > 1.5× avg, Close > Previous High<br>"
                "• Breakdown: Close < VWAP, RSI < 45, Volume > 1.5× avg, Close < Previous Low"
            )

    # ----- Tab 5: AI Intraday Picks -----
    with screener_tab5:
        st.markdown("## 🤖 AI Intraday Picks")
        st.caption("AI‑powered intraday picks – only the highest‑confidence signal per stock is shown. Higher score = stronger signal.")
        with st.spinner("Scanning for AI intraday opportunities..."):
            intraday = intraday_picks()[:20]
        if intraday:
            intraday_df = pd.DataFrame(intraday)
            display_cols = ['Stock', 'Signal', 'Entry', 'Target', 'Stop Loss', 'Volume Surge', 'RSI', 'AI Conf', 'Score']
            intraday_df = intraday_df[[col for col in display_cols if col in intraday_df.columns]]
            st.markdown('<span class="top-pick-badge">⭐ TOP AI INTRADAY PICK</span>', unsafe_allow_html=True)
            st.dataframe(intraday_df, width='stretch')
        else:
            no_stocks_message("AI Intraday Picks", "• Volume surge > 1.2x<br>• Price relative to 20 MA<br>• RSI conditions<br>• AI confidence > 60%<br>• Combined score ≥ 3")

    st.markdown("---")

    # ------------------------------
    # HOLDINGS SECTION (unchanged)
    # ------------------------------
    if st.session_state.holdings_df is not None and not st.session_state.holdings_df.empty:
        if st.session_state.portfolio_df is None:
            portfolio_data = []
            debug_data = []
            criteria_data = {}
            total_value = 0.0
            total_cost = 0.0
            super_buy_count = 0
            buy_count = 0
            hold_count = 0
            sell_count = 0

            for idx, row in st.session_state.holdings_df.iterrows():
                name = row['Instrument']
                ticker = ALL_STOCKS.get(name)
                price_df = get_price_data(ticker)
                if price_df.empty:
                    continue
                close_series = price_df['Close'].squeeze()
                if isinstance(close_series, pd.Series):
                    current_price = close_series.iloc[-1]
                else:
                    current_price = close_series
                cur_value = row['Qty'] * current_price
                if not pd.isna(row['Avg Price']):
                    pnl = row['Qty'] * (current_price - row['Avg Price'])
                    pnl_pct = (current_price - row['Avg Price']) / row['Avg Price'] * 100
                else:
                    pnl = np.nan
                    pnl_pct = np.nan
                fund = get_fundamental_data(ticker)
                rec, criteria, criteria_met, values = screen_stock(fund)
                if rec == "SUPER BUY":
                    super_buy_count += 1
                elif rec == "BUY":
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
                    'Criteria Met': f"{criteria_met}/19",
                })
                debug_data.append({
                    'Stock': name,
                    **values
                })
                criteria_data[name] = criteria
                total_value += cur_value
                if not pd.isna(row['Avg Price']):
                    total_cost += row['Qty'] * row['Avg Price']

            st.session_state.portfolio_df = pd.DataFrame(portfolio_data)
            st.session_state.total_value = total_value
            st.session_state.total_cost = total_cost
            st.session_state.super_buy_count = super_buy_count
            st.session_state.buy_count = buy_count
            st.session_state.hold_count = hold_count
            st.session_state.sell_count = sell_count
            st.session_state.debug_df = pd.DataFrame(debug_data)
            st.session_state.criteria_data = criteria_data

        st.markdown("## 📊 SUPER SCREENER RANKING")
        st.markdown("Based on combined 19‑factor formula. **SUPER BUY** = ≥15 criteria, BUY = 12-14, HOLD = 6-11, SELL = 0-5.")

        with st.expander("🔍 Detailed Criteria Analysis for Your Holdings"):
            st.write("### 📋 Criteria Check for Each Stock")
            st.write("Click on a stock to see which of the 19 criteria are met:")
            if st.session_state.portfolio_df is not None and not st.session_state.portfolio_df.empty:
                selected_stock = st.selectbox("Select stock to view criteria", st.session_state.portfolio_df['Stock'].tolist(), key="holdings_criteria")
                if selected_stock in st.session_state.criteria_data:
                    def display_criteria_table(criteria_dict, title):
                        html = f'<div class="criteria-table"><h4>{title}</h4>'
                        for criterion, met in criteria_dict.items():
                            status = '✅' if met else '❌'
                            color = 'criteria-pass' if met else 'criteria-fail'
                            html += f'<div class="criteria-row"><span>{criterion}</span><span class="{color}">{status}</span></div>'
                        html += '</div>'
                        return html
                    st.markdown(display_criteria_table(st.session_state.criteria_data[selected_stock], f"19-Point Checklist for {selected_stock}"), unsafe_allow_html=True)
                    st.write("### 📊 Detailed Values")
                    stock_debug = st.session_state.debug_df[st.session_state.debug_df['Stock'] == selected_stock].iloc[0]
                    debug_dict = stock_debug.to_dict()
                    debug_df = pd.DataFrame(list(debug_dict.items()), columns=['Metric', 'Value'])
                    debug_df['Value'] = debug_df['Value'].apply(lambda x: f"{x:.2f}" if isinstance(x, (int, float)) and not pd.isna(x) else ('N/A' if pd.isna(x) else x))
                    st.dataframe(debug_df, width='stretch')
            else:
                st.info("No debug data available.")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            try:
                total_val_display = f"₹{float(st.session_state.total_value):,.0f}"
            except:
                total_val_display = "₹0"
            st.markdown(f'<div class="metric-card"><div class="metric-label">Total Portfolio Value</div><div class="metric-value">{total_val_display}</div></div>', unsafe_allow_html=True)
        with col2:
            if st.session_state.total_cost > 0:
                try:
                    total_pnl = float(st.session_state.total_value) - float(st.session_state.total_cost)
                    total_pnl_pct = (total_pnl / float(st.session_state.total_cost)) * 100
                    delta_color = "green" if total_pnl >= 0 else "red"
                    pnl_display = f"₹{total_pnl:+,.0f}"
                    pnl_pct_display = f"{total_pnl_pct:+.2f}%"
                except:
                    pnl_display = "₹0"
                    pnl_pct_display = "0.00%"
                    delta_color = "gray"
                st.markdown(f'<div class="metric-card"><div class="metric-label">Total P&L</div><div class="metric-value">{pnl_display}</div><div class="metric-delta" style="color:{delta_color};">{pnl_pct_display}</div></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="metric-card"><div class="metric-label">Total P&L</div><div class="metric-value">N/A</div></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div class="metric-card"><div class="metric-label">SUPER BUY / BUY / HOLD / SELL</div><div class="metric-value">{st.session_state.super_buy_count} / {st.session_state.buy_count} / {st.session_state.hold_count} / {st.session_state.sell_count}</div></div>', unsafe_allow_html=True)
        with col4:
            st.markdown(f'<div class="metric-card"><div class="metric-label">Portfolio Size</div><div class="metric-value">{len(st.session_state.portfolio_df)}</div></div>', unsafe_allow_html=True)

        col1, col2 = st.columns([1, 1])
        with col1:
            st.subheader("Portfolio Allocation by Value")
            if not st.session_state.portfolio_df.empty:
                cur_val = pd.to_numeric(st.session_state.portfolio_df['Cur Value'], errors='coerce')
                fig = px.pie(st.session_state.portfolio_df, values=cur_val, names='Stock')
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.subheader("Performance Sparkline")
            st.info("Coming soon")

        st.markdown("---")
        st.subheader("Your Holdings – Combined Screener Analysis")
        st.caption("Edit Qty and Avg Price directly in the table. Check 'Delete' and click 'Delete Selected' to sell stock(s).")

        if st.session_state.portfolio_df is not None and not st.session_state.portfolio_df.empty:
            edit_df = st.session_state.portfolio_df.copy()
            edit_df.insert(0, 'Sl.No', range(1, len(edit_df) + 1))
            edit_df['Delete'] = False

            column_config = {
                'Sl.No': st.column_config.NumberColumn('Sl.No', disabled=True),
                'Stock': st.column_config.TextColumn('Stock', disabled=True),
                'Qty': st.column_config.NumberColumn('Qty', min_value=0, step=1, format="%.0f"),
                'Avg Price': st.column_config.NumberColumn('Avg Price', min_value=0, format="%.2f"),
                'LTP (CSV)': st.column_config.NumberColumn('LTP (CSV)', disabled=True, format="%.2f"),
                'Current Price': st.column_config.NumberColumn('Current Price', disabled=True, format="₹%.2f"),
                'Cur Value': st.column_config.NumberColumn('Cur Value', disabled=True, format="₹%.2f"),
                'P&L': st.column_config.NumberColumn('P&L', disabled=True, format="₹%.2f"),
                'P&L %': st.column_config.NumberColumn('P&L %', disabled=True, format="%.2f%%"),
                'Recommendation': st.column_config.TextColumn('Recommendation', disabled=True),
                'Criteria Met': st.column_config.TextColumn('Criteria Met', disabled=True),
                'Delete': st.column_config.CheckboxColumn('Delete')
            }

            st.markdown('<div class="holdings-table">', unsafe_allow_html=True)
            edited_df = st.data_editor(
                edit_df,
                column_config=column_config,
                use_container_width=True,
                hide_index=True,
                num_rows="fixed"
            )
            st.markdown('</div>', unsafe_allow_html=True)

            changes_made = False
            for col in ['Qty', 'Avg Price']:
                if col in edited_df.columns and not edited_df[col].equals(edit_df[col]):
                    changes_made = True
                    break

            if changes_made:
                for idx, row in edited_df.iterrows():
                    stock_name = row['Stock']
                    mask = st.session_state.holdings_df['Instrument'] == stock_name
                    if mask.any():
                        st.session_state.holdings_df.loc[mask, 'Qty'] = row['Qty']
                        st.session_state.holdings_df.loc[mask, 'Avg Price'] = row['Avg Price']
                save_holdings(st.session_state.holdings_df)
                st.session_state.portfolio_df = None
                st.rerun()

            selected_for_deletion = edited_df[edited_df['Delete'] == True]
            if not selected_for_deletion.empty:
                st.warning(f"{len(selected_for_deletion)} stock(s) selected for deletion.")
                if st.button("🗑️ Delete Selected", type="primary"):
                    for _, row in selected_for_deletion.iterrows():
                        stock_name = row['Stock']
                        sold_entry = {
                            'Stock': stock_name,
                            'Qty': row['Qty'],
                            'Avg Price': row['Avg Price'],
                            'Sell Price': row['Current Price'],
                            'Sell Date': datetime.now().date().strftime('%Y-%m-%d'),
                            'P&L': row['P&L'] if not pd.isna(row['P&L']) else 0
                        }
                        st.session_state.sold_history = pd.concat([st.session_state.sold_history, pd.DataFrame([sold_entry])], ignore_index=True)
                        st.session_state.holdings_df = st.session_state.holdings_df[st.session_state.holdings_df['Instrument'] != stock_name].reset_index(drop=True)
                    save_sold(st.session_state.sold_history)
                    save_holdings(st.session_state.holdings_df)
                    st.session_state.portfolio_df = None
                    st.rerun()

            st.markdown("#### Sold History")
            if not st.session_state.sold_history.empty:
                st.dataframe(st.session_state.sold_history, width='stretch')
            else:
                st.info("No sold stocks yet.")
        else:
            st.info("No holdings data available.")
    else:
        st.info("No holdings data. Please add stocks using the section below.")

    # ------------------------------
    # INPUT SECTION (with fixed single stock handling)
    # ------------------------------
    st.markdown('<div class="input-section">', unsafe_allow_html=True)
    st.subheader("📁 Add Holdings")
    col1, col2 = st.columns([2, 1])
    with col1:
        uploaded_file = st.file_uploader("Upload Holdings CSV", type=['csv'], key="file_uploader_bottom")
    with col2:
        single_stock = st.text_input("Or add a single stock", placeholder="e.g., CIPLA or MCX").strip().upper()

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
                # Remove any .NS suffix for consistency
                df_hold['Instrument'] = df_hold['Instrument'].str.replace('.NS', '', regex=False)
                df_hold = df_hold[df_hold['Instrument'].notna() & (df_hold['Instrument'] != '') & (df_hold['Instrument'] != 'NAN')]
                for col in ['Qty', 'Avg Price', 'LTP', 'Cur Value', 'P&L', 'Net Chg %', 'Day Chg %']:
                    df_hold[col] = pd.to_numeric(df_hold[col], errors='coerce')
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
        # Remove any .NS suffix if user typed it
        clean_stock = single_stock.replace('.NS', '').strip()
        if clean_stock in ALL_STOCKS:
            new_row = pd.DataFrame({
                'Instrument': [clean_stock],
                'Qty': [1],
                'Avg Price': [np.nan],
                'LTP': [np.nan],
                'Cur Value': [np.nan],
                'P&L': [np.nan],
                'Net Chg %': [np.nan],
                'Day Chg %': [np.nan]
            })
            if st.session_state.holdings_df is not None:
                if clean_stock not in st.session_state.holdings_df['Instrument'].values:
                    st.session_state.holdings_df = pd.concat([st.session_state.holdings_df, new_row], ignore_index=True)
                    save_holdings(st.session_state.holdings_df)
                    st.session_state.portfolio_df = None
                    st.success(f"Added {clean_stock}.")
                    st.rerun()
                else:
                    st.warning(f"{clean_stock} already in holdings.")
            else:
                st.session_state.holdings_df = new_row
                save_holdings(st.session_state.holdings_df)
                st.session_state.portfolio_df = None
                st.success(f"Added {clean_stock}.")
                st.rerun()
        else:
            st.error(f"{clean_stock} not found in master list. Please check the symbol (e.g., MCX, CIPLA).")

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("---")
    st.caption("Data sourced from Yahoo Finance. Updated: " + st.session_state.last_refresh.strftime("%Y-%m-%d %H:%M"))

# ------------------------------
# ROUTING
# ------------------------------
if not st.session_state.authenticated:
    show_login()
else:
    main_app()

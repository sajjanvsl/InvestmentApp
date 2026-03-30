
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
# ALERT SYSTEM (enhanced with custom keys)
# ------------------------------
class AlertSystem:
    def __init__(self):
        self.alert_cooldown = {}
        self.cooldown_minutes = 15
        
    def should_send_alert(self, key):
        current_time = time.time()
        if key in self.alert_cooldown:
            last_alert = self.alert_cooldown[key]
            minutes_passed = (current_time - last_alert) / 60
            if minutes_passed < self.cooldown_minutes:
                return False
        self.alert_cooldown[key] = current_time
        return True
    
    def send_email_alert(self, stock_name, current_price, target_price, signal_type="Alert", target_zone=""):
        if not st.session_state.get('email_enabled', False):
            return False
            
        sender_email = st.session_state.get('email_sender', '')
        sender_password = st.session_state.get('email_password', '')
        recipient_email = st.session_state.get('email_recipient', '')
        
        if not all([sender_email, sender_password, recipient_email]):
            return False
            
        subject = f"🚨 {signal_type} ALERT: {stock_name}"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #8B0000;">📈 {signal_type} Alert: {stock_name}</h2>
            <table style="border-collapse: collapse; width: 100%; max-width: 400px;">
                <tr style="background-color: #f2f2f2;">
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Current Price:</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">₹{current_price:.2f}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Target Zone:</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{target_zone}</td>
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
    
    def send_telegram_alert(self, stock_name, current_price, target_price, signal_type="Alert", target_zone=""):
        if not st.session_state.get('telegram_enabled', False):
            return False
            
        bot_token = st.session_state.get('telegram_bot_token', '')
        chat_id = st.session_state.get('telegram_chat_id', '')
        
        if not all([bot_token, chat_id]):
            return False
            
        message = f"""🚨 {signal_type} ALERT: {stock_name}

Current Price: ₹{current_price:.2f}
Target Zone: {target_zone}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This is an automated alert from Quant Fund Manager."""
        
        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': message
            }
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                return True
            else:
                st.error(f"Telegram error: {response.text}")
                return False
        except Exception as e:
            st.error(f"Telegram failed: {str(e)}")
            return False
    
    def check_and_send_alerts(self, stock_name, current_price, target_prices):
        alerts_sent = []
        for target_price in target_prices:
            key = f"price_target_{stock_name}_{target_price}"
            if self.should_send_alert(key):
                if st.session_state.get('email_enabled', False):
                    if self.send_email_alert(stock_name, current_price, target_price, "Price Target", f"₹{target_price:.2f}"):
                        alerts_sent.append(f"Email at ₹{target_price:.2f}")
                if st.session_state.get('telegram_enabled', False):
                    if self.send_telegram_alert(stock_name, current_price, target_price, "Price Target", f"₹{target_price:.2f}"):
                        alerts_sent.append(f"Telegram at ₹{target_price:.2f}")
        return alerts_sent

# ------------------------------
# SETTINGS PERSISTENCE
# ------------------------------
SETTINGS_FILE = "settings.json"

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {
        "email_enabled": False,
        "email_sender": "",
        "email_password": "",
        "email_recipient": "sajjanvsl@gmail.com",
        "telegram_enabled": False,
        "telegram_bot_token": "",
        "telegram_chat_id": ""
    }

def save_settings(settings):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=2)

# ------------------------------
# AUTHENTICATION FUNCTIONS
# ------------------------------
USERS_FILE = "users.json"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
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
# DATA FETCHING FUNCTIONS
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
    if os.path.exists(TARGET_PRICES_FILE):
        try:
            with open(TARGET_PRICES_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}

def save_target_prices(target_dict):
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
# PIOTROSKI F-SCORE CALCULATION
# ------------------------------
def calculate_piotroski_score(fund):
    """
    Computes Piotroski F-Score (0-9) based on:
    Profitability: ROA > 0, CFO > 0, ΔROA > 0, Accrual = CFO > ROA
    Leverage/Liquidity: ΔLeverage < 0, ΔLiquidity > 0, No new shares issued
    Operating Efficiency: ΔGross Margin > 0, ΔAsset Turnover > 0
    """
    if fund is None:
        return 0
    
    score = 0
    
    # Profitability
    # 1. Return on Assets (ROA) > 0
    roa = fund.get('roce')  # approximate using ROCE
    if roa is not None and not pd.isna(roa) and roa > 0:
        score += 1
    
    # 2. Cash Flow from Operations (CFO) > 0
    cfo = fund.get('avg_fcf')
    if cfo is not None and not pd.isna(cfo) and cfo > 0:
        score += 1
    
    # 3. Change in ROA > 0 (use 3y growth as proxy)
    roa_growth = fund.get('roce_3y_growth')
    # We need to compute ROCE growth from historical data – not available in current fund dict
    # Instead, use profit growth 3y as a proxy for profitability improvement
    profit_growth = fund.get('profit_growth_3y')
    if profit_growth is not None and not pd.isna(profit_growth) and profit_growth > 0:
        score += 1
    
    # 4. Accrual = CFO > ROA (cash flow higher than accounting profit)
    if cfo is not None and roa is not None and not pd.isna(cfo) and not pd.isna(roa) and cfo > roa:
        score += 1
    
    # Leverage/Liquidity
    # 5. Change in Leverage (D/E) < 0
    de = fund.get('de_ratio')
    # Need historical D/E to compute change – not available. Use current D/E < 0.5 as a proxy
    if de is not None and not pd.isna(de) and de < 0.5:
        score += 1
    
    # 6. Change in Current Ratio > 0 (use ICR > 3 as proxy for liquidity improvement)
    icr = fund.get('icr')
    if icr is not None and not pd.isna(icr) and icr > 3:
        score += 1
    
    # 7. No new shares issued (use share count change – not available; assume no)
    # We'll skip this for now; default to 0 if cannot determine. Could check sharesOutstanding from info.
    shares = fund.get('info', {}).get('sharesOutstanding')
    if shares is not None and shares > 0:
        # If we had previous shares, we could compare; not available, so skip.
        pass
    
    # Operating Efficiency
    # 8. Change in Gross Margin > 0 (use sales growth > profit growth? proxy)
    sales_growth = fund.get('sales_growth_3y')
    profit_growth_ = fund.get('profit_growth_3y')
    if sales_growth is not None and profit_growth_ is not None and not pd.isna(sales_growth) and not pd.isna(profit_growth_) and profit_growth_ > sales_growth:
        score += 1
    
    # 9. Change in Asset Turnover > 0 (use sales growth > 0 as proxy)
    if sales_growth is not None and not pd.isna(sales_growth) and sales_growth > 0:
        score += 1
    
    return min(score, 9)  # ensure max 9

# ------------------------------
# ROBUST FAIR VALUE CALCULATION
# ------------------------------
def get_reliable_eps_and_growth(ticker, current_price):
    """
    Returns (eps, growth) tuple with sanity checks.
    """
    fund = get_fundamental_data(ticker)
    if not fund:
        return None, None

    eps = None
    info = fund.get('info', {})
    # Try trailing EPS
    eps = info.get('trailingEps')
    if eps is None or eps <= 0:
        # Try via trailing PE
        pe = info.get('trailingPE')
        if pe and pe > 0 and current_price > 0:
            eps = current_price / pe
    if eps is None or eps <= 0:
        # Compute from net profit / shares
        net_profit = fund.get('net_profit')  # in crores
        shares = info.get('sharesOutstanding')
        if net_profit and shares and shares > 0:
            eps = (net_profit * 1e7) / shares
    # Sanity: EPS shouldn't be too high relative to price
    if eps and current_price > 0:
        if eps > current_price * 2:
            eps = None  # discard unreasonable

    # Get growth (capped at 30%)
    growth = fund.get('profit_growth_3y')
    if not growth or growth <= 0:
        growth = fund.get('profit_growth_5y')
    if not growth or growth <= 0:
        growth = 10  # default
    growth = min(growth, 30)

    return eps, growth

def get_reliable_fair_value(ticker, current_price):
    eps, growth = get_reliable_eps_and_growth(ticker, current_price)
    if eps and eps > 0 and growth > 0:
        fair_value = eps * growth * 1.5
        # Sanity check
        if 0.5 * current_price <= fair_value <= 5 * current_price:
            return fair_value
    # Fallback: simple estimate
    return current_price * 1.2  # rough 20% upside

# ------------------------------
# SCREEN STOCK FUNCTION (for holdings recommendations)
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
# SCREENER FUNCTIONS (Swing and Intraday)
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
                     (1 if current_price > ma20 else 0) + \
                     (1 if 30 < current_rsi < 70 else 0)
        combined_score = rule_score + (ai_confidence * 3)

        if combined_score >= 3:
            entry = current_price
            target = entry * 1.02
            stop = entry * 0.98
            return {
                'Stock': name,
                'Signal': 'BUY',
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
                     (1 if current_price < ma20 else 0) + \
                     (1 if current_rsi > 70 else 0)
        combined_score = rule_score + (ai_confidence * 3)

        if combined_score >= 3:
            entry = current_price
            target = entry * 0.98
            stop = entry * 1.02
            return {
                'Stock': name,
                'Signal': 'SELL',
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
            stock_signals[name] = buy_sig
        sell_sig = ai_intraday_sell_signal(df, name)
        if sell_sig:
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
    if 'target_prices' not in st.session_state:
        st.session_state.target_prices = load_target_prices()
    if 'settings' not in st.session_state:
        st.session_state.settings = load_settings()
    if 'alert_system' not in st.session_state:
        st.session_state.alert_system = AlertSystem()
    if 'alerts_sent_this_session' not in st.session_state:
        st.session_state.alerts_sent_this_session = set()

    # Sync alert settings from stored settings
    st.session_state.email_enabled = st.session_state.settings.get('email_enabled', False)
    st.session_state.email_sender = st.session_state.settings.get('email_sender', '')
    st.session_state.email_password = st.session_state.settings.get('email_password', '')
    st.session_state.email_recipient = st.session_state.settings.get('email_recipient', 'sajjanvsl@gmail.com')
    st.session_state.telegram_enabled = st.session_state.settings.get('telegram_enabled', False)
    st.session_state.telegram_bot_token = st.session_state.settings.get('telegram_bot_token', '')
    st.session_state.telegram_chat_id = st.session_state.settings.get('telegram_chat_id', '')

    # Header
    col1, col2 = st.columns([6, 1])
    with col1:
        st.markdown('<div class="main-header"><span class="logo">📈 Quant Fund Manager</span><span style="color:#666;">Super Screener Edition</span></div>', unsafe_allow_html=True)
    with col2:
        if st.button("Logout", key="logout_button"):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.rerun()

    st.markdown("#### Combined screener: Original 9‑factor + Magic Formula (19 criteria total)")

    # Alert Settings
    with st.expander("📧 Alert Settings (Email / Telegram)"):
        st.markdown('<div class="alert-settings">', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📧 Email Settings")
            email_enabled = st.checkbox("Enable Email Alerts", value=st.session_state.settings.get("email_enabled", False), key="email_enabled_input")
            email_sender = st.text_input("Sender Email (Gmail)", value=st.session_state.settings.get("email_sender", ""), key="email_sender_input", placeholder="your@gmail.com")
            email_password = st.text_input("App Password", value=st.session_state.settings.get("email_password", ""), type="password", key="email_password_input",
                         help="Use Gmail App Password (not your regular password)")
            email_recipient = st.text_input("Recipient Email", value=st.session_state.settings.get("email_recipient", "sajjanvsl@gmail.com"), key="email_recipient_input")
        
        with col2:
            st.subheader("📱 Telegram Settings")
            telegram_enabled = st.checkbox("Enable Telegram Alerts", value=st.session_state.settings.get("telegram_enabled", False), key="telegram_enabled_input")
            telegram_bot_token = st.text_input("Bot Token", value=st.session_state.settings.get("telegram_bot_token", ""), key="telegram_bot_token_input",
                         help="Get from @BotFather on Telegram")
            telegram_chat_id = st.text_input("Chat ID", value=st.session_state.settings.get("telegram_chat_id", ""), key="telegram_chat_id_input",
                         help="Your numeric chat ID (e.g., 123456789). Get it from @userinfobot.")
            
            if telegram_chat_id.startswith('@'):
                st.warning("⚠️ You entered a username. For direct messages, you need the numeric chat ID. Please get it from @userinfobot.")
            else:
                st.info("💡 After saving, you need to start a conversation with your bot: Send `/start` to `@YourBotUsername` (replace with your bot's username) in Telegram. Then the bot can send you alerts.")
        
        # Button to save settings
        if st.button("💾 Save Alert Settings", key="save_alert_settings_button"):
            st.session_state.settings = {
                "email_enabled": email_enabled,
                "email_sender": email_sender,
                "email_password": email_password,
                "email_recipient": email_recipient,
                "telegram_enabled": telegram_enabled,
                "telegram_bot_token": telegram_bot_token,
                "telegram_chat_id": telegram_chat_id
            }
            save_settings(st.session_state.settings)
            # Update session state
            st.session_state.email_enabled = email_enabled
            st.session_state.email_sender = email_sender
            st.session_state.email_password = email_password
            st.session_state.email_recipient = email_recipient
            st.session_state.telegram_enabled = telegram_enabled
            st.session_state.telegram_bot_token = telegram_bot_token
            st.session_state.telegram_chat_id = telegram_chat_id
            st.success("✅ Settings saved successfully!")
        
        # Test alert buttons
        if st.button("🔔 Send Test Alert", key="test_alert_button"):
            if st.session_state.get('email_enabled', False):
                result = st.session_state.alert_system.send_email_alert("TEST", 100, 90, "Test Alert", "₹90")
                if result:
                    st.success("Test email sent!")
                else:
                    st.error("Test email failed. Check email settings.")
            if st.session_state.get('telegram_enabled', False):
                if st.session_state.telegram_chat_id.startswith('@'):
                    st.error("❌ Telegram test failed: You used a username (@...). Please use the numeric chat ID from @userinfobot.")
                else:
                    result = st.session_state.alert_system.send_telegram_alert("TEST", 100, 90, "Test Alert", "₹90")
                    if result:
                        st.success("Test Telegram message sent!")
                    else:
                        st.error("Test Telegram failed. Please ensure:")
                        st.markdown("1. You have started a conversation with your bot by sending `/start` to `@YourBotUsername` in Telegram.")
                        st.markdown("2. Your numeric chat ID is correct (get it from @userinfobot).")
                        st.markdown("3. The bot token is correct.")
        
        # New button: Manual alert for strong signals
        if st.button("📢 Send Alerts for Strong Signals Now", key="manual_alert_button"):
            # Build current portfolio if not present
            if st.session_state.portfolio_df is None and st.session_state.holdings_df is not None:
                # rebuild portfolio (same logic as in holdings section)
                portfolio_data = []
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
                    try:
                        current_price = float(current_price)
                    except:
                        continue
                    portfolio_data.append({'Stock': name, 'Current Price': current_price})
                temp_df = pd.DataFrame(portfolio_data)
            elif st.session_state.portfolio_df is not None:
                temp_df = st.session_state.portfolio_df[['Stock', 'Current Price']].copy()
            else:
                # no holdings, use sample
                sample_portfolio = [
                    {"Stock": "HDFCBANK", "Current Price": 1680.50},
                    {"Stock": "VBL", "Current Price": 445.75},
                    {"Stock": "IREDA", "Current Price": 115.63},
                    {"Stock": "WAAREEENER", "Current Price": 2890.90},
                    {"Stock": "MAZDOCK", "Current Price": 2332.90},
                    {"Stock": "ADANIPORTS", "Current Price": 1362.40},
                    {"Stock": "BSE", "Current Price": 2952.60},
                    {"Stock": "HAL", "Current Price": 3935.40}
                ]
                temp_df = pd.DataFrame(sample_portfolio)
            
            # Build action data for these stocks (same logic as in final action table)
            action_rows = []
            for _, row in temp_df.iterrows():
                stock = row['Stock']
                current_price = row['Current Price']
                ticker = ALL_STOCKS.get(stock)
                if not ticker:
                    continue
                fair_value = get_reliable_fair_value(ticker, current_price)
                buy_zone_low = fair_value * 0.8
                buy_zone_high = fair_value * 0.85
                sell_zone_low = fair_value * 1.2
                sell_zone_high = fair_value * 1.3
                
                if current_price <= buy_zone_high:
                    if current_price <= buy_zone_low:
                        action = "BUY"
                        priority = "⭐⭐⭐⭐⭐"
                    else:
                        action = "BUY"
                        priority = "⭐⭐⭐⭐"
                elif current_price <= fair_value:
                    action = "BUY (DIP)"
                    priority = "⭐⭐⭐"
                elif current_price <= fair_value * 1.2:
                    action = "HOLD"
                    priority = "⭐⭐⭐"
                elif current_price <= fair_value * 1.5:
                    action = "REDUCE"
                    priority = "⭐⭐"
                else:
                    action = "SELL"
                    priority = "⭐"
                
                action_rows.append({
                    'Stock': stock,
                    'Current Price': current_price,
                    'Action': action,
                    'Priority': priority,
                    'Buy Zone Low': buy_zone_low,
                    'Buy Zone High': buy_zone_high,
                    'Sell Zone Low': sell_zone_low,
                    'Sell Zone High': sell_zone_high
                })
            
            # Now send alerts for strong signals
            alert_count = 0
            for row in action_rows:
                if row['Action'] == 'BUY' and row['Priority'] == '⭐⭐⭐⭐⭐':
                    key = f"strong_buy_{row['Stock']}"
                    if st.session_state.alert_system.should_send_alert(key):
                        target_zone = f"₹{round(row['Buy Zone Low'], 2)} – ₹{round(row['Buy Zone High'], 2)}"
                        if st.session_state.get('telegram_enabled', False):
                            st.session_state.alert_system.send_telegram_alert(
                                row['Stock'], row['Current Price'], row['Buy Zone Low'],
                                "Strong Buy", target_zone
                            )
                        if st.session_state.get('email_enabled', False):
                            st.session_state.alert_system.send_email_alert(
                                row['Stock'], row['Current Price'], row['Buy Zone Low'],
                                "Strong Buy", target_zone
                            )
                        alert_count += 1
                elif row['Action'] == 'SELL':
                    key = f"strong_sell_{row['Stock']}"
                    if st.session_state.alert_system.should_send_alert(key):
                        target_zone = f"₹{round(row['Sell Zone Low'], 2)} – ₹{round(row['Sell Zone High'], 2)}"
                        if st.session_state.get('telegram_enabled', False):
                            st.session_state.alert_system.send_telegram_alert(
                                row['Stock'], row['Current Price'], row['Sell Zone Low'],
                                "Strong Sell", target_zone
                            )
                        if st.session_state.get('email_enabled', False):
                            st.session_state.alert_system.send_email_alert(
                                row['Stock'], row['Current Price'], row['Sell Zone Low'],
                                "Strong Sell", target_zone
                            )
                        alert_count += 1
            if alert_count > 0:
                st.success(f"✅ Sent {alert_count} alert(s) for strong signals.")
            else:
                st.info("No strong buy or sell signals found at this moment.")
        
        st.info("⚠️ For Gmail, you need to enable 2FA and create an App Password. For Telegram, create a bot with @BotFather, then get your numeric chat ID from @userinfobot. You must also send a message to your bot first (e.g., `/start`) to allow it to message you.")
        st.markdown('</div>', unsafe_allow_html=True)

    # Refresh button
    if st.button("🔄 Refresh Data", key="refresh_data_button"):
        st.cache_data.clear()
        st.session_state.last_refresh = datetime.now()
        # Invalidate portfolio to force rebuild
        st.session_state.portfolio_df = None
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

    # ========== TABS (Only 3) ==========
    tab1, tab2, tab3 = st.tabs([
        "🤖 AI Swing Trading Scanner", 
        "🤖 AI Intraday Picks",
        "📊 Custom Fair Value + Final Portfolio Action"
    ])

    # ----- Tab 1: AI Swing Scanner -----
    with tab1:
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

    # ----- Tab 2: AI Intraday Picks -----
    with tab2:
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

    # ----- Tab 3: Custom Fair Value + Final Portfolio Action Table (combined) -----
    with tab3:
        st.markdown("## 📊 Custom Fair Value (EPS × Growth)")
        st.caption("**Formula:** Fair Value = EPS × Growth Rate × 1.5 | **Buy Below:** 80‑85% of Fair Value")
        
        stock_list = [
            {"name": "HAL", "category": "🟢 Core High-Conviction", "symbol": "HAL.NS"},
            {"name": "MAZDOCK", "category": "🟢 Core High-Conviction", "symbol": "MAZDOCK.NS"},
            {"name": "BSE", "category": "🟢 Core High-Conviction", "symbol": "BSE.NS"},
            {"name": "VBL", "category": "🟢 Core High-Conviction", "symbol": "VBL.NS"},
            {"name": "ADANIPORTS", "category": "🟢 Core High-Conviction", "symbol": "ADANIPORTS.NS"},
            {"name": "WAAREEENER", "category": "🚀 High Growth / High Risk", "symbol": "WAAREEENER.NS"},
            {"name": "IREDA", "category": "🚀 High Growth / High Risk", "symbol": "IREDA.NS"},
            {"name": "JIOFIN", "category": "🚀 High Growth / High Risk", "symbol": "JIOFIN.NS"},
            {"name": "ANANTRAJ", "category": "🚀 High Growth / High Risk", "symbol": "ANANTRAJ.NS"},
            {"name": "BAJAJHFL", "category": "⚠️ Defensive / Low Growth", "symbol": "BAJAJHFL.NS"}
        ]
        
        rows = []
        for stock in stock_list:
            ticker = stock["symbol"]
            price_df = get_price_data(ticker)
            if price_df.empty:
                continue
            current_price = price_df['Close'].iloc[-1]
            
            fair_value = get_reliable_fair_value(ticker, current_price)
            if fair_value is None:
                continue
            
            buy_low = fair_value * 0.80
            buy_high = fair_value * 0.85
            
            eps, growth = get_reliable_eps_and_growth(ticker, current_price)
            if eps is None:
                eps = np.nan
            if growth is None:
                growth = np.nan
            
            rows.append({
                "Category": stock["category"],
                "Stock": stock["name"],
                "EPS (₹)": round(eps, 2) if not pd.isna(eps) else "N/A",
                "Growth (%)": round(growth, 1) if not pd.isna(growth) else "N/A",
                "Fair Value (₹)": round(fair_value, 2),
                "Buy Below (₹)": f"₹{round(buy_low, 2)} – ₹{round(buy_high, 2)}"
            })
        
        if rows:
            df_fv = pd.DataFrame(rows)
            for category, group in df_fv.groupby("Category"):
                st.markdown(f"### {category}")
                st.dataframe(
                    group.drop(columns=["Category"]),
                    use_container_width=True,
                    hide_index=True
                )
        else:
            st.info("No fair value data available. Check your internet connection or stock symbols.")
        
        st.markdown("---")
        st.markdown("## 📊 🔥 FINAL PORTFOLIO ACTION TABLE")
        st.caption("**Current Price** vs **Buy Zone** – Buy when price falls into the Buy Zone. **Sell Zone** is for profit booking.")
        
        use_sample = False
        if st.session_state.portfolio_df is None or st.session_state.portfolio_df.empty:
            st.info("No holdings data found. You can either:")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📁 Upload CSV from section below", key="upload_csv_info_button"):
                    st.info("Please use the 'Add Holdings' section at the bottom of the page.")
            with col2:
                if st.button("📊 Use Sample Portfolio Data", key="use_sample_data_button"):
                    use_sample = True
                    st.success("Using sample portfolio data for demonstration.")
        
        sample_portfolio = [
            {"Stock": "HDFCBANK", "Current Price": 1680.50},
            {"Stock": "VBL", "Current Price": 445.75},
            {"Stock": "IREDA", "Current Price": 115.63},
            {"Stock": "WAAREEENER", "Current Price": 2890.90},
            {"Stock": "MAZDOCK", "Current Price": 2332.90},
            {"Stock": "ADANIPORTS", "Current Price": 1362.40},
            {"Stock": "BSE", "Current Price": 2952.60},
            {"Stock": "HAL", "Current Price": 3935.40},
            {"Stock": "IRCTC", "Current Price": 569.54},
            {"Stock": "ICICIAMC", "Current Price": 3112.10},
            {"Stock": "TCS", "Current Price": 2637.40},
            {"Stock": "TRENT", "Current Price": 3899.50},
            {"Stock": "ASTRAL", "Current Price": 1667.90},
            {"Stock": "BAJAJHFL", "Current Price": 87.04},
            {"Stock": "TMCV", "Current Price": 505.30},
            {"Stock": "TMPV", "Current Price": 382.65},
            {"Stock": "ANANTRAJ", "Current Price": 529.79},
            {"Stock": "JIOFIN", "Current Price": 255.40},
            {"Stock": "GANESHHOU", "Current Price": 671.70},
            {"Stock": "NATCOPHARM", "Current Price": 941.00},
            {"Stock": "MON100", "Current Price": 225.19},
            {"Stock": "GOLDBEES", "Current Price": 131.60},
            {"Stock": "SILVERBEES", "Current Price": 252.81},
            {"Stock": "LIQUIDBEES", "Current Price": 999.99},
            {"Stock": "SMALL250", "Current Price": 15.90},
            {"Stock": "MCX", "Current Price": 1800.00},
            {"Stock": "TRUALT", "Current Price": 401.40},
            {"Stock": "CIPLA", "Current Price": 1348.20},
            {"Stock": "NHPC", "Current Price": 75.33},
            {"Stock": "AWHCL", "Current Price": 494.50}
        ]
        
        if use_sample or (st.session_state.portfolio_df is not None and not st.session_state.portfolio_df.empty):
            if use_sample:
                action_df = pd.DataFrame(sample_portfolio)
            else:
                action_df = st.session_state.portfolio_df[['Stock', 'Current Price']].copy()
            
            action_data = []
            fair_values = {}
            
            for _, row in action_df.iterrows():
                stock = row['Stock']
                current_price = row['Current Price']
                
                ticker = ALL_STOCKS.get(stock)
                if not ticker:
                    continue
                
                fair_value = get_reliable_fair_value(ticker, current_price)
                fair_values[stock] = fair_value
                
                buy_zone_low = fair_value * 0.8
                buy_zone_high = fair_value * 0.85
                sell_zone_low = fair_value * 1.2
                sell_zone_high = fair_value * 1.3
                
                if current_price <= buy_zone_high:
                    if current_price <= buy_zone_low:
                        action = "BUY"
                        priority = "⭐⭐⭐⭐⭐"
                        verdict = "Strong Buy - Significant undervaluation"
                    else:
                        action = "BUY"
                        priority = "⭐⭐⭐⭐"
                        verdict = "Undervalued - Accumulate"
                elif current_price <= fair_value:
                    action = "BUY (DIP)"
                    priority = "⭐⭐⭐"
                    verdict = "Fairly valued - Buy on dips"
                elif current_price <= fair_value * 1.2:
                    action = "HOLD"
                    priority = "⭐⭐⭐"
                    verdict = "Hold for growth"
                elif current_price <= fair_value * 1.5:
                    action = "REDUCE"
                    priority = "⭐⭐"
                    verdict = "Overvalued - Consider partial exit"
                else:
                    action = "SELL"
                    priority = "⭐"
                    verdict = "Overvalued - Exit or reduce"
                
                in_buy_zone = "✅ Yes" if buy_zone_low <= current_price <= buy_zone_high else "❌ No"
                
                if "⭐⭐⭐⭐⭐" in priority:
                    allocation = "15–20%"
                elif "⭐⭐⭐⭐" in priority and "DIP" not in action:
                    allocation = "10–12%"
                elif "⭐⭐⭐⭐" in priority:
                    allocation = "8–10%"
                elif "⭐⭐⭐" in priority:
                    allocation = "5–7%"
                elif "⭐⭐" in priority:
                    allocation = "3–5%"
                else:
                    allocation = "0–2%"
                
                # Piotroski score
                fund = get_fundamental_data(ticker)
                piotroski = calculate_piotroski_score(fund) if fund else 0
                
                verdict_map = {
                    "HDFCBANK": "Core Compounder - Banking leader",
                    "VBL": "Strong Growth - Beverage giant",
                    "IREDA": "High Growth - Renewable energy",
                    "WAAREEENER": "Solar Multibagger - High potential",
                    "MAZDOCK": "Tactical - Defence order book",
                    "ADANIPORTS": "Infra Leader - Port monopoly",
                    "BSE": "Exchange Play - Market rally",
                    "HAL": "Defensive Growth - Defence PSU",
                    "IRCTC": "Slow Compounder - Railway monopoly",
                    "ICICIAMC": "Hidden Gem - Asset management",
                    "TCS": "Stable - IT leader",
                    "TRENT": "Expensive Growth - Retail expansion",
                    "ASTRAL": "Overvalued - Wait for correction",
                    "BAJAJHFL": "High Risk - Housing finance",
                    "TMCV": "Weak Fundamentals - Exit",
                    "TMPV": "Value Bet - Turnaround story",
                    "ANANTRAJ": "Realty Growth - Infrastructure",
                    "JIOFIN": "Future Fintech - Long-term",
                    "GANESHHOU": "Cyclical - Real estate",
                    "NATCOPHARM": "Pharma Play - Generic exports",
                    "MON100": "US ETF - Nasdaq tracker",
                    "GOLDBEES": "Gold ETF - Safe haven",
                    "SILVERBEES": "Silver ETF - Industrial demand",
                    "LIQUIDBEES": "Liquid ETF - Cash equivalent",
                    "SMALL250": "Small cap ETF - High risk",
                    "MCX": "Commodity exchange - Cyclical",
                    "TRUALT": "Value pick - Undervalued"
                }
                if stock in verdict_map:
                    verdict = verdict_map[stock]
                
                action_data.append({
                    'Stock': stock,
                    'Current Price': f"₹{current_price:.2f}",
                    'Action': action,
                    'Priority': priority,
                    'Buy Zone (₹)': f"₹{round(buy_zone_low, 2)} – ₹{round(buy_zone_high, 2)}",
                    'In Buy Zone': in_buy_zone,
                    'Sell Zone (₹)': f"₹{round(sell_zone_low, 2)} – ₹{round(sell_zone_high, 2)}",
                    'Allocation': allocation,
                    'Verdict': verdict,
                    'Piotroski Score': piotroski,
                    'Buy Zone Low': buy_zone_low,
                    'Buy Zone High': buy_zone_high,
                    'Sell Zone Low': sell_zone_low,
                    'Sell Zone High': sell_zone_high,
                    'Fair Value': fair_value
                })
            
            result_df = pd.DataFrame(action_data)
            priority_order = {'⭐⭐⭐⭐⭐': 1, '⭐⭐⭐⭐': 2, '⭐⭐⭐': 3, '⭐⭐': 4, '⭐': 5}
            result_df['Priority_Num'] = result_df['Priority'].map(priority_order)
            result_df = result_df.sort_values('Priority_Num').drop(columns=['Priority_Num'])
            
            st.dataframe(
                result_df.style.applymap(
                    lambda x: 'background-color: #d4edda' if x == 'BUY' else 
                             ('background-color: #fff3cd' if x == 'BUY (DIP)' else
                              ('background-color: #f8d7da' if x == 'SELL' else
                               ('background-color: #cce5ff' if x == 'HOLD' else ''))),
                    subset=['Action']
                ).applymap(
                    lambda x: 'background-color: #d4edda' if x == '✅ Yes' else ('background-color: #f8d7da' if x == '❌ No' else ''),
                    subset=['In Buy Zone']
                ),
                use_container_width=True,
                hide_index=True
            )
            
            st.markdown("---")
            st.subheader("📊 Portfolio Summary")
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                buy_count = len(result_df[result_df['Action'].str.contains('BUY')])
                st.metric("BUY Signals", buy_count)
            with col2:
                hold_count = len(result_df[result_df['Action'] == 'HOLD'])
                st.metric("HOLD Signals", hold_count)
            with col3:
                sell_count = len(result_df[result_df['Action'] == 'SELL'])
                st.metric("SELL Signals", sell_count)
            with col4:
                reduce_count = len(result_df[result_df['Action'] == 'REDUCE'])
                st.metric("REDUCE Signals", reduce_count)
            with col5:
                in_zone = len(result_df[result_df['In Buy Zone'] == '✅ Yes'])
                st.metric("In Buy Zone", in_zone)
            
            st.markdown("---")
            st.subheader("🎯 Recommended Allocation by Priority")
            allocation_summary = result_df.groupby('Priority')['Allocation'].first().reset_index()
            if not allocation_summary.empty:
                fig = px.pie(allocation_summary, values='Allocation', names='Priority', title='Suggested Portfolio Weight')
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            st.subheader("🏆 Top 5 BUY Recommendations")
            top_buys = result_df[result_df['Action'].str.contains('BUY')].head(5)
            if not top_buys.empty:
                st.dataframe(top_buys[['Stock', 'Current Price', 'Action', 'Priority', 'Buy Zone (₹)', 'In Buy Zone', 'Verdict']], use_container_width=True, hide_index=True)
            else:
                st.info("No BUY recommendations at this time.")
            
            st.markdown("---")
            st.subheader("⚠️ Stocks to Watch (Above Buy Zone)")
            above_zone = result_df[(result_df['In Buy Zone'] == '❌ No') & (result_df['Action'].str.contains('BUY'))]
            if not above_zone.empty:
                st.dataframe(above_zone[['Stock', 'Current Price', 'Action', 'Buy Zone (₹)', 'Verdict']], use_container_width=True, hide_index=True)
                st.info("💡 These stocks are currently above the recommended buy zone. Consider waiting for price to dip into the buy zone.")
            else:
                st.success("✅ All BUY recommendations are currently in the buy zone!")
            
            # Auto-alerts for strong signals (called automatically when portfolio is built)
            def check_strong_signals_and_alert(portfolio_df):
                if not (st.session_state.get('telegram_enabled', False) or st.session_state.get('email_enabled', False)):
                    return
                
                for _, row in portfolio_df.iterrows():
                    stock = row['Stock']
                    action = row['Action']
                    priority = row['Priority']
                    current_price_str = row['Current Price']
                    current_price = float(current_price_str.replace('₹', '').replace(',', ''))
                    buy_zone_low = row['Buy Zone Low']
                    buy_zone_high = row['Buy Zone High']
                    sell_zone_low = row['Sell Zone Low']
                    sell_zone_high = row['Sell Zone High']
                    
                    if action == 'BUY' and priority == '⭐⭐⭐⭐⭐':
                        key = f"strong_buy_{stock}"
                        if st.session_state.alert_system.should_send_alert(key):
                            if key in st.session_state.alerts_sent_this_session:
                                continue
                            st.session_state.alerts_sent_this_session.add(key)
                            target_zone = f"₹{round(buy_zone_low, 2)} – ₹{round(buy_zone_high, 2)}"
                            if st.session_state.get('telegram_enabled', False):
                                st.session_state.alert_system.send_telegram_alert(stock, current_price, buy_zone_low, "Strong Buy", target_zone)
                            if st.session_state.get('email_enabled', False):
                                st.session_state.alert_system.send_email_alert(stock, current_price, buy_zone_low, "Strong Buy", target_zone)
                    
                    elif action == 'SELL':
                        key = f"strong_sell_{stock}"
                        if st.session_state.alert_system.should_send_alert(key):
                            if key in st.session_state.alerts_sent_this_session:
                                continue
                            st.session_state.alerts_sent_this_session.add(key)
                            target_zone = f"₹{round(sell_zone_low, 2)} – ₹{round(sell_zone_high, 2)}"
                            if st.session_state.get('telegram_enabled', False):
                                st.session_state.alert_system.send_telegram_alert(stock, current_price, sell_zone_low, "Strong Sell", target_zone)
                            if st.session_state.get('email_enabled', False):
                                st.session_state.alert_system.send_email_alert(stock, current_price, sell_zone_low, "Strong Sell", target_zone)
            
            check_strong_signals_and_alert(result_df)
            
        else:
            st.info("No holdings data available. Please add stocks using the section below or click 'Use Sample Portfolio Data' to see a demo.")

    st.markdown("---")

    # ------------------------------
    # HOLDINGS SECTION
    # ------------------------------
    if st.session_state.holdings_df is not None and not st.session_state.holdings_df.empty:
        if st.session_state.portfolio_df is None:
            portfolio_data = []
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
                try:
                    current_price = float(current_price)
                except:
                    continue
                
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
                    'Current Price': current_price,
                    'Cur Value': cur_value,
                    'P&L': pnl,
                    'P&L %': pnl_pct,
                    'Recommendation': rec,
                    'Criteria Met': f"{criteria_met}/19",
                })
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
        
        st.markdown("## 📊 Your Holdings")
        st.dataframe(st.session_state.portfolio_df, use_container_width=True)
        
        st.markdown("---")
        st.subheader("🔔 Live Alerts")
        st.caption("The system automatically checks if any stock has dropped into your buy zone or reached your target price.")
        
        if st.button("🔍 Check Alerts Now", key="check_alerts_button"):
            alerts_triggered = []
            for _, row in st.session_state.portfolio_df.iterrows():
                stock = row['Stock']
                current_price = row['Current Price']
                
                ticker = ALL_STOCKS.get(stock)
                fund = get_fundamental_data(ticker)
                eps_growth_buy = None
                if fund:
                    fair_value = get_reliable_fair_value(ticker, current_price)
                    eps_growth_buy = fair_value * 0.8 if fair_value else None
                
                target_list = []
                if eps_growth_buy:
                    target_list.append(eps_growth_buy)
                if stock in st.session_state.target_prices:
                    user_targets = st.session_state.target_prices[stock]
                    if isinstance(user_targets, list):
                        target_list.extend(user_targets)
                    else:
                        target_list.append(user_targets)
                
                if target_list:
                    alerts_sent = st.session_state.alert_system.check_and_send_alerts(stock, current_price, target_list)
                    if alerts_sent:
                        alerts_triggered.append(f"{stock}: {', '.join(alerts_sent)}")
            
            if alerts_triggered:
                st.success(f"✅ Alerts sent: {', '.join(alerts_triggered)}")
            else:
                st.info("No alerts triggered at this time. Check your target prices and current prices.")
        
        # Editable target prices for each stock
        st.markdown("---")
        st.subheader("✏️ Set Custom Target Prices")
        st.caption("Add or edit target prices per stock. Alerts will be sent when the price drops to or below any of these targets.")
        
        # Display current target prices in a table with ability to edit
        target_df_data = []
        for stock in st.session_state.portfolio_df['Stock'].unique():
            current_targets = st.session_state.target_prices.get(stock, [])
            if isinstance(current_targets, list):
                target_str = ", ".join([f"₹{t:.2f}" for t in current_targets]) if current_targets else "None"
            else:
                target_str = f"₹{current_targets:.2f}" if current_targets else "None"
            target_df_data.append({"Stock": stock, "Current Targets": target_str})
        
        target_df = pd.DataFrame(target_df_data)
        st.dataframe(target_df, use_container_width=True, hide_index=True)
        
        # Input for new target
        col1, col2, col3 = st.columns([2,1,1])
        with col1:
            selected_stock = st.selectbox("Select Stock", st.session_state.portfolio_df['Stock'].unique())
        with col2:
            new_target = st.number_input("Target Price (₹)", min_value=0.0, step=5.0, value=100.0)
        with col3:
            if st.button("Add/Update Target", key="add_target_button"):
                current = st.session_state.target_prices.get(selected_stock, [])
                if not isinstance(current, list):
                    current = [current] if current else []
                if new_target not in current:
                    current.append(new_target)
                    current.sort()
                    st.session_state.target_prices[selected_stock] = current
                    save_target_prices(st.session_state.target_prices)
                    st.success(f"Added target ₹{new_target:.2f} for {selected_stock}")
                else:
                    st.warning("Target already exists.")
                st.rerun()
        
        # Option to remove targets
        with st.expander("🗑️ Remove Target Prices"):
            for stock in st.session_state.portfolio_df['Stock'].unique():
                targets = st.session_state.target_prices.get(stock, [])
                if targets:
                    for t in targets:
                        if st.button(f"Remove ₹{t:.2f} for {stock}", key=f"rem_{stock}_{t}"):
                            if isinstance(targets, list):
                                targets.remove(t)
                                if not targets:
                                    del st.session_state.target_prices[stock]
                                else:
                                    st.session_state.target_prices[stock] = targets
                            else:
                                del st.session_state.target_prices[stock]
                            save_target_prices(st.session_state.target_prices)
                            st.success(f"Removed target ₹{t:.2f} for {stock}")
                            st.rerun()
        
    else:
        st.info("No holdings data. Please add stocks using the section below.")
    
    # ------------------------------
    # INPUT SECTION
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
if not st.session_state.get('authenticated', False):
    show_login()
else:
    main_app()

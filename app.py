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

# ... (keep CSS, imports, etc. same as before) ...

# ------------------------------
# MASTER STOCK LIST (unchanged)
# ------------------------------
ALL_STOCKS = { ... }  # same

# ------------------------------
# DATA PERSISTENCE (unchanged)
# ------------------------------
# ... (load/save functions) ...

# ------------------------------
# IMPROVED FUNDAMENTAL FETCHING
# ------------------------------
def safe_get_latest(df, key):
    """Get the most recent non‑NaN value for a financial statement item."""
    if df is not None and key in df.index:
        vals = df.loc[key]
        if isinstance(vals, pd.Series):
            vals = vals[vals.notna()]
            if len(vals) > 0:
                return vals.iloc[0]
    return np.nan

def safe_get_series(df, key):
    """Return the whole series (years) for a financial item."""
    if df is not None and key in df.index:
        vals = df.loc[key]
        if isinstance(vals, pd.Series):
            vals = vals[vals.notna()]
            if len(vals) > 0:
                return vals
    return pd.Series(dtype=float)

def cagr(series, years=3):
    """Compute CAGR over the last `years` (requires at least 2 points)."""
    if len(series) < 2:
        return np.nan
    # series is from most recent to oldest (pandas order may be reversed)
    # Ensure we have at least `years+1` data points?
    # We'll take the oldest available and newest.
    # To be safe, we'll use first (latest) and last (oldest) if enough years.
    if len(series) >= 2:
        latest = series.iloc[0]
        # find the value approximately `years` years ago
        # If we have more than years, use the one at index `min(years, len-1)`
        idx = min(years, len(series)-1)
        past = series.iloc[idx]
        if past == 0 or np.isnan(past):
            return np.nan
        return ((latest / past) ** (1/idx) - 1) * 100
    return np.nan

def mean_over_period(series, years=3):
    """Average over the last `years` of data."""
    if len(series) == 0:
        return np.nan
    # take first `years` points (most recent)
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

        # Revenue series
        revenue = safe_get_series(financials, 'Total Revenue')
        sales_growth = cagr(revenue, years=3)

        # Net income series
        net_income = safe_get_series(financials, 'Net Income')
        profit_growth = cagr(net_income, years=3)

        # Market Cap (in Cr) – divide by 1e7
        market_cap = info.get('marketCap', 0) / 1e7

        # EBIT series
        ebit_series = safe_get_series(financials, 'EBIT')

        # Total Assets and Current Liabilities for ROCE
        total_assets_series = safe_get_series(balance_sheet, 'Total Assets')
        current_liab_series = safe_get_series(balance_sheet, 'Total Current Liabilities')

        # Compute ROCE for each year (where data available)
        roce_values = []
        min_len = min(len(ebit_series), len(total_assets_series), len(current_liab_series))
        for i in range(min_len):
            ebit = ebit_series.iloc[i]
            ta = total_assets_series.iloc[i]
            cl = current_liab_series.iloc[i]
            capital_employed = ta - cl
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

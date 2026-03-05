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
import warnings
warnings.filterwarnings('ignore')

# ... (keep all existing imports and CSS, authentication, ALL_STOCKS, data fetching, fundamental, screeners, train model, etc.) ...

# ------------------------------
# CRITERIA TABLE DISPLAY FUNCTION
# ------------------------------
def display_criteria_table(criteria_dict, title="Criteria Status"):
    """Display criteria with checkmarks in a formatted table."""
    html = f'<div class="criteria-table"><h4>{title}</h4>'
    for criterion, met in criteria_dict.items():
        status = '✅' if met else '❌'
        color = 'criteria-pass' if met else 'criteria-fail'
        html += f'<div class="criteria-row"><span>{criterion}</span><span class="{color}">{status}</span></div>'
    html += '</div>'
    return html

# ... (keep login, no_stocks_message, and all other functions unchanged) ...

# ------------------------------
# MAIN APP
# ------------------------------
def main_app():
    # ... (session state initialization, header, refresh, debug expander remain same) ...

    # Create tabs
    screener_tab1, screener_tab2, screener_tab3, screener_tab4, screener_tab5 = st.tabs([
        "🤖 AI Swing Scanner", 
        "📉 Swing Pullback", 
        "📈 Swing Breakout", 
        "⚡ Intraday Breakout (5-min)",
        "🤖 AI Intraday Picks"
    ])

    with screener_tab1:
        st.markdown("## 🤖 AI Swing Trading Scanner")
        st.caption("AI-powered swing signals combining technical rules with RandomForest. Click on any stock to expand and see criteria details.")

        with st.spinner("Fetching swing signals..."):
            swing_data = []
            swing_criteria = {}
            today = datetime.now().date()
            total_stocks = len(ALL_STOCKS)
            progress_bar = st.progress(0, text="Scanning stocks...")
            for idx, (name, ticker) in enumerate(ALL_STOCKS.items()):
                df = get_price_data(ticker)
                sig, criteria = ai_swing_signal(df, name)
                if sig and sig['Signal'] == 'SWING BUY':
                    last_seen = st.session_state.swing_history.get(name)
                    if last_seen is None or (today - last_seen).days >= 5:
                        sig['Fresh'] = '✅ Fresh'
                        st.session_state.swing_history[name] = today
                    else:
                        sig['Fresh'] = ''
                    swing_data.append(sig)
                    swing_criteria[name] = criteria
                progress_bar.progress((idx+1)/total_stocks)
            progress_bar.empty()

        if swing_data:
            # Sort by Fresh (top) and then maybe by RSI or something
            swing_data.sort(key=lambda x: (x.get('Fresh', '') != '✅ Fresh', x.get('RSI', 0)))
            
            for i, sig in enumerate(swing_data):
                with st.expander(f"{sig['Stock']} – RSI: {sig['RSI']} | Entry: ₹{sig['Entry']} | Target: ₹{sig['Target']} | Stop: ₹{sig['Stop Loss']}"):
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        st.markdown(f"**Signal:** {sig['Signal']}")
                        st.markdown(f"**AI Confidence:** {sig['AI Conf']}")
                        st.markdown(f"**Holding Days:** {sig['Holding']}")
                    with col2:
                        st.markdown(f"**Fresh:** {sig.get('Fresh', '')}")
                    
                    if sig['Stock'] in swing_criteria:
                        st.markdown(display_criteria_table(swing_criteria[sig['Stock']], f"Criteria for {sig['Stock']}"), unsafe_allow_html=True)
        else:
            no_stocks_message(
                "AI Swing Scanner",
                "• RSI < 45<br>• 20 EMA > 50 EMA<br>• Price > recent low +2%<br>• AI confidence > 60%"
            )

    with screener_tab2:
        st.markdown("## 📉 Swing Pullback Screener")
        st.caption("High probability pullback opportunities. Click on any stock to expand and see criteria details.")
        
        with st.spinner("Scanning for pullback opportunities..."):
            pullback_data = []
            pullback_criteria = {}
            total_stocks = len(ALL_STOCKS)
            progress_bar = st.progress(0, text="Scanning stocks...")
            for idx, (name, ticker) in enumerate(ALL_STOCKS.items()):
                df = get_price_data(ticker)
                sig, criteria = swing_pullback_signal(df, name)
                if sig:
                    pullback_data.append(sig)
                    pullback_criteria[name] = criteria
                progress_bar.progress((idx+1)/total_stocks)
            progress_bar.empty()
        
        if pullback_data:
            for i, sig in enumerate(pullback_data):
                with st.expander(f"{sig['Stock']} – Close: ₹{sig['Close']} | RSI: {sig['RSI']} | Vol Ratio: {sig['Vol Ratio']}"):
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        st.markdown(f"**20 EMA:** ₹{sig['20 EMA']}")
                        st.markdown(f"**50 EMA:** ₹{sig['50 EMA']}")
                    with col2:
                        st.markdown(f"**Entry:** ₹{sig['Entry']}")
                        st.markdown(f"**Target:** ₹{sig['Target']}")
                        st.markdown(f"**Stop Loss:** ₹{sig['Stop Loss']}")
                    
                    if sig['Stock'] in pullback_criteria:
                        st.markdown(display_criteria_table(pullback_criteria[sig['Stock']], f"Criteria for {sig['Stock']}"), unsafe_allow_html=True)
        else:
            no_stocks_message(
                "Swing Pullback Screener",
                "• Close > 50 EMA<br>• 20 EMA > 50 EMA<br>• Close ≤ 1.02 × 20 EMA<br>• RSI between 40-60<br>• Volume > 1.2× average<br>• Price > 100"
            )

    with screener_tab3:
        st.markdown("## 📈 Swing Breakout Screener")
        st.caption("Breakout opportunities. Click on any stock to expand and see criteria details.")
        
        with st.spinner("Scanning for breakout opportunities..."):
            breakout_data = []
            breakout_criteria = {}
            total_stocks = len(ALL_STOCKS)
            progress_bar = st.progress(0, text="Scanning stocks...")
            for idx, (name, ticker) in enumerate(ALL_STOCKS.items()):
                df = get_price_data(ticker)
                sig, criteria = swing_breakout_signal(df, name)
                if sig:
                    breakout_data.append(sig)
                    breakout_criteria[name] = criteria
                progress_bar.progress((idx+1)/total_stocks)
            progress_bar.empty()
        
        if breakout_data:
            for i, sig in enumerate(breakout_data):
                with st.expander(f"{sig['Stock']} – Close: ₹{sig['Close']} | RSI: {sig['RSI']} | Vol Ratio: {sig['Vol Ratio']}"):
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        st.markdown(f"**20d High:** ₹{sig['20d High']}")
                    with col2:
                        st.markdown(f"**Entry:** ₹{sig['Entry']}")
                        st.markdown(f"**Target:** ₹{sig['Target']}")
                        st.markdown(f"**Stop Loss:** ₹{sig['Stop Loss']}")
                    
                    if sig['Stock'] in breakout_criteria:
                        st.markdown(display_criteria_table(breakout_criteria[sig['Stock']], f"Criteria for {sig['Stock']}"), unsafe_allow_html=True)
        else:
            no_stocks_message(
                "Swing Breakout Screener",
                "• Close above 20-day high<br>• Volume > 1.5× average<br>• RSI > 60<br>• 50 EMA > 200 EMA<br>• Price > 100"
            )

    with screener_tab4:
        st.markdown("## ⚡ Intraday Breakout Screener (5-min)")
        st.caption("Real-time 5-minute breakout signals. Click on any stock to expand and see criteria details.")
        
        with st.spinner("Scanning for intraday breakouts..."):
            intraday_breakout_data = []
            intraday_breakout_criteria = {}
            total_stocks = len(ALL_STOCKS)
            progress_bar = st.progress(0, text="Scanning stocks...")
            for idx, (name, ticker) in enumerate(ALL_STOCKS.items()):
                sig, criteria = intraday_breakout_signal(name)
                if sig:
                    intraday_breakout_data.append(sig)
                    intraday_breakout_criteria[name] = criteria
                progress_bar.progress((idx+1)/total_stocks)
            progress_bar.empty()
        
        if intraday_breakout_data:
            for i, sig in enumerate(intraday_breakout_data):
                with st.expander(f"{sig['Stock']} – Close: ₹{sig['Close']} | RSI: {sig['RSI']} | Vol Ratio: {sig['Vol Ratio']}"):
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        st.markdown(f"**VWAP:** ₹{sig['VWAP']}")
                    with col2:
                        st.markdown(f"**Entry:** ₹{sig['Entry']}")
                        st.markdown(f"**Target:** ₹{sig['Target']}")
                        st.markdown(f"**Stop Loss:** ₹{sig['Stop Loss']}")
                    
                    if sig['Stock'] in intraday_breakout_criteria:
                        st.markdown(display_criteria_table(intraday_breakout_criteria[sig['Stock']], f"Criteria for {sig['Stock']}"), unsafe_allow_html=True)
        else:
            no_stocks_message(
                "Intraday Breakout Screener (5-min)",
                "• Close > VWAP<br>• RSI > 55<br>• Volume > 1.5× average<br>• Close > Previous High"
            )

    with screener_tab5:
        st.markdown("## 🤖 AI Intraday Picks")
        st.caption("AI‑powered intraday picks. Higher score = stronger signal. Click on any stock to expand and see criteria details.")
        
        with st.spinner("Scanning for AI intraday opportunities..."):
            intraday = intraday_picks()[:10]
            # Get criteria for each pick
            intraday_criteria = {}
            for pick in intraday:
                name = pick['Stock']
                df = get_price_data(ALL_STOCKS[name])
                _, criteria = ai_intraday_signal(df, name)
                intraday_criteria[name] = criteria
        
        if intraday:
            for i, pick in enumerate(intraday):
                with st.expander(f"{pick['Stock']} – Score: {pick['Score']} | Entry: ₹{pick['Entry']} | RSI: {pick['RSI']}"):
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        st.markdown(f"**Volume Surge:** {pick['Volume Surge']}")
                        st.markdown(f"**AI Conf:** {pick['AI Conf']}")
                    with col2:
                        st.markdown(f"**Target:** ₹{pick['Target']}")
                        st.markdown(f"**Stop Loss:** ₹{pick['Stop Loss']}")
                    
                    if pick['Stock'] in intraday_criteria:
                        st.markdown(display_criteria_table(intraday_criteria[pick['Stock']], f"Criteria for {pick['Stock']}"), unsafe_allow_html=True)
        else:
            no_stocks_message(
                "AI Intraday Picks",
                "• Volume surge > 1.2x<br>• Price > 20 MA<br>• RSI between 30-70<br>• AI confidence > 60%<br>• Combined score ≥ 3"
            )

    st.markdown("---")

    # ------------------------------
    # HOLDINGS SECTION (unchanged, remains after screeners)
    # ------------------------------
    # ... (keep all holdings processing, metrics, and delete functionality) ...

    # ------------------------------
    # INPUT SECTION (unchanged)
    # ------------------------------
    # ... (keep file upload and single stock add) ...

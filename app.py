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
# ENHANCED CSS – FULL BLUE BACKGROUND
# ------------------------------
st.markdown("""
<style>
    /* Force full‑page blue gradient */
    html, body, [data-testid="stAppViewContainer"] {
        background: linear-gradient(145deg, #1e3a8a 0%, #3b82f6 100%) !important;
        background-attachment: fixed !important;
    }
    .stApp {
        background: transparent !important;
    }
    /* Headers with white text for contrast */
    h1, h2, h3, h4, h5, h6 {
        color: white !important;
        font-weight: 600;
        text-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    /* Metric cards – frosted glass */
    .metric-card {
        background: rgba(255, 255, 255, 0.15) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 24px !important;
        padding: 1.5rem !important;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2) !important;
        color: white !important;
        transition: all 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        background: rgba(255, 255, 255, 0.25) !important;
        border-color: rgba(255, 255, 255, 0.5) !important;
    }
    .metric-label {
        color: rgba(255, 255, 255, 0.8) !important;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-value {
        color: white !important;
        font-size: 2rem;
        font-weight: 700;
    }
    .metric-delta {
        color: rgba(255, 255, 255, 0.9) !important;
    }
    /* Tags */
    .buy-tag {
        background: #22c55e !important;
        color: white !important;
        padding: 0.25rem 0.8rem;
        border-radius: 30px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
        box-shadow: 0 2px 6px rgba(0,0,0,0.2);
    }
    .fresh-tag {
        background: #06b6d4 !important;
        color: white !important;
        padding: 0.25rem 0.8rem;
        border-radius: 30px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
        margin-left: 0.5rem;
        box-shadow: 0 2px 6px rgba(0,0,0,0.2);
    }
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background: rgba(255, 255, 255, 0.2) !important;
        backdrop-filter: blur(8px);
        padding: 0.5rem 1.5rem;
        border-radius: 50px;
        border: 1px solid rgba(255, 255, 255, 0.3);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 30px;
        padding: 0.6rem 1.5rem;
        font-weight: 500;
        color: white !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(255, 255, 255, 0.3) !important;
        color: white !important;
        border: 1px solid white;
    }
    /* DataFrames */
    .stDataFrame {
        border-radius: 20px;
        overflow: hidden;
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .stDataFrame table {
        background: transparent !important;
    }
    .stDataFrame th {
        background: rgba(255, 255, 255, 0.2) !important;
        color: white !important;
        font-weight: 600;
    }
    .stDataFrame td {
        color: white !important;
        background: rgba(255, 255, 255, 0.05) !important;
    }
    /* Dividers */
    hr {
        margin: 2rem 0;
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.5), transparent);
    }
    /* Header */
    .main-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 2rem;
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(8px);
        padding: 1rem 2rem;
        border-radius: 40px;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .logo {
        font-size: 1.8rem;
        font-weight: 700;
        color: white !important;
        text-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }
    /* Input section */
    .input-section {
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(8px);
        padding: 2rem;
        border-radius: 30px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        margin-top: 2rem;
    }
    .input-section label {
        color: white !important;
    }
    .stTextInput input, .stFileUploader {
        background: rgba(255, 255, 255, 0.2) !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        color: white !important;
        border-radius: 30px !important;
    }
    /* Priority box */
    .priority-box {
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(8px);
        padding: 2rem;
        border-radius: 30px;
        border-left: 6px solid #fbbf24;
        border: 1px solid rgba(255, 255, 255, 0.2);
        margin-bottom: 2rem;
        color: white !important;
    }
    /* Debug box */
    .debug-box {
        background: rgba(0, 0, 0, 0.2) !important;
        border: 1px dashed rgba(255, 255, 255, 0.4);
        padding: 1rem;
        border-radius: 16px;
    }
    /* Info/warning messages */
    .stAlert {
        background: rgba(255, 255, 255, 0.15) !important;
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        color: white !important;
        border-radius: 16px;
    }
    /* Buttons */
    .stButton button {
        background: rgba(255, 255, 255, 0.2) !important;
        border: 1px solid rgba(255, 255, 255, 0.4) !important;
        color: white !important;
        border-radius: 30px !important;
        transition: all 0.2s;
    }
    .stButton button:hover {
        background: rgba(255, 255, 255, 0.3) !important;
        border-color: white !important;
    }
    /* Delete button (small trash can) */
    .delete-btn {
        background: rgba(239, 68, 68, 0.3) !important;
        border: 1px solid rgba(239, 68, 68, 0.6) !important;
        color: white !important;
        border-radius: 20px !important;
        padding: 0.2rem 0.8rem !important;
    }
    .delete-btn:hover {
        background: rgba(239, 68, 68, 0.5) !important;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------
# (REST OF THE CODE – unchanged from the previous robust version)
# ------------------------------
# ... (all functions and logic remain exactly as in the previous answer)
# ... (I'll omit them here for brevity, but you should keep the full code from the previous answer)

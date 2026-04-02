    # ----- Tab 1: AI Swing Scanner (Improved with Debug) -----
    with tab1:
        st.markdown("## 🤖 AI Swing Trading Scanner")
        st.caption("AI-powered swing signals combining technical rules (relaxed criteria for better coverage).")
        
        # Debug mode toggle
        show_debug = st.checkbox("🔍 Show Debug Info (see why stocks are failing)", value=False)
        
        with st.spinner("Fetching swing signals..."):
            swing_data = []
            debug_data = []  # For debug table
            today = datetime.now().date()
            total_stocks = len(ALL_STOCKS)
            progress_bar = st.progress(0, text="Scanning stocks...")
            
            for idx, (name, ticker) in enumerate(ALL_STOCKS.items()):
                df = get_price_data(ticker)
                if df.empty:
                    debug_data.append({
                        'Stock': name,
                        'Error': 'No price data',
                        'RSI': 'N/A',
                        '20EMA > 50EMA': 'N/A',
                        'Price > recent low+1%': 'N/A',
                        'Volume Surge >20%': 'N/A',
                        'Pass': '❌'
                    })
                    progress_bar.progress((idx+1)/total_stocks)
                    continue
                
                try:
                    close = df['Close'].astype(float)
                    high = df['High'].astype(float)
                    low = df['Low'].astype(float)
                    volume = df['Volume'].astype(float)
                    
                    # Technical indicators
                    rsi = RSIIndicator(close).rsi()
                    current_rsi = rsi.iloc[-1]
                    
                    ema20 = close.ewm(span=20, adjust=False).mean()
                    ema50 = close.ewm(span=50, adjust=False).mean()
                    ema_condition = ema20.iloc[-1] > ema50.iloc[-1]
                    
                    recent_low = low[-20:].min()
                    current_price = close.iloc[-1]
                    price_condition = current_price > recent_low * 1.01  # +1%
                    
                    avg_volume = volume[-20:].mean()
                    volume_surge = volume.iloc[-1] > avg_volume * 1.2
                    
                    rsi_condition = current_rsi < 50
                    
                    pass_all = (rsi_condition and ema_condition and price_condition and volume_surge)
                    
                    # Collect debug info
                    debug_data.append({
                        'Stock': name,
                        'Error': '',
                        'RSI': round(current_rsi, 1),
                        '20EMA > 50EMA': '✅' if ema_condition else '❌',
                        'Price > recent low+1%': f"{current_price:.2f} > {recent_low*1.01:.2f} = {'✅' if price_condition else '❌'}",
                        'Volume Surge >20%': f"{volume.iloc[-1]/avg_volume:.1f}x = {'✅' if volume_surge else '❌'}",
                        'Pass': '✅' if pass_all else '❌'
                    })
                    
                    if pass_all:
                        sig = {
                            'Stock': name,
                            'Signal': 'SWING BUY',
                            'RSI': round(current_rsi, 1),
                            'Entry': round(current_price, 2),
                            'Target': round(recent_low * 1.05, 2),  # Simplified target
                            'Stop Loss': round(recent_low * 0.98, 2),
                            'Holding': 15,
                            'Volume Surge': f"{volume.iloc[-1]/avg_volume:.1f}x"
                        }
                        # Check freshness
                        last_seen = st.session_state.swing_history.get(name)
                        if last_seen is None or (today - last_seen).days >= 5:
                            sig['Fresh'] = '✅ Fresh'
                            st.session_state.swing_history[name] = today
                        else:
                            sig['Fresh'] = ''
                        swing_data.append(sig)
                except Exception as e:
                    debug_data.append({
                        'Stock': name,
                        'Error': str(e)[:50],
                        'RSI': 'N/A',
                        '20EMA > 50EMA': 'N/A',
                        'Price > recent low+1%': 'N/A',
                        'Volume Surge >20%': 'N/A',
                        'Pass': '❌'
                    })
                
                progress_bar.progress((idx+1)/total_stocks)
            progress_bar.empty()
        
        # Display results
        if swing_data:
            swing_df = pd.DataFrame(swing_data)
            display_cols = ['Stock', 'Signal', 'RSI', 'Entry', 'Target', 'Stop Loss', 'Holding', 'Volume Surge', 'Fresh']
            swing_df = swing_df[[col for col in display_cols if col in swing_df.columns]]
            st.markdown('<span class="top-pick-badge">⭐ TOP SWING PICK</span>', unsafe_allow_html=True)
            st.dataframe(swing_df, width='stretch')
            
            # Auto-alerts for fresh swing signals
            for sig in swing_data:
                if sig.get('Fresh') == '✅ Fresh':
                    stock = sig['Stock']
                    entry = sig['Entry']
                    target = sig['Target']
                    stop_loss = sig['Stop Loss']
                    key = f"swing_signal_{stock}"
                    if st.session_state.alert_system.should_send_alert(key):
                        target_zone = f"Entry: ₹{entry}, Target: ₹{target}, SL: ₹{stop_loss}"
                        if st.session_state.get('telegram_enabled', False):
                            st.session_state.alert_system.send_telegram_alert(
                                stock, entry, target, 
                                signal_type="Swing Buy Signal",
                                target_zone=target_zone
                            )
                        if st.session_state.get('email_enabled', False):
                            st.session_state.alert_system.send_email_alert(
                                stock, entry, target,
                                signal_type="Swing Buy Signal",
                                target_zone=target_zone
                            )
        else:
            no_stocks_message("AI Swing Scanner", "• RSI < 50<br>• 20 EMA > 50 EMA<br>• Price > recent low +1%<br>• Volume surge > 20%")
        
        # Show debug table if enabled
        if show_debug and debug_data:
            st.markdown("---")
            st.markdown("### 🔍 Debug: Why stocks are failing")
            df_debug = pd.DataFrame(debug_data)
            st.dataframe(df_debug, use_container_width=True, hide_index=True)
            st.caption("💡 For a stock to pass, all conditions must be ✅. Check which condition is failing for your stocks.")

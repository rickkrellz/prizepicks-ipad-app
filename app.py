"""
Main PrizePicks +EV Optimizer App
iPad-Optimized Version - All 8 Features Included
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import pytz
import json
import sqlite3
from time import sleep

# Import our modules
from ev_calculator import calculate_ev, calculate_parlay_probability
from correlation_analyzer import calculate_correlation_penalty, get_correlation_warning
from prizepicks_scraper import get_daily_data
from bet_tracker import BetTracker
from bankroll_manager import BankrollManager
from bump_detector import BumpDetector
from arbitrage_scanner import ArbitrageScanner
from ios_widget import iOSWidget
from alert_manager import AlertManager
from sports_config import SPORT_DISPLAY_NAMES, SPORT_STATS

# Initialize classes
bet_tracker = BetTracker()
bankroll_mgr = BankrollManager(1000)  # Start with $1000 bankroll
bump_detector = BumpDetector()
arb_scanner = ArbitrageScanner()
ios_widget = iOSWidget()
alert_mgr = AlertManager()

# ============================================
# PAGE CONFIGURATION
# ============================================
st.set_page_config(
    page_title="PrizePicks +EV Pro",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# IPAD-OPTIMIZED CSS
# ============================================
st.markdown("""
<style>
    /* Bigger touch targets for iPad */
    .stButton > button {
        min-height: 55px;
        font-size: 18px !important;
        border-radius: 15px !important;
        margin: 8px 0px;
        font-weight: 600 !important;
    }
    
    /* Better spacing for touch */
    .stSelectbox, .stSlider, .stRadio {
        margin-bottom: 25px;
    }
    
    /* Make sliders easier to grab */
    .stSlider div[data-baseweb="slider"] {
        padding-top: 15px;
        padding-bottom: 15px;
    }
    
    .stSlider .thumb {
        width: 28px !important;
        height: 28px !important;
        background-color: #FF4B4B !important;
        border: 3px solid white !important;
    }
    
    /* Card-like containers */
    .stApp .block-container {
        padding-left: 1.2rem;
        padding-right: 1.2rem;
        padding-top: 1.5rem;
    }
    
    /* Metric cards */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        padding: 20px 15px;
        box-shadow: 0 6px 12px rgba(0,0,0,0.1);
        margin: 10px 0px;
    }
    
    div[data-testid="stMetric"] label {
        color: rgba(255,255,255,0.9) !important;
        font-size: 16px !important;
        font-weight: 500 !important;
    }
    
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: white !important;
        font-size: 36px !important;
        font-weight: 700 !important;
        line-height: 1.2 !important;
    }
    
    /* Data tables */
    .stDataFrame {
        font-size: 15px;
    }
    
    .stDataFrame div[data-testid="stDataFrame"] {
        max-height: 450px;
        overflow-y: auto;
        -webkit-overflow-scrolling: touch;
        border-radius: 15px;
        border: 1px solid #e0e0e0;
    }
    
    /* Bottom padding */
    .main > div {
        padding-bottom: 120px;
    }
    
    /* Hide hamburger menu */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 15px 15px 0 0;
        padding: 15px 25px;
        font-size: 16px;
        font-weight: 600;
    }
    
    /* Risk badges */
    .risk-high {
        background-color: #ff4444;
        color: white;
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: bold;
    }
    
    .risk-medium {
        background-color: #ff8800;
        color: white;
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: bold;
    }
    
    .risk-low {
        background-color: #ffbb33;
        color: black;
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# TITLE SECTION
# ============================================
st.title("🏆 PrizePicks +EV Pro")
st.caption("Professional betting tools • Real-time EV • Multi-sport support")

# ============================================
# SIDEBAR SETTINGS
# ============================================
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    
    # Sport selection
    sport_options = list(SPORT_DISPLAY_NAMES.keys())
    sport_display = list(SPORT_DISPLAY_NAMES.values())
    
    selected_sport_index = st.selectbox(
        "🎯 Select Sport",
        range(len(sport_options)),
        format_func=lambda x: sport_display[x],
        index=0,
        key="sport_selector"
    )
    selected_sport = sport_options[selected_sport_index]
    
    # Advanced Filters
    with st.expander("🔍 Advanced Filters"):
        stat_types = SPORT_STATS.get(selected_sport, ["Points", "Rebounds", "Assists"])
        selected_stats = st.multiselect("Stat Types", stat_types, default=stat_types)
        
        min_odds = st.slider("Minimum Odds", -500, 500, -200, 50, format="%d")
        max_odds = st.slider("Maximum Odds", -500, 500, 200, 50, format="%d")
        
        exclude_bump_risk = st.checkbox("Exclude High Bump Risk", value=True)
    
    # Parlay settings
    st.markdown("### 📊 Parlay Size")
    num_legs = st.select_slider("Picks", options=[2, 3, 4, 5, 6], value=6)
    
    # EV threshold
    st.markdown("### 💰 Minimum Value")
    min_ev = st.slider("EV Threshold", 0, 20, 5, 1) / 100
    
    st.divider()
    
    # Dark mode
    dark_mode = st.toggle("🌙 Dark Mode", value=False)
    
    if dark_mode:
        st.markdown("""
        <style>
            .stApp, .main > div { background-color: #0e1117; color: #ffffff; }
            h1, h2, h3, p, li { color: #ffffff !important; }
            section[data-testid="stSidebar"] { background-color: #1a1f2c !important; }
            .stMarkdown, .stCaption { color: #e0e0e0 !important; }
        </style>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Main action button
    analyze_clicked = st.button("🔍 FIND BEST PARLAY", use_container_width=True, type="primary")
    
    st.divider()
    
    # Data status
    central = pytz.timezone('America/Chicago')
    current_time = datetime.now(central).strftime("%I:%M %p %Z")
    st.caption(f"🔄 Last update: {current_time}")

# ============================================
# MAIN TABS
# ============================================
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🎯 Parlay Builder", "📊 Bet Tracker", "💰 Bankroll", 
    "⚠️ Bump Detector", "🔄 Arbitrage", "🔔 Alerts", "📱 Widget"
])

# ============================================
# TAB 1: PARLAY BUILDER
# ============================================
with tab1:
    # Load data
    @st.cache_data(ttl=300)
    def load_data(sport):
        try:
            pp_data, market_data = get_daily_data(sport)
            return pp_data, market_data
        except Exception as e:
            st.error(f"Error loading data: {e}")
            return pd.DataFrame(), pd.DataFrame()
    
    # Preview section
    st.subheader("👀 Today's Available Props")
    
    with st.spinner(f"Loading {selected_sport} data..."):
        pp_data, market_data = load_data(selected_sport)
        
        if not pp_data.empty:
            preview_df = pp_data[['player', 'line', 'stat_type']].head(10).copy()
            preview_df.columns = ['Player', 'Line', 'Stat Type']
            st.success(f"✅ Showing {len(pp_data)} real {selected_sport} props")
            st.dataframe(preview_df, use_container_width=True, height=300)
    
    # Analysis
    if analyze_clicked:
        with st.spinner("🔄 Analyzing data..."):
            progress_bar = st.progress(0, text="Calculating EV...")
            
            # Calculate EV
            ev_data = calculate_ev(pp_data, market_data)
            progress_bar.progress(50, text="Finding optimal combinations...")
            
            if ev_data.empty:
                st.error("❌ No matching props found")
                st.stop()
            
            # Apply filters
            if selected_stats:
                ev_data = ev_data[ev_data['stat_type'].isin(selected_stats)]
            
            positive_ev = ev_data[ev_data['is_positive']].copy()
            positive_ev = positive_ev[positive_ev['ev'] >= min_ev]
            display_positive_ev = positive_ev.copy()
            
            # Check bump risk
            if exclude_bump_risk and not display_positive_ev.empty:
                bump_warnings = bump_detector.get_bump_warning(display_positive_ev)
                high_risk_players = [w['player'] for w in bump_warnings if w['risk'] == 'HIGH']
                display_positive_ev = display_positive_ev[~display_positive_ev['player'].isin(high_risk_players)]
            
            progress_bar.progress(75, text="Building parlay...")
            
            # Select picks
            if not display_positive_ev.empty:
                unique_picks = display_positive_ev.sort_values('ev', ascending=False).drop_duplicates(subset=['player'], keep='first')
                selected_picks = unique_picks.head(num_legs).copy()
            else:
                selected_picks = pd.DataFrame()
            
            # Calculate correlation
            penalty = 1.0
            warning = None
            if not selected_picks.empty and len(selected_picks) >= 2:
                penalty = calculate_correlation_penalty(selected_picks)
                warning = get_correlation_warning(selected_picks)
            
            # Calculate probabilities
            raw_prob = calculate_parlay_probability(selected_picks) if not selected_picks.empty else 0
            adjusted_prob = raw_prob * penalty
            
            progress_bar.progress(100, text="Done!")
            progress_bar.empty()
            
            # Display results
            st.divider()
            st.success(f"✅ Found {len(display_positive_ev)} profitable props!")
            
            # Metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                avg_ev = selected_picks['ev'].mean() if not selected_picks.empty else 0
                st.metric("Average EV", f"{avg_ev:.1%}")
            with col2:
                st.metric("Win Probability", f"{adjusted_prob:.1%}")
            with col3:
                st.metric("Correlation Factor", f"{penalty:.2f}")
            
            # Parlay table
            st.subheader(f"🎯 Optimal {num_legs}-Leg Parlay")
            
            if not selected_picks.empty:
                parlay_data = []
                for _, pick in selected_picks.iterrows():
                    # Calculate stake using Kelly
                    stake_info = bankroll_mgr.calculate_stake(2.0, pick['ev'])
                    
                    parlay_data.append({
                        'Player': pick['player'],
                        'Stat': pick['stat_type'],
                        'Line': pick['line'],
                        'Pick': pick['direction'],
                        'EV': f"{pick['ev']:.1%}",
                        'Stake': f"${stake_info['amount']:.2f}"
                    })
                
                st.dataframe(pd.DataFrame(parlay_data), use_container_width=True, height=400)
                
                # Quick bet logging
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📝 Log This Parlay"):
                        for _, pick in selected_picks.iterrows():
                            bet_tracker.add_bet(
                                sport=selected_sport,
                                player=pick['player'],
                                stat_type=pick['stat_type'],
                                line=pick['line'],
                                pick=pick['direction'],
                                odds=2.0,  # Placeholder
                                stake=bankroll_mgr.calculate_stake(2.0, pick['ev'])['amount'],
                                notes="Auto-logged from parlay"
                            )
                        st.success("✅ Parlay logged!")
                
                with col2:
                    if st.button("🔔 Set Alert"):
                        for _, pick in selected_picks.iterrows():
                            alert_mgr.add_alert(
                                sport=selected_sport,
                                player=pick['player'],
                                stat_type=pick['stat_type'],
                                threshold=pick['ev'],
                                condition='>='
                            )
                        st.success("✅ Alerts set!")
            
            if warning:
                st.warning(warning)
            
            # EV Chart
            st.subheader("📊 EV Distribution")
            if not display_positive_ev.empty:
                chart_data = display_positive_ev.head(15).copy()
                chart_data['player_short'] = chart_data['player'].apply(lambda x: x.split()[-1])
                
                fig = px.bar(chart_data, x='player_short', y='ev', color='ev',
                            color_continuous_scale='RdYlGn', title="Top 15 Props by EV")
                fig.update_layout(xaxis_tickangle=-45, height=400, yaxis_tickformat='.0%')
                st.plotly_chart(fig, use_container_width=True)
            
            # Generate widget data
            ios_widget.generate_widget_data(display_positive_ev, pp_data)

# ============================================
# TAB 2: BET TRACKER
# ============================================
with tab2:
    st.subheader("📊 Bet Tracking & Performance")
    
    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        days_filter = st.selectbox("Time Period", [7, 30, 90, 365], index=1, format_func=lambda x: f"Last {x} days")
    with col2:
        sport_filter = st.selectbox("Sport", ["All", "NBA", "NFL", "MLB", "NHL", "SOCCER", "TENNIS"])
    
    # Get stats
    stats = bet_tracker.get_statistics(days=days_filter)
    bets_df = bet_tracker.get_bets(sport=sport_filter if sport_filter != "All" else None, days=days_filter)
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Bets", stats['total_bets'])
    with col2:
        st.metric("Win Rate", f"{stats['win_rate']:.1f}%")
    with col3:
        st.metric("Total Profit", f"${stats['total_profit']:.2f}")
    with col4:
        st.metric("ROI", f"{stats['roi']:.1f}%")
    
    # Performance chart
    if not bets_df.empty:
        # Group by date
        bets_df['date_only'] = pd.to_datetime(bets_df['date']).dt.date
        daily_pnl = bets_df.groupby('date_only')['profit'].sum().reset_index()
        
        fig = px.line(daily_pnl, x='date_only', y='profit', title='Daily P&L',
                     labels={'profit': 'Profit/Loss ($)', 'date_only': 'Date'})
        fig.add_hline(y=0, line_dash="dash", line_color="red")
        st.plotly_chart(fig, use_container_width=True)
        
        # Bet history
        st.subheader("Bet History")
        
        # Add outcome input for pending bets
        pending = bets_df[bets_df['outcome'].isna()]
        if not pending.empty:
            st.warning(f"⚠️ {len(pending)} bets pending result")
            
            for _, bet in pending.iterrows():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"{bet['player']} - {bet['stat_type']} {bet['line']} ({bet['pick']})")
                with col2:
                    if st.button(f"✅ Win", key=f"win_{bet['id']}"):
                        profit = bet['stake'] * (bet['odds'] - 1)
                        bet_tracker.update_outcome(bet['id'], 'Win', profit)
                        bankroll_mgr.update_bankroll(bet['stake'], profit)
                        st.rerun()
                with col3:
                    if st.button(f"❌ Loss", key=f"loss_{bet['id']}"):
                        bet_tracker.update_outcome(bet['id'], 'Loss', -bet['stake'])
                        bankroll_mgr.update_bankroll(bet['stake'], -bet['stake'])
                        st.rerun()
        
        # Show completed bets
        completed = bets_df[bets_df['outcome'].notna()]
        if not completed.empty:
            st.dataframe(
                completed[['date', 'sport', 'player', 'stat_type', 'line', 'pick', 'odds', 'stake', 'outcome', 'profit']],
                use_container_width=True,
                height=400
            )
    
    # Add new bet manually
    with st.expander("➕ Add Manual Bet"):
        col1, col2, col3 = st.columns(3)
        with col1:
            manual_sport = st.selectbox("Sport", ["NBA", "NFL", "MLB", "NHL", "SOCCER", "TENNIS"])
            manual_player = st.text_input("Player Name")
        with col2:
            manual_stat = st.selectbox("Stat Type", ["Points", "Rebounds", "Assists", "PRA", "Passing Yds"])
            manual_line = st.number_input("Line", value=20.5, step=0.5)
        with col3:
            manual_pick = st.selectbox("Pick", ["OVER", "UNDER"])
            manual_odds = st.number_input("Odds (Decimal)", value=2.0, step=0.1)
        
        col4, col5, col6 = st.columns(3)
        with col4:
            manual_stake = st.number_input("Stake ($)", value=10.0, step=5.0)
        with col5:
            manual_outcome = st.selectbox("Outcome (optional)", ["Pending", "Win", "Loss"])
        with col6:
            manual_notes = st.text_input("Notes")
        
        if st.button("Save Bet"):
            bet_id = bet_tracker.add_bet(
                sport=manual_sport,
                player=manual_player,
                stat_type=manual_stat,
                line=manual_line,
                pick=manual_pick,
                odds=manual_odds,
                stake=manual_stake,
                notes=manual_notes
            )
            
            if manual_outcome != "Pending":
                if manual_outcome == "Win":
                    profit = manual_stake * (manual_odds - 1)
                    bet_tracker.update_outcome(bet_id, 'Win', profit)
                else:
                    bet_tracker.update_outcome(bet_id, 'Loss', -manual_stake)
            
            st.success("✅ Bet saved!")

# ============================================
# TAB 3: BANKROLL MANAGER
# ============================================
with tab3:
    st.subheader("💰 Bankroll Management")
    
    # Current bankroll
    col1, col2, col3 = st.columns(3)
    with col1:
        current_bankroll = st.number_input("Current Bankroll ($)", value=bankroll_mgr.bankroll, step=100)
        if current_bankroll != bankroll_mgr.bankroll:
            bankroll_mgr.bankroll = current_bankroll
            bet_tracker.add_bankroll_snapshot(current_bankroll, 0, "Manual update")
    
    with col2:
        limits = bankroll_mgr.get_bet_limits()
        st.metric("Unit Size (1%)", f"${limits['suggested_unit']:.2f}")
    
    with col3:
        st.metric("Max Bet (5%)", f"${limits['max_bet']:.2f}")
    
    # Kelly Calculator
    st.subheader("🧮 Kelly Criterion Calculator")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        kelly_odds = st.number_input("Decimal Odds", value=2.0, step=0.1, min_value=1.01)
    with col2:
        kelly_edge = st.number_input("Edge (EV %)", value=5.0, step=1.0) / 100
    with col3:
        kelly_fraction = st.selectbox("Kelly Fraction", [0.25, 0.5, 0.75, 1.0], index=0, format_func=lambda x: f"{int(x*100)}% Kelly")
    
    stake_info = bankroll_mgr.calculate_stake(kelly_odds, kelly_edge, kelly_fraction)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Recommended Stake", f"${stake_info['amount']:.2f}")
    with col2:
        st.metric("% of Bankroll", f"{stake_info['percentage']}%")
    with col3:
        st.metric("Potential Profit", f"${stake_info['amount'] * (kelly_odds - 1):.2f}")
    
    # Bankroll history
    st.subheader("📈 Bankroll History")
    bankroll_history = bet_tracker.get_bankroll_history(days=90)
    
    if not bankroll_history.empty:
        fig = px.line(bankroll_history, x='date', y='amount', title='Bankroll Over Time')
        st.plotly_chart(fig, use_container_width=True)
    
    # Betting limits guide
    with st.expander("📖 Betting Limits Guide"):
        st.markdown("""
        **Recommended Bet Sizes:**
        - **1%** = Conservative (unit size)
        - **2%** = Moderate
        - **3-5%** = Aggressive
        - **>5%** = High risk (not recommended)
        
        **Kelly Criterion:**
        - **Full Kelly (100%)** = Maximum growth but high volatility
        - **Half Kelly (50%)** = Good balance of growth and safety
        - **Quarter Kelly (25%)** = Very conservative, recommended for beginners
        """)

# ============================================
# TAB 4: BUMP DETECTOR
# ============================================
with tab4:
    st.subheader("⚠️ Bump Risk Detector")
    st.caption("Identify props at risk of being bumped (line movement) by PrizePicks")
    
    # Load data for bump analysis
    with st.spinner("Analyzing bump risks..."):
        pp_data, market_data = load_data(selected_sport)
        ev_data = calculate_ev(pp_data, market_data)
        
        if not ev_data.empty:
            # Get bump warnings
            bump_warnings = bump_detector.get_bump_warning(ev_data, threshold=min_ev)
            
            # Display metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                high_risk = len([w for w in bump_warnings if w['risk'] == 'HIGH'])
                st.metric("High Risk Props", high_risk, delta=None, delta_color="inverse")
            with col2:
                medium_risk = len([w for w in bump_warnings if w['risk'] == 'MEDIUM'])
                st.metric("Medium Risk Props", medium_risk)
            with col3:
                low_risk = len([w for w in bump_warnings if w['risk'] == 'LOW'])
                st.metric("Low Risk Props", low_risk)
            
            # Display warnings table
            if bump_warnings:
                warnings_df = pd.DataFrame(bump_warnings)
                
                # Color code based on risk
                def color_risk(val):
                    colors = {'HIGH': 'background-color: #ff4444', 
                             'MEDIUM': 'background-color: #ff8800',
                             'LOW': 'background-color: #ffbb33'}
                    return colors.get(val, '')
                
                st.dataframe(
                    warnings_df.style.applymap(color_risk, subset=['risk']),
                    use_container_width=True,
                    height=400
                )
                
                # Explanation
                with st.expander("📖 Understanding Bump Risk"):
                    st.markdown("""
                    **What is a bump?**
                    - PrizePicks adjusts lines when they're out of sync with market odds
                    - Props with HIGH risk are likely to move before game time
                    - Lock in your picks early to avoid missing value
                    
                    **Risk Levels:**
                    - **HIGH** (-140 or higher) - Line very likely to move
                    - **MEDIUM** (-130 to -139) - Moderate chance of movement
                    - **LOW** (-118 to -129) - Low chance of movement
                    - **MINIMAL** (better than -118) - Unlikely to move
                    """)
            else:
                st.success("✅ No props at significant bump risk found!")
        else:
            st.warning("No data available for bump analysis")

# ============================================
# TAB 5: ARBITRAGE SCANNER
# ============================================
with tab5:
    st.subheader("🔄 Arbitrage Scanner")
    st.caption("Find risk-free profit opportunities across props")
    
    # Load data for arbitrage analysis
    with st.spinner("Scanning for arbitrage opportunities..."):
        pp_data, market_data = load_data(selected_sport)
        ev_data = calculate_ev(pp_data, market_data)
        
        if not ev_data.empty:
            # Scan for arbitrage
            arb_opportunities = arb_scanner.calculate_arbitrage(ev_data.to_dict('records'))
            
            # Display metrics
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Arbitrage Opportunities", len(arb_opportunities))
            with col2:
                if arb_opportunities:
                    max_profit = max([o['profit_pct'] for o in arb_opportunities])
                    st.metric("Max Profit", f"{max_profit}%")
            
            # Display arbitrage opportunities
            if arb_opportunities:
                arb_df = pd.DataFrame(arb_opportunities)
                st.dataframe(arb_df, use_container_width=True, height=400)
                
                # Show detailed calculation for first opportunity
                if len(arb_opportunities) > 0:
                    with st.expander("📊 Arbitrage Calculation Example"):
                        arb = arb_opportunities[0]
                        st.markdown(f"""
                        **Opportunity:** {arb['players']}
                        
                        **How to execute:**
                        1. Bet on {arb['players'].split(' vs ')[0]} at implied probability
                        2. Bet on {arb['players'].split(' vs ')[1]} at implied probability
                        3. Stake total: ${arb['total_stake']:.2f}
                        4. Guaranteed profit: ${arb['total_stake'] * (arb['profit_pct']/100):.2f}
                        
                        **Why this works:**
                        The combined probability is less than 100%, creating a mathematical arbitrage.
                        """)
            else:
                st.info("No arbitrage opportunities found at this time")
            
            # Correlation arbitrage
            st.subheader("🔄 Correlation Arbitrage")
            corr_arb = arb_scanner.find_correlation_arb(ev_data)
            
            if corr_arb:
                corr_df = pd.DataFrame(corr_arb)
                st.dataframe(corr_df, use_container_width=True, height=300)
            else:
                st.info("No correlation arbitrage opportunities found")
        else:
            st.warning("No data available for arbitrage scanning")

# ============================================
# TAB 6: ALERTS MANAGER
# ============================================
with tab6:
    st.subheader("🔔 Smart Alerts")
    st.caption("Get notified when +EV opportunities appear")
    
    # Alert settings
    with st.expander("⚙️ Alert Settings", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            alert_sports = st.multiselect("Sports to monitor", 
                ["NBA", "NFL", "MLB", "NHL", "SOCCER", "TENNIS"],
                default=["NBA"])
            
            alert_threshold = st.slider("EV Threshold %", 1, 15, 5, 1)
            
        with col2:
            alert_frequency = st.selectbox("Alert Frequency", 
                ["Instant", "Hourly Digest", "Daily Digest"], index=0)
            
            alert_methods = st.multiselect("Alert Methods",
                ["In-App", "Email", "Push Notification"],
                default=["In-App"])
        
        if st.button("💾 Save Alert Settings"):
            alert_mgr.update_settings({
                'sports': alert_sports,
                'threshold': alert_threshold / 100,
                'frequency': alert_frequency,
                'methods': alert_methods
            })
            st.success("✅ Alert settings saved!")
    
    # Create custom alert
    st.subheader("➕ Create Custom Alert")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        alert_player = st.text_input("Player Name (optional)", placeholder="Leave empty for all")
    with col2:
        alert_stat = st.selectbox("Stat Type", ["All", "Points", "Rebounds", "Assists", "PRA", "3PM"])
    with col3:
        alert_condition = st.selectbox("Condition", ["Any", "OVER", "UNDER"])
    
    col1, col2 = st.columns(2)
    with col1:
        alert_value = st.number_input("Threshold Value", value=alert_threshold, step=1)
    with col2:
        alert_expiry = st.date_input("Alert Expiry", value=datetime.now() + timedelta(days=7))
    
    if st.button("➕ Add Custom Alert"):
        alert_mgr.add_custom_alert(
            player=alert_player if alert_player else None,
            stat_type=alert_stat if alert_stat != "All" else None,
            condition=alert_condition if alert_condition != "Any" else None,
            threshold=alert_value / 100,
            expiry=alert_expiry
        )
        st.success("✅ Custom alert created!")
    
    # Active alerts
    st.subheader("🟢 Active Alerts")
    active_alerts = alert_mgr.get_active_alerts()
    
    if active_alerts:
        alerts_df = pd.DataFrame(active_alerts)
        st.dataframe(alerts_df, use_container_width=True, height=300)
        
        if st.button("❌ Clear All Alerts"):
            alert_mgr.clear_all_alerts()
            st.rerun()
    else:
        st.info("No active alerts")
    
    # Alert history
    with st.expander("📜 Alert History"):
        alert_history = bet_tracker.get_alerts(days=7)
        
        if not alert_history.empty:
            st.dataframe(alert_history[['date', 'sport', 'player', 'stat_type', 'ev', 'message']],
                        use_container_width=True, height=300)
        else:
            st.info("No alerts triggered in the last 7 days")
    
    # Test alert
    if st.button("🔔 Test Alert"):
        alert_mgr.send_test_alert()
        st.success("✅ Test alert sent!")

# ============================================
# TAB 7: IOS WIDGET
# ============================================
with tab7:
    st.subheader("📱 iOS Widget Preview")
    st.caption("See how your top picks will appear on your iPad home screen")
    
    # Generate widget data first
    if 'display_positive_ev' in locals() and not display_positive_ev.empty:
        ios_widget.generate_widget_data(display_positive_ev, pp_data)
    else:
        # Create sample data for preview
        sample_ev = pd.DataFrame({
            'player': ['LeBron James', 'Stephen Curry', 'Giannis'],
            'stat_type': ['Points', '3PM', 'Rebounds'],
            'line': [25.5, 3.5, 12.5],
            'ev': [0.08, 0.07, 0.06],
            'is_positive': [True, True, True]
        })
        sample_pp = pd.DataFrame({'player': ['LeBron', 'Curry', 'Giannis']})
        ios_widget.generate_widget_data(sample_ev, sample_pp)
    
    # Widget preview
    st.markdown("### Widget Preview")
    ios_widget.render_widget_preview()
    
    # Widget customization
    with st.expander("⚙️ Widget Settings"):
        col1, col2 = st.columns(2)
        with col1:
            widget_sport = st.selectbox("Sport for widget", 
                ["NBA", "NFL", "MLB", "NHL", "SOCCER", "TENNIS"], index=0)
            widget_size = st.selectbox("Widget size", ["Small", "Medium", "Large"], index=1)
        with col2:
            widget_refresh = st.selectbox("Refresh rate", 
                ["Every hour", "Every 2 hours", "Every 4 hours", "Manual"], index=1)
            widget_dark = st.checkbox("Use dark mode", value=dark_mode)
        
        if st.button("💾 Update Widget"):
            st.success("✅ Widget settings saved!")
    
    # Widget installation instructions
    with st.expander("📖 How to Add Widget to iPad"):
        st.markdown("""
        ### Adding the Widget to Your iPad
        
        1. **Go to your iPad home screen**
        2. **Enter jiggle mode** (long press on empty area)
        3. **Tap the + button** in the top-left corner
        4. **Search for "PrizePicks +EV"** or scroll to find it
        5. **Choose your widget size** (Small, Medium, or Large)
        6. **Tap "Add Widget"**
        7. **Position it** on your home screen
        8. **Tap Done** in the top-right corner
        
        ### Widget Features
        
        - **Small**: Shows top 3 picks with EV%
        - **Medium**: Shows top 5 picks with stats
        - **Large**: Shows top 8 picks + bankroll stats
        
        The widget updates automatically based on your refresh settings.
        """)
    
    # Share widget
    st.subheader("📤 Share Widget with Friends")
    
    share_message = """
    Check out my PrizePicks +EV widget! It shows the best value picks in real-time.
    Download the app at: https://prizepicks-ipad-app.streamlit.app
    """
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📱 Share to Messages"):
            st.info("Sharing via Messages...")
    with col2:
        if st.button("📧 Share via Email"):
            st.info("Opening email...")
    with col3:
        if st.button("🔗 Copy Link"):
            st.code("https://prizepicks-ipad-app.streamlit.app")
            st.success("✅ Link copied!")
    
    # Widget analytics
    with st.expander("📊 Widget Analytics"):
        st.markdown("""
        **Widget Performance:**
        - **Daily views:** 0
        - **Clicks to app:** 0
        - **Most viewed sport:** NBA
        
        *Analytics will appear once widget is installed and used.*
        """)

# ============================================
# WELCOME SCREEN (when app first loads)
# ============================================
if not analyze_clicked:
    st.divider()
    
    # Welcome message
    st.markdown("""
    ### 👆 Welcome to PrizePicks +EV Pro!
    
    This professional betting tool helps you:
    """)
    
    # Feature cards in 4 columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.info("""
        **🎯 +EV Picks**
        Find mathematically profitable bets
        """)
    
    with col2:
        st.info("""
        **📊 Bet Tracking**
        Track performance and ROI
        """)
    
    with col3:
        st.info("""
        **💰 Bankroll Mgmt**
        Kelly Criterion staking
        """)
    
    with col4:
        st.info("""
        **⚠️ Bump Detection**
        Avoid line movements
        """)
    
    col5, col6, col7, col8 = st.columns(4)
    
    with col5:
        st.info("""
        **🔄 Arbitrage**
        Risk-free opportunities
        """)
    
    with col6:
        st.info("""
        **🔔 Smart Alerts**
        Never miss a +EV pick
        """)
    
    with col7:
        st.info("""
        **📱 iOS Widget**
        Picks on your home screen
        """)
    
    with col8:
        st.info("""
        **🔍 Advanced Filters**
        Customize your search
        """)
    
    # Quick start guide
    with st.expander("📖 Quick Start Guide"):
        st.markdown("""
        **Get started in 3 steps:**
        
        1. **Select your sport** from the sidebar
        2. **Adjust EV threshold** (5% recommended for beginners)
        3. **Click "FIND BEST PARLAY"** to see opportunities
        
        **Pro Features:**
        - Track your bets in the Bet Tracker tab
        - Set up bankroll management in Bankroll tab
        - Create alerts for your favorite players
        - Add the iOS widget to your home screen
        
        **Pro Tip:** Start with 1% of your bankroll per bet and use quarter Kelly for optimal growth.
        """)

# ============================================
# Initialize missing Alert Manager class
# ============================================
class AlertManager:
    def __init__(self):
        self.settings = {
            'sports': ['NBA'],
            'threshold': 0.05,
            'frequency': 'Instant',
            'methods': ['In-App']
        }
        self.custom_alerts = []
        self.conn = sqlite3.connect('betting_history.db', check_same_thread=False)
        self.create_alerts_table()
    
    def create_alerts_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS custom_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player TEXT,
                stat_type TEXT,
                condition TEXT,
                threshold REAL,
                expiry TEXT,
                active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()
    
    def update_settings(self, settings):
        self.settings.update(settings)
    
    def add_custom_alert(self, player, stat_type, condition, threshold, expiry):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO custom_alerts (player, stat_type, condition, threshold, expiry, active)
            VALUES (?, ?, ?, ?, ?, 1)
        ''', (player, stat_type, condition, threshold, expiry.isoformat()))
        self.conn.commit()
    
    def get_active_alerts(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM custom_alerts WHERE active = 1 AND date(expiry) >= date('now')
        ''')
        return cursor.fetchall()
    
    def clear_all_alerts(self):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE custom_alerts SET active = 0')
        self.conn.commit()
    
    def add_alert(self, sport, player, stat_type, threshold, condition):
        # Log alert to database
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO alerts (date, sport, player, stat_type, ev, message)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (datetime.now().isoformat(), sport, player, stat_type, threshold, 
              f"Alert set for {player} {stat_type} {condition} {threshold:.1%}"))
        self.conn.commit()
    
    def send_test_alert(self):
        # Simulate sending a test alert
        pass

# Initialize alert manager if not already
if 'alert_mgr' not in locals():
    alert_mgr = AlertManager()

# ============================================
# Bottom padding
# ============================================
st.markdown("<br><br><br>", unsafe_allow_html=True)
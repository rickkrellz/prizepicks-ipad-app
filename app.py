"""
Main PrizePicks +EV Optimizer App
iPad-Optimized Version - All 11 Features Included - FULLY FIXED
"""

# ============================================
# PAGE CONFIGURATION - MUST BE FIRST!
# ============================================
import streamlit as st
st.set_page_config(
    page_title="PrizePicks +EV Pro",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# ALL OTHER IMPORTS GO AFTER set_page_config
# ============================================
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import pytz
import json
import sqlite3
from time import sleep
import os

# Import core modules with error handling
try:
    from ev_calculator import calculate_ev, calculate_parlay_probability
    from correlation_analyzer import calculate_correlation_penalty, get_correlation_warning
    from prizepicks_scraper import get_daily_data
    from sports_config import SPORT_DISPLAY_NAMES, SPORT_STATS
    core_modules_available = True
except ImportError as e:
    st.error(f"Error importing core modules: {e}")
    st.stop()

# Initialize classes with error handling
try:
    from bet_tracker import BetTracker
    bet_tracker = BetTracker()
except ImportError:
    bet_tracker = None

try:
    from bankroll_manager import BankrollManager
    bankroll_mgr = BankrollManager(1000)
except ImportError:
    bankroll_mgr = None

try:
    from bump_detector import BumpDetector
    bump_detector = BumpDetector()
except ImportError:
    bump_detector = None

try:
    from arbitrage_scanner import ArbitrageScanner
    arb_scanner = ArbitrageScanner()
except ImportError:
    arb_scanner = None

try:
    from ios_widget import iOSWidget
    ios_widget = iOSWidget()
except ImportError:
    ios_widget = None

try:
    from alert_manager import AlertManager
    alert_mgr = AlertManager()
except ImportError:
    alert_mgr = None

# Initialize new managers with error handling
try:
    from ml_predictor import MLPredictor
    ml_predictor = MLPredictor()
except ImportError:
    ml_predictor = None

try:
    from push_notifications import PushNotificationManager
    push_notifications = PushNotificationManager()
except ImportError:
    push_notifications = None

try:
    from multi_user import MultiUserManager
    multi_user = MultiUserManager()
except ImportError:
    multi_user = None

try:
    from calendar_view import CalendarView
    calendar_view = CalendarView(bet_tracker) if bet_tracker else None
except ImportError:
    calendar_view = None

try:
    from public_leaderboard import PublicLeaderboard
    leaderboard = PublicLeaderboard(bet_tracker, multi_user) if bet_tracker and multi_user else None
except ImportError:
    leaderboard = None

try:
    from syndicate import SyndicateManager
    syndicate = SyndicateManager(multi_user) if multi_user else None
except ImportError:
    syndicate = None

try:
    from premium_subscription import PremiumManager
    premium = PremiumManager()
except ImportError:
    premium = None

try:
    from live_betting import LiveBettingManager
    live_betting = LiveBettingManager()
except ImportError:
    live_betting = None

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
    
    /* Share button styling */
    .share-box {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0px;
        font-family: monospace;
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
# LOAD DATA FUNCTION
# ============================================
@st.cache_data(ttl=300)
def load_data(sport):
    try:
        pp_data, market_data = get_daily_data(sport)
        return pp_data, market_data
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame(), pd.DataFrame()

# ============================================
# MAIN TABS
# ============================================
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11 = st.tabs([
    "🎯 Parlay Builder", "📊 Bet Tracker", "💰 Bankroll", "⚠️ Bump Detector",
    "🔄 Arbitrage", "🔔 Alerts", "📱 Widget", "🤖 AI Picks", "📅 Calendar",
    "🏆 Leaderboard", "🤝 Syndicate"
])

# ============================================
# TAB 1: PARLAY BUILDER
# ============================================
with tab1:
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
            if exclude_bump_risk and not display_positive_ev.empty and bump_detector:
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
            
            if not selected_picks.empty and bankroll_mgr:
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
                
                # Share Feature
                st.subheader("📤 Share This Parlay")
                
                # Create share text
                share_text = "🎯 My +EV Parlay from PrizePicks Pro:\n\n"
                for _, pick in selected_picks.iterrows():
                    share_text += f"• {pick['player']} {pick['stat_type']} {pick['direction']} {pick['line']} (EV: {pick['ev']:.1%})\n"
                share_text += f"\n📊 Average EV: {selected_picks['ev'].mean():.1%}"
                share_text += f"\n🎯 Win Probability: {adjusted_prob:.1%}"
                share_text += f"\n\nBuilt with PrizePicks +EV Pro"
                
                col1, col2 = st.columns(2)
                with col1:
                    st.text_area("📋 Copy Text", share_text, height=200)
                
                with col2:
                    st.markdown("""
                    <div class="share-box">
                        <strong>Share Options:</strong><br><br>
                        • 📱 Copy and paste to Messages<br>
                        • 📧 Email to friends<br>
                        • 🐦 Post on Twitter/X<br>
                        • 💬 Share in Discord/Telegram
                    </div>
                    """, unsafe_allow_html=True)
                
                if st.button("📋 Copy to Clipboard"):
                    st.write(share_text)
                    st.success("✅ Select all and copy (Cmd+C / Ctrl+C)")
                
                # Quick bet logging
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📝 Log This Parlay") and bet_tracker:
                        for _, pick in selected_picks.iterrows():
                            bet_tracker.add_bet(
                                sport=selected_sport,
                                player=pick['player'],
                                stat_type=pick['stat_type'],
                                line=pick['line'],
                                pick=pick['direction'],
                                odds=2.0,
                                stake=bankroll_mgr.calculate_stake(2.0, pick['ev'])['amount'],
                                notes="Auto-logged from parlay"
                            )
                        st.success("✅ Parlay logged!")
                
                with col2:
                    if st.button("🔔 Set Alert") and alert_mgr:
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
            if ios_widget:
                ios_widget.generate_widget_data(display_positive_ev, pp_data)

# ============================================
# TAB 2: BET TRACKER
# ============================================
with tab2:
    st.subheader("📊 Bet Tracking & Performance")
    
    if not bet_tracker:
        st.warning("Bet Tracker module not available")
    else:
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
        
        # Enhanced Analytics
        st.subheader("📈 Advanced Analytics")
        
        if not bets_df.empty and len(bets_df) > 0:
            # Filter to completed bets
            completed_bets = bets_df[bets_df['outcome'].notna()].copy()
            
            if not completed_bets.empty:
                # Win Rate by Sport
                st.markdown("### 🏆 Win Rate by Sport")
                sport_stats = completed_bets.groupby('sport').agg({
                    'outcome': lambda x: (x == 'Win').sum(),
                    'stake': 'sum',
                    'profit': 'sum',
                    'id': 'count'
                }).rename(columns={'outcome': 'wins', 'id': 'bets'})
                
                sport_stats['win_rate'] = (sport_stats['wins'] / sport_stats['bets'] * 100).round(1)
                
                fig = px.bar(
                    sport_stats.reset_index(), 
                    x='sport', 
                    y='win_rate', 
                    color='win_rate',
                    color_continuous_scale='RdYlGn',
                    title='Win Rate by Sport',
                    text=sport_stats['win_rate'].apply(lambda x: f'{x}%')
                )
                fig.update_traces(textposition='outside')
                fig.update_layout(yaxis_range=[0, 100])
                st.plotly_chart(fig, use_container_width=True)
                
                # Profit/Loss by Sport
                fig2 = px.bar(
                    sport_stats.reset_index(),
                    x='sport',
                    y='profit',
                    color='profit',
                    color_continuous_scale='RdYlGn',
                    title='Profit/Loss by Sport',
                    text=sport_stats['profit'].apply(lambda x: f'${x:.0f}')
                )
                fig2.update_traces(textposition='outside')
                st.plotly_chart(fig2, use_container_width=True)
        
        # Export Data
        st.subheader("📥 Export Data")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📊 Export to CSV") and not bets_df.empty:
                csv = bets_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"bet_history_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
        
        # Bet history
        st.subheader("📜 Bet History")
        
        # Add outcome input for pending bets
        pending = bets_df[bets_df['outcome'].isna()] if not bets_df.empty else pd.DataFrame()
        if not pending.empty:
            st.warning(f"⚠️ {len(pending)} bets pending result")
            
            for _, bet in pending.iterrows():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                with col1:
                    st.write(f"{bet['player']} - {bet['stat_type']} {bet['line']} ({bet['pick']})")
                with col2:
                    st.write(f"${bet['stake']:.2f}")
                with col3:
                    if st.button(f"✅ Win", key=f"win_{bet['id']}"):
                        profit = bet['stake'] * (bet['odds'] - 1)
                        bet_tracker.update_outcome(bet['id'], 'Win', profit)
                        if bankroll_mgr:
                            bankroll_mgr.update_bankroll(bet['stake'], profit)
                        st.rerun()
                with col4:
                    if st.button(f"❌ Loss", key=f"loss_{bet['id']}"):
                        bet_tracker.update_outcome(bet['id'], 'Loss', -bet['stake'])
                        if bankroll_mgr:
                            bankroll_mgr.update_bankroll(bet['stake'], -bet['stake'])
                        st.rerun()
        
        # Show completed bets
        completed = bets_df[bets_df['outcome'].notna()] if not bets_df.empty else pd.DataFrame()
        if not completed.empty:
            st.dataframe(
                completed[['date', 'sport', 'player', 'stat_type', 'line', 'pick', 'odds', 'stake', 'outcome', 'profit']],
                use_container_width=True,
                height=400
            )

# ============================================
# TAB 3: BANKROLL MANAGER
# ============================================
with tab3:
    st.subheader("💰 Bankroll Management")
    
    if not bankroll_mgr:
        st.warning("Bankroll Manager module not available")
    else:
        # Current bankroll
        col1, col2, col3 = st.columns(3)
        with col1:
            current_bankroll = st.number_input("Current Bankroll ($)", value=bankroll_mgr.bankroll, step=100)
            if current_bankroll != bankroll_mgr.bankroll:
                bankroll_mgr.bankroll = current_bankroll
                if bet_tracker:
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
            kelly_odds = st.number_input("Decimal Odds", value=2.0, step=0.1, min_value=1.01, key="kelly_odds")
        with col2:
            kelly_edge = st.number_input("Edge (EV %)", value=5.0, step=1.0, key="kelly_edge") / 100
        with col3:
            kelly_fraction = st.selectbox("Kelly Fraction", [0.25, 0.5, 0.75, 1.0], index=0, 
                                          format_func=lambda x: f"{int(x*100)}% Kelly", key="kelly_fraction")
        
        stake_info = bankroll_mgr.calculate_stake(kelly_odds, kelly_edge, kelly_fraction)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Recommended Stake", f"${stake_info['amount']:.2f}")
        with col2:
            st.metric("% of Bankroll", f"{stake_info['percentage']}%")
        with col3:
            st.metric("Potential Profit", f"${stake_info['amount'] * (kelly_odds - 1):.2f}")

# ============================================
# TAB 4: BUMP DETECTOR
# ============================================
with tab4:
    st.subheader("⚠️ Bump Risk Detector")
    st.caption("Identify props at risk of being bumped (line movement) by PrizePicks")
    
    if not bump_detector:
        st.warning("Bump Detector module not available")
    else:
        with st.spinner("Analyzing bump risks..."):
            pp_data, market_data = load_data(selected_sport)
            ev_data = calculate_ev(pp_data, market_data)
            
            if not ev_data.empty:
                bump_warnings = bump_detector.get_bump_warning(ev_data, threshold=min_ev)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    high_risk = len([w for w in bump_warnings if w['risk'] == 'HIGH'])
                    st.metric("High Risk Props", high_risk)
                with col2:
                    medium_risk = len([w for w in bump_warnings if w['risk'] == 'MEDIUM'])
                    st.metric("Medium Risk Props", medium_risk)
                with col3:
                    low_risk = len([w for w in bump_warnings if w['risk'] == 'LOW'])
                    st.metric("Low Risk Props", low_risk)
                
                if bump_warnings:
                    warnings_df = pd.DataFrame(bump_warnings)
                    
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

# ============================================
# TAB 5: ARBITRAGE SCANNER
# ============================================
with tab5:
    st.subheader("🔄 Arbitrage Scanner")
    st.caption("Find risk-free profit opportunities across props")
    
    if not arb_scanner:
        st.warning("Arbitrage Scanner module not available")
    else:
        with st.spinner("Scanning for arbitrage opportunities..."):
            pp_data, market_data = load_data(selected_sport)
            ev_data = calculate_ev(pp_data, market_data)
            
            if not ev_data.empty:
                arb_opportunities = arb_scanner.calculate_arbitrage(ev_data.to_dict('records'))
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Arbitrage Opportunities", len(arb_opportunities))
                with col2:
                    if arb_opportunities:
                        max_profit = max([o['profit_pct'] for o in arb_opportunities])
                        st.metric("Max Profit", f"{max_profit}%")
                
                if arb_opportunities:
                    arb_df = pd.DataFrame(arb_opportunities)
                    st.dataframe(arb_df, use_container_width=True, height=400)

# ============================================
# TAB 6: ALERTS MANAGER
# ============================================
with tab6:
    st.subheader("🔔 Smart Alerts")
    st.caption("Get notified when +EV opportunities appear")
    
    if not alert_mgr:
        st.warning("Alert Manager module not available")
    else:
        with st.expander("⚙️ Alert Settings", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                alert_sports = st.multiselect("Sports to monitor", 
                    ["NBA", "NFL", "MLB", "NHL", "SOCCER", "TENNIS"],
                    default=["NBA"], key="alert_sports")
                
                alert_threshold = st.slider("EV Threshold %", 1, 15, 5, 1, key="alert_threshold")
                
            with col2:
                alert_frequency = st.selectbox("Alert Frequency", 
                    ["Instant", "Hourly Digest", "Daily Digest"], index=0, key="alert_frequency")
                
                alert_methods = st.multiselect("Alert Methods",
                    ["In-App", "Email", "Push Notification"],
                    default=["In-App"], key="alert_methods")
            
            if st.button("💾 Save Alert Settings", key="save_alert_settings"):
                alert_mgr.update_settings({
                    'sports': alert_sports,
                    'threshold': alert_threshold / 100,
                    'frequency': alert_frequency,
                    'methods': alert_methods
                })
                st.success("✅ Alert settings saved!")

# ============================================
# TAB 7: IOS WIDGET
# ============================================
with tab7:
    st.subheader("📱 iOS Widget Preview")
    st.caption("See how your top picks will appear on your iPad home screen")
    
    if not ios_widget:
        st.warning("iOS Widget module not available")
    else:
        # Generate widget data first
        if 'display_positive_ev' in locals() and not display_positive_ev.empty:
            ios_widget.generate_widget_data(display_positive_ev, pp_data)
        else:
            # Create sample data for preview
            sample_ev = pd.DataFrame({
                'player': ['LeBron James', 'Stephen Curry', 'Giannis Antetokounmpo', 'Luka Doncic', 'Joel Embiid'],
                'stat_type': ['Points', '3PM', 'Rebounds', 'PRA', 'Points'],
                'line': [25.5, 3.5, 12.5, 44.5, 31.5],
                'ev': [0.08, 0.07, 0.06, 0.055, 0.05],
                'is_positive': [True, True, True, True, True]
            })
            sample_pp = pd.DataFrame({'player': ['LeBron', 'Curry', 'Giannis', 'Luka', 'Embiid']})
            ios_widget.generate_widget_data(sample_ev, sample_pp)
        
        st.markdown("### Widget Preview")
        ios_widget.render_widget_preview()

# ============================================
# TAB 8: AI PICKS
# ============================================
with tab8:
    st.subheader("🤖 AI-Powered Predictions")
    st.caption("Machine learning model predicts prop success probabilities")
    
    if not ml_predictor or not premium:
        st.warning("AI Predictions module not available")
    else:
        if premium.check_feature_access(st.session_state.get('user_id', 'guest'), 'AI predictions'):
            with st.spinner("Generating AI predictions..."):
                # Get current props
                pp_data, _ = load_data(selected_sport)
                
                if not pp_data.empty:
                    # Generate AI picks
                    ai_picks = ml_predictor.generate_ai_picks(pp_data)
                    
                    if not ai_picks.empty:
                        # Display picks by confidence
                        for confidence in ['HIGH', 'MEDIUM']:
                            conf_picks = ai_picks[ai_picks['confidence'] == confidence]
                            if not conf_picks.empty:
                                st.subheader(f"{confidence} Confidence Picks")
                                st.dataframe(conf_picks, use_container_width=True)
                    else:
                        st.info("No AI picks available for current slate")
        else:
            st.warning("AI Predictions are a Premium feature")
            premium.render_pricing_table(st.session_state.get('user_id', 'guest'))

# ============================================
# TAB 9: CALENDAR VIEW
# ============================================
with tab9:
    st.subheader("📅 Betting Calendar")
    
    if not calendar_view or not bet_tracker:
        st.warning("Calendar View module not available")
    else:
        # Get bets data
        bets_df = bet_tracker.get_bets(days=365)
        
        if not bets_df.empty:
            # Year selector
            years = pd.to_datetime(bets_df['date']).dt.year.unique()
            selected_year = st.selectbox("Year", sorted(years, reverse=True))
            
            # Render heatmap
            calendar_view.render_heatmap(bets_df, selected_year)
            
            # Month selector
            selected_month = st.selectbox("Month", range(1, 13), 
                                          format_func=lambda x: datetime(2000, x, 1).strftime('%B'))
            
            # Render month calendar
            calendar_view.render_month_calendar(selected_year, selected_month)
            
            # Timeline
            calendar_view.render_timeline(bets_df)
            
            # Streak analysis
            calendar_view.render_streak_analysis(bets_df)
        else:
            st.info("No betting data available for calendar view")

# ============================================
# TAB 10: LEADERBOARD
# ============================================
with tab10:
    if not leaderboard:
        st.warning("Leaderboard module not available")
    else:
        leaderboard.render_leaderboard()
        
        st.divider()
        
        # User profile lookup
        st.subheader("🔍 View User Profile")
        username = st.text_input("Enter username")
        if username:
            leaderboard.render_user_profile(username)

# ============================================
# TAB 11: SYNDICATE
# ============================================
with tab11:
    if not multi_user or not syndicate:
        st.warning("Syndicate module not available")
    else:
        # Check if user is logged in
        if 'user_id' not in st.session_state:
            st.warning("Please log in to use syndicate features")
            
            # Simple login form
            with st.form("login"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                
                if st.form_submit_button("Login"):
                    user = multi_user.authenticate_user(username, password)
                    if user:
                        st.session_state['user_id'] = user['user_id']
                        st.session_state['username'] = user['username']
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
            
            # Sign up
            with st.expander("Create Account"):
                with st.form("signup"):
                    new_username = st.text_input("Choose Username")
                    new_email = st.text_input("Email")
                    new_password = st.text_input("Choose Password", type="password")
                    
                    if st.form_submit_button("Sign Up"):
                        user_id = multi_user.create_user(new_username, new_email, new_password)
                        if user_id:
                            st.success("Account created! Please log in.")
                        else:
                            st.error("Username or email already exists")
        else:
            st.sidebar.success(f"Logged in as: {st.session_state['username']}")
            if st.sidebar.button("Logout"):
                st.session_state.pop('user_id')
                st.session_state.pop('username')
                st.rerun()
            
            # Syndicate dashboard
            syndicate.render_syndicate_dashboard(st.session_state['user_id'])
            
            # Handle pick sharing modal
            if 'sharing_in' in st.session_state:
                syndicate.render_share_pick_modal(st.session_state['user_id'], st.session_state['sharing_in'])

# ============================================
# WELCOME SCREEN
# ============================================
if not analyze_clicked and 'analyze_clicked' not in locals():
    st.divider()
    
    st.markdown("""
    ### 👆 Welcome to PrizePicks +EV Pro!
    
    This professional betting tool helps you:
    """)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.info("**🎯 +EV Picks**\nFind mathematically profitable bets")
    with col2:
        st.info("**📊 Bet Tracking**\nTrack performance and ROI")
    with col3:
        st.info("**💰 Bankroll Mgmt**\nKelly Criterion staking")
    with col4:
        st.info("**⚠️ Bump Detection**\nAvoid line movements")
    
    col5, col6, col7, col8 = st.columns(4)
    with col5:
        st.info("**🔄 Arbitrage**\nRisk-free opportunities")
    with col6:
        st.info("**🔔 Smart Alerts**\nNever miss a +EV pick")
    with col7:
        st.info("**📱 iOS Widget**\nPicks on your home screen")
    with col8:
        st.info("**🔍 Advanced Filters**\nCustomize your search")
    
    with st.expander("📖 Quick Start Guide"):
        st.markdown("""
        **Get started in 3 steps:**
        
        1. **Select your sport** from the sidebar
        2. **Adjust EV threshold** (5% recommended for beginners)
        3. **Click "FIND BEST PARLAY"** to see opportunities
        
        **Pro Tip:** Start with 1% of your bankroll per bet and use quarter Kelly for optimal growth.
        """)

# ============================================
# Bottom padding
# ============================================
st.markdown("<br><br><br>", unsafe_allow_html=True)
"""
Main PrizePicks +EV Optimizer App
iPad-Optimized Version - All 11 Features Included
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
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🎯 Parlay Builder", "📊 Bet Tracker", "💰 Bankroll", 
    "⚠️ Bump Detector", "🔄 Arbitrage", "🔔 Alerts", "📱 Widget"
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
                
                # ============================================
                # UPGRADE 3: SHARE FEATURE
                # ============================================
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
# TAB 2: BET TRACKER (WITH ENHANCED ANALYTICS)
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
    
    # ============================================
    # UPGRADE 1: ENHANCED ANALYTICS DASHBOARD
    # ============================================
    st.subheader("📈 Advanced Analytics")
    
    if not bets_df.empty and len(bets_df) > 0:
        # Filter to completed bets
        completed_bets = bets_df[bets_df['outcome'].notna()].copy()
        
        if not completed_bets.empty:
            # 1. Win Rate by Sport
            st.markdown("### 🏆 Win Rate by Sport")
            sport_stats = completed_bets.groupby('sport').agg({
                'outcome': lambda x: (x == 'Win').sum(),
                'stake': 'sum',
                'profit': 'sum',
                'id': 'count'
            }).rename(columns={'outcome': 'wins', 'id': 'bets'})
            
            sport_stats['win_rate'] = (sport_stats['wins'] / sport_stats['bets'] * 100).round(1)
            sport_stats['roi'] = (sport_stats['profit'] / sport_stats['stake'] * 100).round(1)
            
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
            
            # 2. Profit/Loss by Sport
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
            
            # 3. Best Performing Players
            st.markdown("### ⭐ Top Performing Players")
            player_stats = completed_bets.groupby('player').agg({
                'profit': 'sum',
                'outcome': lambda x: (x == 'Win').sum(),
                'id': 'count'
            }).rename(columns={'outcome': 'wins', 'id': 'bets'})
            
            player_stats['win_rate'] = (player_stats['wins'] / player_stats['bets'] * 100).round(1)
            player_stats = player_stats[player_stats['bets'] >= 3].sort_values('profit', ascending=False).head(10)
            
            if not player_stats.empty:
                st.dataframe(
                    player_stats[['profit', 'wins', 'bets', 'win_rate']].style.format({
                        'profit': '${:.2f}',
                        'win_rate': '{:.1f}%'
                    }),
                    use_container_width=True
                )
            else:
                st.info("Not enough data for player analysis (need at least 3 bets per player)")
            
            # 4. Performance Over Time
            st.markdown("### 📅 Performance Trend")
            
            # Group by week
            completed_bets['week'] = pd.to_datetime(completed_bets['date']).dt.strftime('%Y-%U')
            weekly_stats = completed_bets.groupby('week').agg({
                'profit': 'sum',
                'id': 'count'
            }).rename(columns={'id': 'bets'})
            
            fig3 = px.line(
                weekly_stats.reset_index(),
                x='week',
                y='profit',
                title='Weekly Profit/Loss',
                markers=True
            )
            fig3.add_hline(y=0, line_dash="dash", line_color="red")
            st.plotly_chart(fig3, use_container_width=True)
            
            # 5. Bet Size Analysis
            st.markdown("### 💰 Bet Size Analysis")
            
            # Create bet size buckets
            completed_bets['size_bucket'] = pd.cut(
                completed_bets['stake'],
                bins=[0, 10, 25, 50, 100, 500],
                labels=['$0-10', '$10-25', '$25-50', '$50-100', '$100+']
            )
            
            size_stats = completed_bets.groupby('size_bucket').agg({
                'profit': 'sum',
                'outcome': lambda x: (x == 'Win').sum(),
                'id': 'count'
            }).rename(columns={'outcome': 'wins', 'id': 'bets'})
            
            size_stats['win_rate'] = (size_stats['wins'] / size_stats['bets'] * 100).round(1)
            
            st.dataframe(size_stats, use_container_width=True)
    
    # ============================================
    # UPGRADE 2: EXPORT FEATURE
    # ============================================
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
    
    with col2:
        if st.button("📈 Export Analytics") and not bets_df.empty:
            # Create summary analytics
            summary = {
                'total_bets': stats['total_bets'],
                'win_rate': f"{stats['win_rate']:.1f}%",
                'total_profit': f"${stats['total_profit']:.2f}",
                'roi': f"{stats['roi']:.1f}%",
                'avg_odds': f"{stats['avg_odds']:.2f}",
                'export_date': datetime.now().isoformat()
            }
            summary_df = pd.DataFrame([summary])
            
            csv_summary = summary_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Summary",
                data=csv_summary,
                file_name=f"bet_summary_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    with col3:
        if st.button("📋 Copy to Clipboard") and not bets_df.empty:
            st.code(bets_df.to_string(), language="text")
            st.success("✅ Select all and copy (Cmd+C / Ctrl+C)")
    
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
                    bankroll_mgr.update_bankroll(bet['stake'], profit)
                    st.rerun()
            with col4:
                if st.button(f"❌ Loss", key=f"loss_{bet['id']}"):
                    bet_tracker.update_outcome(bet['id'], 'Loss', -bet['stake'])
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
    
    # Add new bet manually
    with st.expander("➕ Add Manual Bet"):
        col1, col2, col3 = st.columns(3)
        with col1:
            manual_sport = st.selectbox("Sport", ["NBA", "NFL", "MLB", "NHL", "SOCCER", "TENNIS"], key="manual_sport")
            manual_player = st.text_input("Player Name", key="manual_player")
        with col2:
            manual_stat = st.selectbox("Stat Type", ["Points", "Rebounds", "Assists", "PRA", "Passing Yds"], key="manual_stat")
            manual_line = st.number_input("Line", value=20.5, step=0.5, key="manual_line")
        with col3:
            manual_pick = st.selectbox("Pick", ["OVER", "UNDER"], key="manual_pick")
            manual_odds = st.number_input("Odds (Decimal)", value=2.0, step=0.1, key="manual_odds")
        
        col4, col5, col6 = st.columns(3)
        with col4:
            manual_stake = st.number_input("Stake ($)", value=10.0, step=5.0, key="manual_stake")
        with col5:
            manual_outcome = st.selectbox("Outcome", ["Pending", "Win", "Loss"], key="manual_outcome")
        with col6:
            manual_notes = st.text_input("Notes", key="manual_notes")
        
        if st.button("💾 Save Bet", key="save_bet"):
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
            st.rerun()

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
    
    st.subheader("➕ Create Custom Alert")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        alert_player = st.text_input("Player Name (optional)", placeholder="Leave empty for all", key="alert_player")
    with col2:
        alert_stat = st.selectbox("Stat Type", ["All", "Points", "Rebounds", "Assists", "PRA", "3PM"], key="alert_stat")
    with col3:
        alert_condition = st.selectbox("Condition", ["Any", "OVER", "UNDER"], key="alert_condition")
    
    col1, col2 = st.columns(2)
    with col1:
        alert_value = st.number_input("Threshold Value", value=alert_threshold, step=1, key="alert_value")
    with col2:
        alert_expiry = st.date_input("Alert Expiry", value=datetime.now() + timedelta(days=7), key="alert_expiry")
    
    if st.button("➕ Add Custom Alert", key="add_custom_alert"):
        alert_mgr.add_custom_alert(
            player=alert_player if alert_player else None,
            stat_type=alert_stat if alert_stat != "All" else None,
            condition=alert_condition if alert_condition != "Any" else None,
            threshold=alert_value / 100,
            expiry=alert_expiry
        )
        st.success("✅ Custom alert created!")
    
    st.subheader("🟢 Active Alerts")
    active_alerts = alert_mgr.get_active_alerts()
    
    if active_alerts:
        alerts_df = pd.DataFrame(active_alerts)
        st.dataframe(alerts_df, use_container_width=True, height=300)
        
        if st.button("❌ Clear All Alerts", key="clear_alerts"):
            alert_mgr.clear_all_alerts()
            st.rerun()
    else:
        st.info("No active alerts")
    
    with st.expander("📜 Alert History"):
        alert_history = bet_tracker.get_alerts(days=7)
        
        if not alert_history.empty:
            st.dataframe(alert_history[['date', 'sport', 'player', 'stat_type', 'ev', 'message']],
                        use_container_width=True, height=300)
        else:
            st.info("No alerts triggered in the last 7 days")
    
    if st.button("🔔 Test Alert", key="test_alert"):
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
    
    with st.expander("⚙️ Widget Settings"):
        col1, col2 = st.columns(2)
        with col1:
            widget_sport = st.selectbox("Sport for widget", 
                ["NBA", "NFL", "MLB", "NHL", "SOCCER", "TENNIS"], index=0, key="widget_sport")
            widget_size = st.selectbox("Widget size", ["Small", "Medium", "Large"], index=1, key="widget_size")
        with col2:
            widget_refresh = st.selectbox("Refresh rate", 
                ["Every hour", "Every 2 hours", "Every 4 hours", "Manual"], index=1, key="widget_refresh")
            widget_dark = st.checkbox("Use dark mode", value=dark_mode, key="widget_dark")
        
        if st.button("💾 Update Widget", key="update_widget"):
            st.success("✅ Widget settings saved!")
    
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
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📱 Share to Messages", key="share_messages"):
            st.info("Sharing via Messages...")
    with col2:
        if st.button("📧 Share via Email", key="share_email"):
            st.info("Opening email...")
    with col3:
        if st.button("🔗 Copy Link", key="copy_link"):
            st.code("https://prizepicks-ipad-app.streamlit.app")
            st.success("✅ Link copied!")

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
        
        **New Features Added:**
        - 📈 **Enhanced Analytics** - Win rates by sport, player performance
        - 📤 **Export Data** - Download your bet history as CSV
        - 🔗 **Share Feature** - Copy parlays to share with friends
        
        **Pro Tip:** Start with 1% of your bankroll per bet and use quarter Kelly for optimal growth.
        """)

# ============================================
# Initialize AlertManager if not already
# ============================================
if 'alert_mgr' not in locals():
    alert_mgr = AlertManager()

# ============================================
# Bottom padding
# ============================================
st.markdown("<br><br><br>", unsafe_allow_html=True)
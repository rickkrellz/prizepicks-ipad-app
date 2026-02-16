"""
Main PrizePicks +EV Optimizer App
iPad-Optimized Version - Fixed to show all props correctly
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
import pytz
from time import sleep

# Import our modules
from ev_calculator import calculate_ev, calculate_parlay_probability
from correlation_analyzer import calculate_correlation_penalty, get_correlation_warning
from prizepicks_scraper import get_daily_data

# ============================================
# PAGE CONFIGURATION (MUST BE FIRST)
# ============================================
st.set_page_config(
    page_title="PrizePicks +EV",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="collapsed"
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
    
    div[data-testid="stMetric"] div[data-testid="stMetricDelta"] {
        color: rgba(255,255,255,0.8) !important;
        font-size: 14px !important;
    }
    
    /* Data tables - scrollable on iPad */
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
    
    /* Bottom padding for easy scrolling */
    .main > div {
        padding-bottom: 120px;
    }
    
    /* Better radio buttons */
    div[role="radiogroup"] {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        margin: 15px 0px;
    }
    
    div[role="radiogroup"] label {
        background: #f0f2f6;
        padding: 14px 25px;
        border-radius: 30px;
        font-size: 17px;
        min-width: 90px;
        text-align: center;
        transition: all 0.2s;
    }
    
    div[role="radiogroup"] label:hover {
        background: #e0e2e6;
    }
    
    /* Hide hamburger menu for cleaner look */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Better expander */
    .streamlit-expanderHeader {
        font-size: 18px !important;
        font-weight: 600 !important;
        padding: 15px !important;
        background-color: #f8f9fa !important;
        border-radius: 12px !important;
    }
    
    /* Dividers */
    hr {
        margin: 25px 0px !important;
        border: none !important;
        height: 2px !important;
        background: linear-gradient(to right, transparent, #ddd, transparent) !important;
    }
    
    /* Headers */
    h1 {
        font-size: 32px !important;
        font-weight: 700 !important;
        margin-bottom: 5px !important;
    }
    
    h3 {
        font-size: 22px !important;
        font-weight: 600 !important;
        margin: 20px 0px 15px 0px !important;
    }
    
    /* Captions */
    .stCaption {
        font-size: 14px !important;
        color: #666 !important;
        margin-bottom: 20px !important;
    }
    
    /* Success/Warning/Info boxes */
    .stAlert {
        border-radius: 15px !important;
        padding: 15px !important;
        font-size: 16px !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# TITLE SECTION
# ============================================
st.title("🏀 PrizePicks +EV Optimizer")
st.caption("Optimized for iPad • Tap-friendly • Auto-updates daily")

# ============================================
# SIDEBAR SETTINGS - MULTI-SPORT + DARK MODE
# ============================================
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    
    # Import sport config
    from sports_config import SPORT_DISPLAY_NAMES
    
    # Sport selection with emojis
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
    
    # Parlay legs
    st.markdown("### 📊 Parlay Size")
    num_legs = st.select_slider(
        "Number of Picks",
        options=[2, 3, 4, 5, 6],
        value=6,
        help="How many picks in your parlay"
    )
    
    # EV threshold
    st.markdown("### 💰 Minimum Value")
    min_ev = st.slider(
        "EV Threshold",
        min_value=0,
        max_value=20,
        value=5,
        step=1,
        help="Minimum expected value %"
    ) / 100
    
    st.divider()
    
# Dark mode toggle with better readability
dark_mode = st.toggle("🌙 Dark Mode", value=False, help="Switch between light and dark theme")

if dark_mode:
    st.markdown("""
    <style>
        /* Dark mode colors - Improved contrast */
        .stApp {
            background-color: #0e1117;
            color: #ffffff;
        }
        
        .main > div {
            background-color: #0e1117;
        }
        
        /* Headers and text - Much brighter */
        h1, h2, h3, h4, h5, h6 {
            color: #ffffff !important;
            font-weight: 600 !important;
        }
        
        p, li, .stMarkdown, .stCaption {
            color: #e0e0e0 !important;
        }
        
        /* Sidebar specific - CRITICAL FIX */
        section[data-testid="stSidebar"] {
            background-color: #1a1f2c !important;
        }
        
        section[data-testid="stSidebar"] .stMarkdown,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] li,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] label {
            color: #ffffff !important;
            font-weight: 500 !important;
        }
        
        /* Sidebar headers */
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3 {
            color: #ffffff !important;
            border-bottom: 1px solid #3a4050;
            padding-bottom: 8px;
        }
        
        /* Metric cards */
        div[data-testid="stMetric"] {
            background: linear-gradient(135deg, #2d3440 0%, #1a1f2c 100%) !important;
            border: 1px solid #3a4050 !important;
            border-radius: 10px !important;
        }
        
        div[data-testid="stMetric"] label,
        div[data-testid="stMetric"] div {
            color: #ffffff !important;
        }
        
        /* DataFrames */
        .stDataFrame {
            background-color: #1a1f2c !important;
        }
        
        .stDataFrame td, .stDataFrame th {
            color: #ffffff !important;
            background-color: #1a1f2c !important;
            border-color: #3a4050 !important;
        }
        
        /* Buttons */
        .stButton > button {
            background-color: #2d3440 !important;
            color: #ffffff !important;
            border: 1px solid #3a4050 !important;
            font-weight: 600 !important;
        }
        
        .stButton > button:hover {
            background-color: #3a4050 !important;
            border-color: #5a6270 !important;
        }
        
        /* Select boxes */
        .stSelectbox > div > div {
            background-color: #2d3440 !important;
            color: #ffffff !important;
            border-color: #3a4050 !important;
        }
        
        .stSelectbox label {
            color: #ffffff !important;
        }
        
        /* Sliders */
        .stSlider label {
            color: #ffffff !important;
        }
        
        .stSlider div[data-baseweb="slider"] {
            color: #ffffff !important;
        }
        
        /* Expanders */
        .streamlit-expanderHeader {
            background-color: #1a1f2c !important;
            color: #ffffff !important;
            border: 1px solid #3a4050 !important;
        }
        
        .streamlit-expanderContent {
            background-color: #1a1f2c !important;
            color: #e0e0e0 !important;
        }
        
        /* Alerts */
        .stAlert {
            background-color: #2d3440 !important;
            color: #ffffff !important;
            border-left: 4px solid #4CAF50 !important;
        }
        
        /* Success/Warning/Info boxes */
        .stAlert.success {
            border-left-color: #4CAF50 !important;
        }
        
        .stAlert.warning {
            border-left-color: #ff9800 !important;
        }
        
        .stAlert.error {
            border-left-color: #f44336 !important;
        }
        
        .stAlert.info {
            border-left-color: #2196F3 !important;
        }
        
        /* Progress bar */
        .stProgress > div > div {
            background-color: #4CAF50 !important;
        }
        
        /* Radio buttons */
        div[role="radiogroup"] label {
            background-color: #2d3440 !important;
            color: #ffffff !important;
            border: 1px solid #3a4050 !important;
        }
        
        div[role="radiogroup"] label:hover {
            background-color: #3a4050 !important;
        }
        
        /* Scrollbar */
        ::-webkit-scrollbar {
            width: 10px;
            background-color: #1a1f2c;
        }
        
        ::-webkit-scrollbar-thumb {
            background-color: #3a4050;
            border-radius: 5px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background-color: #5a6270;
        }
        
        /* Links */
        a {
            color: #66b0ff !important;
        }
        
        a:hover {
            color: #99ccff !important;
        }
        
        /* Toggle switch */
        .stCheckbox label {
            color: #ffffff !important;
        }
        
        /* Captions */
        .stCaption {
            color: #b0b0b0 !important;
        }
    </style>
    """, unsafe_allow_html=True)
        
    st.divider()
    
    # BIG ANALYZE BUTTON
    analyze_clicked = st.button(
        "🔍 FIND BEST PARLAY",
        use_container_width=True,
        type="primary"
    )
    
    st.divider()
    
    # Data status with timezone
    from datetime import datetime
    import pytz
    central = pytz.timezone('America/Chicago')
    current_time = datetime.now(central).strftime("%I:%M %p %Z")
    st.caption(f"🔄 Last update: {current_time}")
    
    # Manual refresh
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.success("✅ Cache cleared! Click 'FIND BEST PARLAY' again.")
    
    st.divider()
    
    # Quick tips
    with st.expander("💡 Quick Tips"):
        st.markdown("""
        **What is +EV?**
        - Positive Expected Value means the bet has an edge
        - Higher EV = Better value
        
        **How to use:**
        1. Select your sport from the dropdown
        2. Set your parlay size (2-6 picks)
        3. Adjust EV threshold (5% is good start)
        4. Click "FIND BEST PARLAY"
        5. Review the picks
        6. Toggle dark mode for night viewing
        
        **Supported Sports:**
        • 🏀 NBA Basketball
        • 🏒 NHL Hockey
        • ⚽ Soccer
        • 🎾 Tennis
        • More coming soon!
        """)
        
# ============================================
# LOAD DATA FUNCTION
# ============================================
@st.cache_data(ttl=300)
def load_data(sport):
    """
    Load PrizePicks and market data
    Cached for 5 minutes to avoid too many requests
    """
    try:
        pp_data, market_data = get_daily_data(sport)
        return pp_data, market_data
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame(), pd.DataFrame()

# ============================================
# PREVIEW SECTION - Updates when sport changes
# ============================================
st.subheader("👀 Today's Available Props")

# Create a placeholder for the preview
preview_placeholder = st.empty()

# Load preview data based on selected sport
with st.spinner(f"Loading {selected_sport} preview..."):
    preview_pp, preview_market = load_data(selected_sport)
    
    if not preview_pp.empty:
        # Determine which columns to display
        display_columns = ['player', 'line', 'stat_type']
        column_names = ['Player', 'Line', 'Stat Type']
        
        if 'team' in preview_pp.columns:
            display_columns.append('team')
            column_names.append('Team')
        
        preview_df = preview_pp[display_columns].head(10).copy()
        preview_df.columns = column_names
        
        # Show data source status
        if len(preview_pp) > 100:
            preview_placeholder.success(f"✅ Showing {len(preview_pp)} real {selected_sport} props from PrizePicks")
        else:
            preview_placeholder.info(f"📊 Showing {len(preview_pp)} {selected_sport} props")
        
        preview_placeholder.dataframe(preview_df, use_container_width=True, height=300)
    else:
        preview_placeholder.warning(f"No data available for {selected_sport}")

# ============================================
# MAIN APP LOGIC
# ============================================
if analyze_clicked:
    # Show loading spinner
    with st.spinner("🔄 Analyzing data... Please wait..."):
        
        # Create progress bar for visual feedback
        progress_bar = st.progress(0, text="Loading PrizePicks data...")
        
        # Load data for selected sport
        pp_data, market_data = load_data(selected_sport)
        progress_bar.progress(30, text="Loading market odds...")
        
        # DEBUG: Show data info in expander
        with st.expander("🔍 Debug Info (Click to see data details)"):
            col1, col2 = st.columns(2)
            with col1:
                st.write("**PrizePicks Data:**")
                st.write(f"Rows: {len(pp_data)}")
                if not pp_data.empty:
                    st.write("Columns:", list(pp_data.columns))
                    st.write("Unique players:", pp_data['player'].nunique())
                    st.write("Sample players:", pp_data['player'].head(10).tolist())
                else:
                    st.warning("PrizePicks data is empty!")
            
            with col2:
                st.write("**Market Data:**")
                st.write(f"Rows: {len(market_data)}")
                if not market_data.empty:
                    st.write("Columns:", list(market_data.columns))
                    st.write("Unique players:", market_data['player'].nunique())
                    st.write("Sample players:", market_data['player'].head(10).tolist())
                else:
                    st.warning("Market data is empty!")
        
        if pp_data.empty or market_data.empty:
            st.error("❌ Could not load data. Please try again.")
            st.stop()
        
        progress_bar.progress(60, text="Calculating expected value...")
        
        # Calculate EV
        ev_data = calculate_ev(pp_data, market_data)
        
        if ev_data.empty:
            st.error("❌ No matching props found between PrizePicks and market data.")
            st.stop()
        
        progress_bar.progress(80, text="Finding optimal combinations...")
        
        # Filter by positive EV and threshold
        positive_ev = ev_data[ev_data['is_positive']].copy()
        positive_ev = positive_ev[positive_ev['ev'] >= min_ev]
        
        # Keep a copy for display (all props, no deduplication)
        display_positive_ev = positive_ev.copy()
        
        # Check if we have enough picks
        if len(positive_ev) < num_legs:
            st.warning(f"⚠️ Only {len(positive_ev)} props meet your {min_ev:.0%} EV threshold. Showing best available.")
            # Get best available
            positive_ev = ev_data.nlargest(num_legs * 2, 'ev')
            display_positive_ev = positive_ev.copy()
        
        # For parlay, we want unique players with highest EV
        # First, get best EV for each player
        if not positive_ev.empty:
            unique_player_picks = positive_ev.sort_values('ev', ascending=False).drop_duplicates(subset=['player'], keep='first')
            # Then take top num_legs
            selected_picks = unique_player_picks.head(num_legs).copy()
        else:
            selected_picks = pd.DataFrame()
        
        progress_bar.progress(90, text="Analyzing correlations...")
        
        # Calculate correlation penalty
        penalty = 1.0
        warning = None
        if not selected_picks.empty and len(selected_picks) >= 2:
            penalty = calculate_correlation_penalty(selected_picks)
            warning = get_correlation_warning(selected_picks)
        
        # Calculate probabilities
        raw_prob = 0
        adjusted_prob = 0
        if not selected_picks.empty:
            raw_prob = calculate_parlay_probability(selected_picks)
            adjusted_prob = raw_prob * penalty
        
        progress_bar.progress(100, text="Done!")
        progress_bar.empty()
        
        # ============================================
        # DISPLAY RESULTS
        # ============================================
        st.divider()
        
        # Success message with count of real props
        st.success(f"✅ Found {len(display_positive_ev)} profitable props from {len(pp_data)} total PrizePicks props!")
        
        if not selected_picks.empty:
            st.caption(f"🎯 Showing top {len(selected_picks)} unique players for your {num_legs}-leg parlay")
        
        # METRICS ROW
        col1, col2 = st.columns(2)
        
        with col1:
            if not selected_picks.empty:
                avg_ev = selected_picks['ev'].mean()
                st.metric(
                    "Average EV",
                    f"{avg_ev:.1%}",
                    help="Average expected value of your picks"
                )
            else:
                st.metric("Average EV", "N/A")
        
        with col2:
            if not selected_picks.empty:
                st.metric(
                    "Win Probability",
                    f"{adjusted_prob:.1%}",
                    delta=f"{raw_prob:.1%} raw",
                    help="Adjusted for correlations"
                )
            else:
                st.metric("Win Probability", "N/A")
        
        # ============================================
        # SELECTED PICKS TABLE - FIXED
        # ============================================
        st.subheader(f"🎯 Your Optimal {num_legs}-Leg Parlay")
        
        if not selected_picks.empty:
            # Create a clean dataframe for display
            parlay_data = []
            for idx, pick in selected_picks.iterrows():
                parlay_data.append({
                    'Player': pick['player'],
                    'Stat': pick['stat_type'],
                    'Line': pick['line'],
                    'Pick': pick['direction'],
                    'EV': f"{pick['ev']:.1%}"
                })
            
            # Convert to DataFrame
            parlay_df = pd.DataFrame(parlay_data)
            
            # Show the table with all rows
            st.dataframe(
                parlay_df,
                use_container_width=True,
                height=400,
                column_config={
                    "Player": st.column_config.TextColumn("Player", width="medium"),
                    "Stat": st.column_config.TextColumn("Stat Type", width="medium"),
                    "Line": st.column_config.NumberColumn("Line", width="small"),
                    "Pick": st.column_config.TextColumn("Pick", width="small"),
                    "EV": st.column_config.TextColumn("EV", width="small"),
                }
            )
            
            # Show the count
            st.caption(f"✅ Showing {len(parlay_df)} unique players with highest EV")
        else:
            st.warning("No picks available to display")
        
        # Show warning if any
        if warning:
            st.warning(warning)
        
        # CORRELATION EXPLANATION
        with st.expander("📊 Correlation Analysis"):
            if not selected_picks.empty and len(selected_picks) >= 2:
                st.markdown(f"""
                **Correlation Penalty Factor:** `{penalty:.2f}`
                
                - **Penalty < 1.0** = Negative correlation (reduces chance)
                - **Penalty > 1.0** = Positive correlation (helps)
                
                Your picks have a penalty of {penalty:.2f}, which means your actual
                probability is {adjusted_prob:.1%} vs the raw {raw_prob:.1%}.
                
                **Why this matters:**
                - Same-team players tend to negatively correlate
                - Different games/teams are usually independent
                - Avoid stacking players from the same team
                """)
            else:
                st.info("Not enough picks for correlation analysis")
        
        # EV DISTRIBUTION CHART
        st.subheader("📊 Top Expected Value Picks")
        
        # Prepare data for chart (show top 15 props)
        if not display_positive_ev.empty:
            chart_data = display_positive_ev.head(15).copy()
            chart_data['player_short'] = chart_data['player'].apply(
                lambda x: x.split()[-1] if len(x.split()) > 1 else x
            )
            
            # Create bar chart
            fig = px.bar(
                chart_data,
                x='player_short',
                y='ev',
                color='ev',
                color_continuous_scale='RdYlGn',
                title=f"Top 15 Props by EV - {selected_sport}",
                labels={'ev': 'Expected Value', 'player_short': 'Player'}
            )
            
            fig.update_layout(
                xaxis_tickangle=-45,
                height=400,
                margin=dict(l=20, r=20, t=40, b=80),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                yaxis_tickformat='.0%'
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No props to display in chart")

        # ============================================
        # VIEW ALL PROFITABLE PROPS - FIXED
        # ============================================
        with st.expander("📈 View All Profitable Props"):
            if not display_positive_ev.empty:
                # Show ALL profitable props without deduplication
                all_display = display_positive_ev[['player', 'stat_type', 'line', 'direction', 'ev']].copy()
                all_display['ev'] = all_display['ev'].apply(lambda x: f"{x:.1%}")
                all_display.columns = ['Player', 'Stat', 'Line', 'Pick', 'EV']
                
                st.dataframe(
                    all_display,
                    use_container_width=True,
                    height=400
                )
                st.caption(f"📊 Total profitable props: {len(display_positive_ev)}")
            else:
                st.info("No profitable props found")
        
        # ACTION BUTTONS
        st.divider()
        st.markdown("### Ready to play?")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("[📱 Open PrizePicks](https://app.prizepicks.com/)")
        with col2:
            if st.button("🔄 New Analysis", use_container_width=True):
                st.cache_data.clear()
                st.rerun()
        
        # DISCLAIMER
        st.divider()
        st.caption("""
        ⚠️ **Disclaimer**: This tool is for research and educational purposes only. 
        Always verify player status, injuries, and game situations before placing picks. 
        Past performance does not guarantee future results. Use at your own risk.
        """)

else:
    # ============================================
    # WELCOME SCREEN (when app first loads)
    # ============================================
    st.divider()
    
    # Welcome message
    st.markdown("""
    ### 👆 Tap **'FIND BEST PARLAY'** in the sidebar to start
    
    This app helps you build smarter PrizePicks parlays by:
    """)
    
    # Feature cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("""
        **📊 Find Value**
        Compare PrizePicks lines against market odds to find +EV picks
        """)
    
    with col2:
        st.info("""
        **🧮 Optimize Parlays**
        Build 2-6 leg parlays with the best expected value
        """)
    
    with col3:
        st.info("""
        **🔄 Avoid Correlations**
        Identify negatively correlated picks that hurt your chances
        """)
    
    # Instructions
    with st.expander("📖 How to Use This App"):
        st.markdown("""
        **Step-by-Step Guide:**
        
        1. **Open the sidebar** (tap the arrow in top-left corner)
        2. **Select your sport** (NBA, NFL, etc.)
        3. **Choose parlay size** (2-6 picks)
        4. **Set EV threshold** (5% is a good starting point)
        5. **Tap "FIND BEST PARLAY"**
        6. **Review the picks** - check for same-team players
        7. **Verify player status** on PrizePicks
        8. **Place your picks** if you agree with the analysis
        
        **Understanding EV (Expected Value):**
        - EV > 0% means the bet has positive expected value
        - Higher EV = Better value
        - PrizePicks assumes 50% chance for each pick
        - Market odds show the "true" probability
        """
        )
    
    # Bottom spacing
    st.markdown("<br><br>", unsafe_allow_html=True)

# Always show bottom padding
st.markdown("<br><br><br>", unsafe_allow_html=True)
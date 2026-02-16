"""
PrizePicks Data Fetcher - Reads from JSON files updated by GitHub Actions
"""

import pandas as pd
import streamlit as st
from datetime import datetime
import json
import os

@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_prizepicks_data(sport="NBA"):
    """
    Read PrizePicks data from JSON files (updated by GitHub Actions)
    """
    try:
        # Try multiple possible file paths
        possible_paths = [
            f"prizepicks_{sport.lower()}_latest.json",  # Current directory
            f"/mount/src/prizepicks-ipad-app/prizepicks_{sport.lower()}_latest.json",  # Full path
        ]
        
        file_found = None
        for filepath in possible_paths:
            if os.path.exists(filepath):
                file_found = filepath
                break
        
        if file_found:
            st.sidebar.write(f"📁 Reading from: {file_found}")  # Debug info
            
            with open(file_found, 'r') as f:
                data = json.load(f)
            
            df = pd.DataFrame(data)
            
            if not df.empty:
                # Get file modification time
                mod_time = datetime.fromtimestamp(os.path.getmtime(file_found))
                st.sidebar.success(
                    f"✅ Loaded {len(df)} real {sport} props "
                    f"(updated {mod_time.strftime('%m/%d %I:%M %p')})"
                )
                return df
            else:
                st.sidebar.warning(f"JSON file for {sport} is empty")
                return get_enhanced_mock_data(sport)
        else:
            st.sidebar.warning(f"No data file found for {sport}. Tried: {possible_paths}")
            
            # List all files in directory to help debug
            try:
                files = os.listdir('.')
                json_files = [f for f in files if f.endswith('.json')]
                if json_files:
                    st.sidebar.info(f"Found JSON files: {json_files}")
            except:
                pass
                
            return get_enhanced_mock_data(sport)
            
    except Exception as e:
        st.sidebar.error(f"Error reading data: {e}")
        return get_enhanced_mock_data(sport)

def get_enhanced_mock_data(sport="NBA"):
    """
    Enhanced mock data as fallback
    """
    if sport == "NBA":
        mock_data = [
            {"player": "LeBron James", "line": 25.5, "stat_type": "Points", "team": "LAL"},
            {"player": "Anthony Davis", "line": 28.5, "stat_type": "Points", "team": "LAL"},
            {"player": "Stephen Curry", "line": 27.5, "stat_type": "Points", "team": "GSW"},
            {"player": "Giannis Antetokounmpo", "line": 32.5, "stat_type": "Points", "team": "MIL"},
            {"player": "Jayson Tatum", "line": 26.5, "stat_type": "Points", "team": "BOS"},
            {"player": "Nikola Jokic", "line": 24.5, "stat_type": "Points", "team": "DEN"},
            {"player": "Joel Embiid", "line": 31.5, "stat_type": "Points", "team": "PHI"},
            {"player": "Luka Doncic", "line": 30.5, "stat_type": "Points", "team": "DAL"},
            {"player": "Shai Gilgeous-Alexander", "line": 29.5, "stat_type": "Points", "team": "OKC"},
            {"player": "Trae Young", "line": 26.5, "stat_type": "Points", "team": "ATL"},
        ]
    elif sport == "NFL":
        mock_data = [
            {"player": "Patrick Mahomes", "line": 285.5, "stat_type": "Passing Yds", "team": "KC"},
            {"player": "Travis Kelce", "line": 75.5, "stat_type": "Receiving Yds", "team": "KC"},
            {"player": "Jalen Hurts", "line": 245.5, "stat_type": "Passing Yds", "team": "PHI"},
            {"player": "Josh Allen", "line": 265.5, "stat_type": "Passing Yds", "team": "BUF"},
        ]
    else:
        mock_data = []
    
    df = pd.DataFrame(mock_data)
    st.sidebar.info(f"📊 Using mock data for {sport} (no JSON file found)")
    return df

@st.cache_data(ttl=300)
def fetch_market_odds(sport="NBA"):
    """
    Fetch market odds from The Odds API
    """
    import requests
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    API_KEY = os.getenv("ODDS_API_KEY")
    
    if not API_KEY:
        return get_enhanced_market_data(sport)
    
    sport_mapping = {
        "NBA": "basketball_nba",
        "NFL": "americanfootball_nfl",
        "MLB": "baseball_mlb",
        "NHL": "icehockey_nhl"
    }
    
    api_sport = sport_mapping.get(sport, "basketball_nba")
    
    url = f"https://api.the-odds-api.com/v4/sports/{api_sport}/odds"
    params = {
        "apiKey": API_KEY,
        "regions": "us",
        "markets": "player_points,player_rebounds,player_assists,player_pass_yds,player_receiving_yds",
        "oddsFormat": "decimal"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            odds_data = response.json()
            
            props = []
            for game in odds_data:
                for bookmaker in game.get('bookmakers', []):
                    for market in bookmaker.get('markets', []):
                        for outcome in market.get('outcomes', []):
                            if outcome.get('price', 0) > 0:
                                implied_prob = 1 / outcome['price']
                                props.append({
                                    'player': outcome.get('description', 'Unknown'),
                                    'market_line': float(outcome.get('point', 0)),
                                    'implied_prob': round(implied_prob, 3)
                                })
            
            df = pd.DataFrame(props)
            if not df.empty:
                df = df.drop_duplicates(subset=['player', 'market_line'])
                return df
            
        return get_enhanced_market_data(sport)
        
    except Exception as e:
        print(f"Market odds error: {e}")
        return get_enhanced_market_data(sport)

def get_enhanced_market_data(sport="NBA"):
    """Enhanced mock market data"""
    if sport == "NBA":
        return pd.DataFrame([
            {"player": "LeBron James", "market_line": 25.0, "implied_prob": 0.58},
            {"player": "Anthony Davis", "market_line": 28.0, "implied_prob": 0.55},
            {"player": "Stephen Curry", "market_line": 27.0, "implied_prob": 0.62},
        ])
    else:
        return pd.DataFrame([
            {"player": "Patrick Mahomes", "market_line": 280.5, "implied_prob": 0.62},
        ])

def get_daily_data(sport="NBA"):
    """Main function to get both PrizePicks and market data"""
    pp_df = fetch_prizepicks_data(sport)
    market_df = fetch_market_odds(sport)
    return pp_df, market_df

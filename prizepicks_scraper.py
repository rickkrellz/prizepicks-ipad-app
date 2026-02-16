"""
PrizePicks Real Data Fetcher
Uses PrizePicks internal API to get real data
"""

import requests
import pandas as pd
import streamlit as st
from datetime import datetime
import time

@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_prizepicks_data(sport="NBA"):
    """
    Fetch REAL PrizePicks data using their internal API
    """
    # Map sports to league IDs (verified working)
    league_ids = {
        "NBA": 7,
        "NFL": 12,
        "MLB": 3,  
        "NHL": 4,
        "WNBA": 8,
        "PGA": 6,
        "UFC": 15,
    }
    
    league_id = league_ids.get(sport, 7)
    
    # PrizePicks internal API endpoint
    url = f"https://api.prizepicks.com/projections?league_id={league_id}&per_page=250&single_stat=true"
    
    headers = {
        "Connection": "keep-alive",
        "Accept": "application/json; charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Access-Control-Allow-Credentials": "true",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Referer": "https://app.prizepicks.com/",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
    }
    
    try:
        response = requests.get(url=url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Parse the response structure
            # PrizePicks API returns:
            # - 'data': contains the projections (props)
            # - 'included': contains related data like player names, teams
            
            # Create dictionaries for lookups
            players = {}
            teams = {}
            
            # First, extract all included data
            for item in data.get('included', []):
                item_type = item.get('type')
                item_id = item.get('id')
                attributes = item.get('attributes', {})
                
                if item_type == 'new_player':
                    players[item_id] = {
                        'name': attributes.get('name', 'Unknown'),
                        'team_id': attributes.get('team_id')
                    }
                elif item_type == 'team':
                    teams[item_id] = attributes.get('name', 'Unknown')
            
            # Now extract the projections from 'data'
            props = []
            for item in data.get('data', []):
                attributes = item.get('attributes', {})
                relationships = item.get('relationships', {})
                
                # Get player info
                player_data = relationships.get('new_player', {}).get('data', {})
                player_id = player_data.get('id')
                player_info = players.get(player_id, {})
                player_name = player_info.get('name', 'Unknown')
                
                # Get team info
                team_id = player_info.get('team_id')
                team_name = teams.get(team_id, 'Unknown')
                
                # Get stat type and line
                stat_type = attributes.get('stat_type', 'Unknown')
                line_score = attributes.get('line_score')
                
                # Convert line to float if possible
                try:
                    line_value = float(line_score) if line_score else None
                except (ValueError, TypeError):
                    line_value = None
                
                # Only add if we have valid data
                if player_name != 'Unknown' and line_value:
                    props.append({
                        'player': player_name,
                        'line': line_value,
                        'stat_type': stat_type,
                        'team': team_name,
                        'sport': sport,
                        'game_time': attributes.get('start_time', ''),
                        'projection_type': attributes.get('projection_type', ''),
                        'timestamp': datetime.now().isoformat()
                    })
            
            # Create DataFrame
            df = pd.DataFrame(props)
            
            if not df.empty:
                st.sidebar.success(f"✅ Loaded {len(df)} real {sport} props from PrizePicks")
                return df
            else:
                st.sidebar.warning("API returned empty data, using mock data")
                return get_mock_data(sport)
                
        else:
            st.sidebar.warning(f"API returned {response.status_code}, using mock data")
            return get_mock_data(sport)
            
    except Exception as e:
        st.sidebar.warning(f"API error: {e}, using mock data")
        return get_mock_data(sport)

@st.cache_data(ttl=300)
def fetch_market_odds(sport="NBA"):
    """
    Fetch real market odds from The Odds API
    """
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    API_KEY = os.getenv("ODDS_API_KEY")
    
    if not API_KEY:
        return get_mock_market_data(sport)
    
    # Map sports to The Odds API format
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
        "markets": "player_points,player_rebounds,player_assists",
        "oddsFormat": "decimal"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            odds_data = response.json()
            
            # Parse odds data
            props = []
            for game in odds_data:
                for bookmaker in game.get('bookmakers', []):
                    for market in bookmaker.get('markets', []):
                        for outcome in market.get('outcomes', []):
                            # Convert decimal odds to implied probability
                            implied_prob = 1 / outcome['price']
                            props.append({
                                'player': outcome.get('description', 'Unknown'),
                                'market_line': float(outcome.get('point', 0)),
                                'implied_prob': round(implied_prob, 3)
                            })
            
            df = pd.DataFrame(props)
            if not df.empty:
                # Remove duplicates (keep first occurrence)
                df = df.drop_duplicates(subset=['player', 'market_line'])
                return df
            
        return get_mock_market_data(sport)
        
    except Exception as e:
        print(f"Market odds error: {e}")
        return get_mock_market_data(sport)

def get_mock_data(sport="NBA"):
    """Fallback mock data if API fails"""
    mock_data = {
        "NBA": [
            {"player": "LeBron James", "line": 25.5, "stat_type": "Points", "team": "LAL"},
            {"player": "Anthony Davis", "line": 28.5, "stat_type": "Points", "team": "LAL"},
            {"player": "Stephen Curry", "line": 27.5, "stat_type": "Points", "team": "GSW"},
            {"player": "Giannis Antetokounmpo", "line": 32.5, "stat_type": "Points", "team": "MIL"},
            {"player": "Jayson Tatum", "line": 26.5, "stat_type": "Points", "team": "BOS"},
        ],
        "NFL": [
            {"player": "Patrick Mahomes", "line": 285.5, "stat_type": "Passing Yds", "team": "KC"},
            {"player": "Travis Kelce", "line": 75.5, "stat_type": "Receiving Yds", "team": "KC"},
        ]
    }
    df = pd.DataFrame(mock_data.get(sport, []))
    st.sidebar.info("📊 Using mock data (API unavailable)")
    return df

def get_mock_market_data(sport="NBA"):
    """Fallback mock market data"""
    return pd.DataFrame([
        {"player": "LeBron James", "market_line": 25.0, "implied_prob": 0.58},
        {"player": "Anthony Davis", "market_line": 28.0, "implied_prob": 0.55},
        {"player": "Stephen Curry", "market_line": 27.0, "implied_prob": 0.62},
    ])

def get_daily_data(sport="NBA"):
    """Main function to get both PrizePicks and market data"""
    with st.spinner(f"Fetching real {sport} data..."):
        pp_df = fetch_prizepicks_data(sport)
        market_df = fetch_market_odds(sport)
    return pp_df, market_df

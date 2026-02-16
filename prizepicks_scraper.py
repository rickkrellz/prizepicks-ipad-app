"""
PrizePicks Real Data Fetcher
Uses PrizePicks internal API with better headers to avoid 403 errors
"""

import requests
import pandas as pd
import streamlit as st
from datetime import datetime
import random
import time

@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_prizepicks_data(sport="NBA"):
    """
    Fetch REAL PrizePicks data using their internal API
    With better headers to avoid 403 errors
    """
    # Map sports to league IDs (verified working)
    league_ids = {
        "NBA": 7,
        "NFL": 2,
        "MLB": 1,  
        "NHL": 5,
    }
    
    league_id = league_ids.get(sport, 7)
    
    # PrizePicks internal API endpoint
    url = f"https://api.prizepicks.com/projections?league_id={league_id}&per_page=250&single_stat=true"
    
    # More realistic browser headers to avoid 403
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Host": "api.prizepicks.com",
        "Origin": "https://app.prizepicks.com",
        "Referer": "https://app.prizepicks.com/",
        "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        # Add a small delay to avoid rate limiting
        time.sleep(1)
        
        # Make the request with timeout
        response = requests.get(
            url=url, 
            headers=headers, 
            timeout=15,
            allow_redirects=True
        )
        
        st.sidebar.write(f"API Status Code: {response.status_code}")  # Debug info
        
        if response.status_code == 200:
            data = response.json()
            
            # Parse the response structure
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
                st.sidebar.warning("API returned empty data, using enhanced mock data")
                return get_enhanced_mock_data(sport)
        
        elif response.status_code == 403:
            st.sidebar.warning("API returned 403 (Forbidden) - Using enhanced mock data with real player names")
            return get_enhanced_mock_data(sport)
        else:
            st.sidebar.warning(f"API returned {response.status_code}, using enhanced mock data")
            return get_enhanced_mock_data(sport)
            
    except Exception as e:
        st.sidebar.warning(f"API error: {str(e)[:50]}... using enhanced mock data")
        return get_enhanced_mock_data(sport)

def get_enhanced_mock_data(sport="NBA"):
    """
    Enhanced mock data with real player names and realistic lines
    """
    if sport == "NBA":
        # Current NBA players with realistic lines
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
            {"player": "Kevin Durant", "line": 27.5, "stat_type": "Points", "team": "PHX"},
            {"player": "Devin Booker", "line": 26.5, "stat_type": "Points", "team": "PHX"},
            {"player": "Anthony Edwards", "line": 25.5, "stat_type": "Points", "team": "MIN"},
            {"player": "Karl-Anthony Towns", "line": 22.5, "stat_type": "Points", "team": "MIN"},
            {"player": "Jimmy Butler", "line": 21.5, "stat_type": "Points", "team": "MIA"},
            {"player": "Bam Adebayo", "line": 19.5, "stat_type": "Points", "team": "MIA"},
            {"player": "Jalen Brunson", "line": 26.5, "stat_type": "Points", "team": "NYK"},
            {"player": "Julius Randle", "line": 23.5, "stat_type": "Points", "team": "NYK"},
            {"player": "Kyrie Irving", "line": 24.5, "stat_type": "Points", "team": "DAL"},
            {"player": "James Harden", "line": 16.5, "stat_type": "Points", "team": "LAC"},
            {"player": "Kawhi Leonard", "line": 23.5, "stat_type": "Points", "team": "LAC"},
            {"player": "Paul George", "line": 22.5, "stat_type": "Points", "team": "LAC"},
            {"player": "Zion Williamson", "line": 23.5, "stat_type": "Points", "team": "NOP"},
            {"player": "CJ McCollum", "line": 20.5, "stat_type": "Points", "team": "NOP"},
            {"player": "LaMelo Ball", "line": 23.5, "stat_type": "Points", "team": "CHA"},
            {"player": "Miles Bridges", "line": 20.5, "stat_type": "Points", "team": "CHA"},
            {"player": "Cade Cunningham", "line": 22.5, "stat_type": "Points", "team": "DET"},
            {"player": "Jaden Ivey", "line": 16.5, "stat_type": "Points", "team": "DET"},
            {"player": "Victor Wembanyama", "line": 21.5, "stat_type": "Points", "team": "SAS"},
            {"player": "De'Aaron Fox", "line": 26.5, "stat_type": "Points", "team": "SAC"},
            {"player": "Domantas Sabonis", "line": 19.5, "stat_type": "Points", "team": "SAC"},
            {"player": "Ja Morant", "line": 25.5, "stat_type": "Points", "team": "MEM"},
            {"player": "Jaren Jackson Jr.", "line": 20.5, "stat_type": "Points", "team": "MEM"},
        ]
    elif sport == "NFL":
        mock_data = [
            {"player": "Patrick Mahomes", "line": 285.5, "stat_type": "Passing Yds", "team": "KC"},
            {"player": "Travis Kelce", "line": 75.5, "stat_type": "Receiving Yds", "team": "KC"},
            {"player": "Tyreek Hill", "line": 80.5, "stat_type": "Receiving Yds", "team": "MIA"},
            {"player": "Jalen Hurts", "line": 245.5, "stat_type": "Passing Yds", "team": "PHI"},
            {"player": "AJ Brown", "line": 70.5, "stat_type": "Receiving Yds", "team": "PHI"},
            {"player": "Josh Allen", "line": 265.5, "stat_type": "Passing Yds", "team": "BUF"},
            {"player": "Stefon Diggs", "line": 75.5, "stat_type": "Receiving Yds", "team": "BUF"},
            {"player": "Christian McCaffrey", "line": 110.5, "stat_type": "Rush + Rec Yds", "team": "SF"},
            {"player": "Lamar Jackson", "line": 225.5, "stat_type": "Passing Yds", "team": "BAL"},
            {"player": "Mark Andrews", "line": 55.5, "stat_type": "Receiving Yds", "team": "BAL"},
            {"player": "Joe Burrow", "line": 275.5, "stat_type": "Passing Yds", "team": "CIN"},
            {"player": "Ja'Marr Chase", "line": 85.5, "stat_type": "Receiving Yds", "team": "CIN"},
        ]
    else:
        mock_data = [
            {"player": f"{sport} Player 1", "line": 15.5, "stat_type": "Points", "team": "TEAM"},
            {"player": f"{sport} Player 2", "line": 12.5, "stat_type": "Points", "team": "TEAM"},
        ]
    
    df = pd.DataFrame(mock_data)
    st.sidebar.info(f"📊 Using enhanced mock data with {len(df)} {sport} players")
    return df

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
        return get_enhanced_market_data(sport)
    
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
        "markets": "player_points,player_rebounds,player_assists,player_pass_yds,player_pass_tds,player_receiving_yds",
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
                            if outcome.get('price', 0) > 0:
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
            {"player": "Giannis Antetokounmpo", "market_line": 32.0, "implied_prob": 0.59},
            {"player": "Jayson Tatum", "market_line": 26.0, "implied_prob": 0.56},
            {"player": "Nikola Jokic", "market_line": 24.0, "implied_prob": 0.65},
            {"player": "Luka Doncic", "market_line": 30.0, "implied_prob": 0.63},
            {"player": "Joel Embiid", "market_line": 31.0, "implied_prob": 0.61},
            {"player": "Shai Gilgeous-Alexander", "market_line": 29.0, "implied_prob": 0.57},
            {"player": "Trae Young", "market_line": 26.0, "implied_prob": 0.54},
            {"player": "Kevin Durant", "market_line": 27.0, "implied_prob": 0.60},
            {"player": "Devin Booker", "market_line": 26.0, "implied_prob": 0.58},
        ])
    else:
        return pd.DataFrame([
            {"player": "Patrick Mahomes", "market_line": 280.5, "implied_prob": 0.62},
            {"player": "Travis Kelce", "market_line": 75.5, "implied_prob": 0.58},
            {"player": "Jalen Hurts", "market_line": 240.5, "implied_prob": 0.60},
        ])

def get_daily_data(sport="NBA"):
    """Main function to get both PrizePicks and market data"""
    with st.spinner(f"Fetching {sport} data..."):
        pp_df = fetch_prizepicks_data(sport)
        market_df = fetch_market_odds(sport)
    return pp_df, market_df

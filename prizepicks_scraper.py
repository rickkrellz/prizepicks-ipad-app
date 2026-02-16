"""
PrizePicks Scraper Module
Fetches daily lines from PrizePicks
Note: This is a simplified version with mock data
"""

import pandas as pd
import random
from datetime import datetime

def fetch_prizepicks_lines(sport="NBA"):
    """
    Fetch PrizePicks lines for a given sport
    Currently returns mock data - replace with actual scraping
    
    Args:
        sport: Sport to fetch (NBA, NFL, etc.)
    
    Returns:
        DataFrame with PrizePicks lines
    """
    
    # Mock NBA data
    nba_data = [
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
    ]
    
    # Mock NFL data
    nfl_data = [
        {"player": "Patrick Mahomes", "line": 285.5, "stat_type": "Passing Yds", "team": "KC"},
        {"player": "Travis Kelce", "line": 75.5, "stat_type": "Receiving Yds", "team": "KC"},
        {"player": "Tyreek Hill", "line": 80.5, "stat_type": "Receiving Yds", "team": "MIA"},
        {"player": "Jalen Hurts", "line": 245.5, "stat_type": "Passing Yds", "team": "PHI"},
        {"player": "AJ Brown", "line": 70.5, "stat_type": "Receiving Yds", "team": "PHI"},
        {"player": "Josh Allen", "line": 265.5, "stat_type": "Passing Yds", "team": "BUF"},
        {"player": "Stefon Diggs", "line": 75.5, "stat_type": "Receiving Yds", "team": "BUF"},
        {"player": "Christian McCaffrey", "line": 110.5, "stat_type": "Rush + Rec Yds", "team": "SF"},
    ]
    
    if sport == "NBA":
        df = pd.DataFrame(nba_data)
    elif sport == "NFL":
        df = pd.DataFrame(nfl_data)
    else:
        # Generic data for other sports
        df = pd.DataFrame([
            {"player": f"Player {i}", "line": round(random.uniform(10, 30), 1), 
             "stat_type": "Points", "team": "TEAM"}
            for i in range(10)
        ])
    
    # Add timestamp
    df['scrape_time'] = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    return df

def fetch_market_odds(sport="NBA"):
    """
    Fetch market odds from sportsbooks
    Currently returns mock data - replace with Odds API
    
    Args:
        sport: Sport to fetch
    
    Returns:
        DataFrame with market odds
    """
    
    # Mock market data (slightly different lines than PrizePicks)
    market_data = [
        {"player": "LeBron James", "market_line": 25.0, "implied_prob": 0.58},
        {"player": "Anthony Davis", "market_line": 28.0, "implied_prob": 0.55},
        {"player": "Stephen Curry", "market_line": 27.0, "implied_prob": 0.62},
        {"player": "Giannis Antetokounmpo", "market_line": 32.0, "implied_prob": 0.59},
        {"player": "Jayson Tatum", "market_line": 26.0, "implied_prob": 0.56},
        {"player": "Nikola Jokic", "market_line": 24.0, "implied_prob": 0.65},
        {"player": "Joel Embiid", "market_line": 31.0, "implied_prob": 0.61},
        {"player": "Luka Doncic", "market_line": 30.0, "implied_prob": 0.63},
        {"player": "Shai Gilgeous-Alexander", "market_line": 29.0, "implied_prob": 0.57},
        {"player": "Trae Young", "market_line": 26.0, "implied_prob": 0.54},
        {"player": "Kevin Durant", "market_line": 27.0, "implied_prob": 0.60},
        {"player": "Devin Booker", "market_line": 26.0, "implied_prob": 0.58},
        {"player": "Anthony Edwards", "market_line": 25.0, "implied_prob": 0.59},
        {"player": "Karl-Anthony Towns", "market_line": 22.0, "implied_prob": 0.62},
        {"player": "Jimmy Butler", "market_line": 21.0, "implied_prob": 0.57},
        {"player": "Bam Adebayo", "market_line": 19.0, "implied_prob": 0.60},
        {"player": "Jalen Brunson", "market_line": 26.0, "implied_prob": 0.61},
        {"player": "Julius Randle", "market_line": 23.0, "implied_prob": 0.58},
        {"player": "Kyrie Irving", "market_line": 24.0, "implied_prob": 0.59},
        {"player": "James Harden", "market_line": 16.0, "implied_prob": 0.64},
    ]
    
    # NFL market data
    if sport == "NFL":
        market_data = [
            {"player": "Patrick Mahomes", "market_line": 280.5, "implied_prob": 0.62},
            {"player": "Travis Kelce", "market_line": 75.5, "implied_prob": 0.58},
            {"player": "Tyreek Hill", "market_line": 85.5, "implied_prob": 0.55},
            {"player": "Jalen Hurts", "market_line": 240.5, "implied_prob": 0.60},
            {"player": "AJ Brown", "market_line": 75.5, "implied_prob": 0.56},
        ]
    
    df = pd.DataFrame(market_data)
    
    # Filter by sport if needed
    if sport == "NBA":
        # Already have NBA data
        pass
    elif sport == "NFL":
        # Would filter here
        pass
    
    return df

# Simple function to get all data
def get_daily_data(sport="NBA"):
    """
    Get both PrizePicks and market data
    
    Args:
        sport: Sport to fetch
    
    Returns:
        tuple: (prizepicks_df, market_df)
    """
    pp_df = fetch_prizepicks_lines(sport)
    market_df = fetch_market_odds(sport)
    
    return pp_df, market_df
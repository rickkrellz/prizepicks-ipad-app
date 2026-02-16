"""
Sports Configuration for PrizePicks Multi-Sport Support
Centralizes all sport IDs, stat types, and display names
"""

# PrizePicks League IDs (verified working)
PRIZEPICKS_LEAGUES = {
    # Major Sports - Currently Active
    "NBA": 7,           # Basketball - Active
    "NHL": 5,           # Hockey - Active
    "SOCCER": 10,       # Soccer - Active (Multiple leagues)
    "TENNIS": 11,       # Tennis - Active
    
    # Coming Soon (Seasonal)
    "MLB": 1,           # Baseball - Starts March
    "NFL": 2,           # Football - Starts September
    "WNBA": 8,          # Women's Basketball - Starts May
    "PGA": 6,           # Golf - Active but limited props
    "UFC": 15,          # MMA - Active
}

# Display Names for Dropdown (with emojis)
SPORT_DISPLAY_NAMES = {
    "NBA": "🏀 NBA Basketball",
    "NHL": "🏒 NHL Hockey",
    "SOCCER": "⚽ Soccer (All Leagues)",
    "TENNIS": "🎾 Tennis (ATP/WTA)",
    "MLB": "⚾ MLB Baseball (Coming March)",
    "NFL": "🏈 NFL Football (Coming Sept)",
    "WNBA": "🏀 WNBA Basketball (Coming May)",
    "PGA": "⛳ PGA Golf",
    "UFC": "🥊 UFC MMA",
}

# Stat Types by Sport
SPORT_STATS = {
    "NBA": ["Points", "Rebounds", "Assists", "PRA", "3PM", "BLK", "STL", "TO"],
    "NHL": ["Goals", "Assists", "Points", "Shots", "Hits", "Blocks"],
    "SOCCER": ["Goals", "Assists", "Shots", "Shots on Target", "Passes", "Tackles"],
    "TENNIS": ["Aces", "Double Faults", "Games Won", "Sets Won", "Total Games"],
    "MLB": ["Hits", "HRs", "RBIs", "Runs", "Strikeouts", "Total Bases"],
    "NFL": ["Pass Yds", "Rush Yds", "Rec Yds", "Pass TDs", "Fantasy Pts"],
    "WNBA": ["Points", "Rebounds", "Assists", "Steals", "Blocks"],
    "PGA": ["Birdies", "Pars", "Bogeys", "Total Strokes"],
    "UFC": ["Sig Strikes", "Takedowns", "Knockdowns", "Fight Time"],
}

# The Odds API Market Mappings
ODDS_API_MARKETS = {
    "NBA": "player_points,player_rebounds,player_assists,player_threes,player_blocks,player_steals",
    "NHL": "player_goals,player_assists,player_shots,player_hits",
    "SOCCER": "player_goals,player_assists,player_shots,player_passes",
    "TENNIS": "player_aces,player_double_faults,player_games_won",
    "MLB": "player_hits,player_homeruns,player_rbi,player_runs,player_strikeouts",
    "NFL": "player_pass_yds,player_pass_tds,player_rush_yds,player_rush_tds,player_receiving_yds",
    "WNBA": "player_points,player_rebounds,player_assists,player_steals,player_blocks",
}
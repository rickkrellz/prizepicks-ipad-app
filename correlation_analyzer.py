"""
Correlation Analyzer Module
Analyzes correlations between players to optimize parlays
"""

import pandas as pd
import numpy as np

def get_team_from_player(player_name):
    """
    Extract team from player name (simplified heuristic)
    You can expand this dictionary with more players
    """
    # Dictionary of player -> team mappings
    player_teams = {
        # Lakers
        "LeBron James": "LAL",
        "Anthony Davis": "LAL",
        "Austin Reaves": "LAL",
        "D'Angelo Russell": "LAL",
        
        # Warriors
        "Stephen Curry": "GSW",
        "Klay Thompson": "GSW",
        "Draymond Green": "GSW",
        "Andrew Wiggins": "GSW",
        
        # Bucks
        "Giannis Antetokounmpo": "MIL",
        "Damian Lillard": "MIL",
        "Khris Middleton": "MIL",
        "Brook Lopez": "MIL",
        
        # Celtics
        "Jayson Tatum": "BOS",
        "Jaylen Brown": "BOS",
        "Kristaps Porzingis": "BOS",
        "Jrue Holiday": "BOS",
        
        # Nuggets
        "Nikola Jokic": "DEN",
        "Jamal Murray": "DEN",
        "Michael Porter Jr.": "DEN",
        "Aaron Gordon": "DEN",
        
        # 76ers
        "Joel Embiid": "PHI",
        "Tyrese Maxey": "PHI",
        "Tobias Harris": "PHI",
        
        # Mavericks
        "Luka Doncic": "DAL",
        "Kyrie Irving": "DAL",
        "Tim Hardaway Jr.": "DAL",
        
        # Thunder
        "Shai Gilgeous-Alexander": "OKC",
        "Jalen Williams": "OKC",
        "Chet Holmgren": "OKC",
        
        # Hawks
        "Trae Young": "ATL",
        "Dejounte Murray": "ATL",
        "Jalen Johnson": "ATL",
        
        # Suns
        "Kevin Durant": "PHX",
        "Devin Booker": "PHX",
        "Bradley Beal": "PHX",
        
        # Clippers
        "Kawhi Leonard": "LAC",
        "Paul George": "LAC",
        "James Harden": "LAC",
        "Russell Westbrook": "LAC",
        
        # Timberwolves
        "Anthony Edwards": "MIN",
        "Karl-Anthony Towns": "MIN",
        "Rudy Gobert": "MIN",
        
        # Heat
        "Jimmy Butler": "MIA",
        "Bam Adebayo": "MIA",
        "Tyler Herro": "MIA",
        
        # Knicks
        "Jalen Brunson": "NYK",
        "Julius Randle": "NYK",
        "OG Anunoby": "NYK",
    }
    
    # Try exact match
    if player_name in player_teams:
        return player_teams[player_name]
    
    # Try partial match
    for name, team in player_teams.items():
        if name in player_name or player_name in name:
            return team
    
    return "OTHER"

def calculate_correlation_matrix(players_list):
    """
    Calculate correlation matrix for a list of players
    Uses heuristic based on team and position
    
    Args:
        players_list: List of player names
    
    Returns:
        DataFrame: Correlation matrix
    """
    n = len(players_list)
    
    # Create empty matrix with 1s on diagonal
    corr_matrix = pd.DataFrame(
        np.eye(n),
        index=players_list,
        columns=players_list
    )
    
    # Get teams for each player
    teams = {player: get_team_from_player(player) for player in players_list}
    
    # Fill correlation values
    for i in range(n):
        for j in range(i+1, n):
            player1 = players_list[i]
            player2 = players_list[j]
            
            # Same team -> negative correlation
            if teams[player1] == teams[player2] and teams[player1] != "OTHER":
                # Stronger negative for same team
                corr = -0.25
            # Different teams -> slight positive
            elif teams[player1] != "OTHER" and teams[player2] != "OTHER":
                corr = 0.10
            # Unknown team -> neutral
            else:
                corr = 0.0
            
            # Fill both sides of matrix
            corr_matrix.iloc[i, j] = corr
            corr_matrix.iloc[j, i] = corr
    
    return corr_matrix

def calculate_correlation_penalty(picks_df, weight=0.3):
    """
    Calculate penalty based on correlations
    
    Args:
        picks_df: DataFrame with selected picks
        weight: How much to weight correlations
    
    Returns:
        float: Penalty factor (0.7 to 1.3)
    """
    if len(picks_df) < 2:
        return 1.0
    
    players = picks_df['player'].tolist()
    corr_matrix = calculate_correlation_matrix(players)
    
    # Get all correlation pairs
    correlations = []
    for i in range(len(players)):
        for j in range(i+1, len(players)):
            corr = corr_matrix.iloc[i, j]
            correlations.append(corr)
    
    if not correlations:
        return 1.0
    
    # Average correlation
    avg_corr = np.mean(correlations)
    
    # Calculate penalty
    # Negative correlations -> reduce probability
    # Positive correlations -> increase probability
    penalty = 1.0 + (avg_corr * weight)
    
    # Bound the penalty
    return max(0.7, min(1.3, penalty))

def get_correlation_warning(picks_df):
    """Get warning message if correlations are bad"""
    if len(picks_df) < 2:
        return None
    
    players = picks_df['player'].tolist()
    teams = {player: get_team_from_player(player) for player in players}
    
    # Check for same-team pairs
    same_teams = []
    for i in range(len(players)):
        for j in range(i+1, len(players)):
            if teams[players[i]] == teams[players[j]] and teams[players[i]] != "OTHER":
                same_teams.append((players[i], players[j], teams[players[i]]))
    
    if same_teams:
        teams_str = ", ".join([f"{p1} & {p2} ({team})" for p1, p2, team in same_teams[:2]])
        return f"⚠️ Same team detected: {teams_str}. This reduces parlay chance."
    
    return None
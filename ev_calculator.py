"""
EV Calculator Module
Calculates Expected Value for PrizePicks props
"""

import pandas as pd
import numpy as np

def calculate_ev(prizepicks_df, market_df):
    """
    Calculate Expected Value for each prop
    
    Args:
        prizepicks_df: DataFrame with PrizePicks lines
        market_df: DataFrame with market odds
    
    Returns:
        DataFrame with EV calculations
    """
    if prizepicks_df.empty or market_df.empty:
        return pd.DataFrame()
    
    # Merge data on player name
    merged = pd.merge(
        prizepicks_df, 
        market_df, 
        on='player',
        how='inner'
    )
    
    if merged.empty:
        return pd.DataFrame()
    
    # Calculate EV for each prop
    def calculate_pick_ev(row):
        # PrizePicks assumes 50% probability
        pp_implied_prob = 0.5
        
        # Determine if Over or Under has value
        if row['line'] < row['market_line']:
            # PrizePicks line is lower -> Over is easier/better
            ev = row['implied_prob'] - pp_implied_prob
            direction = 'OVER'
        else:
            # PrizePicks line is higher -> Under is easier/better
            ev = (1 - row['implied_prob']) - pp_implied_prob
            direction = 'UNDER'
        
        return pd.Series({
            'ev': round(ev, 3),
            'direction': direction,
            'is_positive': ev > 0,
            'edge_amount': abs(row['line'] - row['market_line'])
        })
    
    # Apply calculation
    results = merged.apply(calculate_pick_ev, axis=1)
    merged = pd.concat([merged, results], axis=1)
    
    # Sort by EV (best first)
    merged = merged.sort_values('ev', ascending=False)
    
    return merged

def calculate_parlay_probability(picks_df):
    """
    Calculate probability of hitting all picks
    Assumes independence (simplified)
    
    Args:
        picks_df: DataFrame with selected picks
    
    Returns:
        float: Combined probability
    """
    if picks_df.empty:
        return 0.0
    
    probs = []
    for _, pick in picks_df.iterrows():
        if pick['direction'] == 'OVER':
            probs.append(pick['implied_prob'])
        else:
            probs.append(1 - pick['implied_prob'])
    
    # Multiply all probabilities
    combined_prob = np.prod(probs)
    
    return round(combined_prob, 4)

def get_value_grade(ev_value):
    """Convert EV to letter grade"""
    if ev_value >= 0.10:
        return "A+"
    elif ev_value >= 0.07:
        return "A"
    elif ev_value >= 0.05:
        return "B"
    elif ev_value >= 0.03:
        return "C"
    elif ev_value >= 0.01:
        return "D"
    else:
        return "F"
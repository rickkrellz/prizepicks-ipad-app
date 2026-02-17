"""
Arbitrage Scanner - Find risk-free betting opportunities
"""

import itertools
from decimal import Decimal, getcontext

getcontext().prec = 6

class ArbitrageScanner:
    def __init__(self):
        self.min_profit_pct = 0.01  # Minimum 1% profit to show
    
    def calculate_arbitrage(self, props, odds_key='implied_prob'):
        """
        Check for arbitrage opportunities between props
        """
        opportunities = []
        
        # Check all combinations of 2 props
        for prop1, prop2 in itertools.combinations(props, 2):
            # Skip same player
            if prop1['player'] == prop2['player']:
                continue
            
            # Calculate combined probability
            total_prob = prop1[odds_key] + prop2[odds_key]
            
            if total_prob < 1.0:
                profit_pct = (1 / total_prob - 1) * 100
                
                if profit_pct >= self.min_profit_pct:
                    # Calculate stakes
                    stake1 = (1 / total_prob) * prop1[odds_key]
                    stake2 = (1 / total_prob) * prop2[odds_key]
                    
                    opportunities.append({
                        'type': 'Two-way arb',
                        'players': f"{prop1['player']} vs {prop2['player']}",
                        'stats': f"{prop1['stat_type']} & {prop2['stat_type']}",
                        'profit_pct': round(profit_pct, 2),
                        'stakes': {
                            prop1['player']: round(stake1 * 100, 2),
                            prop2['player']: round(stake2 * 100, 2)
                        },
                        'total_stake': round((stake1 + stake2) * 100, 2),
                        'guaranteed_profit': round((1 / total_prob - 1) * 100, 2)
                    })
        
        # Check for 3-way arb (more complex, but possible)
        for prop1, prop2, prop3 in itertools.combinations(props, 3):
            # Skip same player
            if len({prop1['player'], prop2['player'], prop3['player']}) < 3:
                continue
            
            total_prob = prop1[odds_key] + prop2[odds_key] + prop3[odds_key]
            
            if total_prob < 1.0:
                profit_pct = (1 / total_prob - 1) * 100
                
                if profit_pct >= self.min_profit_pct:
                    opportunities.append({
                        'type': 'Three-way arb',
                        'players': f"{prop1['player']}, {prop2['player']}, {prop3['player']}",
                        'stats': f"{prop1['stat_type']}, {prop2['stat_type']}, {prop3['stat_type']}",
                        'profit_pct': round(profit_pct, 2),
                        'total_stake': 100,  # Placeholder - would need exact calculation
                        'guaranteed_profit': round(profit_pct, 2)
                    })
        
        return opportunities
    
    def find_correlation_arb(self, ev_data):
        """
        Find opportunities where negatively correlated props create value
        """
        opportunities = []
        
        # Group by game
        games = ev_data.groupby('game_id') if 'game_id' in ev_data.columns else []
        
        for _, game_props in games:
            # Find same-game props that are negatively correlated
            players = game_props['player'].unique()
            
            if len(players) >= 2:
                # Check opposing props (e.g., Player A OVER points, Player B UNDER)
                for player1 in players[:5]:
                    player1_props = game_props[game_props['player'] == player1]
                    
                    for player2 in players[1:5]:
                        if player1 == player2:
                            continue
                            
                        player2_props = game_props[game_props['player'] == player2]
                        
                        for p1 in player1_props.itertuples():
                            for p2 in player2_props.itertuples():
                                # Check if props are from same team
                                if p1.team == p2.team and p1.direction != p2.direction:
                                    # This could be a correlation play
                                    opportunities.append({
                                        'type': 'Same-game correlation',
                                        'players': f"{p1.player} & {p2.player}",
                                        'stats': f"{p1.stat_type} ({p1.direction}) & {p2.stat_type} ({p2.direction})",
                                        'ev': (p1.ev + p2.ev) / 2,
                                        'note': 'Negatively correlated - good parlay candidate'
                                    })
        
        return opportunities
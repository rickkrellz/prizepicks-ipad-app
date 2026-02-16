"""
Bankroll Manager - Kelly Criterion and stake calculations
"""

import math

class BankrollManager:
    def __init__(self, initial_bankroll=1000):
        self.bankroll = initial_bankroll
    
    def kelly_criterion(self, odds, edge, full_kelly=0.25):
        """
        Calculate optimal stake using Kelly Criterion
        odds: decimal odds (e.g., 2.0 for even money)
        edge: your edge (EV as decimal, e.g., 0.05 for 5%)
        full_kelly: fraction of Kelly to use (0.25 = quarter Kelly)
        """
        if odds <= 1 or edge <= 0:
            return 0
        
        # Convert edge to implied probability
        p = 0.5 + edge  # Simplified - in reality you'd use market implied prob
        
        # Kelly formula: (p * odds - 1) / (odds - 1)
        kelly = (p * odds - 1) / (odds - 1)
        
        # Apply fractional Kelly and ensure positive
        stake_pct = max(0, kelly * full_kelly)
        
        return stake_pct
    
    def calculate_stake(self, odds, edge, unit_size=0.01):
        """
        Calculate stake amount based on multiple methods
        Returns: stake amount, method used
        """
        methods = []
        
        # Method 1: Kelly Criterion
        kelly_pct = self.kelly_criterion(odds, edge)
        if kelly_pct > 0:
            methods.append(("Kelly", kelly_pct))
        
        # Method 2: Fixed percentage (1% of bankroll)
        methods.append(("Fixed 1%", unit_size))
        
        # Method 3: Confidence-based
        confidence_pct = edge * 2  # Scale edge to stake percentage
        methods.append(("Confidence", min(0.05, max(0.005, confidence_pct))))
        
        # Use the most conservative method
        recommended_pct = min([pct for _, pct in methods])
        recommended_amount = self.bankroll * recommended_pct
        
        return {
            "amount": round(recommended_amount, 2),
            "percentage": round(recommended_pct * 100, 2),
            "methods": {name: round(pct * 100, 2) for name, pct in methods}
        }
    
    def update_bankroll(self, stake, profit):
        """Update bankroll after bet settlement"""
        self.bankroll += profit
        return self.bankroll
    
    def get_bet_limits(self):
        """Get current betting limits based on bankroll"""
        return {
            "min_bet": max(1, self.bankroll * 0.001),
            "max_bet": self.bankroll * 0.05,
            "suggested_unit": self.bankroll * 0.01
        }
"""
Bump Detector - Identify lines at risk of being bumped
"""

class BumpDetector:
    def __init__(self):
        # PrizePicks bump thresholds
        self.bump_thresholds = {
            "standard": {
                "risk_levels": [
                    {"threshold": 1.71, "risk": "HIGH"},  # -140 or higher
                    {"threshold": 1.67, "risk": "MEDIUM"},  # -150
                    {"threshold": 1.59, "risk": "LOW"},    # -170
                ]
            }
        }
    
    def calculate_bump_risk(self, implied_prob):
        """
        Calculate risk of line being bumped
        implied_prob: market implied probability (0-1)
        """
        # Convert probability to decimal odds
        if implied_prob <= 0 or implied_prob >= 1:
            return {"risk": "UNKNOWN", "color": "gray"}
        
        decimal_odds = 1 / implied_prob
        
        # Determine risk level
        if decimal_odds <= 1.71:  # -140 or higher
            risk = "HIGH"
            color = "red"
        elif decimal_odds <= 1.77:  # -130 to -139
            risk = "MEDIUM"
            color = "orange"
        elif decimal_odds <= 1.85:  # -118 to -129
            risk = "LOW"
            color = "yellow"
        else:
            risk = "MINIMAL"
            color = "green"
        
        return {
            "risk": risk,
            "color": color,
            "decimal_odds": round(decimal_odds, 2),
            "american_odds": self.decimal_to_american(decimal_odds)
        }
    
    def decimal_to_american(self, decimal_odds):
        """Convert decimal odds to American format"""
        if decimal_odds >= 2.0:
            return f"+{int((decimal_odds - 1) * 100)}"
        else:
            return f"{int(-100 / (decimal_odds - 1))}"
    
    def get_bump_warning(self, ev_data, threshold=0.05):
        """Generate warnings for props at risk of bumping"""
        warnings = []
        
        for _, prop in ev_data.iterrows():
            if prop['implied_prob'] > 0.55:  # Only check if market thinks it's likely
                risk = self.calculate_bump_risk(prop['implied_prob'])
                
                if risk['risk'] in ["HIGH", "MEDIUM"]:
                    warnings.append({
                        'player': prop['player'],
                        'stat': prop['stat_type'],
                        'risk': risk['risk'],
                        'odds': risk['american_odds'],
                        'ev': f"{prop['ev']:.1%}",
                        'line': prop['line'],
                        'direction': prop['direction']
                    })
        
        return warnings
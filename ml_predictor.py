"""
AI Predictions Module - Machine Learning model for prop success prediction
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib
import streamlit as st
from datetime import datetime, timedelta
import requests

class MLPredictor:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = [
            'avg_points_last_5', 'avg_rebounds_last_5', 'avg_assists_last_5',
            'fg_percentage', 'minutes_played', 'opponent_defense_rating',
            'home_away', 'days_rest', 'previous_prop_success_rate',
            'line_value', 'market_consensus'
        ]
        self.load_model()
    
    def load_model(self):
        """Load trained model if exists"""
        try:
            self.model = joblib.load('prop_predictor_model.pkl')
            self.scaler = joblib.load('scaler.pkl')
        except:
            self.model = None
    
    def train_model(self, historical_data):
        """
        Train ML model on historical prop data
        historical_data should contain features and actual outcomes
        """
        if len(historical_data) < 100:
            return False
        
        # Prepare features and target
        X = historical_data[self.feature_columns]
        y = historical_data['result']  # 1 for success, 0 for failure
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate
        accuracy = self.model.score(X_test_scaled, y_test)
        
        # Save model
        joblib.dump(self.model, 'prop_predictor_model.pkl')
        joblib.dump(self.scaler, 'scaler.pkl')
        
        return accuracy
    
    def predict_prop_success(self, prop_features):
        """
        Predict probability of prop success
        prop_features: dict with feature values
        """
        if self.model is None:
            return 0.5  # Return 50% if no model trained
        
        # Create feature array
        features = np.array([[
            prop_features.get(f, 0) for f in self.feature_columns
        ]])
        
        # Scale features
        features_scaled = self.scaler.transform(features)
        
        # Predict probability
        prob = self.model.predict_proba(features_scaled)[0][1]
        
        return prob
    
    def get_ai_recommendation(self, prop, player_stats, market_data):
        """
        Get AI-powered recommendation for a prop
        """
        if self.model is None:
            return {
                'confidence': 'LOW',
                'prediction': None,
                'message': 'AI model not trained yet. Need more historical data.'
            }
        
        # Extract features
        features = {
            'avg_points_last_5': player_stats.get('avg_points', 0),
            'avg_rebounds_last_5': player_stats.get('avg_rebounds', 0),
            'avg_assists_last_5': player_stats.get('avg_assists', 0),
            'fg_percentage': player_stats.get('fg_pct', 0.45),
            'minutes_played': player_stats.get('minutes', 32),
            'opponent_defense_rating': market_data.get('opponent_defense', 110),
            'home_away': 1 if player_stats.get('is_home', True) else 0,
            'days_rest': player_stats.get('days_rest', 1),
            'previous_prop_success_rate': player_stats.get('prop_success_rate', 0.5),
            'line_value': prop.get('line', 20),
            'market_consensus': market_data.get('consensus_line', prop.get('line', 20))
        }
        
        # Get prediction
        prob = self.predict_prop_success(features)
        
        # Determine confidence
        if abs(prob - 0.5) > 0.2:
            confidence = 'HIGH'
        elif abs(prob - 0.5) > 0.1:
            confidence = 'MEDIUM'
        else:
            confidence = 'LOW'
        
        return {
            'confidence': confidence,
            'prediction': prob,
            'recommendation': 'OVER' if prob > 0.55 else 'UNDER' if prob < 0.45 else 'NEUTRAL',
            'message': f"AI predicts {prob:.1%} probability of success"
        }
    
    def generate_ai_picks(self, props_data, days_ahead=3):
        """
        Generate AI-powered pick recommendations for upcoming games
        """
        ai_picks = []
        
        for _, prop in props_data.iterrows():
            # Mock player stats (in reality, you'd fetch from database)
            player_stats = {
                'avg_points': prop.get('avg_points', 20),
                'avg_rebounds': prop.get('avg_rebounds', 5),
                'avg_assists': prop.get('avg_assists', 4),
                'minutes': 32,
                'is_home': True,
                'days_rest': 1,
                'prop_success_rate': 0.52
            }
            
            market_data = {
                'opponent_defense': 110,
                'consensus_line': prop.get('market_line', prop.get('line', 20))
            }
            
            ai_rec = self.get_ai_recommendation(prop, player_stats, market_data)
            
            if ai_rec['confidence'] in ['HIGH', 'MEDIUM']:
                ai_picks.append({
                    'player': prop['player'],
                    'stat': prop['stat_type'],
                    'line': prop['line'],
                    'recommendation': ai_rec['recommendation'],
                    'confidence': ai_rec['confidence'],
                    'probability': ai_rec['prediction'],
                    'ev': prop.get('ev', 0)
                })
        
        return pd.DataFrame(ai_picks)
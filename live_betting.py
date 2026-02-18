"""
Live Betting Module - Real-time in-game props and updates
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import random
import plotly.graph_objects as go
import threading

class LiveBettingManager:
    def __init__(self):
        self.live_games = {}
        self.active_props = {}
        self.update_thread = None
        self.is_running = False
    
    def start_live_updates(self):
        """Start background thread for live updates"""
        if not self.is_running:
            self.is_running = True
            self.update_thread = threading.Thread(target=self._update_loop)
            self.update_thread.daemon = True
            self.update_thread.start()
    
    def stop_live_updates(self):
        """Stop live updates"""
        self.is_running = False
    
    def _update_loop(self):
        """Background loop for live updates"""
        while self.is_running:
            self._fetch_live_data()
            time.sleep(30)  # Update every 30 seconds
    
    def _fetch_live_data(self):
        """Fetch live game data (mock implementation)"""
        # In production, connect to real-time data API
        for game_id in self.live_games:
            # Update scores and stats
            self.live_games[game_id]['score'] += random.randint(0, 2)
            self.live_games[game_id]['time_remaining'] -= 30
            
            # Update player props
            for player in self.live_games[game_id]['players']:
                for prop in player['props']:
                    # Simulate stat accumulation
                    prop['current'] += random.random() * 2
    
    def add_live_game(self, game_id, home_team, away_team, start_time):
        """Add a live game to track"""
        self.live_games[game_id] = {
            'home_team': home_team,
            'away_team': away_team,
            'score': '0-0',
            'time_remaining': 2880,  # 48 minutes in seconds
            'period': 1,
            'status': 'scheduled',
            'players': [],
            'start_time': start_time
        }
    
    def add_player_prop(self, game_id, player_name, stat_type, line, odds):
        """Add a player prop to track"""
        if game_id in self.live_games:
            player_prop = {
                'player': player_name,
                'stat_type': stat_type,
                'line': line,
                'odds': odds,
                'current': 0,
                'projected': 0,
                'status': 'pending'
            }
            
            # Find or create player entry
            for player in self.live_games[game_id]['players']:
                if player['name'] == player_name:
                    player['props'].append(player_prop)
                    break
            else:
                self.live_games[game_id]['players'].append({
                    'name': player_name,
                    'props': [player_prop]
                })
    
    def get_live_props(self, sport="NBA"):
        """Get all live props"""
        live_props = []
        
        for game_id, game in self.live_games.items():
            if game['status'] == 'live' or game['status'] == 'scheduled':
                for player in game['players']:
                    for prop in player['props']:
                        # Calculate projected stats
                        if game['time_remaining'] > 0:
                            pace = prop['current'] / (2880 - game['time_remaining']) * 2880
                            prop['projected'] = pace
                        
                        # Determine if likely to hit
                        if prop['current'] > prop['line']:
                            likelihood = 'HIGH'
                        elif prop['projected'] > prop['line']:
                            likelihood = 'MEDIUM'
                        else:
                            likelihood = 'LOW'
                        
                        live_props.append({
                            'game_id': game_id,
                            'matchup': f"{game['away_team']} @ {game['home_team']}",
                            'time': game['time_remaining'],
                            'period': game['period'],
                            'score': game['score'],
                            'player': prop['player'],
                            'stat': prop['stat_type'],
                            'line': prop['line'],
                            'current': round(prop['current'], 1),
                            'projected': round(prop['projected'], 1),
                            'remaining_needed': round(prop['line'] - prop['current'], 1),
                            'likelihood': likelihood,
                            'status': prop['status']
                        })
        
        return pd.DataFrame(live_props)
    
    def render_live_dashboard(self):
        """Render live betting dashboard"""
        st.subheader("🔥 Live Betting Dashboard")
        
        # Start/stop controls
        col1, col2 = st.columns(2)
        with col1:
            if st.button("▶️ Start Live Updates"):
                self.start_live_updates()
                st.success("Live updates started!")
        with col2:
            if st.button("⏹️ Stop Live Updates"):
                self.stop_live_updates()
                st.info("Live updates stopped")
        
        # Get live props
        live_df = self.get_live_props()
        
        if not live_df.empty:
            # Filter by status
            status_filter = st.selectbox("Filter by status", 
                ['All', 'High Likelihood', 'Medium Likelihood', 'Live', 'Scheduled'])
            
            if status_filter == 'High Likelihood':
                live_df = live_df[live_df['likelihood'] == 'HIGH']
            elif status_filter == 'Medium Likelihood':
                live_df = live_df[live_df['likelihood'] == 'MEDIUM']
            
            # Display live games
            for game_id in live_df['game_id'].unique():
                game_data = live_df[live_df['game_id'] == game_id]
                
                with st.expander(f"🎮 {game_data.iloc[0]['matchup']} - {game_data.iloc[0]['score']}", expanded=True):
                    # Game info
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Time Remaining", 
                                 f"{game_data.iloc[0]['time']//60}:{game_data.iloc[0]['time']%60:02d}")
                    with col2:
                        st.metric("Period", game_data.iloc[0]['period'])
                    with col3:
                        st.metric("Live Props", len(game_data))
                    with col4:
                        st.metric("Last Update", "30s ago")
                    
                    # Props table
                    display_cols = ['player', 'stat', 'line', 'current', 'projected', 
                                   'remaining_needed', 'likelihood']
                    display_df = game_data[display_cols].copy()
                    
                    # Color code likelihood
                    def color_likelihood(val):
                        colors = {
                            'HIGH': 'background-color: #4CAF50',
                            'MEDIUM': 'background-color: #FFC107',
                            'LOW': 'background-color: #F44336'
                        }
                        return colors.get(val, '')
                    
                    st.dataframe(
                        display_df.style.applymap(color_likelihood, subset=['likelihood']),
                        use_container_width=True,
                        height=300
                    )
                    
                    # Quick bet buttons
                    if st.button(f"⚡ Quick Bet - {game_data.iloc[0]['player']}", key=f"bet_{game_id}"):
                        st.info("Quick bet feature - would integrate with PrizePicks API")
        else:
            st.info("No live games currently available")
        
        # Live odds movement chart
        st.subheader("📈 Live Odds Movement")
        
        # Mock data for demonstration
        times = pd.date_range(end=datetime.now(), periods=20, freq='1min')
        mock_odds = [100 + i*2 + random.randint(-5, 5) for i in range(20)]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=times,
            y=mock_odds,
            mode='lines+markers',
            name='Live Odds'
        ))
        fig.add_hline(y=110, line_dash="dash", line_color="green", annotation_text="Current Line")
        fig.update_layout(
            title="Prop Odds Movement (Last 20 minutes)",
            xaxis_title="Time",
            yaxis_title="Odds",
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
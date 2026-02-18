"""
Public Leaderboard Module - Compete with other users
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sqlite3
import numpy as np

class PublicLeaderboard:
    def __init__(self, bet_tracker, multi_user_manager):
        self.bet_tracker = bet_tracker
        self.multi_user = multi_user_manager
        self.conn = sqlite3.connect('leaderboard.db', check_same_thread=False)
        self.create_tables()
    
    def create_tables(self):
        """Create leaderboard tables"""
        cursor = self.conn.cursor()
        
        # Leaderboard rankings (cached for performance)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leaderboard_cache (
                rank INTEGER,
                user_id TEXT,
                display_name TEXT,
                total_profit REAL,
                roi REAL,
                win_rate REAL,
                total_bets INTEGER,
                best_streak INTEGER,
                avg_odds REAL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                period TEXT,
                PRIMARY KEY (user_id, period)
            )
        ''')
        
        # Leaderboard history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leaderboard_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                user_id TEXT,
                rank INTEGER,
                profit REAL,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # User achievements
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS achievements (
                achievement_id TEXT PRIMARY KEY,
                name TEXT,
                description TEXT,
                icon TEXT,
                criteria TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # User earned achievements
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_achievements (
                user_id TEXT,
                achievement_id TEXT,
                earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, achievement_id)
            )
        ''')
        
        self.insert_default_achievements()
        self.conn.commit()
    
    def insert_default_achievements(self):
        """Insert default achievements"""
        cursor = self.conn.cursor()
        
        achievements = [
            ('first_bet', 'First Bet', 'Place your first bet', '🎯', 'bets>=1'),
            ('win_streak_5', 'On Fire!', 'Win 5 bets in a row', '🔥', 'streak>=5'),
            ('win_streak_10', 'Unstoppable', 'Win 10 bets in a row', '⚡', 'streak>=10'),
            ('profit_100', 'Three Figures', 'Reach $100 profit', '💰', 'profit>=100'),
            ('profit_1000', 'Four Figures', 'Reach $1,000 profit', '💎', 'profit>=1000'),
            ('profit_10000', 'High Roller', 'Reach $10,000 profit', '👑', 'profit>=10000'),
            ('bets_100', 'Veteran', 'Place 100 bets', '🏆', 'bets>=100'),
            ('roi_20', 'Sharp Bettor', 'Maintain 20% ROI', '📈', 'roi>=20'),
            ('roi_50', 'Elite', 'Maintain 50% ROI', '⭐', 'roi>=50'),
            ('arb_finder', 'Arbitrage Master', 'Find your first arbitrage', '🔄', 'arb>=1'),
        ]
        
        for ach in achievements:
            cursor.execute('''
                INSERT OR IGNORE INTO achievements (achievement_id, name, description, icon, criteria)
                VALUES (?, ?, ?, ?, ?)
            ''', ach)
        
        self.conn.commit()
    
    def update_leaderboard(self, period='all_time'):
        """Update leaderboard cache"""
        cursor = self.conn.cursor()
        
        # Get all users with stats
        users = self.multi_user.get_all_users()
        
        rankings = []
        for user in users:
            user_id, username, email, created, last_login, bankroll, total_bets, total_profit = user
            
            # Calculate additional stats
            cursor.execute('''
                SELECT COUNT(*) as total, 
                       SUM(CASE WHEN outcome = 'Win' THEN 1 ELSE 0 END) as wins,
                       AVG(odds) as avg_odds
                FROM bets WHERE user_id = ?
            ''', (user_id,))
            
            bet_stats = cursor.fetchone()
            total_bets = bet_stats[0] or 0
            wins = bet_stats[1] or 0
            avg_odds = bet_stats[2] or 0
            
            win_rate = (wins / total_bets * 100) if total_bets > 0 else 0
            roi = (total_profit / (total_bets * 100) * 100) if total_bets > 0 else 0
            
            # Get best streak
            cursor.execute('''
                SELECT best_streak FROM user_stats WHERE user_id = ?
            ''', (user_id,))
            streak_result = cursor.fetchone()
            best_streak = streak_result[0] if streak_result else 0
            
            rankings.append({
                'user_id': user_id,
                'display_name': username,
                'total_profit': total_profit,
                'roi': roi,
                'win_rate': win_rate,
                'total_bets': total_bets,
                'best_streak': best_streak,
                'avg_odds': avg_odds
            })
        
        # Sort by profit
        rankings.sort(key=lambda x: x['total_profit'], reverse=True)
        
        # Insert into cache
        for rank, user in enumerate(rankings, 1):
            cursor.execute('''
                INSERT OR REPLACE INTO leaderboard_cache 
                (rank, user_id, display_name, total_profit, roi, win_rate, total_bets, best_streak, avg_odds, period)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                rank, user['user_id'], user['display_name'], 
                user['total_profit'], user['roi'], user['win_rate'],
                user['total_bets'], user['best_streak'], user['avg_odds'],
                period
            ))
        
        self.conn.commit()
    
    def get_leaderboard(self, period='all_time', limit=100):
        """Get current leaderboard"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT rank, display_name, total_profit, roi, win_rate, total_bets, best_streak
            FROM leaderboard_cache
            WHERE period = ?
            ORDER BY rank
            LIMIT ?
        ''', (period, limit))
        
        results = cursor.fetchall()
        
        if results:
            df = pd.DataFrame(results, columns=[
                'Rank', 'User', 'Profit', 'ROI %', 'Win Rate %', 'Bets', 'Best Streak'
            ])
            return df
        return pd.DataFrame()
    
    def check_achievements(self, user_id):
        """Check and award achievements for a user"""
        cursor = self.conn.cursor()
        
        # Get user stats
        cursor.execute('''
            SELECT total_bets, total_profit, best_streak FROM user_stats WHERE user_id = ?
        ''', (user_id,))
        
        stats = cursor.fetchone()
        if not stats:
            return []
        
        total_bets, total_profit, best_streak = stats
        
        # Get all achievements
        cursor.execute('SELECT achievement_id, criteria FROM achievements')
        achievements = cursor.fetchall()
        
        new_achievements = []
        
        for ach_id, criteria in achievements:
            # Check if already earned
            cursor.execute('''
                SELECT 1 FROM user_achievements 
                WHERE user_id = ? AND achievement_id = ?
            ''', (user_id, ach_id))
            
            if cursor.fetchone():
                continue
            
            # Parse criteria
            earned = False
            if 'bets>=' in criteria:
                threshold = int(criteria.split('>=')[1])
                earned = total_bets >= threshold
            elif 'profit>=' in criteria:
                threshold = int(criteria.split('>=')[1])
                earned = total_profit >= threshold
            elif 'streak>=' in criteria:
                threshold = int(criteria.split('>=')[1])
                earned = best_streak >= threshold
            
            if earned:
                cursor.execute('''
                    INSERT INTO user_achievements (user_id, achievement_id)
                    VALUES (?, ?)
                ''', (user_id, ach_id))
                new_achievements.append(ach_id)
        
        self.conn.commit()
        return new_achievements
    
    def get_user_achievements(self, user_id):
        """Get achievements earned by user"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT a.icon, a.name, a.description, ua.earned_at
            FROM user_achievements ua
            JOIN achievements a ON ua.achievement_id = a.achievement_id
            WHERE ua.user_id = ?
            ORDER BY ua.earned_at DESC
        ''', (user_id,))
        
        results = cursor.fetchall()
        
        achievements = []
        for icon, name, desc, earned_at in results:
            achievements.append({
                'icon': icon,
                'name': name,
                'description': desc,
                'earned_at': earned_at
            })
        
        return achievements
    
    def render_leaderboard(self):
        """Render public leaderboard"""
        st.subheader("🏆 Public Leaderboard")
        
        # Period selector
        period = st.selectbox(
            "Time Period",
            ['All Time', 'This Month', 'This Week', 'Today'],
            index=0
        )
        
        period_map = {
            'All Time': 'all_time',
            'This Month': 'month',
            'This Week': 'week',
            'Today': 'day'
        }
        
        # Update leaderboard
        self.update_leaderboard(period_map[period])
        
        # Get leaderboard data
        leaderboard_df = self.get_leaderboard(period_map[period])
        
        if not leaderboard_df.empty:
            # Format columns
            leaderboard_df['Profit'] = leaderboard_df['Profit'].apply(lambda x: f"${x:,.2f}")
            leaderboard_df['ROI %'] = leaderboard_df['ROI %'].apply(lambda x: f"{x:.1f}%")
            leaderboard_df['Win Rate %'] = leaderboard_df['Win Rate %'].apply(lambda x: f"{x:.1f}%")
            
            # Add medals for top 3
            def add_rank_emoji(rank):
                if rank == 1:
                    return "🥇 1"
                elif rank == 2:
                    return "🥈 2"
                elif rank == 3:
                    return "🥉 3"
                return str(rank)
            
            leaderboard_df['Rank'] = leaderboard_df['Rank'].apply(add_rank_emoji)
            
            # Display leaderboard
            st.dataframe(
                leaderboard_df.set_index('Rank'),
                use_container_width=True,
                height=500
            )
            
            # Top 3 podium
            if len(leaderboard_df) >= 3:
                st.subheader("🏆 Top Performers")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown(f"""
                    <div style="text-align: center; padding: 20px;">
                        <div style="font-size: 48px;">🥈</div>
                        <div style="font-size: 20px; font-weight: bold;">{leaderboard_df.iloc[1]['User']}</div>
                        <div>${float(leaderboard_df.iloc[1]['Profit'][1:].replace(',','')):,.2f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%); border-radius: 10px;">
                        <div style="font-size: 48px;">🥇</div>
                        <div style="font-size: 24px; font-weight: bold;">{leaderboard_df.iloc[0]['User']}</div>
                        <div style="font-size: 18px;">${float(leaderboard_df.iloc[0]['Profit'][1:].replace(',','')):,.2f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f"""
                    <div style="text-align: center; padding: 20px;">
                        <div style="font-size: 48px;">🥉</div>
                        <div style="font-size: 20px; font-weight: bold;">{leaderboard_df.iloc[2]['User']}</div>
                        <div>${float(leaderboard_df.iloc[2]['Profit'][1:].replace(',','')):,.2f}</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Stats
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Players", len(leaderboard_df))
            with col2:
                total_profit = leaderboard_df['Profit'].apply(
                    lambda x: float(x[1:].replace(',', ''))
                ).sum()
                st.metric("Total Profit", f"${total_profit:,.2f}")
            with col3:
                avg_roi = leaderboard_df['ROI %'].apply(
                    lambda x: float(x[:-1])
                ).mean()
                st.metric("Average ROI", f"{avg_roi:.1f}%")
            with col4:
                avg_win_rate = leaderboard_df['Win Rate %'].apply(
                    lambda x: float(x[:-1])
                ).mean()
                st.metric("Avg Win Rate", f"{avg_win_rate:.1f}%")
        else:
            st.info("No leaderboard data available yet")
    
    def render_achievements(self, user_id):
        """Render user achievements"""
        st.subheader("🏅 Your Achievements")
        
        achievements = self.get_user_achievements(user_id)
        
        if achievements:
            # Display in a grid
            cols = st.columns(3)
            for idx, ach in enumerate(achievements):
                with cols[idx % 3]:
                    st.markdown(f"""
                    <div style="
                        border: 1px solid #4CAF50;
                        border-radius: 10px;
                        padding: 15px;
                        margin: 5px;
                        text-align: center;
                        background: linear-gradient(135deg, #f5f5f5 0%, #ffffff 100%);
                    ">
                        <div style="font-size: 36px;">{ach['icon']}</div>
                        <div style="font-weight: bold;">{ach['name']}</div>
                        <div style="font-size: 12px; color: #666;">{ach['description']}</div>
                        <div style="font-size: 10px; color: #999; margin-top: 5px;">{ach['earned_at'][:10]}</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No achievements earned yet. Start betting to earn achievements!")
    
    def render_user_profile(self, username):
        """Render public user profile"""
        # Get user data
        users = self.multi_user.get_all_users()
        user_data = None
        
        for user in users:
            if user[1] == username:  # username match
                user_data = user
                break
        
        if user_data:
            user_id, username, email, created, last_login, bankroll, total_bets, total_profit = user_data
            
            st.subheader(f"👤 {username}'s Profile")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Member Since", created[:10])
            with col2:
                st.metric("Total Bets", total_bets)
            with col3:
                st.metric("Total Profit", f"${total_profit:.2f}")
            with col4:
                roi = (total_profit / (total_bets * 100) * 100) if total_bets > 0 else 0
                st.metric("ROI", f"{roi:.1f}%")
            
            # Show achievements
            self.render_achievements(user_id)
        else:
            st.error("User not found")
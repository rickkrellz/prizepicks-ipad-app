"""
Multi-User Support Module - Track multiple users/bankrolls
"""

import sqlite3
import pandas as pd
import streamlit as st
from datetime import datetime
import hashlib
import uuid

class MultiUserManager:
    def __init__(self):
        self.conn = sqlite3.connect('multi_user.db', check_same_thread=False)
        self.create_tables()
        self.current_user = None
    
    def create_tables(self):
        """Create user management tables"""
        cursor = self.conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT UNIQUE,
                email TEXT UNIQUE,
                password_hash TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # User profiles
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id TEXT PRIMARY KEY,
                display_name TEXT,
                avatar_url TEXT,
                bio TEXT,
                bankroll REAL DEFAULT 1000,
                units REAL DEFAULT 10,
                risk_profile TEXT DEFAULT 'moderate',
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # User statistics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_stats (
                user_id TEXT PRIMARY KEY,
                total_bets INTEGER DEFAULT 0,
                winning_bets INTEGER DEFAULT 0,
                total_profit REAL DEFAULT 0,
                roi REAL DEFAULT 0,
                best_streak INTEGER DEFAULT 0,
                worst_streak INTEGER DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # User settings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id TEXT PRIMARY KEY,
                theme TEXT DEFAULT 'light',
                notifications BOOLEAN DEFAULT 1,
                default_sport TEXT DEFAULT 'NBA',
                default_ev_threshold REAL DEFAULT 0.05,
                default_parlay_size INTEGER DEFAULT 6,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # User sessions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT,
                login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                logout_time TIMESTAMP,
                ip_address TEXT,
                device_info TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        self.conn.commit()
    
    def hash_password(self, password):
        """Hash password for storage"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_user(self, username, email, password, display_name=None):
        """Create a new user account"""
        cursor = self.conn.cursor()
        user_id = str(uuid.uuid4())
        password_hash = self.hash_password(password)
        
        try:
            # Insert user
            cursor.execute('''
                INSERT INTO users (user_id, username, email, password_hash)
                VALUES (?, ?, ?, ?)
            ''', (user_id, username, email, password_hash))
            
            # Create profile
            cursor.execute('''
                INSERT INTO user_profiles (user_id, display_name)
                VALUES (?, ?)
            ''', (user_id, display_name or username))
            
            # Create stats
            cursor.execute('''
                INSERT INTO user_stats (user_id)
                VALUES (?)
            ''', (user_id,))
            
            # Create settings
            cursor.execute('''
                INSERT INTO user_settings (user_id)
                VALUES (?)
            ''', (user_id,))
            
            self.conn.commit()
            return user_id
        except sqlite3.IntegrityError:
            return None
    
    def authenticate_user(self, username_or_email, password):
        """Authenticate a user"""
        cursor = self.conn.cursor()
        password_hash = self.hash_password(password)
        
        cursor.execute('''
            SELECT user_id, username, email FROM users 
            WHERE (username = ? OR email = ?) AND password_hash = ? AND is_active = 1
        ''', (username_or_email, username_or_email, password_hash))
        
        result = cursor.fetchone()
        
        if result:
            user_id = result[0]
            # Update last login
            cursor.execute('''
                UPDATE users SET last_login = ? WHERE user_id = ?
            ''', (datetime.now().isoformat(), user_id))
            self.conn.commit()
            
            return {
                'user_id': user_id,
                'username': result[1],
                'email': result[2]
            }
        return None
    
    def create_session(self, user_id, ip_address=None, device_info=None):
        """Create a new session for logged-in user"""
        cursor = self.conn.cursor()
        session_id = str(uuid.uuid4())
        
        cursor.execute('''
            INSERT INTO user_sessions (session_id, user_id, ip_address, device_info)
            VALUES (?, ?, ?, ?)
        ''', (session_id, user_id, ip_address, device_info))
        
        self.conn.commit()
        return session_id
    
    def end_session(self, session_id):
        """End a user session"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE user_sessions SET logout_time = ? WHERE session_id = ?
        ''', (datetime.now().isoformat(), session_id))
        self.conn.commit()
    
    def get_user_profile(self, user_id):
        """Get complete user profile"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT u.username, u.email, u.created_at, u.last_login,
                   p.display_name, p.avatar_url, p.bio, p.bankroll, p.units, p.risk_profile,
                   s.total_bets, s.winning_bets, s.total_profit, s.roi, s.best_streak,
                   st.theme, st.notifications, st.default_sport, st.default_ev_threshold
            FROM users u
            JOIN user_profiles p ON u.user_id = p.user_id
            JOIN user_stats s ON u.user_id = s.user_id
            JOIN user_settings st ON u.user_id = st.user_id
            WHERE u.user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        
        if result:
            return {
                'username': result[0],
                'email': result[1],
                'created_at': result[2],
                'last_login': result[3],
                'display_name': result[4],
                'avatar_url': result[5],
                'bio': result[6],
                'bankroll': result[7],
                'units': result[8],
                'risk_profile': result[9],
                'stats': {
                    'total_bets': result[10],
                    'winning_bets': result[11],
                    'total_profit': result[12],
                    'roi': result[13],
                    'best_streak': result[14]
                },
                'settings': {
                    'theme': result[15],
                    'notifications': bool(result[16]),
                    'default_sport': result[17],
                    'default_ev_threshold': result[18]
                }
            }
        return None
    
    def update_user_stats(self, user_id, bet_result):
        """Update user statistics after a bet"""
        cursor = self.conn.cursor()
        
        # Get current stats
        cursor.execute('''
            SELECT total_bets, winning_bets, total_profit, best_streak, worst_streak
            FROM user_stats WHERE user_id = ?
        ''', (user_id,))
        
        current = cursor.fetchone()
        
        if current:
            total_bets = current[0] + 1
            winning_bets = current[1] + (1 if bet_result['win'] else 0)
            total_profit = current[2] + bet_result['profit']
            roi = (total_profit / (total_bets * 100)) * 100 if total_bets > 0 else 0
            
            # Update streak
            if 'streak' in bet_result:
                best_streak = max(current[3], bet_result['streak'])
                worst_streak = min(current[4], bet_result['streak'])
            else:
                best_streak = current[3]
                worst_streak = current[4]
            
            cursor.execute('''
                UPDATE user_stats 
                SET total_bets = ?, winning_bets = ?, total_profit = ?, 
                    roi = ?, best_streak = ?, worst_streak = ?, updated_at = ?
                WHERE user_id = ?
            ''', (total_bets, winning_bets, total_profit, roi, 
                  best_streak, worst_streak, datetime.now().isoformat(), user_id))
            
            self.conn.commit()
    
    def update_settings(self, user_id, settings):
        """Update user settings"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            UPDATE user_settings 
            SET theme = ?, notifications = ?, default_sport = ?, default_ev_threshold = ?
            WHERE user_id = ?
        ''', (
            settings.get('theme', 'light'),
            settings.get('notifications', True),
            settings.get('default_sport', 'NBA'),
            settings.get('default_ev_threshold', 0.05),
            user_id
        ))
        
        self.conn.commit()
    
    def update_profile(self, user_id, profile_data):
        """Update user profile"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            UPDATE user_profiles 
            SET display_name = ?, bio = ?, bankroll = ?, units = ?, risk_profile = ?
            WHERE user_id = ?
        ''', (
            profile_data.get('display_name', ''),
            profile_data.get('bio', ''),
            profile_data.get('bankroll', 1000),
            profile_data.get('units', 10),
            profile_data.get('risk_profile', 'moderate'),
            user_id
        ))
        
        self.conn.commit()
    
    def get_all_users(self):
        """Get list of all users (admin function)"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT u.user_id, u.username, u.email, u.created_at, u.last_login,
                   p.bankroll, s.total_bets, s.total_profit
            FROM users u
            JOIN user_profiles p ON u.user_id = p.user_id
            JOIN user_stats s ON u.user_id = s.user_id
            WHERE u.is_active = 1
            ORDER BY s.total_profit DESC
        ''')
        
        return cursor.fetchall()
    
    def get_leaderboard(self, limit=50):
        """Get user leaderboard by profit"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT p.display_name, s.total_profit, s.roi, s.total_bets, s.winning_bets
            FROM user_stats s
            JOIN user_profiles p ON s.user_id = p.user_id
            ORDER BY s.total_profit DESC
            LIMIT ?
        ''', (limit,))
        
        return cursor.fetchall()
"""
Push Notifications Module - Real iOS push notifications
"""

import streamlit as st
import requests
import json
from datetime import datetime
import sqlite3

class PushNotificationManager:
    def __init__(self):
        self.conn = sqlite3.connect('notifications.db', check_same_thread=False)
        self.create_tables()
        # For production, use actual Firebase or OneSignal credentials
        self.onesignal_app_id = "YOUR_ONESIGNAL_APP_ID"
        self.onesignal_api_key = "YOUR_ONESIGNAL_API_KEY"
    
    def create_tables(self):
        """Create notification tables"""
        cursor = self.conn.cursor()
        
        # Device tokens table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS device_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                device_token TEXT UNIQUE,
                device_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Notification history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notification_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                title TEXT,
                message TEXT,
                data TEXT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # User notification preferences
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notification_preferences (
                user_id TEXT PRIMARY KEY,
                new_picks BOOLEAN DEFAULT 1,
                bump_alerts BOOLEAN DEFAULT 1,
                arbitrage_alerts BOOLEAN DEFAULT 1,
                daily_summary BOOLEAN DEFAULT 1,
                ev_threshold REAL DEFAULT 0.05
            )
        ''')
        
        self.conn.commit()
    
    def register_device(self, user_id, device_token, device_type='ios'):
        """Register a device for push notifications"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO device_tokens (user_id, device_token, device_type)
            VALUES (?, ?, ?)
        ''', (user_id, device_token, device_type))
        self.conn.commit()
    
    def unregister_device(self, device_token):
        """Remove device from notifications"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM device_tokens WHERE device_token = ?', (device_token,))
        self.conn.commit()
    
    def send_notification(self, user_id, title, message, data=None):
        """
        Send push notification to a specific user
        """
        cursor = self.conn.cursor()
        cursor.execute('SELECT device_token FROM device_tokens WHERE user_id = ?', (user_id,))
        tokens = cursor.fetchall()
        
        for (token,) in tokens:
            self.send_onesignal_notification(token, title, message, data)
        
        # Log notification
        cursor.execute('''
            INSERT INTO notification_history (user_id, title, message, data)
            VALUES (?, ?, ?, ?)
        ''', (user_id, title, message, json.dumps(data) if data else None))
        self.conn.commit()
    
    def send_to_all(self, title, message, data=None, filter_criteria=None):
        """
        Send notification to all users (or filtered)
        """
        cursor = self.conn.cursor()
        
        if filter_criteria:
            # Apply filters based on preferences
            query = '''
                SELECT t.device_token, t.user_id 
                FROM device_tokens t
                JOIN notification_preferences p ON t.user_id = p.user_id
                WHERE {}
            '''.format(filter_criteria)
        else:
            query = 'SELECT device_token, user_id FROM device_tokens'
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        for token, user_id in results:
            self.send_onesignal_notification(token, title, message, data)
            
            # Log notification
            cursor.execute('''
                INSERT INTO notification_history (user_id, title, message, data)
                VALUES (?, ?, ?, ?)
            ''', (user_id, title, message, json.dumps(data) if data else None))
        
        self.conn.commit()
    
    def send_onesignal_notification(self, device_token, title, message, data=None):
        """
        Send notification via OneSignal (or Firebase)
        This is a mock implementation - replace with actual API calls
        """
        # Mock implementation - in production, use actual OneSignal API
        st.success(f"🔔 [MOCK] Push notification sent: {title} - {message}")
        
        # Actual OneSignal API call would look like:
        """
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Basic {self.onesignal_api_key}'
        }
        
        payload = {
            'app_id': self.onesignal_app_id,
            'include_player_ids': [device_token],
            'headings': {'en': title},
            'contents': {'en': message},
            'data': data or {}
        }
        
        response = requests.post(
            'https://onesignal.com/api/v1/notifications',
            headers=headers,
            json=payload
        )
        """
    
    def get_user_preferences(self, user_id):
        """Get notification preferences for a user"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM notification_preferences WHERE user_id = ?
        ''', (user_id,))
        result = cursor.fetchone()
        
        if result:
            return {
                'new_picks': bool(result[1]),
                'bump_alerts': bool(result[2]),
                'arbitrage_alerts': bool(result[3]),
                'daily_summary': bool(result[4]),
                'ev_threshold': result[5]
            }
        else:
            # Default preferences
            return {
                'new_picks': True,
                'bump_alerts': True,
                'arbitrage_alerts': True,
                'daily_summary': True,
                'ev_threshold': 0.05
            }
    
    def update_preferences(self, user_id, preferences):
        """Update user notification preferences"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO notification_preferences 
            (user_id, new_picks, bump_alerts, arbitrage_alerts, daily_summary, ev_threshold)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            preferences.get('new_picks', True),
            preferences.get('bump_alerts', True),
            preferences.get('arbitrage_alerts', True),
            preferences.get('daily_summary', True),
            preferences.get('ev_threshold', 0.05)
        ))
        self.conn.commit()
    
    def send_bump_alert(self, user_id, prop_data):
        """Send alert for high bump risk props"""
        title = "⚠️ Bump Risk Alert"
        message = f"{prop_data['player']} {prop_data['stat']} at {prop_data['risk']} risk of moving"
        self.send_notification(user_id, title, message, prop_data)
    
    def send_new_pick_alert(self, user_id, pick_data):
        """Send alert for new +EV picks"""
        title = "🎯 New +EV Pick Found!"
        message = f"{pick_data['player']} {pick_data['stat']} EV: {pick_data['ev']:.1%}"
        self.send_notification(user_id, title, message, pick_data)
    
    def send_daily_summary(self, user_id):
        """Send daily summary of opportunities"""
        title = "📊 Your Daily Betting Summary"
        message = "Check out today's top +EV picks and opportunities"
        self.send_notification(user_id, title, message)
    
    def get_notification_history(self, user_id, days=7):
        """Get notification history for a user"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM notification_history 
            WHERE user_id = ? AND sent_at >= datetime('now', '-' || ? || ' days')
            ORDER BY sent_at DESC
        ''', (user_id, days))
        
        return cursor.fetchall()
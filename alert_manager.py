"""
Alert Manager - Smart notification system for +EV opportunities
"""

import sqlite3
import smtplib
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st

class AlertManager:
    def __init__(self):
        self.settings = {
            'sports': ['NBA'],
            'threshold': 0.05,
            'frequency': 'Instant',
            'methods': ['In-App'],
            'email': '',
            'push_token': ''
        }
        self.conn = sqlite3.connect('betting_history.db', check_same_thread=False)
        self.create_tables()
    
    def create_tables(self):
        """Create alert tables if they don't exist"""
        cursor = self.conn.cursor()
        
        # Custom alerts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS custom_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player TEXT,
                stat_type TEXT,
                condition TEXT,
                threshold REAL,
                expiry TEXT,
                active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Alert history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alert_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_type TEXT,
                sport TEXT,
                player TEXT,
                stat_type TEXT,
                value REAL,
                message TEXT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
    
    def update_settings(self, settings):
        """Update alert settings"""
        self.settings.update(settings)
        # Save to database
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO settings (key, value)
            VALUES (?, ?)
        ''', ('alert_settings', str(self.settings)))
        self.conn.commit()
    
    def add_custom_alert(self, player=None, stat_type=None, condition=None, 
                        threshold=0.05, expiry=None):
        """Add a custom alert rule"""
        cursor = self.conn.cursor()
        if expiry is None:
            expiry = (datetime.now() + timedelta(days=30)).isoformat()
        elif isinstance(expiry, datetime):
            expiry = expiry.isoformat()
        
        cursor.execute('''
            INSERT INTO custom_alerts 
            (player, stat_type, condition, threshold, expiry, active)
            VALUES (?, ?, ?, ?, ?, 1)
        ''', (player, stat_type, condition, threshold, expiry))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def get_active_alerts(self):
        """Get all active custom alerts"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM custom_alerts 
            WHERE active = 1 AND date(expiry) >= date('now')
            ORDER BY created_at DESC
        ''')
        
        alerts = cursor.fetchall()
        return [{
            'id': a[0],
            'player': a[1],
            'stat_type': a[2],
            'condition': a[3],
            'threshold': a[4],
            'expiry': a[5],
            'created_at': a[7]
        } for a in alerts]
    
    def check_alerts(self, ev_data):
        """Check if any props trigger active alerts"""
        triggered = []
        
        if ev_data.empty:
            return triggered
        
        active_alerts = self.get_active_alerts()
        
        for alert in active_alerts:
            # Filter data based on alert criteria
            filtered = ev_data.copy()
            
            if alert['player']:
                filtered = filtered[filtered['player'] == alert['player']]
            
            if alert['stat_type']:
                filtered = filtered[filtered['stat_type'] == alert['stat_type']]
            
            if alert['condition'] and alert['condition'] != 'Any':
                if alert['condition'] == 'OVER':
                    filtered = filtered[filtered['direction'] == 'OVER']
                elif alert['condition'] == 'UNDER':
                    filtered = filtered[filtered['direction'] == 'UNDER']
            
            # Check threshold
            if alert['threshold']:
                filtered = filtered[filtered['ev'] >= alert['threshold']]
            
            # Record triggered alerts
            for _, prop in filtered.iterrows():
                triggered.append({
                    'alert_id': alert['id'],
                    'player': prop['player'],
                    'stat_type': prop['stat_type'],
                    'ev': prop['ev'],
                    'message': f"{prop['player']} {prop['stat_type']} EV: {prop['ev']:.1%}"
                })
                
                # Log to history
                self.log_alert('custom', prop['sport'], prop['player'], 
                              prop['stat_type'], prop['ev'], 
                              f"Alert triggered: {prop['player']}")
        
        return triggered
    
    def log_alert(self, alert_type, sport, player, stat_type, value, message):
        """Log alert to history"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO alert_history (alert_type, sport, player, stat_type, value, message)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (alert_type, sport, player, stat_type, value, message))
        self.conn.commit()
    
    def get_alert_history(self, days=7):
        """Get alert history"""
        query = '''
            SELECT * FROM alert_history 
            WHERE sent_at >= datetime('now', '-' || ? || ' days')
            ORDER BY sent_at DESC
        '''
        return pd.read_sql_query(query, self.conn, params=[days])
    
    def clear_all_alerts(self):
        """Deactivate all custom alerts"""
        cursor = self.conn.cursor()
        cursor.execute('UPDATE custom_alerts SET active = 0')
        self.conn.commit()
    
    def delete_alert(self, alert_id):
        """Delete a specific alert"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM custom_alerts WHERE id = ?', (alert_id,))
        self.conn.commit()
    
    def send_test_alert(self):
        """Send a test alert to verify settings"""
        # In-app alert
        st.success("🔔 TEST ALERT: This is a test notification!")
        
        # Email alert if configured
        if self.settings['email']:
            try:
                # Add email sending logic here
                pass
            except Exception as e:
                st.error(f"Email failed: {e}")
        
        # Log test alert
        self.log_alert('test', 'NBA', 'Test', 'Points', 0.05, 'Test alert')
        
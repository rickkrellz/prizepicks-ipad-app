"""
Bet Tracker - Log and analyze your betting performance
"""

import sqlite3
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

class BetTracker:
    def __init__(self):
        self.conn = sqlite3.connect('betting_history.db', check_same_thread=False)
        self.create_tables()
    
    def create_tables(self):
        """Create database tables if they don't exist"""
        cursor = self.conn.cursor()
        
        # Bets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                sport TEXT NOT NULL,
                player TEXT NOT NULL,
                stat_type TEXT NOT NULL,
                line REAL NOT NULL,
                pick TEXT NOT NULL,
                odds REAL NOT NULL,
                stake REAL NOT NULL,
                outcome TEXT,
                profit REAL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Alerts table for notification history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                sport TEXT NOT NULL,
                player TEXT NOT NULL,
                stat_type TEXT NOT NULL,
                ev REAL NOT NULL,
                message TEXT NOT NULL,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Bankroll history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bankroll (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                change REAL,
                note TEXT,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
    
    def add_bet(self, sport, player, stat_type, line, pick, odds, stake, notes=""):
        """Add a new bet to track"""
        cursor = self.conn.cursor()
        date = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        cursor.execute('''
            INSERT INTO bets (date, sport, player, stat_type, line, pick, odds, stake, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (date, sport, player, stat_type, line, pick, odds, stake, notes))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def update_outcome(self, bet_id, outcome, profit):
        """Update bet with result"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE bets 
            SET outcome = ?, profit = ?
            WHERE id = ?
        ''', (outcome, profit, bet_id))
        self.conn.commit()
    
    def get_bets(self, sport=None, days=30):
        """Get betting history with filters"""
        query = "SELECT * FROM bets WHERE date >= date('now', '-' || ? || ' days')"
        params = [days]
        
        if sport and sport != "All":
            query += " AND sport = ?"
            params.append(sport)
        
        query += " ORDER BY date DESC"
        
        df = pd.read_sql_query(query, self.conn, params=params)
        return df
    
    def get_statistics(self, days=30):
        """Calculate betting performance metrics"""
        df = self.get_bets(days=days)
        
        if df.empty:
            return {
                "total_bets": 0,
                "wins": 0,
                "losses": 0,
                "win_rate": 0,
                "total_stake": 0,
                "total_profit": 0,
                "roi": 0,
                "avg_odds": 0
            }
        
        completed = df[df['outcome'].notna()]
        
        stats = {
            "total_bets": len(df),
            "wins": len(completed[completed['outcome'] == 'Win']),
            "losses": len(completed[completed['outcome'] == 'Loss']),
            "total_stake": df['stake'].sum(),
            "total_profit": completed['profit'].sum() if not completed.empty else 0,
        }
        
        stats["win_rate"] = (stats["wins"] / stats["total_bets"] * 100) if stats["total_bets"] > 0 else 0
        stats["roi"] = (stats["total_profit"] / stats["total_stake"] * 100) if stats["total_stake"] > 0 else 0
        stats["avg_odds"] = df['odds'].mean() if not df.empty else 0
        
        return stats
    
    def add_bankroll_snapshot(self, amount, change=0, note=""):
        """Record bankroll history"""
        cursor = self.conn.cursor()
        date = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        cursor.execute('''
            INSERT INTO bankroll (date, amount, change, note)
            VALUES (?, ?, ?, ?)
        ''', (date, amount, change, note))
        
        self.conn.commit()
    
    def get_bankroll_history(self, days=90):
        """Get bankroll trend"""
        query = "SELECT * FROM bankroll WHERE date >= date('now', '-' || ? || ' days') ORDER BY date"
        df = pd.read_sql_query(query, self.conn, params=[days])
        return df
    
    def add_alert(self, sport, player, stat_type, ev, message):
        """Log sent alerts"""
        cursor = self.conn.cursor()
        date = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        cursor.execute('''
            INSERT INTO alerts (date, sport, player, stat_type, ev, message)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (date, sport, player, stat_type, ev, message))
        
        self.conn.commit()
    
    def get_alerts(self, days=7):
        """Get recent alerts"""
        query = "SELECT * FROM alerts WHERE date >= date('now', '-' || ? || ' days') ORDER BY date DESC"
        df = pd.read_sql_query(query, self.conn, params=[days])
        return df
    
    def close(self):
        """Close database connection"""
        self.conn.close()
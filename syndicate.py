"""
Syndicate Features Module - Share picks and collaborate with groups
"""

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import uuid
import json
import plotly.graph_objects as go
import plotly.express as px

class SyndicateManager:
    def __init__(self, multi_user_manager):
        self.multi_user = multi_user_manager
        self.conn = sqlite3.connect('syndicate.db', check_same_thread=False)
        self.create_tables()
    
    def create_tables(self):
        """Create syndicate management tables"""
        cursor = self.conn.cursor()
        
        # Syndicates/groups
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS syndicates (
                syndicate_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                owner_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_private BOOLEAN DEFAULT 0,
                join_code TEXT UNIQUE,
                max_members INTEGER DEFAULT 50,
                min_bankroll REAL DEFAULT 0,
                min_experience TEXT DEFAULT 'beginner',
                logo_url TEXT
            )
        ''')
        
        # Syndicate members
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS syndicate_members (
                syndicate_id TEXT,
                user_id TEXT,
                role TEXT DEFAULT 'member',
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_contributed REAL DEFAULT 0,
                total_wagered REAL DEFAULT 0,
                total_profit REAL DEFAULT 0,
                status TEXT DEFAULT 'active',
                PRIMARY KEY (syndicate_id, user_id),
                FOREIGN KEY (syndicate_id) REFERENCES syndicates(syndicate_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Shared picks
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shared_picks (
                pick_id TEXT PRIMARY KEY,
                syndicate_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                sport TEXT NOT NULL,
                player TEXT NOT NULL,
                stat_type TEXT NOT NULL,
                line REAL NOT NULL,
                pick TEXT NOT NULL,
                odds REAL NOT NULL,
                confidence TEXT,
                analysis TEXT,
                stake REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                status TEXT DEFAULT 'active',
                views INTEGER DEFAULT 0,
                likes INTEGER DEFAULT 0,
                comments INTEGER DEFAULT 0,
                FOREIGN KEY (syndicate_id) REFERENCES syndicates(syndicate_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Pick comments
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pick_comments (
                comment_id TEXT PRIMARY KEY,
                pick_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                comment TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (pick_id) REFERENCES shared_picks(pick_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Pick results
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pick_results (
                pick_id TEXT PRIMARY KEY,
                result TEXT CHECK(result IN ('win', 'loss', 'push', 'pending')),
                profit REAL,
                settled_at TIMESTAMP,
                FOREIGN KEY (pick_id) REFERENCES shared_picks(pick_id)
            )
        ''')
        
        # Syndicate bankroll
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS syndicate_bankroll (
                syndicate_id TEXT PRIMARY KEY,
                total_bankroll REAL DEFAULT 0,
                allocated_funds REAL DEFAULT 0,
                available_funds REAL DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (syndicate_id) REFERENCES syndicates(syndicate_id)
            )
        ''')
        
        # Syndicate chat
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS syndicate_chat (
                message_id TEXT PRIMARY KEY,
                syndicate_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (syndicate_id) REFERENCES syndicates(syndicate_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Invitations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS syndicate_invites (
                invite_id TEXT PRIMARY KEY,
                syndicate_id TEXT NOT NULL,
                invited_by TEXT NOT NULL,
                invitee_email TEXT,
                invite_code TEXT UNIQUE,
                status TEXT DEFAULT 'pending',
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (syndicate_id) REFERENCES syndicates(syndicate_id),
                FOREIGN KEY (invited_by) REFERENCES users(user_id)
            )
        ''')
        
        self.conn.commit()
    
    def create_syndicate(self, owner_id, name, description="", is_private=False, max_members=50):
        """Create a new syndicate"""
        cursor = self.conn.cursor()
        syndicate_id = str(uuid.uuid4())
        join_code = str(uuid.uuid4())[:8].upper() if is_private else None
        
        cursor.execute('''
            INSERT INTO syndicates (syndicate_id, name, description, owner_id, is_private, join_code, max_members)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (syndicate_id, name, description, owner_id, is_private, join_code, max_members))
        
        # Add owner as member with admin role
        cursor.execute('''
            INSERT INTO syndicate_members (syndicate_id, user_id, role)
            VALUES (?, ?, ?)
        ''', (syndicate_id, owner_id, 'admin'))
        
        # Initialize bankroll
        cursor.execute('''
            INSERT INTO syndicate_bankroll (syndicate_id)
            VALUES (?)
        ''', (syndicate_id,))
        
        self.conn.commit()
        return syndicate_id, join_code
    
    def join_syndicate(self, user_id, syndicate_id=None, join_code=None):
        """Join a syndicate"""
        cursor = self.conn.cursor()
        
        if join_code:
            cursor.execute('''
                SELECT syndicate_id FROM syndicates WHERE join_code = ? AND is_private = 1
            ''', (join_code,))
            result = cursor.fetchone()
            if result:
                syndicate_id = result[0]
            else:
                return False, "Invalid join code"
        
        if not syndicate_id:
            return False, "Syndicate not specified"
        
        # Check if already a member
        cursor.execute('''
            SELECT 1 FROM syndicate_members WHERE syndicate_id = ? AND user_id = ?
        ''', (syndicate_id, user_id))
        
        if cursor.fetchone():
            return False, "Already a member"
        
        # Check member limit
        cursor.execute('''
            SELECT COUNT(*) FROM syndicate_members WHERE syndicate_id = ?
        ''', (syndicate_id,))
        member_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT max_members FROM syndicates WHERE syndicate_id = ?', (syndicate_id,))
        max_members = cursor.fetchone()[0]
        
        if member_count >= max_members:
            return False, "Syndicate is full"
        
        # Add member
        cursor.execute('''
            INSERT INTO syndicate_members (syndicate_id, user_id, role)
            VALUES (?, ?, ?)
        ''', (syndicate_id, user_id, 'member'))
        
        self.conn.commit()
        return True, "Successfully joined syndicate"
    
    def share_pick(self, syndicate_id, user_id, pick_data):
        """Share a pick with syndicate members"""
        cursor = self.conn.cursor()
        pick_id = str(uuid.uuid4())
        
        expires_at = (datetime.now() + timedelta(hours=pick_data.get('expiry_hours', 24))).isoformat()
        
        cursor.execute('''
            INSERT INTO shared_picks 
            (pick_id, syndicate_id, user_id, sport, player, stat_type, line, pick, odds, 
             confidence, analysis, stake, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            pick_id, syndicate_id, user_id,
            pick_data['sport'], pick_data['player'], pick_data['stat_type'],
            pick_data['line'], pick_data['pick'], pick_data['odds'],
            pick_data.get('confidence'), pick_data.get('analysis'),
            pick_data.get('stake'), expires_at
        ))
        
        self.conn.commit()
        return pick_id
    
    def get_syndicate_picks(self, syndicate_id, status='active'):
        """Get all shared picks in a syndicate"""
        cursor = self.conn.cursor()
        
        query = '''
            SELECT p.*, u.username, pr.result, pr.profit
            FROM shared_picks p
            JOIN users u ON p.user_id = u.user_id
            LEFT JOIN pick_results pr ON p.pick_id = pr.pick_id
            WHERE p.syndicate_id = ? AND p.status = ?
            ORDER BY p.created_at DESC
        '''
        
        cursor.execute(query, (syndicate_id, status))
        results = cursor.fetchall()
        
        if results:
            columns = ['pick_id', 'syndicate_id', 'user_id', 'sport', 'player', 'stat_type',
                      'line', 'pick', 'odds', 'confidence', 'analysis', 'stake',
                      'created_at', 'expires_at', 'status', 'views', 'likes', 'comments',
                      'username', 'result', 'profit']
            
            df = pd.DataFrame(results, columns=columns)
            return df
        return pd.DataFrame()
    
    def comment_on_pick(self, pick_id, user_id, comment):
        """Add comment to a shared pick"""
        cursor = self.conn.cursor()
        comment_id = str(uuid.uuid4())
        
        cursor.execute('''
            INSERT INTO pick_comments (comment_id, pick_id, user_id, comment)
            VALUES (?, ?, ?, ?)
        ''', (comment_id, pick_id, user_id, comment))
        
        # Update comment count
        cursor.execute('''
            UPDATE shared_picks SET comments = comments + 1 WHERE pick_id = ?
        ''', (pick_id,))
        
        self.conn.commit()
        return comment_id
    
    def like_pick(self, pick_id, user_id):
        """Like a shared pick"""
        cursor = self.conn.cursor()
        
        # Check if already liked
        cursor.execute('''
            SELECT 1 FROM pick_likes WHERE pick_id = ? AND user_id = ?
        ''', (pick_id, user_id))
        
        if cursor.fetchone():
            return False
        
        # Add like
        cursor.execute('''
            INSERT INTO pick_likes (pick_id, user_id) VALUES (?, ?)
        ''', (pick_id, user_id))
        
        # Update like count
        cursor.execute('''
            UPDATE shared_picks SET likes = likes + 1 WHERE pick_id = ?
        ''', (pick_id,))
        
        self.conn.commit()
        return True
    
    def update_pick_result(self, pick_id, result, profit=None):
        """Update the result of a shared pick"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO pick_results (pick_id, result, profit, settled_at)
            VALUES (?, ?, ?, ?)
        ''', (pick_id, result, profit, datetime.now().isoformat()))
        
        # Update pick status
        cursor.execute('''
            UPDATE shared_picks SET status = 'settled' WHERE pick_id = ?
        ''', (pick_id,))
        
        self.conn.commit()
    
    def get_syndicate_stats(self, syndicate_id):
        """Get statistics for a syndicate"""
        cursor = self.conn.cursor()
        
        # Member count
        cursor.execute('''
            SELECT COUNT(*) FROM syndicate_members WHERE syndicate_id = ?
        ''', (syndicate_id,))
        member_count = cursor.fetchone()[0]
        
        # Pick stats
        cursor.execute('''
            SELECT 
                COUNT(*) as total_picks,
                SUM(CASE WHEN pr.result = 'win' THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN pr.result = 'loss' THEN 1 ELSE 0 END) as losses,
                SUM(pr.profit) as total_profit,
                AVG(p.odds) as avg_odds
            FROM shared_picks p
            LEFT JOIN pick_results pr ON p.pick_id = pr.pick_id
            WHERE p.syndicate_id = ?
        ''', (syndicate_id,))
        
        stats = cursor.fetchone()
        
        return {
            'member_count': member_count,
            'total_picks': stats[0] or 0,
            'wins': stats[1] or 0,
            'losses': stats[2] or 0,
            'total_profit': stats[3] or 0,
            'avg_odds': stats[4] or 0,
            'win_rate': (stats[1] / stats[0] * 100) if stats[0] > 0 else 0
        }
    
    def get_user_syndicates(self, user_id):
        """Get all syndicates a user belongs to"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT s.*, sm.role
            FROM syndicates s
            JOIN syndicate_members sm ON s.syndicate_id = sm.syndicate_id
            WHERE sm.user_id = ? AND sm.status = 'active'
        ''', (user_id,))
        
        results = cursor.fetchall()
        
        if results:
            columns = ['syndicate_id', 'name', 'description', 'owner_id', 'created_at',
                      'is_private', 'join_code', 'max_members', 'min_bankroll',
                      'min_experience', 'logo_url', 'role']
            
            df = pd.DataFrame(results, columns=columns)
            return df
        return pd.DataFrame()
    
    def send_invite(self, syndicate_id, invited_by, invitee_email=None):
        """Send syndicate invitation"""
        cursor = self.conn.cursor()
        invite_id = str(uuid.uuid4())
        invite_code = str(uuid.uuid4())[:8].upper()
        expires_at = (datetime.now() + timedelta(days=7)).isoformat()
        
        cursor.execute('''
            INSERT INTO syndicate_invites 
            (invite_id, syndicate_id, invited_by, invitee_email, invite_code, expires_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (invite_id, syndicate_id, invited_by, invitee_email, invite_code, expires_at))
        
        self.conn.commit()
        return invite_code
    
    def accept_invite(self, invite_code, user_id):
        """Accept syndicate invitation"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT syndicate_id FROM syndicate_invites 
            WHERE invite_code = ? AND status = 'pending' AND expires_at > datetime('now')
        ''', (invite_code,))
        
        result = cursor.fetchone()
        if result:
            syndicate_id = result[0]
            
            # Join syndicate
            success, message = self.join_syndicate(user_id, syndicate_id)
            
            if success:
                # Update invite status
                cursor.execute('''
                    UPDATE syndicate_invites SET status = 'accepted' WHERE invite_code = ?
                ''', (invite_code,))
                self.conn.commit()
            
            return success, message
        
        return False, "Invalid or expired invite code"
    
    def render_syndicate_dashboard(self, user_id):
        """Render syndicate dashboard"""
        st.subheader("🤝 Syndicate Features")
        
        # Get user's syndicates
        user_syndicates = self.get_user_syndicates(user_id)
        
        tab1, tab2, tab3, tab4 = st.tabs([
            "📋 My Syndicates", "➕ Create New", "🔍 Discover", "📊 Analytics"
        ])
        
        with tab1:
            if not user_syndicates.empty:
                for _, syndicate in user_syndicates.iterrows():
                    with st.expander(f"🏛️ {syndicate['name']} - {syndicate['role']}", expanded=True):
                        col1, col2, col3, col4 = st.columns(4)
                        
                        stats = self.get_syndicate_stats(syndicate['syndicate_id'])
                        
                        with col1:
                            st.metric("Members", stats['member_count'])
                        with col2:
                            st.metric("Total Picks", stats['total_picks'])
                        with col3:
                            st.metric("Win Rate", f"{stats['win_rate']:.1f}%")
                        with col4:
                            st.metric("Total Profit", f"${stats['total_profit']:.2f}")
                        
                        # Show recent picks
                        picks_df = self.get_syndicate_picks(syndicate['syndicate_id'])
                        
                        if not picks_df.empty:
                            st.subheader("📊 Recent Shared Picks")
                            
                            display_df = picks_df[['username', 'sport', 'player', 'stat_type', 
                                                  'line', 'pick', 'odds', 'confidence', 'created_at']].head(5)
                            st.dataframe(display_df, use_container_width=True)
                            
                            # Share a new pick button
                            if st.button(f"🎯 Share Pick in {syndicate['name']}", key=f"share_{syndicate['syndicate_id']}"):
                                st.session_state['sharing_in'] = syndicate['syndicate_id']
                        
                        # Syndicate chat
                        with st.expander("💬 Syndicate Chat"):
                            st.text_area("Message", key=f"chat_{syndicate['syndicate_id']}")
                            if st.button("Send", key=f"send_{syndicate['syndicate_id']}"):
                                st.success("Message sent!")
            else:
                st.info("You're not a member of any syndicates yet")
        
        with tab2:
            st.subheader("Create New Syndicate")
            
            with st.form("create_syndicate"):
                name = st.text_input("Syndicate Name")
                description = st.text_area("Description")
                is_private = st.checkbox("Private Syndicate")
                max_members = st.number_input("Max Members", min_value=2, max_value=100, value=50)
                min_bankroll = st.number_input("Minimum Bankroll ($)", min_value=0, value=0)
                
                if st.form_submit_button("Create Syndicate"):
                    syndicate_id, join_code = self.create_syndicate(
                        user_id, name, description, is_private, max_members
                    )
                    
                    st.success(f"Syndicate created successfully!")
                    if is_private:
                        st.info(f"Share this join code with friends: **{join_code}**")
        
        with tab3:
            st.subheader("Discover Syndicates")
            
            # Search/filter
            col1, col2 = st.columns(2)
            with col1:
                search = st.text_input("Search syndicates")
            with col2:
                filter_type = st.selectbox("Type", ["All", "Public", "Private"])
            
            # Mock discover results
            st.info("Join public syndicates or enter an invite code below")
            
            invite_code = st.text_input("Enter Invite Code")
            if st.button("Join with Code"):
                success, message = self.accept_invite(invite_code, user_id)
                if success:
                    st.success(message)
                else:
                    st.error(message)
        
        with tab4:
            st.subheader("Syndicate Analytics")
            
            if not user_syndicates.empty:
                selected = st.selectbox("Select Syndicate", user_syndicates['name'].tolist())
                syndicate_data = user_syndicates[user_syndicates['name'] == selected].iloc[0]
                
                stats = self.get_syndicate_stats(syndicate_data['syndicate_id'])
                
                # Performance metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Wagered", f"${stats['total_picks'] * 100:,.2f}")
                with col2:
                    st.metric("ROI", f"{(stats['total_profit'] / (stats['total_picks'] * 100) * 100):.1f}%")
                with col3:
                    st.metric("Avg Odds", f"{stats['avg_odds']:.2f}")
                
                # Performance chart
                picks_df = self.get_syndicate_picks(syndicate_data['syndicate_id'])
                
                if not picks_df.empty and 'created_at' in picks_df.columns:
                    picks_df['created_at'] = pd.to_datetime(picks_df['created_at'])
                    picks_df['date'] = picks_df['created_at'].dt.date
                    
                    daily_stats = picks_df.groupby('date').size().reset_index(name='count')
                    
                    fig = px.bar(daily_stats, x='date', y='count', 
                                title='Daily Pick Activity')
                    st.plotly_chart(fig, use_container_width=True)
    
    def render_share_pick_modal(self, user_id, syndicate_id):
        """Render modal for sharing a pick"""
        st.subheader("🎯 Share a Pick")
        
        with st.form("share_pick"):
            col1, col2 = st.columns(2)
            with col1:
                sport = st.selectbox("Sport", ["NBA", "NFL", "MLB", "NHL", "SOCCER", "TENNIS"])
                player = st.text_input("Player Name")
                stat_type = st.selectbox("Stat Type", 
                    ["Points", "Rebounds", "Assists", "PRA", "Passing Yds", "Goals"])
            with col2:
                line = st.number_input("Line", value=20.5, step=0.5)
                pick = st.selectbox("Pick", ["OVER", "UNDER"])
                odds = st.number_input("Odds", value=2.0, step=0.1)
            
            confidence = st.select_slider("Confidence", 
                options=["Very Low", "Low", "Medium", "High", "Very High"])
            analysis = st.text_area("Analysis / Reasoning")
            stake = st.number_input("Recommended Stake ($)", value=10.0, step=5.0)
            expiry_hours = st.number_input("Expires in (hours)", value=24, min_value=1)
            
            if st.form_submit_button("Share Pick"):
                pick_data = {
                    'sport': sport,
                    'player': player,
                    'stat_type': stat_type,
                    'line': line,
                    'pick': pick,
                    'odds': odds,
                    'confidence': confidence,
                    'analysis': analysis,
                    'stake': stake,
                    'expiry_hours': expiry_hours
                }
                
                pick_id = self.share_pick(syndicate_id, user_id, pick_data)
                st.success(f"Pick shared successfully! ID: {pick_id}")
                st.session_state.pop('sharing_in', None)
                st.rerun()
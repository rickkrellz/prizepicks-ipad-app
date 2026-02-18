"""
Premium Subscription Module - Stripe integration for paid tiers
Handles missing secrets gracefully - FIXED INDENTATION
"""

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import uuid

class PremiumManager:
    def __init__(self):
        # Safely get Stripe keys from secrets
        try:
            self.stripe_api_key = st.secrets.get("STRIPE_API_KEY", None)
            self.stripe_webhook_secret = st.secrets.get("STRIPE_WEBHOOK_SECRET", None)
            self.stripe_available = self.stripe_api_key is not None and self.stripe_webhook_secret is not None
        except:
            self.stripe_api_key = None
            self.stripe_webhook_secret = None
            self.stripe_available = False
        
        # Pricing tiers
        self.tiers = {
            'free': {
                'name': 'Free',
                'price': 0,
                'features': [
                    'Basic EV calculations',
                    '10 alerts/month',
                    'Manual bet tracking',
                    'Basic filters',
                    'Single user'
                ]
            },
            'pro_monthly': {
                'name': 'Pro Monthly',
                'price': 4.99,
                'features': [
                    'Unlimited alerts',
                    'Arbitrage scanner',
                    'Bankroll management',
                    'Bump detector',
                    'Export data',
                    'Advanced analytics',
                    'Calendar view',
                    'Performance charts'
                ]
            },
            'pro_yearly': {
                'name': 'Pro Yearly',
                'price': 49.99,
                'features': [
                    'All Pro Monthly features',
                    '2 months free',
                    'AI predictions',
                    'Custom alerts',
                    'Email support'
                ]
            },
            'elite': {
                'name': 'Elite',
                'price': 99.99,
                'features': [
                    'All Pro features',
                    'Live betting data',
                    'Syndicate tools',
                    'Multi-account tracking',
                    'Public leaderboard',
                    'API access'
                ]
            }
        }
        
        self.conn = sqlite3.connect('subscriptions.db', check_same_thread=False)
        self.create_tables()
    
    def create_tables(self):
        """Create subscription management tables"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                subscription_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                tier TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_date TIMESTAMP,
                auto_renew BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feature_access (
                user_id TEXT PRIMARY KEY,
                tier TEXT NOT NULL,
                alerts_remaining INTEGER DEFAULT 10,
                alerts_reset_date TIMESTAMP,
                last_access TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
    
    def get_user_tier(self, user_id):
        """Get current subscription tier for user"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT tier, status, end_date FROM subscriptions 
            WHERE user_id = ? AND status = 'active' AND (end_date IS NULL OR end_date > datetime('now'))
            ORDER BY end_date DESC LIMIT 1
        ''', (user_id,))
        
        result = cursor.fetchone()
        
        if result:
            return {
                'tier': result[0],
                'status': result[1],
                'end_date': result[2]
            }
        return {'tier': 'free', 'status': 'active', 'end_date': None}
    
    def check_feature_access(self, user_id, feature):
        """Check if user has access to a specific feature"""
        user_tier = self.get_user_tier(user_id)
        tier_config = self.tiers.get(user_tier['tier'], self.tiers['free'])
        
        if feature == 'alerts':
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT alerts_remaining FROM feature_access WHERE user_id = ?
            ''', (user_id,))
            result = cursor.fetchone()
            
            if result and result[0] > 0:
                return True
            elif user_tier['tier'] == 'free':
                return False
            return True
        
        # Check if feature is in tier's features list
        feature_list = ' '.join(tier_config['features']).lower()
        return feature.lower() in feature_list
    
    def render_pricing_table(self, user_id):
        """Render pricing comparison table"""
        current_tier = self.get_user_tier(user_id)['tier']
        
        st.subheader("💎 Premium Plans")
        st.markdown("Upgrade to unlock advanced features!")
        
        if not self.stripe_available:
            st.info("🔧 **Demo Mode**: Upgrades will be simulated.")
        
        # Pricing cards
        cols = st.columns(len(self.tiers))
        
        for idx, (tier_key, tier) in enumerate(self.tiers.items()):
            with cols[idx]:
                is_current = tier_key == current_tier
                border = '3px solid #4CAF50' if is_current else '1px solid #ddd'
                bg_color = '#f0fff0' if is_current else 'white'
                
                st.markdown(f"""
                <div style="
                    border: {border};
                    border-radius: 10px;
                    padding: 20px;
                    background-color: {bg_color};
                    text-align: center;
                    height: 400px;
                    display: flex;
                    flex-direction: column;
                ">
                    <h3>{tier['name']}</h3>
                    <h2>${tier['price']}</h2>
                    <p style="font-size: 14px; color: #666;">{'per month' if tier_key != 'free' else ''}</p>
                    <div style="flex-grow: 1; text-align: left; margin: 20px 0;">
                """, unsafe_allow_html=True)
                
                for feature in tier['features'][:5]:
                    st.markdown(f"✅ {feature}")
                if len(tier['features']) > 5:
                    st.markdown(f"... and {len(tier['features']) - 5} more")
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                if tier_key == 'free':
                    if is_current:
                        st.button("✓ Current Plan", disabled=True, key=f"free_btn_{idx}")
                else:
                    if is_current:
                        st.button("✓ Current Plan", disabled=True, key=f"current_{tier_key}_{idx}")
                    else:
                        if st.button(f"Upgrade", key=f"upgrade_{tier_key}_{idx}"):
                            st.session_state['demo_upgrade'] = tier_key
                            st.success(f"[DEMO] Upgraded to {tier['name']}!")
                            st.rerun()
        
        # Feature comparison table - FIXED INDENTATION
        with st.expander("📊 Feature Comparison"):
            feature_data = {
                'Feature': [
                    'EV Calculations',
                    'Monthly Alerts',
                    'Bet Tracking',
                    'Basic Filters',
                    'Arbitrage Scanner',
                    'Bankroll Management',
                    'Bump Detector',
                    'Export Data',
                    'Advanced Analytics',
                    'AI Predictions',
                    'Live Betting',
                    'Syndicate Tools',
                    'Multi-Account',
                    'Calendar View',
                    'Performance Charts',
                    'Leaderboard Access'
                ],
                'Free': ['Basic', '10', 'Manual', 'Basic', '❌', '❌', '❌', '❌', '❌', '❌', '❌', '❌', '❌', '❌', '❌', '❌'],
                'Pro Monthly': ['Advanced', 'Unlimited', 'Auto', 'Advanced', '✅', '✅', '✅', '✅', 'Basic', '❌', '❌', '❌', '❌', '✅', '✅', '❌'],
                'Pro Yearly': ['Advanced', 'Unlimited', 'Auto', 'Advanced', '✅', '✅', '✅', '✅', 'Advanced', '✅', '❌', '❌', '❌', '✅', '✅', '✅'],
                'Elite': ['Premium', 'Unlimited', 'Pro', 'Premium', '✅', '✅', '✅', '✅', 'Premium', '✅', '✅', '✅', '✅', '✅', '✅', '✅']
            }
            
            feature_matrix = pd.DataFrame(feature_data)
            st.dataframe(feature_matrix.set_index('Feature'), use_container_width=True)
"""
Premium Subscription Module - Stripe integration for paid tiers
"""

import streamlit as st
import stripe
import sqlite3
from datetime import datetime, timedelta
import hashlib
import uuid
import hmac
import json

class PremiumManager:
    def __init__(self):
        # Stripe configuration (replace with your actual keys)
        self.stripe_api_key = st.secrets.get("STRIPE_API_KEY", "YOUR_STRIPE_SECRET_KEY")
        self.stripe_webhook_secret = st.secrets.get("STRIPE_WEBHOOK_SECRET", "YOUR_WEBHOOK_SECRET")
        stripe.api_key = self.stripe_api_key
        
        # Pricing tiers
        self.tiers = {
            'free': {
                'name': 'Free',
                'price': 0,
                'features': [
                    'Basic EV calculations',
                    '10 alerts/month',
                    'Manual bet tracking',
                    'Basic filters'
                ]
            },
            'pro_monthly': {
                'name': 'Pro Monthly',
                'price': 4.99,
                'stripe_price_id': 'price_pro_monthly',  # Replace with actual Stripe price ID
                'features': [
                    'Unlimited alerts',
                    'Arbitrage scanner',
                    'Bankroll management',
                    'Bump detector',
                    'Export data',
                    'Advanced analytics',
                    'Priority support'
                ]
            },
            'pro_yearly': {
                'name': 'Pro Yearly',
                'price': 49.99,
                'stripe_price_id': 'price_pro_yearly',  # Replace with actual Stripe price ID
                'features': [
                    'All Pro Monthly features',
                    '2 months free',
                    'AI predictions',
                    'API access',
                    'Custom alerts'
                ]
            },
            'elite': {
                'name': 'Elite',
                'price': 99.99,
                'stripe_price_id': 'price_elite',  # Replace with actual Stripe price ID
                'features': [
                    'All Pro features',
                    'Live betting data',
                    'Syndicate tools',
                    'Multi-account tracking',
                    'API access',
                    'White-label option',
                    'Dedicated support'
                ]
            }
        }
        
        self.conn = sqlite3.connect('subscriptions.db', check_same_thread=False)
        self.create_tables()
    
    def create_tables(self):
        """Create subscription management tables"""
        cursor = self.conn.cursor()
        
        # Subscriptions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                subscription_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                tier TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_date TIMESTAMP,
                auto_renew BOOLEAN DEFAULT 1,
                stripe_subscription_id TEXT,
                stripe_customer_id TEXT,
                payment_method TEXT,
                last_payment TIMESTAMP,
                next_payment TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Payment history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payment_history (
                payment_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                subscription_id TEXT,
                amount REAL NOT NULL,
                currency TEXT DEFAULT 'usd',
                status TEXT,
                stripe_payment_intent_id TEXT,
                payment_method TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Feature access
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feature_access (
                user_id TEXT PRIMARY KEY,
                tier TEXT NOT NULL,
                alerts_remaining INTEGER DEFAULT 10,
                alerts_reset_date TIMESTAMP,
                api_calls_today INTEGER DEFAULT 0,
                api_calls_reset_date TIMESTAMP,
                last_access TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Promo codes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS promo_codes (
                code TEXT PRIMARY KEY,
                description TEXT,
                discount_percent INTEGER,
                valid_from TIMESTAMP,
                valid_until TIMESTAMP,
                max_uses INTEGER,
                used_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
        
        # Special handling for usage-based features
        if feature == 'alerts':
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT alerts_remaining FROM feature_access WHERE user_id = ?
            ''', (user_id,))
            result = cursor.fetchone()
            
            if result and result[0] > 0:
                return True
            return user_tier['tier'] != 'free'  # Free users have limited alerts
        
        # Check if feature is in tier's features list
        return feature in tier_config['features']
    
    def use_alert(self, user_id):
        """Consume one alert from user's quota"""
        cursor = self.conn.cursor()
        
        # Check if alerts need reset
        cursor.execute('''
            SELECT alerts_remaining, alerts_reset_date FROM feature_access WHERE user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        if result:
            remaining, reset_date = result
            
            # Reset if past reset date
            if reset_date and datetime.now() > datetime.fromisoformat(reset_date):
                remaining = self.get_monthly_alert_quota(user_id)
                reset_date = (datetime.now() + timedelta(days=30)).isoformat()
            
            if remaining > 0:
                cursor.execute('''
                    UPDATE feature_access 
                    SET alerts_remaining = ?, alerts_reset_date = ?
                    WHERE user_id = ?
                ''', (remaining - 1, reset_date, user_id))
                self.conn.commit()
                return True
        
        return False
    
    def get_monthly_alert_quota(self, user_id):
        """Get monthly alert quota based on tier"""
        user_tier = self.get_user_tier(user_id)
        quotas = {
            'free': 10,
            'pro_monthly': 1000,
            'pro_yearly': 1000,
            'elite': 10000
        }
        return quotas.get(user_tier['tier'], 10)
    
    def create_checkout_session(self, user_id, tier, success_url, cancel_url):
        """Create Stripe checkout session"""
        try:
            tier_config = self.tiers.get(tier)
            if not tier_config or tier == 'free':
                return None
            
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': tier_config['stripe_price_id'],
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    'user_id': user_id,
                    'tier': tier
                }
            )
            
            return session.url
        except Exception as e:
            st.error(f"Error creating checkout session: {e}")
            return None
    
    def handle_webhook(self, payload, sig_header):
        """Handle Stripe webhook events"""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.stripe_webhook_secret
            )
        except ValueError:
            return {'error': 'Invalid payload'}
        except stripe.error.SignatureVerificationError:
            return {'error': 'Invalid signature'}
        
        # Handle the event
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            self.handle_checkout_completed(session)
        elif event['type'] == 'invoice.payment_succeeded':
            invoice = event['data']['object']
            self.handle_payment_succeeded(invoice)
        elif event['type'] == 'customer.subscription.deleted':
            subscription = event['data']['object']
            self.handle_subscription_cancelled(subscription)
        
        return {'status': 'success'}
    
    def handle_checkout_completed(self, session):
        """Handle successful checkout"""
        cursor = self.conn.cursor()
        user_id = session['metadata']['user_id']
        tier = session['metadata']['tier']
        subscription_id = session['subscription']
        customer_id = session['customer']
        
        # Calculate end date (30 days from now for monthly)
        end_date = (datetime.now() + timedelta(days=30)).isoformat()
        
        # Create subscription record
        sub_uuid = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO subscriptions 
            (subscription_id, user_id, tier, stripe_subscription_id, stripe_customer_id, end_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (sub_uuid, user_id, tier, subscription_id, customer_id, end_date))
        
        # Create feature access record
        cursor.execute('''
            INSERT OR REPLACE INTO feature_access (user_id, tier, alerts_remaining, alerts_reset_date)
            VALUES (?, ?, ?, ?)
        ''', (user_id, tier, self.get_monthly_alert_quota(user_id), 
              (datetime.now() + timedelta(days=30)).isoformat()))
        
        self.conn.commit()
    
    def handle_payment_succeeded(self, invoice):
        """Handle successful payment"""
        cursor = self.conn.cursor()
        subscription_id = invoice['subscription']
        
        # Update subscription end date
        cursor.execute('''
            UPDATE subscriptions 
            SET last_payment = ?, next_payment = ?
            WHERE stripe_subscription_id = ?
        ''', (datetime.now().isoformat(), 
              (datetime.now() + timedelta(days=30)).isoformat(),
              subscription_id))
        
        # Record payment
        payment_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO payment_history (payment_id, user_id, amount, stripe_payment_intent_id)
            VALUES (?, ?, ?, ?)
        ''', (payment_id, invoice['customer'], invoice['amount_paid'] / 100, 
              invoice['payment_intent']))
        
        self.conn.commit()
    
    def handle_subscription_cancelled(self, subscription):
        """Handle subscription cancellation"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            UPDATE subscriptions 
            SET status = 'cancelled', auto_renew = 0
            WHERE stripe_subscription_id = ?
        ''', (subscription['id'],))
        
        self.conn.commit()
    
    def render_pricing_table(self, user_id):
        """Render pricing comparison table"""
        current_tier = self.get_user_tier(user_id)['tier']
        
        st.subheader("💎 Premium Plans")
        st.markdown("Upgrade to unlock advanced features and increase your winning edge!")
        
        # Pricing cards in columns
        cols = st.columns(len(self.tiers))
        
        for idx, (tier_key, tier) in enumerate(self.tiers.items()):
            with cols[idx]:
                # Card styling
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
                    height: 450px;
                    display: flex;
                    flex-direction: column;
                ">
                    <h3>{tier['name']}</h3>
                    <h2>${tier['price']}</h2>
                    <p style="font-size: 14px; color: #666;">{'per month' if tier_key != 'free' else ''}</p>
                    <div style="flex-grow: 1; text-align: left; margin: 20px 0;">
                """, unsafe_allow_html=True)
                
                for feature in tier['features']:
                    st.markdown(f"✅ {feature}")
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                if tier_key == 'free':
                    if is_current:
                        st.button("Current Plan", disabled=True, key=f"btn_{tier_key}")
                    else:
                        st.button("Downgrade", disabled=True, key=f"btn_{tier_key}")
                else:
                    if is_current:
                        st.button("✓ Current Plan", disabled=True, key=f"btn_{tier_key}")
                    else:
                        if st.button(f"Upgrade to {tier['name']}", key=f"btn_{tier_key}"):
                            # Create checkout session
                            checkout_url = self.create_checkout_session(
                                user_id=user_id,
                                tier=tier_key,
                                success_url=f"https://prizepicks-ipad-app.streamlit.app?success=1",
                                cancel_url=f"https://prizepicks-ipad-app.streamlit.app?canceled=1"
                            )
                            if checkout_url:
                                st.markdown(f'<meta http-equiv="refresh" content="0; url={checkout_url}">', 
                                          unsafe_allow_html=True)
        
        # Feature comparison table
        with st.expander("📊 Detailed Feature Comparison"):
            feature_matrix = pd.DataFrame({
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
                    'API Access',
                    'Live Betting',
                    'Syndicate Tools',
                    'Multi-Account',
                    'Priority Support'
                ],
                'Free': ['✅ Basic', '10', '✅ Manual', '✅ Basic', '❌', '❌', '❌', '❌', '❌', '❌', '❌', '❌', '❌', '❌', '❌'],
                'Pro Monthly': ['✅ Advanced', 'Unlimited', '✅ Auto', '✅ Advanced', '✅', '✅', '✅', '✅', '✅ Basic', '❌', '❌', '❌', '❌', '❌', '✅ Email'],
                'Pro Yearly': ['✅ Advanced', 'Unlimited', '✅ Auto', '✅ Advanced', '✅', '✅', '✅', '✅', '✅ Advanced', '✅', '✅', '❌', '❌', '❌', '✅ Priority'],
                'Elite': ['✅ Premium', 'Unlimited', '✅ Pro', '✅ Premium', '✅', '✅', '✅', '✅', '✅ Premium', '✅', '✅ Unlimited', '✅', '✅', '✅', '✅ 24/7']
            })
            
            st.dataframe(feature_matrix.set_index('Feature'), use_container_width=True)
    
    def get_subscription_management_ui(self, user_id):
        """Render subscription management interface"""
        current = self.get_user_tier(user_id)
        
        st.subheader("📋 Your Subscription")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Current Plan", self.tiers[current['tier']]['name'])
        with col2:
            if current['end_date']:
                st.metric("Renewal Date", current['end_date'][:10])
        
        if current['tier'] != 'free':
            st.info(f"✅ You have access to all {self.tiers[current['tier']]['name']} features")
            
            if st.button("Cancel Subscription"):
                # Handle cancellation
                st.warning("This will cancel your subscription at the end of the billing period")
                if st.button("Confirm Cancellation"):
                    # Cancel logic here
                    st.success("Subscription cancelled successfully")
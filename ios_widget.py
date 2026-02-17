"""
iOS Widget Support - Generate widget data for iOS home screen
"""

import json
import pandas as pd
from datetime import datetime
import streamlit as st

class iOSWidget:
    def __init__(self):
        self.widget_data = {
            'top_picks': [],
            'stats': {},
            'last_updated': None
        }
    
    def generate_widget_data(self, ev_data, pp_data):
        """
        Generate data for iOS widget display
        """
        # Get top 3 EV picks
        if not ev_data.empty and 'ev' in ev_data.columns:
            top_picks = ev_data.nlargest(3, 'ev')[['player', 'stat_type', 'line', 'ev']].to_dict('records')
        else:
            top_picks = []
        
        # Format for widget
        formatted_picks = []
        for pick in top_picks:
            formatted_picks.append({
                'player': pick['player'],
                'stat': pick['stat_type'],
                'ev': f"{pick['ev']:.1%}" if isinstance(pick['ev'], (int, float)) else "N/A",
                'line': pick['line']
            })
        
        # Calculate stats safely
        profitable_props = 0
        avg_ev = 0
        
        if not ev_data.empty:
            if 'is_positive' in ev_data.columns:
                profitable_props = len(ev_data[ev_data['is_positive']])
            elif 'ev' in ev_data.columns:
                profitable_props = len(ev_data[ev_data['ev'] > 0])
            
            if 'ev' in ev_data.columns:
                avg_ev = ev_data['ev'].mean()
        
        stats = {
            'total_props': len(pp_data) if pp_data is not None else 0,
            'profitable_props': profitable_props,
            'avg_ev': avg_ev if avg_ev else 0
        }
        
        self.widget_data = {
            'top_picks': formatted_picks,
            'stats': stats,
            'last_updated': datetime.now().isoformat()
        }
        
        # Save to file for widget to read
        self.save_widget_data()
        
        return self.widget_data
    
    def save_widget_data(self):
        """Save widget data to JSON file"""
        try:
            with open('widget_data.json', 'w') as f:
                json.dump(self.widget_data, f, indent=2)
        except Exception as e:
            print(f"Error saving widget data: {e}")
    
    def get_widget_data(self):
        """Get current widget data"""
        try:
            with open('widget_data.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return self.widget_data
        except Exception as e:
            print(f"Error loading widget data: {e}")
            return self.widget_data
    
    def render_widget_preview(self):
        """
        Render a preview of how the widget will look on iOS
        """
        data = self.get_widget_data()
        
        # Ensure stats has all required keys
        if 'stats' not in data:
            data['stats'] = {'profitable_props': 0, 'total_props': 0, 'avg_ev': 0}
        
        # Create widget preview
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 20px;
            padding: 20px;
            color: white;
            width: 300px;
            margin: 0 auto;
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        ">
            <div style="font-size: 14px; opacity: 0.9;">🏆 PrizePicks +EV</div>
            <div style="font-size: 24px; font-weight: bold; margin: 10px 0;">Top Picks</div>
        """, unsafe_allow_html=True)
        
        # Display top picks
        for pick in data['top_picks'][:3]:
            st.markdown(f"""
            <div style="
                background: rgba(255,255,255,0.1);
                border-radius: 10px;
                padding: 10px;
                margin: 5px 0;
            ">
                <div style="font-weight: bold;">{pick.get('player', 'N/A')}</div>
                <div style="font-size: 12px;">{pick.get('stat', 'N/A')} @ {pick.get('line', 'N/A')} | EV: {pick.get('ev', 'N/A')}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Display stats safely
        profitable = data['stats'].get('profitable_props', 0)
        last_updated = data.get('last_updated', datetime.now().isoformat())
        
        # Format time
        try:
            time_str = last_updated[11:16] if len(last_updated) > 16 else "N/A"
        except:
            time_str = "N/A"
        
        st.markdown(f"""
            <div style="
                display: flex;
                justify-content: space-between;
                margin-top: 15px;
                font-size: 12px;
                opacity: 0.9;
            ">
                <span>📊 {profitable} profitable</span>
                <span>⏱️ {time_str}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Add instructions
        st.markdown("""
        <div style="text-align: center; margin-top: 20px; font-size: 12px; color: #666;">
            This is a preview of how the widget will appear on your iPad home screen.
            The actual widget updates automatically based on your data.
        </div>
        """, unsafe_allow_html=True)
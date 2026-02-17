"""
iOS Widget Support - Generate widget data for iOS home screen
"""

import json
import pandas as pd
from datetime import datetime

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
        top_picks = ev_data.nlargest(3, 'ev')[['player', 'stat_type', 'line', 'ev']].to_dict('records')
        
        # Format for widget
        formatted_picks = []
        for pick in top_picks:
            formatted_picks.append({
                'player': pick['player'],
                'stat': pick['stat_type'],
                'ev': f"{pick['ev']:.1%}",
                'line': pick['line']
            })
        
        # Calculate stats
        stats = {
            'total_props': len(pp_data),
            'profitable_props': len(ev_data[ev_data['is_positive']]) if 'is_positive' in ev_data.columns else 0,
            'avg_ev': ev_data['ev'].mean() if not ev_data.empty else 0
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
        with open('widget_data.json', 'w') as f:
            json.dump(self.widget_data, f, indent=2)
    
    def get_widget_data(self):
        """Get current widget data"""
        try:
            with open('widget_data.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return self.widget_data
    
    def render_widget_preview(self):
        """
        Render a preview of how the widget will look on iOS
        """
        import streamlit as st
        
        data = self.get_widget_data()
        
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
            <div style="font-size: 14px; opacity: 0.9;">PrizePicks +EV</div>
            <div style="font-size: 24px; font-weight: bold; margin: 10px 0;">Top Picks</div>
        """, unsafe_allow_html=True)
        
        for pick in data['top_picks'][:3]:
            st.markdown(f"""
            <div style="
                background: rgba(255,255,255,0.1);
                border-radius: 10px;
                padding: 10px;
                margin: 5px 0;
            ">
                <div style="font-weight: bold;">{pick['player']}</div>
                <div style="font-size: 12px;">{pick['stat']} @ {pick['line']} | EV: {pick['ev']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown(f"""
            <div style="
                display: flex;
                justify-content: space-between;
                margin-top: 15px;
                font-size: 12px;
                opacity: 0.9;
            ">
                <span>📊 {data['stats']['profitable_props']} profitable</span>
                <span>⏱️ {data['last_updated'][11:16]}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
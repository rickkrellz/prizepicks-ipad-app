"""
Calendar View Module - Visualize betting activity on a calendar
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import calendar

class CalendarView:
    def __init__(self, bet_tracker):
        self.bet_tracker = bet_tracker
    
    def create_heatmap_data(self, bets_df, year=None, month=None):
        """Create data for calendar heatmap"""
        if bets_df.empty:
            return pd.DataFrame()
        
        # Convert dates
        bets_df['date_obj'] = pd.to_datetime(bets_df['date'])
        
        if year:
            bets_df = bets_df[bets_df['date_obj'].dt.year == year]
        if month:
            bets_df = bets_df[bets_df['date_obj'].dt.month == month]
        
        # Group by date
        daily_stats = bets_df.groupby(bets_df['date_obj'].dt.date).agg({
            'profit': 'sum',
            'id': 'count',
            'outcome': lambda x: (x == 'Win').sum()
        }).rename(columns={'id': 'bets', 'outcome': 'wins'})
        
        daily_stats['win_rate'] = (daily_stats['wins'] / daily_stats['bets'] * 100).round(1)
        
        return daily_stats
    
    def render_month_calendar(self, year, month):
        """Render a monthly calendar view"""
        # Get month name
        month_name = calendar.month_name[month]
        
        st.subheader(f"📅 {month_name} {year}")
        
        # Get calendar grid
        cal = calendar.monthcalendar(year, month)
        
        # Create HTML table for calendar
        html = '<table style="width:100%; border-collapse: collapse;">'
        
        # Header with day names
        html += '<tr>'
        for day in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']:
            html += f'<th style="border:1px solid #ddd; padding:10px; text-align:center;">{day}</th>'
        html += '</tr>'
        
        # Calendar rows
        for week in cal:
            html += '<tr>'
            for day in week:
                if day == 0:
                    html += '<td style="border:1px solid #ddd; padding:15px; text-align:center; background-color:#f5f5f5;"></td>'
                else:
                    html += f'<td style="border:1px solid #ddd; padding:15px; text-align:center; vertical-align:top;">'
                    html += f'<div style="font-weight:bold; margin-bottom:5px;">{day}</div>'
                    
                    # Add bet indicators here (would need actual data)
                    html += '<div style="font-size:10px; color:#666;">No bets</div>'
                    
                    html += '</td>'
            html += '</tr>'
        
        html += '</table>'
        
        st.markdown(html, unsafe_allow_html=True)
    
    def render_heatmap(self, bets_df, year):
        """Render a year heatmap of betting activity"""
        if bets_df.empty:
            st.info("No data available for heatmap")
            return
        
        # Prepare data
        daily_stats = self.create_heatmap_data(bets_df, year=year)
        
        if daily_stats.empty:
            st.info(f"No betting data for {year}")
            return
        
        # Create date range for the year
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31)
        all_dates = pd.date_range(start_date, end_date, freq='D')
        
        # Create full dataframe
        heatmap_df = pd.DataFrame(index=all_dates.date)
        heatmap_df['profit'] = 0
        heatmap_df['bets'] = 0
        
        for date, row in daily_stats.iterrows():
            if date in heatmap_df.index:
                heatmap_df.loc[date, 'profit'] = row['profit']
                heatmap_df.loc[date, 'bets'] = row['bets']
        
        # Add week and day columns
        heatmap_df['week'] = heatmap_df.index.to_series().apply(lambda x: x.isocalendar()[1])
        heatmap_df['weekday'] = heatmap_df.index.to_series().apply(lambda x: x.weekday())
        
        # Pivot for heatmap
        pivot_profit = heatmap_df.pivot_table(
            values='profit', 
            index='weekday', 
            columns='week', 
            aggfunc='first',
            fill_value=0
        )
        
        pivot_bets = heatmap_df.pivot_table(
            values='bets', 
            index='weekday', 
            columns='week', 
            aggfunc='first',
            fill_value=0
        )
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=pivot_profit.values,
            x=pivot_profit.columns,
            y=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            colorscale='RdYlGn',
            zmid=0,
            text=pivot_bets.values,
            texttemplate='%{text}',
            textfont={"size": 10},
            hoverongaps=False,
            hovertemplate='Week %{x}<br>%{y}<br>Profit: $%{z:.2f}<br>Bets: %{text}<extra></extra>'
        ))
        
        fig.update_layout(
            title=f'Betting Activity Heatmap - {year}',
            xaxis_title='Week Number',
            yaxis_title='Day of Week',
            height=300,
            width=800
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_timeline(self, bets_df):
        """Render a timeline of betting activity"""
        if bets_df.empty:
            st.info("No data for timeline")
            return
        
        # Prepare data
        bets_df['date_obj'] = pd.to_datetime(bets_df['date'])
        completed = bets_df[bets_df['outcome'].notna()].copy()
        
        if completed.empty:
            st.info("No completed bets for timeline")
            return
        
        # Create cumulative profit
        completed = completed.sort_values('date_obj')
        completed['cumulative_profit'] = completed['profit'].cumsum()
        
        # Create figure
        fig = go.Figure()
        
        # Add cumulative profit line
        fig.add_trace(go.Scatter(
            x=completed['date_obj'],
            y=completed['cumulative_profit'],
            mode='lines+markers',
            name='Cumulative Profit',
            line=dict(color='green', width=2),
            marker=dict(size=8)
        ))
        
        # Add zero line
        fig.add_hline(y=0, line_dash="dash", line_color="red", opacity=0.5)
        
        # Add win/loss markers
        wins = completed[completed['outcome'] == 'Win']
        losses = completed[completed['outcome'] == 'Loss']
        
        fig.add_trace(go.Scatter(
            x=wins['date_obj'],
            y=wins['cumulative_profit'],
            mode='markers',
            name='Wins',
            marker=dict(color='green', size=12, symbol='triangle-up'),
            hoverinfo='text',
            hovertext=wins.apply(lambda x: f"Win: ${x['profit']:.2f}<br>{x['player']} {x['stat_type']}", axis=1)
        ))
        
        fig.add_trace(go.Scatter(
            x=losses['date_obj'],
            y=losses['cumulative_profit'],
            mode='markers',
            name='Losses',
            marker=dict(color='red', size=12, symbol='triangle-down'),
            hoverinfo='text',
            hovertext=losses.apply(lambda x: f"Loss: ${x['profit']:.2f}<br>{x['player']} {x['stat_type']}", axis=1)
        ))
        
        fig.update_layout(
            title='Profit Timeline',
            xaxis_title='Date',
            yaxis_title='Cumulative Profit ($)',
            height=400,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_streak_analysis(self, bets_df):
        """Analyze winning and losing streaks"""
        if bets_df.empty:
            return
        
        completed = bets_df[bets_df['outcome'].notna()].copy()
        if completed.empty:
            return
        
        completed = completed.sort_values('date_obj')
        
        # Calculate streaks
        streaks = []
        current_streak = 0
        streak_type = None
        
        for _, bet in completed.iterrows():
            if bet['outcome'] == 'Win':
                if streak_type == 'win':
                    current_streak += 1
                else:
                    if current_streak > 0:
                        streaks.append((streak_type, current_streak))
                    streak_type = 'win'
                    current_streak = 1
            else:  # Loss
                if streak_type == 'loss':
                    current_streak += 1
                else:
                    if current_streak > 0:
                        streaks.append((streak_type, current_streak))
                    streak_type = 'loss'
                    current_streak = 1
        
        # Add last streak
        if current_streak > 0:
            streaks.append((streak_type, current_streak))
        
        # Find best and worst streaks
        win_streaks = [s[1] for s in streaks if s[0] == 'win']
        loss_streaks = [s[1] for s in streaks if s[0] == 'loss']
        
        best_win_streak = max(win_streaks) if win_streaks else 0
        worst_loss_streak = max(loss_streaks) if loss_streaks else 0
        current_streak_type = streak_type if current_streak > 0 else None
        current_streak_length = current_streak if current_streak > 0 else 0
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Best Win Streak", best_win_streak)
        with col2:
            st.metric("Worst Loss Streak", worst_loss_streak)
        with col3:
            if current_streak_type == 'win':
                st.metric("Current Streak", f"🔥 {current_streak_length} wins")
            elif current_streak_type == 'loss':
                st.metric("Current Streak", f"📉 {current_streak_length} losses")
            else:
                st.metric("Current Streak", "None")
        with col4:
            streak_profit = completed.tail(current_streak_length)['profit'].sum() if current_streak_length > 0 else 0
            st.metric("Streak Profit", f"${streak_profit:.2f}")
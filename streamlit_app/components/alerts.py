"""
Alerts Component
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

def display_alerts(alerts_df, inventory_df):
    """Display stock-out alerts and analytics"""
    
    if len(alerts_df) == 0:
        st.success("✅ No active alerts! All inventory levels are healthy.")
        return
    
    # Alert summary
    col1, col2, col3 = st.columns(3)
    
    with col1:
        high_priority = len(alerts_df[alerts_df['priority'] == 'HIGH'])
        st.metric("🔴 High Priority", high_priority)
    
    with col2:
        medium_priority = len(alerts_df[alerts_df['priority'] == 'MEDIUM'])
        st.metric("🟡 Medium Priority", medium_priority)
    
    with col3:
        avg_days_open = alerts_df['days_open'].mean() if len(alerts_df) > 0 else 0
        st.metric("📅 Avg Days Open", f"{avg_days_open:.1f}")
    
    st.markdown("---")
    
    # Visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        # Alerts by location
        location_alerts = alerts_df.groupby('location').size().reset_index(name='count')
        fig = px.bar(
            location_alerts,
            x='location',
            y='count',
            title="Alerts by Location",
            color='count',
            color_continuous_scale='Reds'
        )
        fig.update_layout(showlegend=False, xaxis_tickangle=-45)
        st.plotly_chart(fig, width="stretch")
    
    with col2:
        # Alerts by category
        category_alerts = alerts_df.groupby('category').size().reset_index(name='count')
        fig = px.pie(
            category_alerts,
            values='count',
            names='category',
            title="Alerts by Category",
            color_discrete_sequence=px.colors.sequential.Reds_r
        )
        st.plotly_chart(fig, width="stretch")
    
    # Priority-based alert list
    st.subheader("🚨 Active Alerts")
    
    # Filter options
    priority_filter = st.multiselect(
        "Filter by Priority",
        options=['HIGH', 'MEDIUM', 'LOW'],
        default=['HIGH', 'MEDIUM', 'LOW']
    )
    
    filtered_alerts = alerts_df[alerts_df['priority'].isin(priority_filter)]
    
    # Display alerts as cards
    for _, alert in filtered_alerts.iterrows():
        priority_color = {
            'HIGH': '#ff4b4b',
            'MEDIUM': '#ffa500',
            'LOW': '#ffeb3b'
        }
        
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
            
            with col1:
                st.markdown(f"**{alert['item_name']}**")
                st.caption(f"{alert['location']} • {alert['category']}")
            
            with col2:
                st.metric("Current Stock", alert['current_stock'])
            
            with col3:
                st.metric("Days to Stockout", f"{alert['days_until_stockout']:.1f}")
            
            with col4:
                priority_emoji = {
                    'HIGH': '🔴',
                    'MEDIUM': '🟡',
                    'LOW': '🟢'
                }
                st.markdown(f"### {priority_emoji[alert['priority']]}")
                st.caption(f"{alert['priority']}")
            
            st.markdown(f"<div style='height:2px; background-color:{priority_color[alert['priority']]};'></div>", 
                       unsafe_allow_html=True)
            st.markdown("")
    
    # Alert timeline
    st.subheader("📊 Alert Timeline")
    
    if 'alert_date' in alerts_df.columns:
        alerts_df['alert_date'] = pd.to_datetime(alerts_df['alert_date'])
        timeline_data = alerts_df.groupby('alert_date').size().reset_index(name='count')
        
        fig = px.line(
            timeline_data,
            x='alert_date',
            y='count',
            title="Daily Alert Count",
            markers=True
        )
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Number of Alerts"
        )
        st.plotly_chart(fig, width="stretch")
    
    # Export alerts
    st.subheader("📥 Export Alerts")
    
    csv = filtered_alerts.to_csv(index=False)
    st.download_button(
        label="Download Alerts as CSV",
        data=csv,
        file_name=f"stock_alerts_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

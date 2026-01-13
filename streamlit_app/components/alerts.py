"""
Alerts Component
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

def display_alerts(alerts_df):
    """Display active alerts"""
    st.markdown("## 🚨 Active Stock Alerts")
    
    if len(alerts_df) == 0:
        st.markdown('<div class="success-message">✅ <b>No Critical Alerts!</b> All inventory levels are healthy.</div>', 
                    unsafe_allow_html=True)
        return
    
    # Alert summary
    col1, col2, col3, col4 = st.columns(4)
    
    priority_col = 'PRIORITY' if 'PRIORITY' in alerts_df.columns else 'STOCK_STATUS'
    
    with col1:
        critical = len(alerts_df[alerts_df[priority_col].isin(['CRITICAL', 'HIGH'])])
        st.markdown(f'<div class="critical-alert"><h2>{critical}</h2><p>Critical Alerts</p></div>', 
                    unsafe_allow_html=True)
    
    with col2:
        medium = len(alerts_df[alerts_df[priority_col] == 'MEDIUM']) if 'MEDIUM' in alerts_df[priority_col].values else 0
        st.metric("🟡 Medium Priority", medium)
    
    with col3:
        avg_stockout = alerts_df[alerts_df['DAYS_UNTIL_STOCKOUT'] < 999]['DAYS_UNTIL_STOCKOUT'].mean()
        st.metric("⏱️ Avg Days to Stockout", f"{avg_stockout:.1f}")
    
    with col4:
        locations_affected = alerts_df['LOCATION'].nunique()
        st.metric("📍 Locations Affected", locations_affected)
    
    st.markdown("---")
    
    # Alert list
    st.markdown("### 📋 Alert Details")
    
    # Sort by priority
    if priority_col in alerts_df.columns:
        priority_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        alerts_df['_sort'] = alerts_df[priority_col].map(priority_order)
        alerts_df = alerts_df.sort_values('_sort')
    
    for idx, alert in alerts_df.head(20).iterrows():
        priority = alert.get('PRIORITY', alert.get('STOCK_STATUS', 'UNKNOWN'))
        
        if priority in ['CRITICAL', 'HIGH']:
            alert_class = "critical-alert"
        elif priority == 'MEDIUM':
            alert_class = "warning-alert"
        else:
            alert_class = "success-message"
        
        days_text = f"{alert.get('DAYS_UNTIL_STOCKOUT', 'N/A'):.1f}" if isinstance(alert.get('DAYS_UNTIL_STOCKOUT'), (int, float)) and alert.get('DAYS_UNTIL_STOCKOUT', 999) < 999 else 'N/A'
        
        st.markdown(f"""
        <div class="{alert_class}">
            <h4>🚨 {alert['SKU_NAME']} <span style="float:right; font-size:0.85rem; opacity:0.9;">{priority}</span></h4>
            <p><b>{alert['LOCATION']}</b> • {alert['CATEGORY']} • ABC Class: {alert.get('ABC_CLASS', 'N/A')}</p>
            <p>Stock: <b>{alert['QUANTITY_ON_HAND']:.0f}</b> / Reorder: {alert['REORDER_POINT']:.0f} / Safety: {alert.get('SAFETY_STOCK', 'N/A'):.0f} • Days left: <b>{days_text}</b></p>
        </div>
        """, unsafe_allow_html=True)
    
    if len(alerts_df) > 20:
        st.info(f"Showing top 20 of {len(alerts_df)} alerts. Use filters to narrow down.")

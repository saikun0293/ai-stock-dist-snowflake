"""
Inventory Monitoring Dashboard - Main Application
AI-Powered Stock Management System
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# Import custom modules
from utils import snowflake_connector, data_processing
from components import heatmap, alerts, forecasting, trends

# Page configuration
st.set_page_config(
    page_title="Inventory Monitoring System",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
    .critical-alert {
        background-color: #ff4b4b;
        color: white;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
    .warning-alert {
        background-color: #ffa500;
        color: white;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
    </style>
""", unsafe_allow_html=True)

def load_data():
    """Load data from Snowflake or local CSV for demo"""
    try:
        # Try to load from Snowflake
        conn = snowflake_connector.get_connection()
        if conn:
            inventory_df = snowflake_connector.query_current_inventory(conn)
            alerts_df = snowflake_connector.query_unresolved_alerts(conn)
            forecast_df = snowflake_connector.query_forecast_analysis(conn)
        else:
            raise Exception("No Snowflake connection")
    except Exception as e:
        # Fallback to local demo data
        st.warning("Using demo data. Connect to Snowflake for live data.")
        inventory_df, alerts_df, forecast_df = data_processing.load_demo_data()
    
    return inventory_df, alerts_df, forecast_df

def main():
    # Header
    st.title("📦 Inventory Monitoring & Stock-Out Alert System")
    st.markdown("AI-powered inventory monitoring for essential goods")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Filters")
        
        # Load data
        with st.spinner("Loading data..."):
            inventory_df, alerts_df, forecast_df = load_data()
        
        # Filters
        locations = ["All"] + sorted(inventory_df['location'].unique().tolist())
        selected_location = st.selectbox("Location", locations)
        
        categories = ["All"] + sorted(inventory_df['category'].unique().tolist())
        selected_category = st.selectbox("Category", categories)
        
        stock_status = ["All", "CRITICAL", "LOW", "MODERATE", "GOOD"]
        selected_status = st.selectbox("Stock Status", stock_status)
        
        # Apply filters
        filtered_df = inventory_df.copy()
        if selected_location != "All":
            filtered_df = filtered_df[filtered_df['location'] == selected_location]
        if selected_category != "All":
            filtered_df = filtered_df[filtered_df['category'] == selected_category]
        if selected_status != "All":
            filtered_df = filtered_df[filtered_df['stock_status'] == selected_status]
        
        st.markdown("---")
        st.markdown("### 📊 System Info")
        st.info(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        st.metric("Total Items", len(filtered_df))
        st.metric("Locations", inventory_df['location'].nunique())
    
    # Main content
    # Key Metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        critical_count = len(filtered_df[filtered_df['stock_status'] == 'CRITICAL'])
        st.metric("🔴 Critical Items", critical_count)
    
    with col2:
        low_count = len(filtered_df[filtered_df['stock_status'] == 'LOW'])
        st.metric("🟡 Low Stock", low_count)
    
    with col3:
        moderate_count = len(filtered_df[filtered_df['stock_status'] == 'MODERATE'])
        st.metric("🟠 Moderate", moderate_count)
    
    with col4:
        good_count = len(filtered_df[filtered_df['stock_status'] == 'GOOD'])
        st.metric("🟢 Good Stock", good_count)
    
    with col5:
        active_alerts = len(alerts_df)
        st.metric("⚠️ Active Alerts", active_alerts)
    
    st.markdown("---")
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Heatmap", "🚨 Alerts", "📈 Forecasts", "📉 Trends"])
    
    with tab1:
        st.header("Inventory Heatmap")
        heatmap.display_inventory_heatmap(filtered_df)
    
    with tab2:
        st.header("Stock-Out Alerts")
        alerts.display_alerts(alerts_df, filtered_df)
    
    with tab3:
        st.header("AI Forecasting")
        forecasting.display_forecasts(forecast_df, filtered_df)
    
    with tab4:
        st.header("Stock Trends")
        trends.display_trends(inventory_df, filtered_df)
    
    # Footer
    st.markdown("---")
    st.markdown("""
        <div style='text-align: center; color: gray;'>
            Powered by Snowflake Cortex AI | Built with Streamlit
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

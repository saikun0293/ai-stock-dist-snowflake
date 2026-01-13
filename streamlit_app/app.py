"""
🏥 Inventory Monitoring Dashboard for Essential Goods
AI-Powered Stock Management for Hospitals, NGOs & Distribution Systems
"""

import streamlit as st
import pandas as pd
import logging

# Configure page
st.set_page_config(
    page_title="Inventory Health Monitor",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for hackathon-ready UI
st.markdown("""
<style>
    /* Main container */
    .main { padding: 0rem 1rem; }
    
    /* Metrics styling */
    div[data-testid="metric-container"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        color: white;
    }
    
    div[data-testid="metric-container"] label {
        color: white !important;
        font-weight: 600;
    }
    
    div[data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: white;
        font-size: 2rem;
    }
    
    /* Critical alert styling */
    .critical-alert {
        background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%);
        padding: 12px 16px;
        border-radius: 8px;
        color: white;
        margin: 8px 0;
    }
    
    .critical-alert h4 {
        margin: 0 0 6px 0;
        font-size: 1.1rem;
        font-weight: 600;
    }
    
    .critical-alert p {
        margin: 4px 0;
        font-size: 0.9rem;
        line-height: 1.4;
    }
    
    /* Warning alert */
    .warning-alert {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        padding: 12px 16px;
        border-radius: 8px;
        color: white;
        margin: 8px 0;
        border-left: 4px solid #92400e;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .warning-alert h4 {
        margin: 0 0 6px 0;
        font-size: 1.1rem;
        font-weight: 600;
    }
    
    .warning-alert p {
        margin: 4px 0;
        font-size: 0.9rem;
        line-height: 1.4;
    }
    
    /* Success message */
    .success-message {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        padding: 15px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
    }
    
    /* Header styling */
    h1 {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 800;
    }
    
    /* Button styling */
    .stDownloadButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 600;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: transform 0.2s;
    }
    
    .stDownloadButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: #f7f9fc;
    }
    
    /* Table styling */
    .dataframe {
        border: none !important;
    }
</style>
""", unsafe_allow_html=True)

# Import connectors
try:
    from utils.snowflake_connector import (
        get_connection, query_stock_health, query_active_alerts,
        query_reorder_recommendations, query_location_performance,
        query_category_heatmap, export_reorder_list, log_export
    )
    USE_SNOWFLAKE = True
except Exception as e:
    USE_SNOWFLAKE = False
    st.warning(f"⚠️ Snowflake connector not available. Using demo mode. Error: {e}")

# Import components
from components.alerts import display_alerts
from components.reorder import display_reorder_list
from components.analytics import display_analytics

def load_data_from_snowflake():
    """Load data from Snowflake"""
    conn = get_connection()
    if conn:
        stock_df = query_stock_health(conn)
        alerts_df = query_active_alerts(conn)
        reorder_df = query_reorder_recommendations(conn)
        location_df = query_location_performance(conn)
        heatmap_df = query_category_heatmap(conn)
        return stock_df, alerts_df, reorder_df, location_df, heatmap_df, conn
    return None, None, None, None, None, None

def generate_trends_data(df):
    """Generate time series data for trends analysis"""
    from datetime import datetime, timedelta
    import random
    
    # Create historical data for last 30 days
    trends_data = []
    today = datetime.now()
    
    # Use all filtered items for complete trend analysis
    for _, row in df.iterrows():
        current_stock = row.get('QUANTITY_ON_HAND', 100)
        daily_sales = row.get('AVG_DAILY_SALES', 5)
        
        # Add some randomness to daily sales for more realistic trends
        actual_daily_sales = daily_sales * random.uniform(0.8, 1.2)
        
        # Work BACKWARDS from today so latest date has actual current stock
        for days_ago in range(30, -1, -1):  # 30, 29, 28, ..., 1, 0
            date = today - timedelta(days=days_ago)
            
            # Calculate historical stock (higher in the past)
            if days_ago == 0:
                # Today: use actual current stock
                stock_level = float(current_stock)
            else:
                # Past days: add back consumed stock with variation
                stock_level = float(current_stock + (actual_daily_sales * days_ago) + random.randint(-10, 10))
                stock_level = max(0, stock_level)  # Can't be negative
            
            # Daily consumption with variation
            daily_consumption = actual_daily_sales * random.uniform(0.8, 1.2)
            
            trends_data.append({
                'snapshot_date': date,
                'sku_id': row.get('SKU_ID', ''),
                'item_name': row.get('SKU_NAME', 'Unknown'),
                'location': row.get('LOCATION', 'Unknown'),
                'category': row.get('CATEGORY', 'Unknown'),
                'current_stock': stock_level,
                'consumption': float(max(0, daily_consumption)),
                'reorder_point': float(row.get('REORDER_POINT', 50)),
                'safety_stock': float(row.get('SAFETY_STOCK', 25))
            })
    
    return pd.DataFrame(trends_data)

def load_demo_data():
    """Load demo data from CSV"""
    import random
    
    # Create sample data
    locations = ["Mumbai Central", "Delhi NCR", "Bangalore South", "Chennai East", "Kolkata North"]
    categories = ["Medicines", "Medical Supplies", "Food & Nutrition", "Hygiene Products", "Emergency Supplies"]
    
    data = []
    for i in range(100):
        location = random.choice(locations)
        category = random.choice(categories)
        reorder = random.randint(50, 200)
        
        # Generate more realistic stock levels with better distribution
        # 20% critical, 30% low, 50% healthy
        stock_type = random.choices(['critical', 'low', 'healthy'], weights=[0.2, 0.3, 0.5])[0]
        
        if stock_type == 'critical':
            qty = random.randint(10, int(reorder * 0.4))  # Below safety stock
        elif stock_type == 'low':
            qty = random.randint(int(reorder * 0.5), reorder)  # At or below reorder point
        else:
            qty = random.randint(reorder, int(reorder * 2.5))  # Healthy stock
        
        data.append({
            'SKU_ID': f'SKU{i:04d}',
            'SKU_NAME': f'{category} Item {i}',
            'CATEGORY': category,
            'LOCATION': location,
            'ABC_CLASS': random.choice(['A', 'B', 'C']),
            'QUANTITY_ON_HAND': qty,
            'REORDER_POINT': reorder,
            'SAFETY_STOCK': reorder * 0.5,
            'AVG_DAILY_SALES': random.randint(5, 20),
            'STOCK_STATUS': 'CRITICAL' if qty < reorder * 0.5 else 'LOW' if qty < reorder else 'HEALTHY',
            'RISK_SCORE': 90 if qty < reorder * 0.5 else 70 if qty < reorder else 20,
            'UNIT_COST_USD': random.uniform(10, 500)
        })
    
    df = pd.DataFrame(data)
    df['DAYS_UNTIL_STOCKOUT'] = df.apply(
        lambda x: round(x['QUANTITY_ON_HAND'] / x['AVG_DAILY_SALES'], 1) if x['AVG_DAILY_SALES'] > 0 else 999, axis=1
    )
    
    return df, df[df['RISK_SCORE'] >= 70], df[df['QUANTITY_ON_HAND'] <= df['REORDER_POINT']], None, None, None

def main():
    # Header with emoji
    st.markdown("# 🏥 Inventory Health Monitor")
    st.markdown("### AI-Powered Stock Management for Essential Goods")
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.markdown("## ⚙️ Control Panel")
        
        # Load data
        with st.spinner("🔄 Loading inventory data..."):
            if USE_SNOWFLAKE:
                stock_df, alerts_df, reorder_df, location_df, heatmap_df, conn = load_data_from_snowflake()
                logging.info(f"Successfully loaded data from Snowflake - USE_SNOWFLAKE={USE_SNOWFLAKE}")
                if stock_df is None:
                    logging.info("Falling back to demo data due to failed Snowflake data load.")
                    stock_df, alerts_df, reorder_df, location_df, heatmap_df, conn = load_demo_data()
            else:
                stock_df, alerts_df, reorder_df, location_df, heatmap_df, conn = load_demo_data()
        
        if stock_df is None or len(stock_df) == 0:
            st.error("❌ No data available")
            return
        
        st.success(f"✅ Loaded {len(stock_df)} items")
        
        # Filters
        st.markdown("### 🔍 Filters")
        locations = ["All"] + sorted(stock_df['LOCATION'].unique().tolist())
        selected_location = st.selectbox("📍 Location", locations)
        
        categories = ["All"] + sorted(stock_df['CATEGORY'].unique().tolist())
        selected_category = st.selectbox("📦 Category", categories)
        
        status_options = ["All", "CRITICAL", "LOW", "MODERATE", "HEALTHY"]
        selected_status = st.selectbox("⚡ Stock Status", status_options)
        
        # Apply filters
        filtered_df = stock_df.copy()
        if selected_location != "All":
            filtered_df = filtered_df[filtered_df['LOCATION'] == selected_location]
        if selected_category != "All":
            filtered_df = filtered_df[filtered_df['CATEGORY'] == selected_category]
        if selected_status != "All":
            filtered_df = filtered_df[filtered_df['STOCK_STATUS'] == selected_status]
        
        st.markdown("---")
        st.markdown(f"**Showing:** {len(filtered_df)} items")
    
    # Main Dashboard
    # KPI Metrics Row (based on filtered data)
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        critical_count = len(filtered_df[filtered_df['STOCK_STATUS'] == 'CRITICAL'])
        st.metric("🔴 Critical Items", critical_count)
    
    with col2:
        low_count = len(filtered_df[filtered_df['STOCK_STATUS'] == 'LOW'])
        st.metric("🟡 Low Stock", low_count)
    
    with col3:
        avg_days = filtered_df[filtered_df['DAYS_UNTIL_STOCKOUT'] < 999]['DAYS_UNTIL_STOCKOUT'].mean()
        st.metric("📅 Avg Days to Stockout", f"{avg_days:.1f}", delta=f"Monitor closely", delta_color="inverse")
    
    with col4:
        total_value = filtered_df['QUANTITY_ON_HAND'].sum() * filtered_df['UNIT_COST_USD'].mean()
        st.metric("💰 Total Inventory Value", f"${total_value:,.0f}")
    
    with col5:
        health_score = 100 - (critical_count + low_count) / len(filtered_df) * 100 if len(filtered_df) > 0 else 0
        st.metric("❤️ Overall Health Score", f"{health_score:.0f}%", delta=f"{health_score:.0f}% healthy")
    
    st.markdown("---")
    
    # Tab Navigation
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "🗺️ Heatmap View", 
        "🚨 Active Alerts", 
        "📋 Reorder List", 
        "📊 Analytics", 
        "📈 Forecasting",
        "📉 Trends",
        "🧠 AI Insights"
    ])
    
    # Apply filters to all dataframes
    filtered_alerts_df = alerts_df.copy() if alerts_df is not None else filtered_df[filtered_df['RISK_SCORE'] >= 70].copy()
    if selected_location != "All" and len(filtered_alerts_df) > 0:
        filtered_alerts_df = filtered_alerts_df[filtered_alerts_df['LOCATION'] == selected_location]
    if selected_category != "All" and len(filtered_alerts_df) > 0:
        filtered_alerts_df = filtered_alerts_df[filtered_alerts_df['CATEGORY'] == selected_category]
    
    filtered_reorder_df = reorder_df.copy() if reorder_df is not None else filtered_df.copy()
    if selected_location != "All" and len(filtered_reorder_df) > 0:
        filtered_reorder_df = filtered_reorder_df[filtered_reorder_df['LOCATION'] == selected_location]
    if selected_category != "All" and len(filtered_reorder_df) > 0:
        filtered_reorder_df = filtered_reorder_df[filtered_reorder_df['CATEGORY'] == selected_category]
    
    filtered_heatmap_df = heatmap_df.copy() if heatmap_df is not None else filtered_df.copy()
    if selected_location != "All" and len(filtered_heatmap_df) > 0:
        filtered_heatmap_df = filtered_heatmap_df[filtered_heatmap_df['LOCATION'] == selected_location]
    if selected_category != "All" and len(filtered_heatmap_df) > 0:
        filtered_heatmap_df = filtered_heatmap_df[filtered_heatmap_df['CATEGORY'] == selected_category]
    
    with tab1:
        from components.heatmap import display_heatmap
        display_heatmap(filtered_df, filtered_heatmap_df)
    
    with tab2:
        display_alerts(filtered_alerts_df)
    
    with tab3:
        display_reorder_list(filtered_reorder_df, conn, selected_location, selected_category)
    
    with tab4:
        display_analytics(filtered_df, location_df)
    
    with tab5:
        from components.forecasting import display_forecasts, generate_forecast_data
        forecast_df = generate_forecast_data(filtered_df)
        display_forecasts(forecast_df, filtered_df)
    
    with tab6:
        # Trends tab
        from components.trends import display_trends
        trends_df = generate_trends_data(stock_df if stock_df is not None else filtered_df)
        display_trends(trends_df, filtered_df)
    
    with tab7:
        from components.cortex_ai import display_cortex_features
        if conn is not None:
            display_cortex_features(conn, filtered_df, filtered_alerts_df)
        else:
            st.warning("⚠️ Snowflake connection required for AI features. Connect to Snowflake to enable.")
            st.info("💡 AI features include: Natural Language Chat, Anomaly Detection, Demand Forecasting, and Auto-Generated Insights.")


if __name__ == "__main__":
    main()

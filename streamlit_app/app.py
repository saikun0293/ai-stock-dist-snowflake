"""
🏥 Inventory Monitoring Dashboard for Essential Goods
AI-Powered Stock Management for Hospitals, NGOs & Distribution Systems
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
from io import BytesIO

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
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 15px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.8; }
    }
    
    /* Warning alert */
    .warning-alert {
        background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        padding: 15px;
        border-radius: 10px;
        color: #333;
        margin: 10px 0;
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
    from streamlit_app.utils.snowflake_connector import (
        get_connection, query_stock_health, query_active_alerts,
        query_reorder_recommendations, query_location_performance,
        query_category_heatmap, export_reorder_list, log_export
    )
    USE_SNOWFLAKE = True
except:
    USE_SNOWFLAKE = False
    st.warning("⚠️ Snowflake connector not available. Using demo mode.")

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
        qty = random.randint(0, 500)
        reorder = random.randint(50, 150)
        
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
                if stock_df is None:
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
    # KPI Metrics Row
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        critical_count = len(stock_df[stock_df['STOCK_STATUS'] == 'CRITICAL'])
        st.metric("🔴 Critical Items", critical_count, delta=f"-{critical_count} urgent", delta_color="inverse")
    
    with col2:
        low_count = len(stock_df[stock_df['STOCK_STATUS'] == 'LOW'])
        st.metric("🟡 Low Stock", low_count, delta=f"{low_count} need attention")
    
    with col3:
        avg_days = stock_df[stock_df['DAYS_UNTIL_STOCKOUT'] < 999]['DAYS_UNTIL_STOCKOUT'].mean()
        st.metric("📅 Avg Days to Stockout", f"{avg_days:.1f}", delta=f"Monitor closely")
    
    with col4:
        total_value = stock_df['QUANTITY_ON_HAND'].sum() * stock_df['UNIT_COST_USD'].mean()
        st.metric("💰 Total Inventory Value", f"${total_value:,.0f}")
    
    with col5:
        health_score = 100 - (critical_count + low_count) / len(stock_df) * 100
        st.metric("❤️ Overall Health Score", f"{health_score:.0f}%", delta=f"{health_score:.0f}% healthy")
    
    st.markdown("---")
    
    # Tab Navigation
    tab1, tab2, tab3, tab4 = st.tabs(["🗺️ Heatmap View", "🚨 Active Alerts", "📋 Reorder List", "📊 Analytics"])
    
    with tab1:
        display_heatmap(filtered_df, heatmap_df if heatmap_df is not None else filtered_df)
    
    with tab2:
        display_alerts(alerts_df if alerts_df is not None else filtered_df[filtered_df['RISK_SCORE'] >= 70])
    
    with tab3:
        display_reorder_list(reorder_df if reorder_df is not None else filtered_df, conn, selected_location, selected_category)
    
    with tab4:
        display_analytics(stock_df, location_df)

def display_heatmap(df, heatmap_df):
    """Display interactive heatmap"""
    st.markdown("## 🗺️ Inventory Health Heatmap")
    st.markdown("**Visual overview of stock levels across locations and categories**")
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        view_mode = st.radio("View By", ["Location x Category", "Individual Items"])
        color_metric = st.selectbox("Color By", ["Risk Score", "Stock Status", "Days Until Stockout"])
    
    with col1:
        if view_mode == "Location x Category":
            # Aggregate heatmap
            if 'AVG_RISK_SCORE' in heatmap_df.columns:
                pivot_df = heatmap_df.pivot_table(
                    values='AVG_RISK_SCORE',
                    index='CATEGORY',
                    columns='LOCATION',
                    aggfunc='mean'
                )
            else:
                pivot_df = df.pivot_table(
                    values='RISK_SCORE',
                    index='CATEGORY',
                    columns='LOCATION',
                    aggfunc='mean'
                )
            
            fig = go.Figure(data=go.Heatmap(
                z=pivot_df.values,
                x=pivot_df.columns,
                y=pivot_df.index,
                colorscale='RdYlGn_r',
                text=pivot_df.values.round(1),
                texttemplate='%{text}',
                textfont={"size": 12},
                colorbar=dict(title="Risk Score")
            ))
            
            fig.update_layout(
                title="Stock Health by Location & Category",
                xaxis_title="Location",
                yaxis_title="Category",
                height=500,
                font=dict(size=12)
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        else:
            # Individual items scatter
            fig = px.scatter(
                df.head(200),
                x='LOCATION',
                y='CATEGORY',
                size='QUANTITY_ON_HAND',
                color='RISK_SCORE',
                hover_data=['SKU_NAME', 'QUANTITY_ON_HAND', 'DAYS_UNTIL_STOCKOUT'],
                color_continuous_scale='RdYlGn_r',
                title="Item-Level Stock Health"
            )
            
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
    
    # Stock distribution
    st.markdown("### 📊 Stock Distribution")
    col1, col2 = st.columns(2)
    
    with col1:
        status_counts = df['STOCK_STATUS'].value_counts()
        fig = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title="Items by Stock Status",
            color=status_counts.index,
            color_discrete_map={
                'CRITICAL': '#f5576c',
                'LOW': '#ffa500',
                'MODERATE': '#ffeb3b',
                'HEALTHY': '#4caf50'
            }
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        category_counts = df.groupby('CATEGORY')['STOCK_STATUS'].value_counts().unstack(fill_value=0)
        fig = px.bar(
            category_counts,
            title="Stock Status by Category",
            barmode='stack',
            color_discrete_map={
                'CRITICAL': '#f5576c',
                'LOW': '#ffa500',
                'MODERATE': '#ffeb3b',
                'HEALTHY': '#4caf50'
            }
        )
        st.plotly_chart(fig, use_container_width=True)

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
        
        st.markdown(f"""
        <div class="{alert_class}">
            <h4>🚨 {alert['SKU_NAME']}</h4>
            <p><b>Location:</b> {alert['LOCATION']} | <b>Category:</b> {alert['CATEGORY']}</p>
            <p><b>Current Stock:</b> {alert['QUANTITY_ON_HAND']:.0f} | <b>Reorder Point:</b> {alert['REORDER_POINT']:.0f} | 
               <b>Days to Stockout:</b> {alert.get('DAYS_UNTIL_STOCKOUT', 'N/A')}</p>
            <p><b>Priority:</b> {priority}</p>
        </div>
        """, unsafe_allow_html=True)
    
    if len(alerts_df) > 20:
        st.info(f"Showing top 20 of {len(alerts_df)} alerts. Use filters to narrow down.")

def display_reorder_list(reorder_df, conn, location_filter, category_filter):
    """Display and export reorder recommendations"""
    st.markdown("## 📋 Reorder Recommendations")
    st.markdown("**Export-ready procurement list with recommended order quantities**")
    
    if len(reorder_df) == 0:
        st.success("✅ No items need reordering at this time!")
        return
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_items = len(reorder_df)
        st.metric("📦 Items to Reorder", total_items)
    
    with col2:
        if 'ESTIMATED_ORDER_VALUE_USD' in reorder_df.columns:
            total_value = reorder_df['ESTIMATED_ORDER_VALUE_USD'].sum()
        else:
            total_value = (reorder_df['REORDER_POINT'] * reorder_df['UNIT_COST_USD']).sum()
        st.metric("💰 Total Order Value", f"${total_value:,.0f}")
    
    with col3:
        if 'PRIORITY_SCORE' in reorder_df.columns:
            urgent = len(reorder_df[reorder_df['PRIORITY_SCORE'] >= 8])
        else:
            urgent = len(reorder_df[reorder_df['QUANTITY_ON_HAND'] <= reorder_df['SAFETY_STOCK']])
        st.metric("🚨 Urgent Items", urgent)
    
    with col4:
        suppliers = reorder_df['SUPPLIER_NAME'].nunique() if 'SUPPLIER_NAME' in reorder_df.columns else 0
        st.metric("🏢 Suppliers Involved", suppliers)
    
    st.markdown("---")
    
    # Display table
    display_cols = ['SKU_ID', 'SKU_NAME', 'CATEGORY', 'LOCATION', 'QUANTITY_ON_HAND', 'REORDER_POINT']
    if 'RECOMMENDED_ORDER_QTY' in reorder_df.columns:
        display_cols.append('RECOMMENDED_ORDER_QTY')
    if 'PRIORITY_SCORE' in reorder_df.columns:
        display_cols.append('PRIORITY_SCORE')
    if 'UNIT_COST_USD' in reorder_df.columns:
        display_cols.append('UNIT_COST_USD')
    if 'SUPPLIER_NAME' in reorder_df.columns:
        display_cols.append('SUPPLIER_NAME')
    
    available_cols = [col for col in display_cols if col in reorder_df.columns]
    st.dataframe(reorder_df[available_cols].head(100), use_container_width=True, height=400)
    
    # Export section
    st.markdown("### 📥 Export Reorder List")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        export_format = st.selectbox("Format", ["CSV", "Excel"])
    
    with col2:
        include_all = st.checkbox("Include all items", value=True)
    
    with col3:
        st.write("")  # Spacer
    
    # Generate export
    export_df = reorder_df.copy()
    
    if not include_all:
        export_df = export_df.head(100)
    
    # Rename columns for export
    export_df = export_df.rename(columns={
        'SKU_ID': 'SKU ID',
        'SKU_NAME': 'Item Name',
        'CATEGORY': 'Category',
        'LOCATION': 'Location',
        'QUANTITY_ON_HAND': 'Current Stock',
        'REORDER_POINT': 'Reorder Point',
        'RECOMMENDED_ORDER_QTY': 'Recommended Qty',
        'UNIT_COST_USD': 'Unit Cost (USD)',
        'SUPPLIER_NAME': 'Supplier'
    })
    
    if export_format == "CSV":
        csv = export_df.to_csv(index=False)
        st.download_button(
            label="⬇️ Download CSV",
            data=csv,
            file_name=f"reorder_list_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            export_df.to_excel(writer, sheet_name='Reorder List', index=False)
        
        st.download_button(
            label="⬇️ Download Excel",
            data=buffer.getvalue(),
            file_name=f"reorder_list_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    # Log export if connected to Snowflake
    if conn:
        try:
            log_export(conn, 'REORDER_LIST', len(export_df), 'dashboard_user', export_format,
                      {'location': location_filter, 'category': category_filter})
        except:
            pass

def display_analytics(stock_df, location_df):
    """Display analytics and insights"""
    st.markdown("## 📊 Analytics & Insights")
    
    # Location performance
    if location_df is not None and len(location_df) > 0:
        st.markdown("### 📍 Warehouse Performance")
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=location_df['LOCATION'],
            y=location_df['CRITICAL_COUNT'],
            name='Critical Items',
            marker_color='#f5576c'
        ))
        
        fig.add_trace(go.Bar(
            x=location_df['LOCATION'],
            y=location_df['LOW_STOCK_COUNT'],
            name='Low Stock Items',
            marker_color='#ffa500'
        ))
        
        fig.add_trace(go.Bar(
            x=location_df['LOCATION'],
            y=location_df['HEALTHY_COUNT'],
            name='Healthy Items',
            marker_color='#4caf50'
        ))
        
        fig.update_layout(
            barmode='stack',
            title='Stock Health by Location',
            xaxis_title='Location',
            yaxis_title='Number of Items',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # ABC Analysis
    st.markdown("### 🎯 ABC Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        abc_counts = stock_df['ABC_CLASS'].value_counts()
        fig = px.pie(
            values=abc_counts.values,
            names=abc_counts.index,
            title="Items by ABC Classification",
            color_discrete_sequence=px.colors.sequential.Blues_r
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Risk by ABC class
        abc_risk = stock_df.groupby('ABC_CLASS')['RISK_SCORE'].mean().reset_index()
        fig = px.bar(
            abc_risk,
            x='ABC_CLASS',
            y='RISK_SCORE',
            title="Average Risk Score by ABC Class",
            color='RISK_SCORE',
            color_continuous_scale='RdYlGn_r'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Top issues
    st.markdown("### ⚠️ Top 10 Critical Items")
    
    critical_items = stock_df.nlargest(10, 'RISK_SCORE')[
        ['SKU_NAME', 'LOCATION', 'CATEGORY', 'QUANTITY_ON_HAND', 'REORDER_POINT', 'DAYS_UNTIL_STOCKOUT', 'RISK_SCORE']
    ]
    
    st.dataframe(critical_items, use_container_width=True)

if __name__ == "__main__":
    main()

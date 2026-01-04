"""
Trends Component
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta

def display_trends(full_df, filtered_df):
    """Display stock trends and analytics"""
    
    if len(filtered_df) == 0:
        st.warning("No data available for trend analysis.")
        return
    
    # Time period selector
    col1, col2 = st.columns([3, 1])
    
    with col2:
        days_back = st.selectbox(
            "Time Period",
            options=[7, 14, 30, 60, 90],
            index=2,
            format_func=lambda x: f"Last {x} days"
        )
    
    # Category trends
    st.subheader("📈 Category Stock Trends")
    
    # Aggregate by category
    if 'snapshot_date' in full_df.columns or 'date' in full_df.columns:
        date_col = 'snapshot_date' if 'snapshot_date' in full_df.columns else 'date'
        full_df[date_col] = pd.to_datetime(full_df[date_col])
        
        # Filter by date range
        cutoff_date = datetime.now() - timedelta(days=days_back)
        recent_df = full_df[full_df[date_col] >= cutoff_date]
        
        if len(recent_df) > 0:
            # Stock levels by category over time
            category_trends = recent_df.groupby([date_col, 'category'])['current_stock'].sum().reset_index()
            
            fig = px.line(
                category_trends,
                x=date_col,
                y='current_stock',
                color='category',
                title=f"Stock Levels by Category (Last {days_back} Days)",
                markers=True
            )
            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Total Stock",
                hovermode='x unified'
            )
            st.plotly_chart(fig, width="stretch")
            
            # Consumption trends
            if 'consumption' in recent_df.columns:
                st.subheader("📉 Consumption Trends")
                
                consumption_trends = recent_df.groupby([date_col, 'category'])['consumption'].sum().reset_index()
                
                fig = px.area(
                    consumption_trends,
                    x=date_col,
                    y='consumption',
                    color='category',
                    title=f"Daily Consumption by Category (Last {days_back} Days)"
                )
                fig.update_layout(
                    xaxis_title="Date",
                    yaxis_title="Consumption",
                    hovermode='x unified'
                )
                st.plotly_chart(fig, width="stretch")
    
    # Location comparison
    st.subheader("🏥 Location Comparison")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Stock distribution by location
        location_stock = filtered_df.groupby('location')['current_stock'].sum().reset_index()
        location_stock = location_stock.sort_values('current_stock', ascending=True)
        
        fig = px.bar(
            location_stock,
            x='current_stock',
            y='location',
            orientation='h',
            title="Total Stock by Location",
            color='current_stock',
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig, width="stretch")
    
    with col2:
        # Stock status by location
        status_by_location = filtered_df.groupby(['location', 'stock_status']).size().reset_index(name='count')
        
        fig = px.bar(
            status_by_location,
            x='location',
            y='count',
            color='stock_status',
            title="Stock Status Distribution by Location",
            color_discrete_map={
                'CRITICAL': '#ff4b4b',
                'LOW': '#ffa500',
                'MODERATE': '#ffeb3b',
                'GOOD': '#4caf50'
            },
            barmode='stack'
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, width="stretch")
    
    # Item-level analysis
    st.subheader("🔍 Item-Level Analysis")
    
    # Select an item for detailed view
    selected_item = st.selectbox(
        "Select item for detailed analysis",
        options=sorted(filtered_df['item_name'].unique())
    )
    
    if selected_item:
        item_df = filtered_df[filtered_df['item_name'] == selected_item]
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_stock = item_df['current_stock'].sum()
            st.metric("Total Stock Across Locations", total_stock)
        
        with col2:
            avg_stock_pct = item_df['stock_percentage'].mean()
            st.metric("Avg Stock Percentage", f"{avg_stock_pct:.1f}%")
        
        with col3:
            critical_locations = len(item_df[item_df['stock_status'].isin(['CRITICAL', 'LOW'])])
            st.metric("Locations with Issues", critical_locations)
        
        # Stock by location for selected item
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Current Stock',
            x=item_df['location'],
            y=item_df['current_stock'],
            marker_color='lightblue'
        ))
        
        fig.add_trace(go.Bar(
            name='Max Stock',
            x=item_df['location'],
            y=item_df['max_stock'],
            marker_color='lightgray',
            opacity=0.5
        ))
        
        fig.update_layout(
            title=f"Stock Levels: {selected_item}",
            xaxis_title="Location",
            yaxis_title="Stock Level",
            barmode='overlay',
            xaxis_tickangle=-45
        )
        
        st.plotly_chart(fig, width="stretch")
    
    # Summary statistics
    st.subheader("📊 Summary Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_items = filtered_df['item_name'].nunique()
        st.metric("Unique Items", total_items)
    
    with col2:
        total_locations = filtered_df['location'].nunique()
        st.metric("Locations", total_locations)
    
    with col3:
        avg_stock_percentage = filtered_df['stock_percentage'].mean()
        st.metric("Avg Stock Level", f"{avg_stock_percentage:.1f}%")
    
    with col4:
        items_needing_restock = len(filtered_df[filtered_df['stock_percentage'] < 25])
        st.metric("Items Needing Restock", items_needing_restock)

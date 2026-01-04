"""
Inventory Heatmap Component
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def display_inventory_heatmap(df):
    """Display interactive inventory heatmap"""
    
    if len(df) == 0:
        st.warning("No data available for the selected filters.")
        return
    
    # Display options
    col1, col2 = st.columns([3, 1])
    
    with col2:
        view_by = st.radio("View by", ["Category", "Location"])
        color_by = st.selectbox("Color by", ["Stock Status", "Stock Percentage", "Days Until Stockout"])
    
    with col1:
        # Prepare data for heatmap
        if view_by == "Category":
            pivot_col = 'category'
        else:
            pivot_col = 'location'
        
        # Create pivot table based on color scheme
        if color_by == "Stock Status":
            # Status-based heatmap
            display_status_heatmap(df, pivot_col)
        elif color_by == "Stock Percentage":
            display_percentage_heatmap(df, pivot_col)
        else:
            display_stockout_heatmap(df, pivot_col)
    
    # Detailed table view
    st.subheader("Detailed Inventory")
    
    # Add search and filters
    search = st.text_input("🔍 Search items", "")
    if search:
        df = df[df['item_name'].str.contains(search, case=False)]
    
    # Display table
    display_cols = ['location', 'category', 'item_name', 'current_stock', 
                    'max_stock', 'stock_percentage', 'stock_status', 'days_until_stockout']
    
    # Color code the status column
    def highlight_status(row):
        if row['stock_status'] == 'CRITICAL':
            return ['background-color: #ff4b4b'] * len(row)
        elif row['stock_status'] == 'LOW':
            return ['background-color: #ffa500'] * len(row)
        elif row['stock_status'] == 'MODERATE':
            return ['background-color: #ffeb3b'] * len(row)
        else:
            return ['background-color: #4caf50'] * len(row)
    
    styled_df = df[display_cols].style.apply(highlight_status, axis=1)
    st.dataframe(styled_df, use_container_width=True, height=400)

def display_status_heatmap(df, pivot_col):
    """Display heatmap colored by stock status"""
    
    # Create a matrix for heatmap
    status_map = {'CRITICAL': 1, 'LOW': 2, 'MODERATE': 3, 'GOOD': 4}
    df['status_value'] = df['stock_status'].map(status_map)
    
    # Pivot data
    if pivot_col == 'category':
        heatmap_data = df.pivot_table(
            values='status_value',
            index='item_name',
            columns='location',
            aggfunc='mean'
        )
    else:
        heatmap_data = df.pivot_table(
            values='status_value',
            index='item_name',
            columns='category',
            aggfunc='mean'
        )
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=heatmap_data.columns,
        y=heatmap_data.index,
        colorscale=[
            [0, '#ff4b4b'],      # Critical
            [0.33, '#ffa500'],   # Low
            [0.66, '#ffeb3b'],   # Moderate
            [1, '#4caf50']       # Good
        ],
        hovertemplate='<b>%{y}</b><br>%{x}<br>Status: %{z:.1f}<extra></extra>',
        colorbar=dict(
            title="Stock Status",
            tickvals=[1, 2, 3, 4],
            ticktext=['Critical', 'Low', 'Moderate', 'Good']
        )
    ))
    
    fig.update_layout(
        title=f"Inventory Status Heatmap by {pivot_col.title()}",
        xaxis_title=pivot_col.title(),
        yaxis_title="Item",
        height=600
    )
    
    st.plotly_chart(fig, use_container_width=True)

def display_percentage_heatmap(df, pivot_col):
    """Display heatmap colored by stock percentage"""
    
    # Pivot data
    if pivot_col == 'category':
        heatmap_data = df.pivot_table(
            values='stock_percentage',
            index='item_name',
            columns='location',
            aggfunc='mean'
        )
    else:
        heatmap_data = df.pivot_table(
            values='stock_percentage',
            index='item_name',
            columns='category',
            aggfunc='mean'
        )
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=heatmap_data.columns,
        y=heatmap_data.index,
        colorscale='RdYlGn',
        hovertemplate='<b>%{y}</b><br>%{x}<br>Stock: %{z:.1f}%<extra></extra>',
        colorbar=dict(title="Stock %")
    ))
    
    fig.update_layout(
        title=f"Stock Percentage Heatmap by {pivot_col.title()}",
        xaxis_title=pivot_col.title(),
        yaxis_title="Item",
        height=600
    )
    
    st.plotly_chart(fig, use_container_width=True)

def display_stockout_heatmap(df, pivot_col):
    """Display heatmap colored by days until stockout"""
    
    # Cap days at 30 for visualization
    df['days_capped'] = df['days_until_stockout'].clip(upper=30)
    
    # Pivot data
    if pivot_col == 'category':
        heatmap_data = df.pivot_table(
            values='days_capped',
            index='item_name',
            columns='location',
            aggfunc='mean'
        )
    else:
        heatmap_data = df.pivot_table(
            values='days_capped',
            index='item_name',
            columns='category',
            aggfunc='mean'
        )
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=heatmap_data.columns,
        y=heatmap_data.index,
        colorscale='RdYlGn',
        hovertemplate='<b>%{y}</b><br>%{x}<br>Days: %{z:.1f}<extra></extra>',
        colorbar=dict(title="Days to Stockout")
    ))
    
    fig.update_layout(
        title=f"Days Until Stockout Heatmap by {pivot_col.title()}",
        xaxis_title=pivot_col.title(),
        yaxis_title="Item",
        height=600
    )
    
    st.plotly_chart(fig, use_container_width=True)

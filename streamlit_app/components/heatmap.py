"""
Inventory Heatmap Component
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def display_heatmap(df, heatmap_df):
    """Display interactive heatmap"""
    st.markdown("## 🗺️ Inventory Health Heatmap")
    st.markdown("**Visual overview of stock levels across locations and categories**")
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        view_mode = st.radio("View By", ["Location x Category", "Individual Items"])
        color_metric = st.selectbox("Color By", ["Risk Score", "Days Until Stockout", "Critical Items %"])
    
    with col1:
        if view_mode == "Location x Category":
            # Use pre-aggregated heatmap_df if available from Snowflake
            if heatmap_df is not None and len(heatmap_df) > 0 and 'AVG_RISK_SCORE' in heatmap_df.columns:
                # Determine which column to use based on selection
                if color_metric == "Risk Score":
                    value_col = 'AVG_RISK_SCORE'
                    color_scale = 'RdYlGn_r'  # Red=high risk (bad), Green=low risk (good)
                elif color_metric == "Days Until Stockout":
                    value_col = 'AVG_DAYS_COVERAGE'
                    color_scale = 'RdYlGn'  # Green=more days (good), Red=fewer days (bad)
                else:  # Critical Items %
                    # Calculate percentage of critical items
                    heatmap_df['_critical_pct'] = (heatmap_df['CRITICAL_SKUS'] / heatmap_df['TOTAL_SKUS'] * 100).fillna(0)
                    value_col = '_critical_pct'
                    color_scale = 'RdYlGn_r'  # Red=high % critical (bad), Green=low % (good)
                
                # Create pivot table
                pivot_df = heatmap_df.pivot_table(
                    values=value_col,
                    index='CATEGORY',
                    columns='LOCATION',
                    aggfunc='mean'
                )
            else:
                # Fallback: calculate from raw df
                if color_metric == "Risk Score":
                    value_col = 'RISK_SCORE'
                    color_scale = 'RdYlGn_r'
                elif color_metric == "Days Until Stockout":
                    value_col = 'DAYS_UNTIL_STOCKOUT'
                    color_scale = 'RdYlGn'
                else:  # Critical Items %
                    # Calculate percentage of critical items
                    df['_is_critical'] = (df['STOCK_STATUS'] == 'CRITICAL').astype(int) * 100
                    value_col = '_is_critical'
                    color_scale = 'RdYlGn_r'
                
                pivot_df = df.pivot_table(
                    values=value_col,
                    index='CATEGORY',
                    columns='LOCATION',
                    aggfunc='mean'
                )
            
            # Create heatmap
            fig = go.Figure(data=go.Heatmap(
                z=pivot_df.values,
                x=pivot_df.columns,
                y=pivot_df.index,
                colorscale=color_scale,
                text=pivot_df.values.round(1),
                texttemplate='%{text}',
                textfont={"size": 12},
                colorbar=dict(title=color_metric)
            ))
            
            fig.update_layout(
                title=f"Stock Health by Location & Category ({color_metric})",
                xaxis_title="Location",
                yaxis_title="Category",
                height=500,
                font=dict(size=12)
            )
            
            st.plotly_chart(fig, width="stretch")
        
        else:
            # Individual items scatter - show all filtered items
            if color_metric == "Risk Score":
                color_col = 'RISK_SCORE'
                color_scale = 'RdYlGn_r'
            elif color_metric == "Days Until Stockout":
                color_col = 'DAYS_UNTIL_STOCKOUT'
                color_scale = 'RdYlGn'
                # Cap at 60 days for better visualization (999 = no stockout concern)
                df_plot = df.copy()
                df_plot['_display_days'] = df_plot[color_col].apply(lambda x: min(x, 60))
                color_col = '_display_days'
            else:  # Critical Items %
                color_col = 'RISK_SCORE'
                color_scale = 'RdYlGn_r'
            
            # Use the filtered df directly - shows actual data distribution
            df_plot = df.copy() if color_metric != "Days Until Stockout" else df_plot
            
            fig = px.scatter(
                df_plot,
                x='LOCATION',
                y='CATEGORY',
                size='QUANTITY_ON_HAND',
                color=color_col,
                hover_data=['SKU_NAME', 'QUANTITY_ON_HAND', 'DAYS_UNTIL_STOCKOUT', 'STOCK_STATUS', 'RISK_SCORE'],
                color_continuous_scale=color_scale,
                title=f"Individual Items Distribution by {color_metric} ({len(df_plot)} items)"
            )
            
            fig.update_layout(
                height=500,
                xaxis={'categoryorder': 'category ascending'},
                yaxis={'categoryorder': 'category ascending'}
            )
            st.plotly_chart(fig, width="stretch")
    
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
        st.plotly_chart(fig, width="stretch")
    
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
        st.plotly_chart(fig, width="stretch")

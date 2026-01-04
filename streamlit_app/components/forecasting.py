"""
Forecasting Component
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def display_forecasts(forecast_df, inventory_df):
    """Display AI-powered forecast predictions"""
    
    if len(forecast_df) == 0:
        st.warning("No forecast data available.")
        return
    
    # Forecast summary
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        high_risk = len(forecast_df[forecast_df['stockout_risk'] == 'HIGH RISK'])
        st.metric("🔴 High Risk Items", high_risk)
    
    with col2:
        moderate_risk = len(forecast_df[forecast_df['stockout_risk'] == 'MODERATE RISK'])
        st.metric("🟡 Moderate Risk", moderate_risk)
    
    with col3:
        low_risk = len(forecast_df[forecast_df['stockout_risk'] == 'LOW RISK'])
        st.metric("🟢 Low Risk", low_risk)
    
    with col4:
        avg_accuracy = forecast_df['model_accuracy'].mean()
        st.metric("🎯 Avg Model Accuracy", f"{avg_accuracy:.1f}%")
    
    st.markdown("---")
    
    # Risk distribution
    col1, col2 = st.columns(2)
    
    with col1:
        # Risk by category
        risk_by_category = forecast_df.groupby(['category', 'stockout_risk']).size().reset_index(name='count')
        fig = px.bar(
            risk_by_category,
            x='category',
            y='count',
            color='stockout_risk',
            title="Stockout Risk by Category",
            color_discrete_map={
                'HIGH RISK': '#ff4b4b',
                'MODERATE RISK': '#ffa500',
                'LOW RISK': '#4caf50'
            },
            barmode='stack'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Risk by location
        risk_by_location = forecast_df.groupby(['location', 'stockout_risk']).size().reset_index(name='count')
        fig = px.bar(
            risk_by_location,
            x='location',
            y='count',
            color='stockout_risk',
            title="Stockout Risk by Location",
            color_discrete_map={
                'HIGH RISK': '#ff4b4b',
                'MODERATE RISK': '#ffa500',
                'LOW RISK': '#4caf50'
            },
            barmode='stack'
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    
    # High-risk items details
    st.subheader("⚠️ High-Risk Items (Predicted Stockout)")
    
    high_risk_items = forecast_df[forecast_df['stockout_risk'] == 'HIGH RISK'].sort_values('predicted_days_to_stockout')
    
    if len(high_risk_items) > 0:
        for _, item in high_risk_items.iterrows():
            with st.expander(f"🔴 {item['item_name']} - {item['location']}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Current Stock", item['current_stock'])
                    st.metric("Predicted Stock (14d)", f"{item['predicted_stock']:.0f}")
                
                with col2:
                    st.metric("Predicted Daily Consumption", f"{item['predicted_consumption']:.1f}")
                    st.metric("Days to Stockout", f"{item['predicted_days_to_stockout']:.1f}")
                
                with col3:
                    st.metric("Model Accuracy", f"{item['model_accuracy']:.1f}%")
                    st.metric("Forecast Horizon", f"{item['forecast_horizon_days']} days")
                
                # Confidence interval
                st.markdown("**Consumption Confidence Interval (95%)**")
                st.info(f"Lower: {item['confidence_interval_lower']:.2f} | Upper: {item['confidence_interval_upper']:.2f}")
    else:
        st.success("✅ No high-risk items predicted!")
    
    # Prediction vs Current comparison
    st.subheader("📊 Current vs Predicted Stock Levels")
    
    # Select items to display
    selected_items = st.multiselect(
        "Select items to compare",
        options=forecast_df['item_name'].unique(),
        default=forecast_df['item_name'].unique()[:5]
    )
    
    if selected_items:
        comparison_df = forecast_df[forecast_df['item_name'].isin(selected_items)]
        
        # Create comparison chart
        fig = go.Figure()
        
        # Current stock
        fig.add_trace(go.Bar(
            name='Current Stock',
            x=comparison_df['item_name'],
            y=comparison_df['current_stock'],
            marker_color='lightblue'
        ))
        
        # Predicted stock
        fig.add_trace(go.Bar(
            name='Predicted Stock (14d)',
            x=comparison_df['item_name'],
            y=comparison_df['predicted_stock'],
            marker_color='coral'
        ))
        
        fig.update_layout(
            title="Current vs Predicted Stock Levels",
            xaxis_title="Item",
            yaxis_title="Stock Level",
            barmode='group',
            xaxis_tickangle=-45
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Model performance
    st.subheader("🎯 Model Performance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Accuracy distribution
        fig = px.histogram(
            forecast_df,
            x='model_accuracy',
            nbins=20,
            title="Model Accuracy Distribution",
            labels={'model_accuracy': 'Accuracy (%)'},
            color_discrete_sequence=['#4caf50']
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Accuracy by category
        accuracy_by_category = forecast_df.groupby('category')['model_accuracy'].mean().reset_index()
        fig = px.bar(
            accuracy_by_category,
            x='category',
            y='model_accuracy',
            title="Average Model Accuracy by Category",
            labels={'model_accuracy': 'Accuracy (%)'},
            color='model_accuracy',
            color_continuous_scale='Greens'
        )
        st.plotly_chart(fig, use_container_width=True)

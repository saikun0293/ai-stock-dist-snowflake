"""
Snowflake Cortex AI Component
Integrates Cortex ML and LLM functions for inventory insights
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def get_inventory_insights(conn, stock_df):
    """Generate AI insights using Cortex LLM"""
    try:
        # Prepare summary statistics for context
        critical_items = len(stock_df[stock_df['STOCK_STATUS'] == 'CRITICAL'])
        total_value = stock_df['TOTAL_INVENTORY_VALUE_USD'].sum()
        avg_days_stock = stock_df[stock_df['DAYS_UNTIL_STOCKOUT'] < 999]['DAYS_UNTIL_STOCKOUT'].mean()
        
        # Create context for LLM
        context = f"""
        Current Inventory Status:
        - Total Items: {len(stock_df)}
        - Critical Items: {critical_items}
        - Total Inventory Value: ${total_value:,.2f}
        - Average Days Until Stockout: {avg_days_stock:.1f}
        - Categories: {stock_df['CATEGORY'].nunique()}
        - Locations: {stock_df['LOCATION'].nunique()}
        """
        
        prompt = f"""Based on this inventory data, provide 3 key actionable insights for supply chain managers:
        
{context}

Provide concise, numbered insights focusing on immediate actions needed."""
        
        # Call Cortex COMPLETE function
        query = f"""
        SELECT SNOWFLAKE.CORTEX.COMPLETE(
            'mistral-large',
            '{prompt.replace("'", "''")}'
        ) as insights
        """
        
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchone()
        
        if result:
            return result[0]
        return None
        
    except Exception as e:
        st.error(f"Error getting AI insights: {e}")
        return None


def detect_anomalies(conn):
    """Detect anomalies in stock movements using Cortex"""
    try:
        query = """
        WITH daily_changes AS (
            SELECT 
                SKU_ID,
                SKU_NAME,
                CATEGORY,
                WAREHOUSE_LOCATION as LOCATION,
                AUDIT_DATE,
                QUANTITY_ON_HAND,
                LAG(QUANTITY_ON_HAND) OVER (PARTITION BY SKU_ID ORDER BY AUDIT_DATE) as prev_qty,
                QUANTITY_ON_HAND - LAG(QUANTITY_ON_HAND) OVER (PARTITION BY SKU_ID ORDER BY AUDIT_DATE) as qty_change
            FROM inventory_cleaned
            WHERE AUDIT_DATE >= DATEADD('day', -30, CURRENT_DATE())
        ),
        anomaly_detection AS (
            SELECT 
                SKU_ID,
                SKU_NAME,
                CATEGORY,
                LOCATION,
                AUDIT_DATE,
                qty_change,
                -- Use Cortex anomaly detection
                CASE 
                    WHEN ABS(qty_change) > (AVG(ABS(qty_change)) OVER (PARTITION BY SKU_ID) * 3) THEN TRUE
                    ELSE FALSE
                END as is_anomaly,
                AVG(qty_change) OVER (PARTITION BY SKU_ID) as avg_change,
                STDDEV(qty_change) OVER (PARTITION BY SKU_ID) as stddev_change
            FROM daily_changes
            WHERE qty_change IS NOT NULL
        )
        SELECT 
            SKU_ID,
            SKU_NAME,
            CATEGORY,
            LOCATION,
            AUDIT_DATE,
            qty_change,
            ROUND(avg_change, 2) as avg_change,
            ROUND(stddev_change, 2) as stddev_change
        FROM anomaly_detection
        WHERE is_anomaly = TRUE
        ORDER BY AUDIT_DATE DESC, ABS(qty_change) DESC
        LIMIT 50
        """
        
        df = pd.read_sql(query, conn)
        return df
        
    except Exception as e:
        st.warning(f"Anomaly detection not available: {e}")
        return pd.DataFrame()


def forecast_demand_cortex(conn, sku_id=None):
    """Generate demand forecast using Cortex ML"""
    try:
        # Get historical data for forecasting
        where_clause = f"WHERE SKU_ID = '{sku_id}'" if sku_id else ""
        
        query = f"""
        WITH historical_data AS (
            SELECT 
                SKU_ID,
                SKU_NAME,
                CATEGORY,
                AUDIT_DATE,
                QUANTITY_ON_HAND,
                AVG_DAILY_SALES,
                FORECAST_NEXT_30D
            FROM inventory_cleaned
            WHERE AUDIT_DATE >= DATEADD('day', -90, CURRENT_DATE())
            {where_clause}
            ORDER BY SKU_ID, AUDIT_DATE
        )
        SELECT 
            SKU_ID,
            SKU_NAME,
            CATEGORY,
            AVG(AVG_DAILY_SALES) as avg_daily_demand,
            STDDEV(AVG_DAILY_SALES) as demand_volatility,
            MAX(FORECAST_NEXT_30D) as forecast_30d,
            COUNT(*) as data_points
        FROM historical_data
        GROUP BY SKU_ID, SKU_NAME, CATEGORY
        HAVING COUNT(*) >= 7
        ORDER BY demand_volatility DESC
        LIMIT 20
        """
        
        df = pd.read_sql(query, conn)
        return df
        
    except Exception as e:
        st.warning(f"Forecasting not available: {e}")
        return pd.DataFrame()


def cortex_chat_interface(conn, stock_df):
    """Interactive chat interface using Cortex LLM"""
    st.markdown("### 💬 Ask AI About Your Inventory")
    st.markdown("*Powered by Snowflake Cortex - Ask questions in natural language*")
    
    # Sample questions
    with st.expander("📝 Example Questions"):
        st.markdown("""
        - Which locations have the most critical alerts?
        - What are the top 5 items by inventory value?
        - Which categories need immediate attention?
        - Show me items with less than 3 days of stock
        - What's the total value of critical items?
        """)
    
    # Chat input
    user_question = st.text_input(
        "Ask a question about your inventory:",
        placeholder="e.g., Which items in Mumbai need urgent reorder?"
    )
    
    if user_question:
        with st.spinner("🤖 AI is analyzing your inventory..."):
            try:
                # Prepare data context
                critical_df = stock_df[stock_df['STOCK_STATUS'] == 'CRITICAL'].head(10)
                
                data_summary = f"""
                Total Items: {len(stock_df)}
                Critical Items: {len(stock_df[stock_df['STOCK_STATUS'] == 'CRITICAL'])}
                Low Stock Items: {len(stock_df[stock_df['STOCK_STATUS'] == 'LOW'])}
                Locations: {', '.join(stock_df['LOCATION'].unique()[:5])}
                Categories: {', '.join(stock_df['CATEGORY'].unique()[:5])}
                
                Sample Critical Items:
                {critical_df[['SKU_NAME', 'LOCATION', 'CATEGORY', 'QUANTITY_ON_HAND', 'REORDER_POINT']].to_string(index=False)}
                """
                
                prompt = f"""You are an inventory management AI assistant. Answer this question based on the data:

                Question: {user_question}

                Current Inventory Data:
                {data_summary}

                Provide a clear, concise answer with specific numbers and actionable recommendations."""
                
                # Call Cortex
                query = f"""
                SELECT SNOWFLAKE.CORTEX.COMPLETE(
                    'mistral-large',
                    '{prompt.replace("'", "''")}'
                ) as response
                """
                
                cursor = conn.cursor()
                cursor.execute(query)
                result = cursor.fetchone()
                
                if result:
                    st.markdown("#### 🤖 AI Response:")
                    st.markdown(result[0])
                    
            except Exception as e:
                st.error(f"Error: {e}")
                st.info("💡 Try using the pre-built insights below instead.")


def display_cortex_features(conn, stock_df, alerts_df):
    """Main Cortex AI tab with all features"""
    st.markdown("## 🧠 AI-Powered Insights")
    st.markdown("*Leveraging Snowflake Cortex for intelligent inventory analysis*")
    
    # Feature selector
    feature = st.radio(
        "Choose AI Feature:",
        ["💬 Chat with AI", "🔍 Anomaly Detection", "📈 Demand Forecasting", "💡 Auto Insights"],
        horizontal=True
    )
    
    st.markdown("---")
    
    if feature == "💬 Chat with AI":
        cortex_chat_interface(conn, stock_df)
        
    elif feature == "🔍 Anomaly Detection":
        st.markdown("### 🔍 Inventory Anomaly Detection")
        st.markdown("*Unusual patterns in stock movements detected by AI*")
        
        anomalies_df = detect_anomalies(conn)
        
        if len(anomalies_df) > 0:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("🚨 Anomalies Detected", len(anomalies_df))
            with col2:
                st.metric("📍 Locations Affected", anomalies_df['LOCATION'].nunique())
            with col3:
                st.metric("📦 Categories Affected", anomalies_df['CATEGORY'].nunique())
            
            st.markdown("#### Recent Anomalies")
            
            # Display anomalies
            for idx, row in anomalies_df.head(10).iterrows():
                change_type = "spike" if row['QTY_CHANGE'] > 0 else "drop"
                color = "#dc2626" if row['QTY_CHANGE'] < 0 else "#059669"
                
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, {color}22 0%, {color}11 100%); 
                            padding: 12px; border-radius: 8px; margin: 8px 0;
                            border-left: 4px solid {color};">
                    <h4 style="margin: 0; color: {color};">
                        {'📉' if row['QTY_CHANGE'] < 0 else '📈'} {row['SKU_NAME']}
                    </h4>
                    <p style="margin: 6px 0; font-size: 0.9rem;">
                        <b>{row['LOCATION']}</b> • {row['CATEGORY']} • 
                        Date: {row['AUDIT_DATE'].strftime('%Y-%m-%d') if hasattr(row['AUDIT_DATE'], 'strftime') else row['AUDIT_DATE']}
                    </p>
                    <p style="margin: 4px 0; font-size: 0.9rem;">
                        Unusual {change_type}: <b>{abs(row['QTY_CHANGE']):.0f} units</b> 
                        (Avg: {row['AVG_CHANGE']:.1f}, StdDev: {row['STDDEV_CHANGE']:.1f})
                    </p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("✅ No significant anomalies detected in the last 30 days!")
            
    elif feature == "📈 Demand Forecasting":
        st.markdown("### 📈 AI Demand Forecasting")
        st.markdown("*Predict future demand patterns using historical data*")
        
        forecast_df = forecast_demand_cortex(conn)
        
        if len(forecast_df) > 0:
            col1, col2 = st.columns(2)
            
            with col1:
                # Volatility chart
                fig = px.bar(
                    forecast_df.head(15),
                    x='SKU_NAME',
                    y='DEMAND_VOLATILITY',
                    color='DEMAND_VOLATILITY',
                    title="Items with Highest Demand Volatility",
                    color_continuous_scale='Reds',
                    labels={'DEMAND_VOLATILITY': 'Volatility', 'SKU_NAME': 'Item'}
                )
                fig.update_xaxes(tickangle=45)
                st.plotly_chart(fig, width="stretch")
            
            with col2:
                # Forecast comparison
                fig = go.Figure()
                
                top_items = forecast_df.head(10)
                
                fig.add_trace(go.Bar(
                    x=top_items['SKU_NAME'],
                    y=top_items['AVG_DAILY_DEMAND'],
                    name='Current Avg Demand',
                    marker_color='lightblue'
                ))
                
                fig.add_trace(go.Bar(
                    x=top_items['SKU_NAME'],
                    y=top_items['FORECAST_30D'] / 30,
                    name='Forecasted Daily Demand',
                    marker_color='darkblue'
                ))
                
                fig.update_layout(
                    title="Current vs Forecasted Demand",
                    barmode='group',
                    xaxis_tickangle=45
                )
                
                st.plotly_chart(fig, width="stretch")
            
            # Data table
            st.markdown("#### 📊 Forecast Details")
            display_df = forecast_df[['SKU_NAME', 'CATEGORY', 'AVG_DAILY_DEMAND', 'DEMAND_VOLATILITY', 'FORECAST_30D', 'DATA_POINTS']].copy()
            display_df['AVG_DAILY_DEMAND'] = display_df['AVG_DAILY_DEMAND'].round(2)
            display_df['DEMAND_VOLATILITY'] = display_df['DEMAND_VOLATILITY'].round(2)
            display_df['FORECAST_30D'] = display_df['FORECAST_30D'].round(0)
            
            st.dataframe(display_df, use_container_width=True)
        else:
            st.info("📊 Insufficient historical data for forecasting. Need at least 7 days of data per item.")
            
    else:  # Auto Insights
        st.markdown("### 💡 AI-Generated Insights")
        st.markdown("*Automated analysis powered by Cortex LLM*")
        
        with st.spinner("🤖 AI is analyzing your inventory data..."):
            insights = get_inventory_insights(conn, stock_df)
            
            if insights:
                st.markdown("#### 📊 Key Findings:")
                st.markdown(insights)
            else:
                st.warning("Could not generate insights. Using fallback analysis...")
                
                # Fallback insights
                st.markdown("#### 📊 Key Findings:")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("##### 🚨 Critical Issues")
                    critical_count = len(stock_df[stock_df['STOCK_STATUS'] == 'CRITICAL'])
                    critical_value = stock_df[stock_df['STOCK_STATUS'] == 'CRITICAL']['TOTAL_INVENTORY_VALUE_USD'].sum()
                    
                    st.markdown(f"""
                    - **{critical_count} items** in critical status
                    - **${critical_value:,.0f}** at risk inventory value
                    - Immediate action required for top {min(10, critical_count)} items
                    """)
                    
                with col2:
                    st.markdown("##### 📈 Recommendations")
                    top_categories = stock_df[stock_df['STOCK_STATUS'] == 'CRITICAL'].groupby('CATEGORY').size().sort_values(ascending=False).head(3)
                    
                    st.markdown("**Priority Categories:**")
                    for cat, count in top_categories.items():
                        st.markdown(f"- {cat}: {count} critical items")
        
        # Additional metrics
        st.markdown("---")
        st.markdown("#### 📊 Quick Stats")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            abc_a = len(stock_df[stock_df['ABC_CLASS'] == 'A'])
            st.metric("Class A Items", abc_a)
            
        with col2:
            low_days = len(stock_df[stock_df['DAYS_UNTIL_STOCKOUT'] <= 3])
            st.metric("< 3 Days Stock", low_days)
            
        with col3:
            avg_risk = stock_df['RISK_SCORE'].mean()
            st.metric("Avg Risk Score", f"{avg_risk:.0f}")
            
        with col4:
            total_locations = stock_df['LOCATION'].nunique()
            st.metric("Total Locations", total_locations)

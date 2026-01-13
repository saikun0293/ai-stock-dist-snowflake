"""
Snowflake Cortex AI Component
Integrates Cortex ML and LLM functions for inventory insights
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from prompts.cortex_prompts import build_inventory_insights_prompt, build_chat_prompt


def aggregate_inventory_data(conn, stock_df):
    
    aggregated = {}
    
    aggregated['total_items'] = len(stock_df)
    aggregated['total_locations'] = stock_df['LOCATION'].nunique()
    aggregated['total_categories'] = stock_df['CATEGORY'].nunique()
    aggregated['total_value'] = stock_df['TOTAL_INVENTORY_VALUE_USD'].sum()
    
    aggregated['stock_status_breakdown'] = {
        'CRITICAL': len(stock_df[stock_df['STOCK_STATUS'] == 'CRITICAL']),
        'LOW': len(stock_df[stock_df['STOCK_STATUS'] == 'LOW']),
        'MODERATE': len(stock_df[stock_df['STOCK_STATUS'] == 'MODERATE']),
        'HEALTHY': len(stock_df[stock_df['STOCK_STATUS'] == 'HEALTHY'])
    }
    
    aggregated['critical_timing'] = {
        '3_days': len(stock_df[stock_df['DAYS_UNTIL_STOCKOUT'] <= 3]),
        '7_days': len(stock_df[stock_df['DAYS_UNTIL_STOCKOUT'] <= 7]),
        '14_days': len(stock_df[stock_df['DAYS_UNTIL_STOCKOUT'] <= 14])
    }
    aggregated['avg_days_to_stockout'] = stock_df[stock_df['DAYS_UNTIL_STOCKOUT'] < 999]['DAYS_UNTIL_STOCKOUT'].mean()
    
    abc_analysis = {}
    for abc_class in ['A', 'B', 'C']:
        abc_items = stock_df[stock_df['ABC_CLASS'] == abc_class]
        abc_analysis[abc_class] = {
            'count': len(abc_items),
            'value': abc_items['TOTAL_INVENTORY_VALUE_USD'].sum(),
            'critical_count': len(abc_items[abc_items['STOCK_STATUS'] == 'CRITICAL'])
        }
    aggregated['abc_analysis'] = abc_analysis
    
    location_breakdown = []
    for location in stock_df['LOCATION'].unique():
        loc_data = stock_df[stock_df['LOCATION'] == location]
        location_breakdown.append({
            'location': location,
            'critical': len(loc_data[loc_data['STOCK_STATUS'] == 'CRITICAL']),
            'low': len(loc_data[loc_data['STOCK_STATUS'] == 'LOW']),
            'healthy': len(loc_data[loc_data['STOCK_STATUS'] == 'HEALTHY'])
        })
    aggregated['location_breakdown'] = sorted(location_breakdown, key=lambda x: x['critical'], reverse=True)
    
    category_breakdown = []
    for category in stock_df['CATEGORY'].unique():
        cat_data = stock_df[stock_df['CATEGORY'] == category]
        category_breakdown.append({
            'category': category,
            'critical': len(cat_data[cat_data['STOCK_STATUS'] == 'CRITICAL']),
            'avg_risk': cat_data['RISK_SCORE'].mean()
        })
    aggregated['category_breakdown'] = sorted(category_breakdown, key=lambda x: x['critical'], reverse=True)
    
    try:
        reorder_query = """
        SELECT 
            COUNT(*) as items_to_reorder,
            SUM(CASE WHEN PRIORITY_SCORE >= 8 THEN 1 ELSE 0 END) as urgent_items,
            SUM(ESTIMATED_ORDER_VALUE_USD) as total_order_value
        FROM DT_REORDER_RECOMMENDATIONS
        """
        reorder_result = pd.read_sql(reorder_query, conn).iloc[0].to_dict()
        # Convert keys to lowercase (Snowflake returns uppercase)
        aggregated['reorder_stats'] = {
            'items_to_reorder': reorder_result.get('ITEMS_TO_REORDER', 0) or 0,
            'urgent_items': reorder_result.get('URGENT_ITEMS', 0) or 0,
            'total_order_value': reorder_result.get('TOTAL_ORDER_VALUE', 0) or 0
        }
    except Exception as e:
        # Fallback to calculating from stock_df
        aggregated['reorder_stats'] = {
            'items_to_reorder': len(stock_df[stock_df['QUANTITY_ON_HAND'] <= stock_df['REORDER_POINT']]),
            'urgent_items': len(stock_df[stock_df['STOCK_STATUS'] == 'CRITICAL']),
            'total_order_value': 0
        }
    
    top_critical = stock_df.nlargest(10, 'RISK_SCORE')
    aggregated['top_critical_items'] = [
        {
            'name': row['SKU_NAME'],
            'location': row['LOCATION'],
            'category': row['CATEGORY'],
            'qty': row['QUANTITY_ON_HAND'],
            'days': row['DAYS_UNTIL_STOCKOUT'],
            'risk': row['RISK_SCORE']
        }
        for _, row in top_critical.iterrows()
    ]
    
    return aggregated


def get_inventory_insights(conn, stock_df):
    """Generate AI insights using Cortex LLM with comprehensive aggregated data"""
    try:
        # Aggregate data from all dynamic tables and views
        aggregated_data = aggregate_inventory_data(conn, stock_df)
        
        # Build comprehensive prompt using centralized prompt builder
        prompt = build_inventory_insights_prompt(aggregated_data)
        
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


def cortex_chat_interface(conn, stock_df):
    """Interactive chat interface using Cortex LLM"""
    st.markdown("*Ask AI About Your Inventory*")
    
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
        placeholder="e.g., What's the total value of critical items?"
    )
    
    if user_question:
        with st.spinner("🤖 AI is analyzing your inventory..."):
            try:
                # Aggregate comprehensive data for chat context
                aggregated_data = aggregate_inventory_data(conn, stock_df)
                
                # Build chat-specific prompt
                prompt = build_chat_prompt(user_question, aggregated_data)
                
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
    """Main Cortex AI tab with LLM features"""
    st.markdown("## 🧠 Snowflake Cortex AI")
    
    feature = st.radio(
        "Choose Feature:",
        ["💬 Chat with AI", "💡 Auto-Generated Insights"],
        horizontal=True
    )
    
    if feature == "💬 Chat with AI":
        cortex_chat_interface(conn, stock_df)
            
    else:
        st.markdown("### 💡 AI-Generated Insights")
        st.markdown("*Comprehensive automated analysis from all inventory data sources*")
        
        with st.spinner("🧠 AI is analyzing aggregated data from all dynamic tables..."):
            insights = get_inventory_insights(conn, stock_df)
            
            if insights:
                st.markdown(insights)
                
                # Show comprehensive data context
                aggregated_data = aggregate_inventory_data(conn, stock_df)
                
                with st.expander("📊 View Comprehensive Data Context Used for Analysis"):
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Items", aggregated_data['total_items'])
                        st.metric("Critical Items", aggregated_data['stock_status_breakdown']['CRITICAL'])
                    with col2:
                        st.metric("Total Locations", aggregated_data['total_locations'])
                        st.metric("Low Stock Items", aggregated_data['stock_status_breakdown']['LOW'])
                    with col3:
                        st.metric("Total Categories", aggregated_data['total_categories'])
                        st.metric("Healthy Items", aggregated_data['stock_status_breakdown']['HEALTHY'])
                    with col4:
                        st.metric("Total Value", f"${aggregated_data['total_value']:,.0f}")
                        st.metric("Items to Reorder", aggregated_data['reorder_stats']['items_to_reorder'])
                    
                    st.markdown("##### ABC Classification Analysis")
                    abc_cols = st.columns(3)
                    for i, (abc_class, data) in enumerate(aggregated_data['abc_analysis'].items()):
                        with abc_cols[i]:
                            st.markdown(f"**Class {abc_class}**")
                            st.write(f"Items: {data['count']}")
                            st.write(f"Value: ${data['value']:,.0f}")
                            st.write(f"Critical: {data['critical_count']}")
                    
                    st.markdown("##### Top 5 Critical Items by Risk Score")
                    for item in aggregated_data['top_critical_items'][:5]:
                        st.markdown(f"- **{item['name']}** ({item['location']}, {item['category']}) - Qty: {item['qty']}, Days: {item['days']:.1f}, Risk: {item['risk']:.1f}")
            else:
                st.warning("Unable to generate insights at this time")

"""
Snowflake Cortex AI Component
Integrates Cortex ML and LLM functions for inventory insights
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from prompts.auto_insights import build_inventory_insights_prompt
from prompts.chat import (
    build_sql_generation_prompt,
    build_response_generation_prompt,
    build_error_handling_prompt
)


def aggregate_inventory_data(conn, stock_df):
    """
    Aggregate inventory data using optimized Snowflake queries instead of pandas
    This is much faster as computation happens in Snowflake's optimized engine
    """
    aggregated = {}
    
    # Single optimized query to get all summary statistics
    summary_query = """
    SELECT 
        COUNT(DISTINCT SKU_ID) as total_items,
        COUNT(DISTINCT LOCATION) as total_locations,
        COUNT(DISTINCT CATEGORY) as total_categories,
        ROUND(SUM(TOTAL_INVENTORY_VALUE_USD), 2) as total_value,
        
        -- Stock status breakdown
        COUNT(CASE WHEN STOCK_STATUS = 'CRITICAL' THEN 1 END) as critical_count,
        COUNT(CASE WHEN STOCK_STATUS = 'LOW' THEN 1 END) as low_count,
        COUNT(CASE WHEN STOCK_STATUS = 'MODERATE' THEN 1 END) as moderate_count,
        COUNT(CASE WHEN STOCK_STATUS = 'HEALTHY' THEN 1 END) as healthy_count,
        
        -- Critical timing
        COUNT(CASE WHEN DAYS_UNTIL_STOCKOUT <= 3 THEN 1 END) as days_3_count,
        COUNT(CASE WHEN DAYS_UNTIL_STOCKOUT <= 7 THEN 1 END) as days_7_count,
        COUNT(CASE WHEN DAYS_UNTIL_STOCKOUT <= 14 THEN 1 END) as days_14_count,
        ROUND(AVG(CASE WHEN DAYS_UNTIL_STOCKOUT < 999 THEN DAYS_UNTIL_STOCKOUT END), 1) as avg_days_to_stockout
    FROM DT_STOCK_HEALTH
    """
    
    summary_df = pd.read_sql(summary_query, conn).iloc[0]
    
    aggregated['total_items'] = int(summary_df['TOTAL_ITEMS'])
    aggregated['total_locations'] = int(summary_df['TOTAL_LOCATIONS'])
    aggregated['total_categories'] = int(summary_df['TOTAL_CATEGORIES'])
    aggregated['total_value'] = float(summary_df['TOTAL_VALUE'])
    
    aggregated['stock_status_breakdown'] = {
        'CRITICAL': int(summary_df['CRITICAL_COUNT']),
        'LOW': int(summary_df['LOW_COUNT']),
        'MODERATE': int(summary_df['MODERATE_COUNT']),
        'HEALTHY': int(summary_df['HEALTHY_COUNT'])
    }
    
    aggregated['critical_timing'] = {
        '3_days': int(summary_df['DAYS_3_COUNT']),
        '7_days': int(summary_df['DAYS_7_COUNT']),
        '14_days': int(summary_df['DAYS_14_COUNT'])
    }
    aggregated['avg_days_to_stockout'] = float(summary_df['AVG_DAYS_TO_STOCKOUT']) if summary_df['AVG_DAYS_TO_STOCKOUT'] else 0
    
    # ABC analysis in one query
    abc_query = """
    SELECT 
        ABC_CLASS,
        COUNT(*) as count,
        ROUND(SUM(TOTAL_INVENTORY_VALUE_USD), 2) as value,
        COUNT(CASE WHEN STOCK_STATUS = 'CRITICAL' THEN 1 END) as critical_count
    FROM DT_STOCK_HEALTH
    GROUP BY ABC_CLASS
    ORDER BY ABC_CLASS
    """
    abc_df = pd.read_sql(abc_query, conn)
    aggregated['abc_analysis'] = {
        row['ABC_CLASS']: {
            'count': int(row['COUNT']),
            'value': float(row['VALUE']),
            'critical_count': int(row['CRITICAL_COUNT'])
        }
        for _, row in abc_df.iterrows()
    }
    
    # Location breakdown in one query
    location_query = """
    SELECT 
        LOCATION,
        COUNT(CASE WHEN STOCK_STATUS = 'CRITICAL' THEN 1 END) as critical,
        COUNT(CASE WHEN STOCK_STATUS = 'LOW' THEN 1 END) as low,
        COUNT(CASE WHEN STOCK_STATUS = 'HEALTHY' THEN 1 END) as healthy
    FROM DT_STOCK_HEALTH
    GROUP BY LOCATION
    ORDER BY critical DESC
    LIMIT 10
    """
    location_df = pd.read_sql(location_query, conn)
    aggregated['location_breakdown'] = [
        {
            'location': row['LOCATION'],
            'critical': int(row['CRITICAL']),
            'low': int(row['LOW']),
            'healthy': int(row['HEALTHY'])
        }
        for _, row in location_df.iterrows()
    ]
    
    # Category breakdown in one query
    category_query = """
    SELECT 
        CATEGORY,
        COUNT(CASE WHEN STOCK_STATUS = 'CRITICAL' THEN 1 END) as critical,
        ROUND(AVG(RISK_SCORE), 1) as avg_risk
    FROM DT_STOCK_HEALTH
    GROUP BY CATEGORY
    ORDER BY critical DESC
    LIMIT 10
    """
    category_df = pd.read_sql(category_query, conn)
    aggregated['category_breakdown'] = [
        {
            'category': row['CATEGORY'],
            'critical': int(row['CRITICAL']),
            'avg_risk': float(row['AVG_RISK'])
        }
        for _, row in category_df.iterrows()
    ]
    
    # Reorder stats
    try:
        reorder_query = """
        SELECT 
            COUNT(*) as items_to_reorder,
            SUM(CASE WHEN PRIORITY_SCORE >= 8 THEN 1 ELSE 0 END) as urgent_items,
            ROUND(SUM(ESTIMATED_ORDER_VALUE_USD), 2) as total_order_value
        FROM DT_REORDER_RECOMMENDATIONS
        """
        reorder_result = pd.read_sql(reorder_query, conn).iloc[0]
        aggregated['reorder_stats'] = {
            'items_to_reorder': int(reorder_result['ITEMS_TO_REORDER']) if reorder_result['ITEMS_TO_REORDER'] else 0,
            'urgent_items': int(reorder_result['URGENT_ITEMS']) if reorder_result['URGENT_ITEMS'] else 0,
            'total_order_value': float(reorder_result['TOTAL_ORDER_VALUE']) if reorder_result['TOTAL_ORDER_VALUE'] else 0
        }
    except Exception as e:
        aggregated['reorder_stats'] = {
            'items_to_reorder': 0,
            'urgent_items': 0,
            'total_order_value': 0
        }
    
    # Top critical items
    top_critical_query = """
    SELECT 
        SKU_NAME,
        LOCATION,
        CATEGORY,
        QUANTITY_ON_HAND,
        DAYS_UNTIL_STOCKOUT,
        RISK_SCORE
    FROM DT_STOCK_HEALTH
    ORDER BY RISK_SCORE DESC
    LIMIT 10
    """
    top_critical_df = pd.read_sql(top_critical_query, conn)
    aggregated['top_critical_items'] = [
        {
            'name': row['SKU_NAME'],
            'location': row['LOCATION'],
            'category': row['CATEGORY'],
            'qty': int(row['QUANTITY_ON_HAND']),
            'days': float(row['DAYS_UNTIL_STOCKOUT']),
            'risk': float(row['RISK_SCORE'])
        }
        for _, row in top_critical_df.iterrows()
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
    """Multi-Agent Interactive chat interface using Cortex LLM
    
    Agent 1: Converts natural language to SQL query
    Agent 2: Executes SQL and converts results to natural language response
    """
    st.markdown("*Ask AI About Your Inventory - Powered by Multi-Agent System*")
    
    # Sample questions
    with st.expander("📝 Example Questions"):
        st.markdown("""
        - Which locations have the most critical alerts?
        - What are the top 5 items by inventory value?
        - Which categories need immediate attention?
        - Show me items with less than 3 days of stock
        - What's the total value of critical items?
        - Which suppliers have the best on-time delivery?
        - How many items need reordering this week?
        - Show me all Class A items that are low on stock
        """)
    
    # Chat input
    user_question = st.text_input(
        "Ask a question about your inventory:",
        placeholder="e.g., What's the total value of critical items?"
    )
    
    if user_question:
        # Initialize session state for showing SQL query
        if 'show_sql' not in st.session_state:
            st.session_state.show_sql = False
        
        with st.spinner("🤖 Agent 1: Converting your question to SQL..."):
            try:
                # AGENT 1: Generate SQL query from natural language
                sql_prompt = build_sql_generation_prompt(user_question)
                
                sql_query_result = f"""
                SELECT SNOWFLAKE.CORTEX.COMPLETE(
                    'mistral-large',
                    '{sql_prompt.replace("'", "''")}'
                ) as sql_query
                """
                
                cursor = conn.cursor()
                cursor.execute(sql_query_result)
                sql_result = cursor.fetchone()
                
                if not sql_result or not sql_result[0]:
                    st.error("❌ Failed to generate SQL query. Please rephrase your question.")
                    return
                
                # Extract the SQL query
                generated_sql = sql_result[0].strip()
                
                # Clean up the SQL (remove markdown formatting if present)
                if generated_sql.startswith("```"):
                    generated_sql = generated_sql.split("```")[1]
                    if generated_sql.startswith("sql"):
                        generated_sql = generated_sql[3:]
                generated_sql = generated_sql.strip()
                
                # Show SQL query in expander
                with st.expander("🔍 View Generated SQL Query"):
                    st.code(generated_sql, language="sql")
                
                # AGENT 2: Execute SQL and generate natural language response
                with st.spinner("🤖 Agent 2: Executing query and analyzing results..."):
                    try:
                        # Execute the generated SQL
                        query_df = pd.read_sql(generated_sql, conn)
                        row_count = len(query_df)
                        
                        # Convert results to string format for LLM
                        if row_count == 0:
                            sql_results_str = "No results found."
                        elif row_count <= 20:
                            # Show all results for small datasets
                            sql_results_str = query_df.to_string(index=False)
                        else:
                            # Show first 20 rows for large datasets
                            sql_results_str = query_df.head(20).to_string(index=False)
                            sql_results_str += f"\n... and {row_count - 20} more rows"
                        
                        # Generate natural language response
                        response_prompt = build_response_generation_prompt(
                            user_question,
                            generated_sql,
                            sql_results_str,
                            row_count
                        )
                        
                        response_query = f"""
                        SELECT SNOWFLAKE.CORTEX.COMPLETE(
                            'mistral-large',
                            '{response_prompt.replace("'", "''")}'
                        ) as response
                        """
                        
                        cursor.execute(response_query)
                        response_result = cursor.fetchone()
                        
                        if response_result:
                            st.markdown("#### 🤖 AI Response:")
                            st.markdown(response_result[0])
                            
                            # Show raw data in expander
                            if row_count > 0:
                                with st.expander(f"📊 View Raw Data ({row_count} rows)"):
                                    st.dataframe(query_df, use_container_width=True)
                        
                    except Exception as sql_error:
                        # Handle SQL execution errors with Agent 2
                        error_message = str(sql_error)
                        st.error(f"❌ Query execution failed")
                        
                        with st.spinner("🤖 Analyzing error..."):
                            error_prompt = build_error_handling_prompt(
                                user_question,
                                generated_sql,
                                error_message
                            )
                            
                            error_response_query = f"""
                            SELECT SNOWFLAKE.CORTEX.COMPLETE(
                                'mistral-large',
                                '{error_prompt.replace("'", "''")}'
                            ) as error_response
                            """
                            
                            cursor.execute(error_response_query)
                            error_response = cursor.fetchone()
                            
                            if error_response:
                                st.info(error_response[0])
                            
                            with st.expander("🐛 Technical Error Details"):
                                st.code(error_message)
                    
            except Exception as e:
                st.error(f"❌ An error occurred: {e}")
                st.info("💡 Try using the pre-built insights or rephrase your question.")


def display_cortex_features(conn, stock_df):
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

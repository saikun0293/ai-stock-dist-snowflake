"""
Snowflake Connector Utilities
"""

import streamlit as st
import snowflake.connector
import pandas as pd
from typing import Optional

@st.cache_resource
def get_connection():
    """Establish connection to Snowflake"""
    try:
        # Try to get credentials from Streamlit secrets
        conn = snowflake.connector.connect(
            user=st.secrets.get("snowflake_user", ""),
            password=st.secrets.get("snowflake_password", ""),
            account=st.secrets.get("snowflake_account", ""),
            warehouse=st.secrets.get("snowflake_warehouse", "COMPUTE_WH"),
            database=st.secrets.get("snowflake_database", "INVENTORY_DB"),
            schema=st.secrets.get("snowflake_schema", "INVENTORY_SCHEMA")
        )
        return conn
    except Exception as e:
        st.warning(f"Could not connect to Snowflake: {str(e)}")
        return None

def query_current_inventory(conn) -> pd.DataFrame:
    """Query current inventory status from Snowflake"""
    query = """
        SELECT 
            location,
            category,
            item_name,
            current_stock,
            max_stock,
            stock_percentage,
            stock_status,
            days_until_stockout,
            snapshot_date
        FROM V_CURRENT_INVENTORY
        ORDER BY stock_status, days_until_stockout
    """
    return pd.read_sql(query, conn)

def query_unresolved_alerts(conn) -> pd.DataFrame:
    """Query unresolved alerts from Snowflake"""
    query = """
        SELECT 
            alert_id,
            alert_date,
            location,
            category,
            item_name,
            current_stock,
            alert_type,
            days_until_stockout,
            priority,
            days_open
        FROM V_UNRESOLVED_ALERTS
        ORDER BY priority DESC, alert_date ASC
    """
    return pd.read_sql(query, conn)

def query_forecast_analysis(conn) -> pd.DataFrame:
    """Query forecast analysis from Snowflake"""
    query = """
        SELECT 
            location,
            category,
            item_name,
            current_stock,
            predicted_stock,
            predicted_consumption,
            forecast_horizon_days,
            stockout_risk,
            predicted_days_to_stockout,
            confidence_interval_lower,
            confidence_interval_upper,
            model_accuracy
        FROM V_FORECAST_ANALYSIS
        ORDER BY 
            CASE stockout_risk
                WHEN 'HIGH RISK' THEN 1
                WHEN 'MODERATE RISK' THEN 2
                ELSE 3
            END,
            predicted_days_to_stockout
    """
    return pd.read_sql(query, conn)

def query_stock_trends(conn, location: str, item_name: str, days: int = 30) -> pd.DataFrame:
    """Query historical stock trends for a specific item"""
    query = """
        SELECT 
            snapshot_date,
            current_stock,
            consumption,
            stock_7day_avg,
            consumption_7day_avg
        FROM V_STOCK_TRENDS
        WHERE location = %(location)s
          AND item_name = %(item_name)s
          AND snapshot_date >= DATEADD(day, %(days)s, CURRENT_DATE())
        ORDER BY snapshot_date
    """
    params = {'location': location, 'item_name': item_name, 'days': -days}
    return pd.read_sql(query, conn, params=params)

def query_location_summary(conn) -> pd.DataFrame:
    """Query location-wise summary"""
    query = """
        SELECT 
            location,
            total_items,
            critical_items,
            low_items,
            moderate_items,
            good_items,
            avg_stock_percentage
        FROM V_LOCATION_SUMMARY
        ORDER BY critical_items DESC, low_items DESC
    """
    return pd.read_sql(query, conn)

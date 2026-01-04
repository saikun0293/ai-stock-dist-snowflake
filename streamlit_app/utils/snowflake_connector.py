"""
Snowflake Connector for Inventory App
Connects to inventory_app_db.data_schema
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
            database=st.secrets.get("snowflake_database", "inventory_app_db"),
            schema=st.secrets.get("snowflake_schema", "data_schema")
        )
        return conn
    except Exception as e:
        st.warning(f"Could not connect to Snowflake: {str(e)}")
        return None

def query_stock_health(conn) -> pd.DataFrame:
    """Query current stock health from Dynamic Table"""
    query = """
        SELECT 
            SKU_ID,
            SKU_NAME,
            CATEGORY,
            LOCATION,
            WAREHOUSE_ID,
            ABC_CLASS,
            QUANTITY_ON_HAND,
            AVAILABLE_STOCK,
            REORDER_POINT,
            SAFETY_STOCK,
            LEAD_TIME_DAYS,
            AVG_DAILY_SALES,
            FORECAST_NEXT_30D,
            DAYS_UNTIL_STOCKOUT,
            STOCK_STATUS,
            RISK_SCORE,
            UNIT_COST_USD,
            TOTAL_INVENTORY_VALUE_USD,
            SUPPLIER_NAME,
            LAST_UPDATED
        FROM DT_STOCK_HEALTH
        ORDER BY RISK_SCORE DESC, ABC_CLASS, CATEGORY
        LIMIT 10000
    """
    return pd.read_sql(query, conn)

def query_active_alerts(conn) -> pd.DataFrame:
    """Query active alerts from Dynamic Table"""
    query = """
        SELECT 
            SKU_ID,
            SKU_NAME,
            CATEGORY,
            LOCATION,
            ABC_CLASS,
            QUANTITY_ON_HAND,
            REORDER_POINT,
            SAFETY_STOCK,
            AVG_DAILY_SALES,
            ALERT_TYPE,
            PRIORITY,
            DAYS_UNTIL_STOCKOUT,
            LEAD_TIME_DAYS,
            SUPPLIER_NAME,
            SUPPLIER_ID,
            UNIT_COST_USD,
            TOTAL_INVENTORY_VALUE_USD,
            DAYS_SINCE_LAST_RECEIVED,
            ALERT_GENERATED_AT
        FROM DT_ACTIVE_ALERTS
        ORDER BY 
            CASE PRIORITY
                WHEN 'CRITICAL' THEN 1
                WHEN 'HIGH' THEN 2
                WHEN 'MEDIUM' THEN 3
                ELSE 4
            END,
            DAYS_UNTIL_STOCKOUT NULLS LAST
        LIMIT 5000
    """
    return pd.read_sql(query, conn)

def query_reorder_recommendations(conn) -> pd.DataFrame:
    """Query reorder recommendations from Dynamic Table"""
    query = """
        SELECT 
            SKU_ID,
            SKU_NAME,
            CATEGORY,
            LOCATION,
            WAREHOUSE_ID,
            ABC_CLASS,
            QUANTITY_ON_HAND,
            AVAILABLE_STOCK,
            REORDER_POINT,
            SAFETY_STOCK,
            LEAD_TIME_DAYS,
            AVG_DAILY_SALES,
            FORECAST_NEXT_30D,
            RECOMMENDED_ORDER_QTY,
            ECONOMIC_ORDER_QTY,
            PRIORITY_SCORE,
            UNIT_COST_USD,
            ESTIMATED_ORDER_VALUE_USD,
            SUPPLIER_NAME,
            SUPPLIER_ID,
            SUPPLIER_ONTIME_PCT,
            DAYS_OF_INVENTORY,
            ORDER_FREQUENCY_PER_MONTH,
            RECOMMENDATION_GENERATED_AT
        FROM DT_REORDER_RECOMMENDATIONS
        ORDER BY PRIORITY_SCORE DESC, ESTIMATED_ORDER_VALUE_USD DESC
        LIMIT 5000
    """
    return pd.read_sql(query, conn)

def query_location_performance(conn) -> pd.DataFrame:
    """Query warehouse performance metrics"""
    query = """
        SELECT 
            LOCATION,
            WAREHOUSE_ID,
            TOTAL_SKUS,
            TOTAL_CATEGORIES,
            TOTAL_UNITS,
            TOTAL_VALUE_USD,
            OUT_OF_STOCK_COUNT,
            CRITICAL_COUNT,
            LOW_STOCK_COUNT,
            HEALTHY_COUNT,
            HEALTH_SCORE,
            AVG_DAYS_COVERAGE,
            AVG_SUPPLIER_PERFORMANCE,
            AVG_FORECAST_ACCURACY,
            ITEMS_NEEDING_REORDER,
            LAST_UPDATED
        FROM DT_LOCATION_PERFORMANCE
        ORDER BY HEALTH_SCORE ASC
    """
    return pd.read_sql(query, conn)

def query_category_heatmap(conn) -> pd.DataFrame:
    """Query category heatmap data"""
    query = """
        SELECT 
            LOCATION,
            CATEGORY,
            TOTAL_SKUS,
            OUT_OF_STOCK_SKUS,
            CRITICAL_SKUS,
            LOW_STOCK_SKUS,
            HEALTHY_SKUS,
            TOTAL_UNITS,
            TOTAL_VALUE_USD,
            AVG_DAYS_COVERAGE,
            AVG_RISK_SCORE,
            OVERALL_STATUS,
            LAST_UPDATED
        FROM DT_CATEGORY_HEATMAP
        ORDER BY AVG_RISK_SCORE DESC
    """
    return pd.read_sql(query, conn)

def query_alert_history(conn, days: int = 30) -> pd.DataFrame:
    """Query alert history"""
    query = f"""
        SELECT 
            alert_id,
            alert_timestamp,
            sku_id,
            sku_name,
            category,
            location,
            alert_type,
            priority,
            quantity_on_hand,
            reorder_point,
            days_until_stockout,
            resolved,
            resolved_timestamp,
            supplier_name,
            unit_cost_usd,
            estimated_impact_usd
        FROM ALERT_HISTORY
        WHERE alert_timestamp >= DATEADD(day, -{days}, CURRENT_TIMESTAMP())
        ORDER BY alert_timestamp DESC
        LIMIT 1000
    """
    return pd.read_sql(query, conn)

def query_reorder_action_log(conn, status: str = 'PENDING') -> pd.DataFrame:
    """Query reorder action log"""
    query = f"""
        SELECT 
            action_id,
            action_timestamp,
            sku_id,
            sku_name,
            category,
            location,
            recommended_qty,
            economic_order_qty,
            ordered_qty,
            priority_score,
            unit_cost_usd,
            total_order_value_usd,
            status,
            order_date,
            expected_delivery_date,
            supplier_name,
            supplier_id,
            notes
        FROM REORDER_ACTION_LOG
        WHERE status = '{status}'
        ORDER BY priority_score DESC, action_timestamp DESC
        LIMIT 1000
    """
    return pd.read_sql(query, conn)

def export_reorder_list(conn, location_filter: Optional[str] = None) -> pd.DataFrame:
    """Export reorder list for procurement"""
    query = """
        SELECT 
            r.SKU_ID,
            r.SKU_NAME,
            r.CATEGORY,
            r.LOCATION,
            r.ABC_CLASS,
            r.QUANTITY_ON_HAND AS "Current Stock",
            r.REORDER_POINT AS "Reorder Point",
            r.SAFETY_STOCK AS "Safety Stock",
            r.RECOMMENDED_ORDER_QTY AS "Recommended Qty",
            r.ECONOMIC_ORDER_QTY AS "Economic Order Qty",
            r.PRIORITY_SCORE AS "Priority (1-10)",
            r.LEAD_TIME_DAYS AS "Lead Time (Days)",
            r.AVG_DAILY_SALES AS "Avg Daily Usage",
            r.UNIT_COST_USD AS "Unit Cost (USD)",
            r.ESTIMATED_ORDER_VALUE_USD AS "Order Value (USD)",
            r.SUPPLIER_NAME AS "Supplier",
            r.SUPPLIER_ID AS "Supplier ID",
            r.SUPPLIER_ONTIME_PCT AS "Supplier On-Time %",
            r.RECOMMENDATION_GENERATED_AT AS "Generated At"
        FROM DT_REORDER_RECOMMENDATIONS r
    """
    
    if location_filter and location_filter != "All":
        query += f" WHERE r.LOCATION = '{location_filter}'"
    
    query += " ORDER BY r.PRIORITY_SCORE DESC, r.ESTIMATED_ORDER_VALUE_USD DESC"
    
    return pd.read_sql(query, conn)

def log_export(conn, export_type: str, record_count: int, exported_by: str = 'user', 
               file_format: str = 'CSV', filters_applied: Optional[dict] = None):
    """Log export activity"""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO EXPORT_LOG (export_type, record_count, exported_by, file_format, filters_applied)
            VALUES (%s, %s, %s, %s, PARSE_JSON(%s))
        """, (export_type, record_count, exported_by, file_format, str(filters_applied or {})))
        conn.commit()
    except Exception as e:
        st.error(f"Failed to log export: {e}")

def close_connection(conn):
    """Close Snowflake connection"""
    if conn:
        conn.close()

"""
Snowflake Connector for Inventory App with Logging
Connects to inventory_app_db.data_schema
"""

import streamlit as st
import snowflake.connector
import pandas as pd
from typing import Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@st.cache_resource
def get_connection():
    """Establish connection to Snowflake with detailed logging"""
    try:
        logger.info("Starting Snowflake connection")
        
        # Get credentials from secrets
        account = st.secrets.get("account", "")
        user = st.secrets.get("user", "")
        password = st.secrets.get("password", "")
        warehouse = st.secrets.get("warehouse", "COMPUTE_WH")
        database = st.secrets.get("database", "INVENTORY_APP_DB")
        schema = st.secrets.get("schema", "DATA_SCHEMA")
        
        logger.info(f"Connecting to account: {account}")
        logger.info(f"User: {user}")
        logger.info(f"Warehouse: {warehouse}")
        logger.info(f"Database: {database}")
        logger.info(f"Schema: {schema}")
        
        # Create connection
        conn = snowflake.connector.connect(
            account=account,
            user=user,
            password=password,
            warehouse=warehouse,
            database=database,
            schema=schema
        )
        
        logger.info("✅ Connection established successfully")
        
        # Test the connection
        cursor = conn.cursor()
        cursor.execute("SELECT CURRENT_DATABASE(), CURRENT_SCHEMA(), CURRENT_WAREHOUSE()")
        result = cursor.fetchone()
        if result:
            logger.info(f"Connected to - Database: {result[0]}, Schema: {result[1]}, Warehouse: {result[2]}")
        else:
            logger.warning("Could not retrieve connection details")
        cursor.close()
        
        return conn
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Connection failed: {error_msg}")
        logger.error(f"Account: {st.secrets.get('account', 'NOT SET')}")
        logger.error(f"Error type: {type(e).__name__}")
        st.error(f"Could not connect to Snowflake: {error_msg}")
        return None

def query_stock_health(conn) -> pd.DataFrame:
    """Query current stock health from Dynamic Table"""
    try:
        logger.info("Querying DT_STOCK_HEALTH")
        
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
        df = pd.read_sql(query, conn)
        logger.info(f"✅ Retrieved {len(df)} records from DT_STOCK_HEALTH")
        return df
    except Exception as e:
        logger.error(f"❌ Error querying DT_STOCK_HEALTH: {e}")
        st.error(f"❌ Error loading stock health: {e}")
        return pd.DataFrame()

def query_active_alerts(conn) -> pd.DataFrame:
    """Query active alerts from Dynamic Table"""
    try:
        logger.info("Querying DT_ACTIVE_ALERTS")
        
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
        df = pd.read_sql(query, conn)
        logger.info(f"✅ Retrieved {len(df)} alerts")
        return df
    except Exception as e:
        logger.error(f"❌ Error querying DT_ACTIVE_ALERTS: {e}")
        st.warning(f"⚠️ Could not load alerts: {e}")
        return pd.DataFrame()

def query_reorder_recommendations(conn) -> pd.DataFrame:
    """Query reorder recommendations from Dynamic Table"""
    try:
        logger.info("Querying DT_REORDER_RECOMMENDATIONS")
        
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
        df = pd.read_sql(query, conn)
        logger.info(f"✅ Retrieved {len(df)} reorder recommendations")
        return df
    except Exception as e:
        logger.error(f"❌ Error querying DT_REORDER_RECOMMENDATIONS: {e}")
        st.warning(f"⚠️ Could not load reorder recommendations: {e}")
        return pd.DataFrame()

def query_location_performance(conn) -> pd.DataFrame:
    """Query warehouse performance metrics"""
    try:
        logger.info("Querying DT_LOCATION_PERFORMANCE")
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
        df = pd.read_sql(query, conn)
        logger.info(f"✅ Retrieved {len(df)} location records")
        return df
    except Exception as e:
        logger.error(f"❌ Error querying DT_LOCATION_PERFORMANCE: {e}")
        return pd.DataFrame()

def query_category_heatmap(conn) -> pd.DataFrame:
    """Query category heatmap data"""
    try:
        logger.info("Querying DT_CATEGORY_HEATMAP")
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
        df = pd.read_sql(query, conn)
        logger.info(f"✅ Retrieved {len(df)} heatmap records")
        return df
    except Exception as e:
        logger.error(f"❌ Error querying DT_CATEGORY_HEATMAP: {e}")
        return pd.DataFrame()

def export_reorder_list(conn, location_filter: Optional[str] = None) -> pd.DataFrame:
    """Export reorder list for procurement"""
    try:
        logger.info(f"Exporting reorder list (location filter: {location_filter})")
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
        
        df = pd.read_sql(query, conn)
        logger.info(f"✅ Exported {len(df)} records")
        return df
    except Exception as e:
        logger.error(f"❌ Error exporting reorder list: {e}")
        st.error(f"Export failed: {e}")
        return pd.DataFrame()

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
        cursor.close()
        logger.info(f"✅ Export logged: {export_type}, {record_count} records")
    except Exception as e:
        logger.warning(f"⚠️ Failed to log export: {e}")

def close_connection(conn):
    """Close Snowflake connection"""
    if conn:
        conn.close()
        logger.info("Connection closed")

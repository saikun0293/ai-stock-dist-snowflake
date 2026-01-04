-- ============================================
-- INVENTORY HEATMAP APP - COMPLETE SETUP
-- Dataset:  Kaggle Grocery Inventory (ALL COLUMNS)
-- WITH PROPER DATA TYPE CONVERSIONS
-- ============================================

CREATE DATABASE IF NOT EXISTS inventory_app_db;
USE DATABASE inventory_app_db;

CREATE SCHEMA IF NOT EXISTS data_schema;
USE SCHEMA data_schema;

CREATE WAREHOUSE IF NOT EXISTS compute_wh 
    WITH WAREHOUSE_SIZE = 'X-SMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE;

USE WAREHOUSE compute_wh;

-- ============================================
-- CREATE FILE FORMAT WITH PROPER SETTINGS
-- ============================================
CREATE OR REPLACE FILE FORMAT csv_format
    TYPE = 'CSV'
    FIELD_DELIMITER = '\t'  -- Your data uses TAB separator
    SKIP_HEADER = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    NULL_IF = ('NULL', 'null', '')
    EMPTY_FIELD_AS_NULL = TRUE;

-- Create stage
CREATE OR REPLACE STAGE inventory_stage
    FILE_FORMAT = csv_format;

-- ============================================
-- RAW DATA TABLE - KEEPS ORIGINAL FORMAT
-- ============================================
CREATE OR REPLACE TABLE inventory_raw (
    -- Product Identifiers
    SKU_ID VARCHAR(50),
    SKU_Name VARCHAR(500),
    Category VARCHAR(100),
    ABC_Class VARCHAR(10),
    
    -- Supplier Information
    Supplier_ID VARCHAR(50),
    Supplier_Name VARCHAR(200),
    
    -- Location Information
    Warehouse_ID VARCHAR(50),
    Warehouse_Location VARCHAR(200),
    
    -- Batch & Date Information
    Batch_ID VARCHAR(100),
    Received_Date VARCHAR(50),      -- Keep as string initially
    Last_Purchase_Date VARCHAR(50),
    Expiry_Date VARCHAR(50),
    Audit_Date VARCHAR(50),
    
    -- Stock Levels
    Stock_Age_Days INTEGER,
    Quantity_On_Hand NUMBER(10,2),
    Quantity_Reserved NUMBER(10,2),
    Quantity_Committed NUMBER(10,2),
    Damaged_Qty NUMBER(10,2),
    Returns_Qty NUMBER(10,2),
    
    -- Sales & Demand
    Avg_Daily_Sales VARCHAR(50),    -- Keep as string (has commas)
    Forecast_Next_30d VARCHAR(50),
    Days_of_Inventory VARCHAR(50),
    SKU_Churn_Rate VARCHAR(50),
    Order_Frequency_per_month VARCHAR(50),
    
    -- Reorder Parameters
    Reorder_Point NUMBER(10,2),
    Safety_Stock NUMBER(10,2),
    Lead_Time_Days INTEGER,
    
    -- Financial Data
    Unit_Cost_USD VARCHAR(50),       -- Keep as string (has $ and commas)
    Last_Purchase_Price_USD VARCHAR(50),
    Total_Inventory_Value_USD VARCHAR(50),
    
    -- Quality & Accuracy
    Supplier_OnTime_Pct VARCHAR(50),  -- Keep as string (has %)
    FIFO_FEFO VARCHAR(50),
    Inventory_Status VARCHAR(50),
    Count_Variance NUMBER(10,2),
    Audit_Variance_Pct VARCHAR(50),   -- Keep as string (has %)
    Demand_Forecast_Accuracy_Pct VARCHAR(50),
    
    -- Metadata
    Notes VARCHAR(1000),
    upload_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- ============================================
-- CLEANED & CONVERTED TABLE
-- ============================================
CREATE OR REPLACE TABLE inventory_cleaned (
    SKU_ID VARCHAR(50) NOT NULL,
    SKU_NAME VARCHAR(255),
    CATEGORY VARCHAR(100),
    ABC_CLASS VARCHAR(10),
    SUPPLIER_ID VARCHAR(50),
    SUPPLIER_NAME VARCHAR(255),
    WAREHOUSE_ID VARCHAR(50),
    WAREHOUSE_LOCATION VARCHAR(255),
    BATCH_ID VARCHAR(50),
    RECEIVED_DATE DATE,
    LAST_PURCHASE_DATE DATE,
    EXPIRY_DATE DATE,
    AUDIT_DATE DATE,
    STOCK_AGE_DAYS INTEGER,
    QUANTITY_ON_HAND DECIMAL(18,2),
    QUANTITY_RESERVED DECIMAL(18,2),
    QUANTITY_COMMITTED DECIMAL(18,2),
    DAMAGED_QTY DECIMAL(18,2),
    RETURNS_QTY DECIMAL(18,2),
    AVG_DAILY_SALES DECIMAL(18,2),
    FORECAST_NEXT_30D INTEGER,
    DAYS_OF_INVENTORY DECIMAL(18,2),
    SKU_CHURN_RATE DECIMAL(18,2),
    ORDER_FREQUENCY_PER_MONTH DECIMAL(18,2),
    REORDER_POINT DECIMAL(18,2),
    SAFETY_STOCK DECIMAL(18,2),
    LEAD_TIME_DAYS INTEGER,
    UNIT_COST_USD DECIMAL(18,2),
    LAST_PURCHASE_PRICE_USD DECIMAL(18,2),
    TOTAL_INVENTORY_VALUE_USD DECIMAL(18,2),
    SUPPLIER_ONTIME_PCT DECIMAL(5,2),
    FIFO_FEFO VARCHAR(10),
    INVENTORY_STATUS VARCHAR(50),
    COUNT_VARIANCE DECIMAL(18,2),
    AUDIT_VARIANCE_PCT DECIMAL(5,2),
    DEMAND_FORECAST_ACCURACY_PCT DECIMAL(5,2),
    NOTES VARCHAR(1000),
    UPLOAD_TIMESTAMP TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    PRIMARY KEY (SKU_ID, BATCH_ID)
);

INSERT INTO inventory_cleaned (
    SKU_ID,
    SKU_NAME,
    CATEGORY,
    ABC_CLASS,
    SUPPLIER_ID,
    SUPPLIER_NAME,
    WAREHOUSE_ID,
    WAREHOUSE_LOCATION,
    BATCH_ID,
    RECEIVED_DATE,
    LAST_PURCHASE_DATE,
    EXPIRY_DATE,
    AUDIT_DATE,
    STOCK_AGE_DAYS,
    QUANTITY_ON_HAND,
    QUANTITY_RESERVED,
    QUANTITY_COMMITTED,
    DAMAGED_QTY,
    RETURNS_QTY,
    AVG_DAILY_SALES,
    FORECAST_NEXT_30D,
    DAYS_OF_INVENTORY,
    SKU_CHURN_RATE,
    ORDER_FREQUENCY_PER_MONTH,
    REORDER_POINT,
    SAFETY_STOCK,
    LEAD_TIME_DAYS,
    UNIT_COST_USD,
    LAST_PURCHASE_PRICE_USD,
    TOTAL_INVENTORY_VALUE_USD,
    SUPPLIER_ONTIME_PCT,
    FIFO_FEFO,
    INVENTORY_STATUS,
    COUNT_VARIANCE,
    AUDIT_VARIANCE_PCT,
    DEMAND_FORECAST_ACCURACY_PCT,
    NOTES
)
SELECT 
    -- Clean SKU_ID:  Remove whitespace, uppercase
    TRIM(UPPER(SKU_ID)) AS SKU_ID,
    
    -- Clean SKU_NAME:  Remove extra spaces
    TRIM(SKU_NAME) AS SKU_NAME,
    
    -- Clean CATEGORY:  Standardize case
    TRIM(INITCAP(CATEGORY)) AS CATEGORY,
    
    -- Clean ABC_CLASS: Uppercase, default to 'C' if null
    COALESCE(UPPER(TRIM(ABC_CLASS)), 'C') AS ABC_CLASS,
    
    -- Clean SUPPLIER_ID
    TRIM(UPPER(SUPPLIER_ID)) AS SUPPLIER_ID,
    
    -- Clean SUPPLIER_NAME
    TRIM(SUPPLIER_NAME) AS SUPPLIER_NAME,
    
    -- Clean WAREHOUSE_ID
    TRIM(UPPER(WAREHOUSE_ID)) AS WAREHOUSE_ID,
    
    -- Clean WAREHOUSE_LOCATION
    TRIM(WAREHOUSE_LOCATION) AS WAREHOUSE_LOCATION,
    
    -- Clean BATCH_ID
    TRIM(UPPER(BATCH_ID)) AS BATCH_ID,
    
    -- Clean dates:  Convert strings to proper dates, handle nulls
    TRY_TO_DATE(RECEIVED_DATE, 'YYYY-MM-DD') AS RECEIVED_DATE,
    TRY_TO_DATE(LAST_PURCHASE_DATE, 'YYYY-MM-DD') AS LAST_PURCHASE_DATE,
    TRY_TO_DATE(EXPIRY_DATE, 'YYYY-MM-DD') AS EXPIRY_DATE,
    TRY_TO_DATE(AUDIT_DATE, 'YYYY-MM-DD') AS AUDIT_DATE,
    
    -- Clean numeric fields:  Handle nulls, replace with 0 or appropriate defaults
    COALESCE(TRY_CAST(STOCK_AGE_DAYS AS INTEGER), 0) AS STOCK_AGE_DAYS,
    
    -- Clean quantities: Replace commas, handle nulls, set negatives to 0
    GREATEST(COALESCE(TRY_CAST(REPLACE(QUANTITY_ON_HAND, ',', '') AS DECIMAL(18,2)), 0), 0) AS QUANTITY_ON_HAND,
    GREATEST(COALESCE(TRY_CAST(REPLACE(QUANTITY_RESERVED, ',', '') AS DECIMAL(18,2)), 0), 0) AS QUANTITY_RESERVED,
    GREATEST(COALESCE(TRY_CAST(REPLACE(QUANTITY_COMMITTED, ',', '') AS DECIMAL(18,2)), 0), 0) AS QUANTITY_COMMITTED,
    GREATEST(COALESCE(TRY_CAST(REPLACE(DAMAGED_QTY, ',', '') AS DECIMAL(18,2)), 0), 0) AS DAMAGED_QTY,
    GREATEST(COALESCE(TRY_CAST(REPLACE(RETURNS_QTY, ',', '') AS DECIMAL(18,2)), 0), 0) AS RETURNS_QTY,
    
    -- Clean sales and forecast data
    GREATEST(COALESCE(TRY_CAST(REPLACE(AVG_DAILY_SALES, ',', '') AS DECIMAL(18,2)), 0), 0) AS AVG_DAILY_SALES,
    GREATEST(COALESCE(TRY_CAST(REPLACE(FORECAST_NEXT_30D, ',', '') AS INTEGER), 0), 0) AS FORECAST_NEXT_30D,
    GREATEST(COALESCE(TRY_CAST(REPLACE(DAYS_OF_INVENTORY, ',', '') AS DECIMAL(18,2)), 0), 0) AS DAYS_OF_INVENTORY,
    GREATEST(COALESCE(TRY_CAST(REPLACE(SKU_CHURN_RATE, ',', '') AS DECIMAL(18,2)), 0), 0) AS SKU_CHURN_RATE,
    GREATEST(COALESCE(TRY_CAST(REPLACE(ORDER_FREQUENCY_PER_MONTH, ',', '') AS DECIMAL(18,2)), 0), 0) AS ORDER_FREQUENCY_PER_MONTH,
    
    -- Clean reorder data
    GREATEST(COALESCE(TRY_CAST(REPLACE(REORDER_POINT, ',', '') AS DECIMAL(18,2)), 0), 0) AS REORDER_POINT,
    GREATEST(COALESCE(TRY_CAST(REPLACE(SAFETY_STOCK, ',', '') AS DECIMAL(18,2)), 0), 0) AS SAFETY_STOCK,
    GREATEST(COALESCE(TRY_CAST(LEAD_TIME_DAYS AS INTEGER), 0), 0) AS LEAD_TIME_DAYS,
    
    -- Clean cost data:  Remove $ and commas
    GREATEST(COALESCE(TRY_CAST(REPLACE(REPLACE(UNIT_COST_USD, '$', ''), ',', '') AS DECIMAL(18,2)), 0), 0) AS UNIT_COST_USD,
    GREATEST(COALESCE(TRY_CAST(REPLACE(REPLACE(LAST_PURCHASE_PRICE_USD, '$', ''), ',', '') AS DECIMAL(18,2)), 0), 0) AS LAST_PURCHASE_PRICE_USD,
    GREATEST(COALESCE(TRY_CAST(REPLACE(REPLACE(TOTAL_INVENTORY_VALUE_USD, '$', ''), ',', '') AS DECIMAL(18,2)), 0), 0) AS TOTAL_INVENTORY_VALUE_USD,
    
    -- Clean percentage:  Remove % sign, convert to decimal
    COALESCE(TRY_CAST(REPLACE(SUPPLIER_ONTIME_PCT, '%', '') AS DECIMAL(5,2)), 0) AS SUPPLIER_ONTIME_PCT,
    
    -- Clean FIFO_FEFO: Standardize values
    CASE 
        WHEN UPPER(TRIM(FIFO_FEFO)) IN ('FIFO', 'FEFO') THEN UPPER(TRIM(FIFO_FEFO))
        ELSE 'FIFO'
    END AS FIFO_FEFO,
    
    -- Clean INVENTORY_STATUS: Standardize case
    TRIM(INITCAP(INVENTORY_STATUS)) AS INVENTORY_STATUS,
    
    -- Clean variance data
    COALESCE(TRY_CAST(REPLACE(COUNT_VARIANCE, ',', '') AS DECIMAL(18,2)), 0) AS COUNT_VARIANCE,
    COALESCE(TRY_CAST(REPLACE(AUDIT_VARIANCE_PCT, '%', '') AS DECIMAL(5,2)), 0) AS AUDIT_VARIANCE_PCT,
    COALESCE(TRY_CAST(REPLACE(DEMAND_FORECAST_ACCURACY_PCT, '%', '') AS DECIMAL(5,2)), 0) AS DEMAND_FORECAST_ACCURACY_PCT,
    
    -- Clean notes:  Trim whitespace
    NULLIF(TRIM(NOTES), '') AS NOTES

FROM inventory_raw
WHERE SKU_ID IS NOT NULL  -- Filter out rows with no SKU_ID
  AND BATCH_ID IS NOT NULL;  -- Filter out rows with no BATCH_ID
-- ============================================
-- VERIFY SETUP
-- ============================================
DESCRIBE TABLE inventory_raw;
DESCRIBE TABLE inventory_cleaned;
SELECT 'Setup complete!  Ready for data load.' AS status;

-- After data load, check first few rows:
-- SELECT * FROM inventory_cleaned LIMIT 10;
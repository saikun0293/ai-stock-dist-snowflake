-- ============================================
-- Inventory Monitoring System - Database Setup
-- ============================================

-- Create database and schema
CREATE DATABASE IF NOT EXISTS INVENTORY_DB;
USE DATABASE INVENTORY_DB;

CREATE SCHEMA IF NOT EXISTS INVENTORY_SCHEMA;
USE SCHEMA INVENTORY_SCHEMA;

-- ============================================
-- 1. CORE TABLES
-- ============================================

-- Inventory snapshot table
CREATE OR REPLACE TABLE INVENTORY_SNAPSHOTS (
    snapshot_id NUMBER AUTOINCREMENT PRIMARY KEY,
    snapshot_date DATE NOT NULL,
    location VARCHAR(200) NOT NULL,
    category VARCHAR(50) NOT NULL,
    item_name VARCHAR(200) NOT NULL,
    current_stock NUMBER NOT NULL,
    consumption NUMBER NOT NULL,
    restock_amount NUMBER DEFAULT 0,
    restocked BOOLEAN DEFAULT FALSE,
    reorder_point NUMBER NOT NULL,
    max_stock NUMBER NOT NULL,
    days_until_stockout FLOAT,
    stock_status VARCHAR(20) NOT NULL,
    stock_percentage FLOAT,
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    CONSTRAINT valid_stock_status CHECK (stock_status IN ('CRITICAL', 'LOW', 'MODERATE', 'GOOD'))
);

-- Alert history table
CREATE OR REPLACE TABLE ALERT_HISTORY (
    alert_id NUMBER AUTOINCREMENT PRIMARY KEY,
    alert_date DATE NOT NULL,
    location VARCHAR(200) NOT NULL,
    category VARCHAR(50) NOT NULL,
    item_name VARCHAR(200) NOT NULL,
    current_stock NUMBER NOT NULL,
    alert_type VARCHAR(20) NOT NULL,
    days_until_stockout FLOAT,
    resolved BOOLEAN DEFAULT FALSE,
    priority VARCHAR(20) NOT NULL,
    resolved_date DATE,
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    CONSTRAINT valid_alert_type CHECK (alert_type IN ('CRITICAL', 'LOW')),
    CONSTRAINT valid_priority CHECK (priority IN ('HIGH', 'MEDIUM', 'LOW'))
);

-- Forecast predictions table (for Cortex AI results)
CREATE OR REPLACE TABLE FORECAST_PREDICTIONS (
    prediction_id NUMBER AUTOINCREMENT PRIMARY KEY,
    prediction_date DATE NOT NULL,
    location VARCHAR(200) NOT NULL,
    category VARCHAR(50) NOT NULL,
    item_name VARCHAR(200) NOT NULL,
    predicted_consumption FLOAT,
    predicted_stock FLOAT,
    forecast_horizon_days NUMBER,
    confidence_interval_lower FLOAT,
    confidence_interval_upper FLOAT,
    model_accuracy FLOAT,
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- ============================================
-- 2. INDEXES FOR PERFORMANCE
-- ============================================

-- Indexes on frequently queried columns
CREATE INDEX IF NOT EXISTS idx_inventory_date ON INVENTORY_SNAPSHOTS(snapshot_date);
CREATE INDEX IF NOT EXISTS idx_inventory_location ON INVENTORY_SNAPSHOTS(location);
CREATE INDEX IF NOT EXISTS idx_inventory_status ON INVENTORY_SNAPSHOTS(stock_status);

CREATE INDEX IF NOT EXISTS idx_alert_date ON ALERT_HISTORY(alert_date);
CREATE INDEX IF NOT EXISTS idx_alert_location ON ALERT_HISTORY(location);
CREATE INDEX IF NOT EXISTS idx_alert_resolved ON ALERT_HISTORY(resolved);

-- ============================================
-- 3. VIEWS FOR ANALYTICS
-- ============================================

-- Current inventory status view
CREATE OR REPLACE VIEW V_CURRENT_INVENTORY AS
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
FROM INVENTORY_SNAPSHOTS
QUALIFY ROW_NUMBER() OVER (PARTITION BY location, item_name ORDER BY snapshot_date DESC) = 1;

-- Critical items view (items needing immediate attention)
CREATE OR REPLACE VIEW V_CRITICAL_ITEMS AS
SELECT 
    location,
    category,
    item_name,
    current_stock,
    days_until_stockout,
    stock_status,
    snapshot_date
FROM V_CURRENT_INVENTORY
WHERE stock_status IN ('CRITICAL', 'LOW')
ORDER BY days_until_stockout ASC;

-- Unresolved alerts view
CREATE OR REPLACE VIEW V_UNRESOLVED_ALERTS AS
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
    DATEDIFF(day, alert_date, CURRENT_DATE()) AS days_open
FROM ALERT_HISTORY
WHERE resolved = FALSE
ORDER BY priority DESC, alert_date ASC;

-- Stock trends view (7-day rolling average)
CREATE OR REPLACE VIEW V_STOCK_TRENDS AS
SELECT 
    snapshot_date,
    location,
    category,
    item_name,
    current_stock,
    AVG(current_stock) OVER (
        PARTITION BY location, item_name 
        ORDER BY snapshot_date 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS stock_7day_avg,
    AVG(consumption) OVER (
        PARTITION BY location, item_name 
        ORDER BY snapshot_date 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS consumption_7day_avg
FROM INVENTORY_SNAPSHOTS
ORDER BY snapshot_date DESC, location, item_name;

-- Location-wise summary view
CREATE OR REPLACE VIEW V_LOCATION_SUMMARY AS
SELECT 
    location,
    COUNT(DISTINCT item_name) AS total_items,
    SUM(CASE WHEN stock_status = 'CRITICAL' THEN 1 ELSE 0 END) AS critical_items,
    SUM(CASE WHEN stock_status = 'LOW' THEN 1 ELSE 0 END) AS low_items,
    SUM(CASE WHEN stock_status = 'MODERATE' THEN 1 ELSE 0 END) AS moderate_items,
    SUM(CASE WHEN stock_status = 'GOOD' THEN 1 ELSE 0 END) AS good_items,
    AVG(stock_percentage) AS avg_stock_percentage
FROM V_CURRENT_INVENTORY
GROUP BY location
ORDER BY critical_items DESC, low_items DESC;

-- ============================================
-- 4. FILE FORMAT AND STAGE FOR DATA LOADING
-- ============================================

-- Create file format for CSV
CREATE OR REPLACE FILE FORMAT CSV_FORMAT
    TYPE = 'CSV'
    FIELD_DELIMITER = ','
    SKIP_HEADER = 1
    NULL_IF = ('NULL', 'null', '')
    EMPTY_FIELD_AS_NULL = TRUE
    FIELD_OPTIONALLY_ENCLOSED_BY = '"';

-- Create internal stage for data loading
CREATE OR REPLACE STAGE INVENTORY_STAGE
    FILE_FORMAT = CSV_FORMAT;

-- ============================================
-- 5. HELPER PROCEDURES
-- ============================================

-- Procedure to load data from CSV
CREATE OR REPLACE PROCEDURE LOAD_INVENTORY_DATA(stage_path VARCHAR)
RETURNS VARCHAR
LANGUAGE SQL
AS
$$
BEGIN
    -- Load inventory snapshots
    COPY INTO INVENTORY_SNAPSHOTS (
        snapshot_date, location, category, item_name, current_stock,
        consumption, restock_amount, restocked, reorder_point, max_stock,
        days_until_stockout, stock_status, stock_percentage
    )
    FROM @INVENTORY_STAGE
    FILE_FORMAT = CSV_FORMAT
    PATTERN = '.*inventory_data.csv'
    ON_ERROR = 'CONTINUE';
    
    RETURN 'Data loaded successfully';
END;
$$;

-- Procedure to generate alerts
CREATE OR REPLACE PROCEDURE GENERATE_ALERTS()
RETURNS VARCHAR
LANGUAGE SQL
AS
$$
BEGIN
    -- Insert new alerts for critical and low stock items
    INSERT INTO ALERT_HISTORY (
        alert_date, location, category, item_name, current_stock,
        alert_type, days_until_stockout, resolved, priority
    )
    SELECT 
        CURRENT_DATE(),
        location,
        category,
        item_name,
        current_stock,
        stock_status,
        days_until_stockout,
        FALSE,
        CASE 
            WHEN stock_status = 'CRITICAL' THEN 'HIGH'
            WHEN stock_status = 'LOW' THEN 'MEDIUM'
            ELSE 'LOW'
        END
    FROM V_CRITICAL_ITEMS
    WHERE NOT EXISTS (
        SELECT 1 FROM ALERT_HISTORY ah
        WHERE ah.location = V_CRITICAL_ITEMS.location
          AND ah.item_name = V_CRITICAL_ITEMS.item_name
          AND ah.resolved = FALSE
    );
    
    RETURN 'Alerts generated successfully';
END;
$$;

-- ============================================
-- Grant permissions (adjust as needed)
-- ============================================

GRANT USAGE ON DATABASE INVENTORY_DB TO ROLE PUBLIC;
GRANT USAGE ON SCHEMA INVENTORY_SCHEMA TO ROLE PUBLIC;
GRANT SELECT ON ALL VIEWS IN SCHEMA INVENTORY_SCHEMA TO ROLE PUBLIC;
GRANT SELECT ON ALL TABLES IN SCHEMA INVENTORY_SCHEMA TO ROLE PUBLIC;

-- ============================================
-- Setup complete
-- ============================================

SELECT 'Database setup completed successfully!' AS status;

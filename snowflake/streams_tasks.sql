-- ============================================
-- STREAMS & TASKS FOR AUTOMATION
-- Purpose: Automated monitoring and alerting
-- ============================================

USE DATABASE inventory_app_db;
USE SCHEMA data_schema;
USE WAREHOUSE compute_wh;

-- ============================================
-- 1. CREATE ALERT HISTORY TABLE
-- ============================================
CREATE OR REPLACE TABLE ALERT_HISTORY (
    alert_id NUMBER AUTOINCREMENT PRIMARY KEY,
    alert_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    sku_id VARCHAR(50) NOT NULL,
    sku_name VARCHAR(255),
    category VARCHAR(100),
    location VARCHAR(255),
    warehouse_id VARCHAR(50),
    abc_class VARCHAR(10),
    
    -- Alert Details
    alert_type VARCHAR(20) NOT NULL,  -- STOCKOUT, CRITICAL, LOW_STOCK, URGENT
    priority VARCHAR(20) NOT NULL,    -- CRITICAL, HIGH, MEDIUM, LOW
    
    -- Stock Info
    quantity_on_hand DECIMAL(18,2),
    reorder_point DECIMAL(18,2),
    safety_stock DECIMAL(18,2),
    days_until_stockout DECIMAL(10,2),
    
    -- Resolution
    resolved BOOLEAN DEFAULT FALSE,
    resolved_timestamp TIMESTAMP_NTZ,
    resolved_by VARCHAR(100),
    resolution_notes VARCHAR(500),
    
    -- Supplier Info
    supplier_name VARCHAR(255),
    supplier_id VARCHAR(50),
    lead_time_days INTEGER,
    
    -- Financial
    unit_cost_usd DECIMAL(18,2),
    estimated_impact_usd DECIMAL(18,2)
);

-- ============================================
-- 2. CREATE REORDER ACTION LOG TABLE
-- ============================================
CREATE OR REPLACE TABLE REORDER_ACTION_LOG (
    action_id NUMBER AUTOINCREMENT PRIMARY KEY,
    action_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    sku_id VARCHAR(50) NOT NULL,
    sku_name VARCHAR(255),
    category VARCHAR(100),
    location VARCHAR(255),
    
    -- Reorder Details
    recommended_qty DECIMAL(18,2),
    economic_order_qty DECIMAL(18,2),
    ordered_qty DECIMAL(18,2),
    priority_score INTEGER,
    
    -- Financial
    unit_cost_usd DECIMAL(18,2),
    total_order_value_usd DECIMAL(18,2),
    
    -- Status
    status VARCHAR(20) DEFAULT 'PENDING',  -- PENDING, ORDERED, DELIVERED, CANCELLED
    order_date DATE,
    expected_delivery_date DATE,
    actual_delivery_date DATE,
    
    -- Supplier
    supplier_name VARCHAR(255),
    supplier_id VARCHAR(50),
    
    -- Tracking
    created_by VARCHAR(100),
    notes VARCHAR(500)
);

-- ============================================
-- 3. CREATE EXPORT LOG TABLE
-- ============================================
CREATE OR REPLACE TABLE EXPORT_LOG (
    export_id NUMBER AUTOINCREMENT PRIMARY KEY,
    export_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    export_type VARCHAR(50),  -- REORDER_LIST, ALERTS, STOCK_REPORT
    record_count INTEGER,
    exported_by VARCHAR(100),
    file_format VARCHAR(20),  -- CSV, EXCEL, JSON
    filters_applied VARIANT,  -- JSON object with applied filters
    notes VARCHAR(500)
);

-- ============================================
-- 4. CREATE STREAM FOR INVENTORY CHANGES
-- ============================================
CREATE OR REPLACE STREAM INVENTORY_CHANGES_STREAM
ON TABLE inventory_cleaned
APPEND_ONLY = FALSE;

-- ============================================
-- 5. STORED PROCEDURE: Generate Alert
-- ============================================
CREATE OR REPLACE PROCEDURE SP_GENERATE_ALERTS()
RETURNS STRING
LANGUAGE SQL
AS
$$
BEGIN
    -- Insert new alerts for critical stock levels
    INSERT INTO ALERT_HISTORY (
        sku_id, sku_name, category, location, warehouse_id, abc_class,
        alert_type, priority,
        quantity_on_hand, reorder_point, safety_stock, days_until_stockout,
        supplier_name, supplier_id, lead_time_days,
        unit_cost_usd, estimated_impact_usd
    )
    SELECT 
        SKU_ID,
        SKU_NAME,
        CATEGORY,
        WAREHOUSE_LOCATION,
        WAREHOUSE_ID,
        ABC_CLASS,
        
        -- Alert Type
        CASE 
            WHEN QUANTITY_ON_HAND <= 0 THEN 'STOCKOUT'
            WHEN QUANTITY_ON_HAND <= SAFETY_STOCK THEN 'CRITICAL'
            WHEN QUANTITY_ON_HAND <= REORDER_POINT THEN 'LOW_STOCK'
            WHEN AVG_DAILY_SALES > 0 AND (QUANTITY_ON_HAND / AVG_DAILY_SALES) <= 3 THEN 'URGENT'
            ELSE 'WARNING'
        END AS alert_type,
        
        -- Priority
        CASE 
            WHEN QUANTITY_ON_HAND <= 0 OR (AVG_DAILY_SALES > 0 AND (QUANTITY_ON_HAND / AVG_DAILY_SALES) <= 1) THEN 'CRITICAL'
            WHEN QUANTITY_ON_HAND <= SAFETY_STOCK OR (AVG_DAILY_SALES > 0 AND (QUANTITY_ON_HAND / AVG_DAILY_SALES) <= 3) THEN 'HIGH'
            WHEN QUANTITY_ON_HAND <= REORDER_POINT OR (AVG_DAILY_SALES > 0 AND (QUANTITY_ON_HAND / AVG_DAILY_SALES) <= 7) THEN 'MEDIUM'
            ELSE 'LOW'
        END AS priority,
        
        QUANTITY_ON_HAND,
        REORDER_POINT,
        SAFETY_STOCK,
        
        -- Days until stockout
        CASE 
            WHEN AVG_DAILY_SALES > 0 THEN 
                ROUND((QUANTITY_ON_HAND - QUANTITY_RESERVED - QUANTITY_COMMITTED) / AVG_DAILY_SALES, 1)
            ELSE NULL
        END AS days_until_stockout,
        
        SUPPLIER_NAME,
        SUPPLIER_ID,
        LEAD_TIME_DAYS,
        UNIT_COST_USD,
        
        -- Estimated financial impact (cost of potential stockout)
        ROUND(AVG_DAILY_SALES * LEAD_TIME_DAYS * UNIT_COST_USD, 2) AS estimated_impact_usd
    FROM inventory_cleaned
    WHERE (QUANTITY_ON_HAND <= REORDER_POINT 
           OR (AVG_DAILY_SALES > 0 AND (QUANTITY_ON_HAND / AVG_DAILY_SALES) <= 7))
      AND INVENTORY_STATUS NOT IN ('Discontinued', 'Obsolete')
      -- Avoid duplicate alerts (check if alert already exists for this SKU+Location in last 24 hours)
      AND NOT EXISTS (
          SELECT 1 FROM ALERT_HISTORY ah
          WHERE ah.sku_id = inventory_cleaned.SKU_ID
            AND ah.location = inventory_cleaned.WAREHOUSE_LOCATION
            AND ah.resolved = FALSE
            AND ah.alert_timestamp >= DATEADD(hour, -24, CURRENT_TIMESTAMP())
      );
    
    RETURN 'Alerts generated successfully. Inserted ' || SQLROWCOUNT || ' new alerts.';
END;
$$;

-- ============================================
-- 6. STORED PROCEDURE: Generate Reorder Recommendations
-- ============================================
CREATE OR REPLACE PROCEDURE SP_GENERATE_REORDER_RECOMMENDATIONS()
RETURNS STRING
LANGUAGE SQL
AS
$$
BEGIN
    -- Insert new reorder recommendations
    INSERT INTO REORDER_ACTION_LOG (
        sku_id, sku_name, category, location,
        recommended_qty, economic_order_qty, priority_score,
        unit_cost_usd, total_order_value_usd,
        supplier_name, supplier_id,
        created_by
    )
    SELECT 
        SKU_ID,
        SKU_NAME,
        CATEGORY,
        WAREHOUSE_LOCATION,
        
        -- Recommended Order Quantity
        GREATEST(0, 
            ROUND(SAFETY_STOCK + (AVG_DAILY_SALES * LEAD_TIME_DAYS * 1.5) - 
                  (QUANTITY_ON_HAND - QUANTITY_RESERVED - QUANTITY_COMMITTED))
        ) AS recommended_qty,
        
        -- Economic Order Quantity
        CASE 
            WHEN AVG_DAILY_SALES > 0 THEN
                ROUND(SQRT(2 * AVG_DAILY_SALES * 30 * 10 / NULLIF(UNIT_COST_USD, 0)))
            ELSE REORDER_POINT
        END AS economic_order_qty,
        
        -- Priority Score
        CASE 
            WHEN QUANTITY_ON_HAND <= 0 THEN 10
            WHEN QUANTITY_ON_HAND <= SAFETY_STOCK * 0.5 THEN 9
            WHEN QUANTITY_ON_HAND <= SAFETY_STOCK THEN 8
            WHEN QUANTITY_ON_HAND <= REORDER_POINT * 0.75 THEN 7
            WHEN QUANTITY_ON_HAND <= REORDER_POINT THEN 6
            ELSE 5
        END AS priority_score,
        
        UNIT_COST_USD,
        
        -- Total Order Value
        ROUND((GREATEST(0, 
            ROUND(SAFETY_STOCK + (AVG_DAILY_SALES * LEAD_TIME_DAYS * 1.5) - 
                  (QUANTITY_ON_HAND - QUANTITY_RESERVED - QUANTITY_COMMITTED))
        )) * UNIT_COST_USD, 2) AS total_order_value_usd,
        
        SUPPLIER_NAME,
        SUPPLIER_ID,
        'SYSTEM' AS created_by
    FROM inventory_cleaned
    WHERE QUANTITY_ON_HAND <= REORDER_POINT
      AND INVENTORY_STATUS NOT IN ('Discontinued', 'Obsolete')
      -- Avoid duplicates (check if recommendation already exists in PENDING status)
      AND NOT EXISTS (
          SELECT 1 FROM REORDER_ACTION_LOG ral
          WHERE ral.sku_id = inventory_cleaned.SKU_ID
            AND ral.location = inventory_cleaned.WAREHOUSE_LOCATION
            AND ral.status = 'PENDING'
            AND ral.action_timestamp >= DATEADD(day, -7, CURRENT_TIMESTAMP())
      );
    
    RETURN 'Reorder recommendations generated. Inserted ' || SQLROWCOUNT || ' new recommendations.';
END;
$$;

-- ============================================
-- 7. TASK: Daily Alert Generation
-- Runs every hour to check for new critical stock situations
-- ============================================
CREATE OR REPLACE TASK TASK_HOURLY_ALERT_CHECK
    WAREHOUSE = compute_wh
    SCHEDULE = '60 MINUTE'
AS
    CALL SP_GENERATE_ALERTS();

-- ============================================
-- 8. TASK: Daily Reorder Recommendations
-- Runs every 6 hours to generate reorder recommendations
-- ============================================
CREATE OR REPLACE TASK TASK_REORDER_RECOMMENDATIONS
    WAREHOUSE = compute_wh
    SCHEDULE = '360 MINUTE'
AS
    CALL SP_GENERATE_REORDER_RECOMMENDATIONS();

-- ============================================
-- 9. TASK: Weekly Alert Cleanup
-- Runs weekly to archive resolved alerts older than 90 days
-- ============================================
CREATE OR REPLACE TASK TASK_WEEKLY_ALERT_CLEANUP
    WAREHOUSE = compute_wh
    SCHEDULE = 'USING CRON 0 2 * * 0 America/New_York'  -- Every Sunday at 2 AM
AS
    DELETE FROM ALERT_HISTORY
    WHERE resolved = TRUE
      AND resolved_timestamp < DATEADD(day, -90, CURRENT_TIMESTAMP());

-- ============================================
-- ACTIVATE TASKS
-- ============================================
-- Note: Tasks are created in SUSPENDED state. Execute these to activate:

-- ALTER TASK TASK_HOURLY_ALERT_CHECK RESUME;
-- ALTER TASK TASK_REORDER_RECOMMENDATIONS RESUME;
-- ALTER TASK TASK_WEEKLY_ALERT_CLEANUP RESUME;

-- ============================================
-- VERIFY SETUP
-- ============================================
SELECT 'Streams, tasks, and tables created successfully!' AS STATUS;

-- Check stream
SELECT 'INVENTORY_CHANGES_STREAM' AS OBJECT_NAME, 
       SYSTEM$STREAM_HAS_DATA('INVENTORY_CHANGES_STREAM') AS HAS_DATA;

-- Check tasks
SHOW TASKS LIKE 'TASK_%';

-- Test procedures (optional)
-- CALL SP_GENERATE_ALERTS();
-- CALL SP_GENERATE_REORDER_RECOMMENDATIONS();

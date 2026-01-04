-- ============================================
-- 🎯 MASTER EXECUTION SCRIPT
-- Run this step-by-step in Snowflake
-- ============================================

-- ============================================
-- STEP 1: Verify Your Data is Loaded
-- ============================================
USE DATABASE inventory_app_db;
USE SCHEMA data_schema;
USE WAREHOUSE compute_wh;

-- Check if data exists
SELECT COUNT(*) AS total_records FROM inventory_cleaned;
-- Expected: Should show count > 0

SELECT COUNT(*) AS total_locations FROM (SELECT DISTINCT WAREHOUSE_LOCATION FROM inventory_cleaned);
SELECT COUNT(*) AS total_categories FROM (SELECT DISTINCT CATEGORY FROM inventory_cleaned);
SELECT COUNT(*) AS total_skus FROM (SELECT DISTINCT SKU_ID FROM inventory_cleaned);

-- Sample data preview
SELECT * FROM inventory_cleaned LIMIT 10;

-- ============================================
-- STEP 2: Create Views for Heatmap
-- ============================================
-- Copy-paste and execute entire content of:
-- snowflake/views_heatmap.sql

-- Verify views created:
SHOW VIEWS;

-- Test views:
SELECT COUNT(*) FROM V_STOCK_HEALTH_MATRIX;
SELECT COUNT(*) FROM V_CRITICAL_ITEMS;
SELECT * FROM V_LOCATION_CATEGORY_SUMMARY LIMIT 5;

-- ============================================
-- STEP 3: Create Dynamic Tables
-- ============================================
-- Copy-paste and execute entire content of:
-- snowflake/dynamic_tables.sql

-- Verify dynamic tables created:
SHOW DYNAMIC TABLES;

-- Check if they have data (may take a few minutes for first refresh):
SELECT COUNT(*) FROM DT_STOCK_HEALTH;
SELECT COUNT(*) FROM DT_ACTIVE_ALERTS;
SELECT COUNT(*) FROM DT_REORDER_RECOMMENDATIONS;

-- If empty, manually trigger refresh:
ALTER DYNAMIC TABLE DT_STOCK_HEALTH REFRESH;
ALTER DYNAMIC TABLE DT_ACTIVE_ALERTS REFRESH;
ALTER DYNAMIC TABLE DT_REORDER_RECOMMENDATIONS REFRESH;
ALTER DYNAMIC TABLE DT_LOCATION_PERFORMANCE REFRESH;
ALTER DYNAMIC TABLE DT_CATEGORY_HEATMAP REFRESH;

-- Wait 30 seconds and check again:
SELECT 'DT_STOCK_HEALTH' AS table_name, COUNT(*) FROM DT_STOCK_HEALTH
UNION ALL
SELECT 'DT_ACTIVE_ALERTS', COUNT(*) FROM DT_ACTIVE_ALERTS
UNION ALL
SELECT 'DT_REORDER_RECOMMENDATIONS', COUNT(*) FROM DT_REORDER_RECOMMENDATIONS
UNION ALL
SELECT 'DT_LOCATION_PERFORMANCE', COUNT(*) FROM DT_LOCATION_PERFORMANCE
UNION ALL
SELECT 'DT_CATEGORY_HEATMAP', COUNT(*) FROM DT_CATEGORY_HEATMAP;

-- ============================================
-- STEP 4: Create Streams, Tasks, and Tables
-- ============================================
-- Copy-paste and execute entire content of:
-- snowflake/streams_tasks.sql

-- Verify objects created:
SHOW STREAMS;
SHOW TASKS;
SHOW TABLES LIKE '%ALERT%' OR '%REORDER%' OR '%EXPORT%';

-- Test stored procedures:
CALL SP_GENERATE_ALERTS();
-- Should return: "Alerts generated successfully. Inserted X new alerts."

CALL SP_GENERATE_REORDER_RECOMMENDATIONS();
-- Should return: "Reorder recommendations generated. Inserted X new recommendations."

-- Check if alerts were created:
SELECT COUNT(*) FROM ALERT_HISTORY;
SELECT * FROM ALERT_HISTORY LIMIT 5;

-- Check reorder recommendations:
SELECT COUNT(*) FROM REORDER_ACTION_LOG;
SELECT * FROM REORDER_ACTION_LOG LIMIT 5;

-- ============================================
-- STEP 5: Activate Tasks (OPTIONAL)
-- ============================================
-- Only run these if you want automated hourly/daily processing

-- Resume tasks:
ALTER TASK TASK_HOURLY_ALERT_CHECK RESUME;
ALTER TASK TASK_REORDER_RECOMMENDATIONS RESUME;
ALTER TASK TASK_WEEKLY_ALERT_CLEANUP RESUME;

-- Verify tasks are running:
SHOW TASKS;
-- STATE column should show 'started'

-- To suspend tasks later:
-- ALTER TASK TASK_HOURLY_ALERT_CHECK SUSPEND;
-- ALTER TASK TASK_REORDER_RECOMMENDATIONS SUSPEND;

-- ============================================
-- STEP 6: Test Data for Dashboard
-- ============================================

-- Test query 1: Stock health
SELECT 
    LOCATION,
    CATEGORY,
    COUNT(*) AS items,
    SUM(CASE WHEN STOCK_STATUS = 'CRITICAL' THEN 1 ELSE 0 END) AS critical_items,
    SUM(CASE WHEN STOCK_STATUS = 'LOW' THEN 1 ELSE 0 END) AS low_items
FROM DT_STOCK_HEALTH
GROUP BY LOCATION, CATEGORY
ORDER BY critical_items DESC
LIMIT 10;

-- Test query 2: Active alerts
SELECT 
    PRIORITY,
    COUNT(*) AS alert_count,
    AVG(DAYS_UNTIL_STOCKOUT) AS avg_days_until_stockout
FROM DT_ACTIVE_ALERTS
GROUP BY PRIORITY
ORDER BY 
    CASE PRIORITY
        WHEN 'CRITICAL' THEN 1
        WHEN 'HIGH' THEN 2
        WHEN 'MEDIUM' THEN 3
        ELSE 4
    END;

-- Test query 3: Reorder recommendations
SELECT 
    SKU_NAME,
    LOCATION,
    QUANTITY_ON_HAND,
    REORDER_POINT,
    RECOMMENDED_ORDER_QTY,
    PRIORITY_SCORE,
    ESTIMATED_ORDER_VALUE_USD
FROM DT_REORDER_RECOMMENDATIONS
ORDER BY PRIORITY_SCORE DESC
LIMIT 10;

-- Test query 4: Location performance
SELECT 
    LOCATION,
    TOTAL_SKUS,
    CRITICAL_COUNT,
    LOW_STOCK_COUNT,
    HEALTH_SCORE,
    ITEMS_NEEDING_REORDER
FROM DT_LOCATION_PERFORMANCE
ORDER BY HEALTH_SCORE ASC;

-- Test query 5: Category heatmap
SELECT 
    LOCATION,
    CATEGORY,
    TOTAL_SKUS,
    CRITICAL_SKUS,
    AVG_RISK_SCORE,
    OVERALL_STATUS
FROM DT_CATEGORY_HEATMAP
ORDER BY AVG_RISK_SCORE DESC
LIMIT 20;

-- ============================================
-- STEP 7: (Optional) Create Test Critical Items
-- ============================================
-- This makes your demo more dramatic by creating some critical situations

-- Backup original data first
CREATE OR REPLACE TABLE inventory_cleaned_backup AS SELECT * FROM inventory_cleaned;

-- Create some critical situations for demo
UPDATE inventory_cleaned 
SET QUANTITY_ON_HAND = 5,
    AUDIT_DATE = CURRENT_DATE()
WHERE SKU_ID IN (
    SELECT SKU_ID 
    FROM inventory_cleaned 
    WHERE CATEGORY = 'Medicines'
    LIMIT 3
);

-- Create some low stock situations
UPDATE inventory_cleaned 
SET QUANTITY_ON_HAND = REORDER_POINT * 0.8,
    AUDIT_DATE = CURRENT_DATE()
WHERE SKU_ID IN (
    SELECT SKU_ID 
    FROM inventory_cleaned 
    WHERE CATEGORY = 'Fresh Produce'
    LIMIT 5
);

-- Refresh dynamic tables to see new critical items
ALTER DYNAMIC TABLE DT_STOCK_HEALTH REFRESH;
ALTER DYNAMIC TABLE DT_ACTIVE_ALERTS REFRESH;

-- Check results
SELECT COUNT(*) AS critical_items 
FROM DT_STOCK_HEALTH 
WHERE STOCK_STATUS = 'CRITICAL';

-- To restore original data:
-- DELETE FROM inventory_cleaned;
-- INSERT INTO inventory_cleaned SELECT * FROM inventory_cleaned_backup;

-- ============================================
-- STEP 8: Performance Optimization (Optional)
-- ============================================

-- Clustering keys for better query performance
ALTER TABLE inventory_cleaned CLUSTER BY (WAREHOUSE_LOCATION, CATEGORY);

-- Adding search optimization for text searches
ALTER TABLE inventory_cleaned ADD SEARCH OPTIMIZATION ON EQUALITY(SKU_NAME);

-- ============================================
-- STEP 9: Grant Permissions (if multi-user)
-- ============================================

-- Grant read access to dashboard user
GRANT USAGE ON DATABASE inventory_app_db TO ROLE PUBLIC;
GRANT USAGE ON SCHEMA data_schema TO ROLE PUBLIC;
GRANT SELECT ON ALL TABLES IN SCHEMA data_schema TO ROLE PUBLIC;
GRANT SELECT ON ALL VIEWS IN SCHEMA data_schema TO ROLE PUBLIC;
GRANT SELECT ON ALL DYNAMIC TABLES IN SCHEMA data_schema TO ROLE PUBLIC;

-- ============================================
-- ✅ VERIFICATION CHECKLIST
-- ============================================

-- Run this final check:
SELECT 'Database Setup' AS check_item, 'inventory_app_db' AS status;

SELECT 
    'Views Created' AS check_item, 
    COUNT(*)::VARCHAR || ' views' AS status 
FROM INFORMATION_SCHEMA.VIEWS 
WHERE TABLE_SCHEMA = 'DATA_SCHEMA';

SELECT 
    'Dynamic Tables Created' AS check_item, 
    COUNT(*)::VARCHAR || ' dynamic tables' AS status
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_SCHEMA = 'DATA_SCHEMA' 
  AND TABLE_TYPE = 'DYNAMIC TABLE';

SELECT 
    'Tasks Created' AS check_item,
    COUNT(*)::VARCHAR || ' tasks' AS status
FROM INFORMATION_SCHEMA.TASKS
WHERE TASK_SCHEMA = 'DATA_SCHEMA';

SELECT 
    'Data Records' AS check_item,
    COUNT(*)::VARCHAR || ' records' AS status
FROM inventory_cleaned;

SELECT 
    'Critical Alerts' AS check_item,
    COUNT(*)::VARCHAR || ' alerts' AS status
FROM DT_ACTIVE_ALERTS
WHERE PRIORITY IN ('CRITICAL', 'HIGH');

-- ============================================
-- 🎉 READY FOR DASHBOARD!
-- ============================================
-- If all checks pass, you're ready to:
-- 1. Configure streamlit_app/.streamlit/secrets.toml
-- 2. Run: streamlit run app.py
-- 3. Open: http://localhost:8501
-- ============================================

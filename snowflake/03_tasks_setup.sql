-- ============================================
-- Snowflake Tasks for Automation
-- ============================================

USE DATABASE INVENTORY_DB;
USE SCHEMA INVENTORY_SCHEMA;

-- ============================================
-- Task 1: Process inventory changes every 5 minutes
-- ============================================

CREATE OR REPLACE TASK TASK_PROCESS_INVENTORY_CHANGES
    WAREHOUSE = COMPUTE_WH
    SCHEDULE = '5 MINUTE'
WHEN
    SYSTEM$STREAM_HAS_DATA('INVENTORY_CHANGES_STREAM')
AS
    CALL PROCESS_INVENTORY_CHANGES();

-- ============================================
-- Task 2: Generate daily forecast predictions
-- ============================================

CREATE OR REPLACE TASK TASK_DAILY_FORECAST
    WAREHOUSE = COMPUTE_WH
    SCHEDULE = 'USING CRON 0 6 * * * UTC'  -- Daily at 6 AM UTC
AS
    CALL GENERATE_FORECAST_PREDICTIONS();

-- ============================================
-- Task 3: Clean up old alerts (monthly)
-- ============================================

CREATE OR REPLACE TASK TASK_CLEANUP_OLD_ALERTS
    WAREHOUSE = COMPUTE_WH
    SCHEDULE = 'USING CRON 0 0 1 * * UTC'  -- First day of month at midnight
AS
BEGIN
    -- Archive resolved alerts older than 90 days
    DELETE FROM ALERT_HISTORY
    WHERE resolved = TRUE
      AND resolved_date < DATEADD(day, -90, CURRENT_DATE());
END;

-- ============================================
-- Task 4: Refresh inventory statistics
-- ============================================

CREATE OR REPLACE TASK TASK_REFRESH_STATISTICS
    WAREHOUSE = COMPUTE_WH
    SCHEDULE = '1 HOUR'
AS
BEGIN
    -- Refresh table statistics for query optimization
    ALTER TABLE INVENTORY_SNAPSHOTS RECALCULATE STATISTICS;
    ALTER TABLE ALERT_HISTORY RECALCULATE STATISTICS;
END;

-- ============================================
-- Task Management Commands
-- ============================================

-- Resume all tasks (uncomment to activate)
-- ALTER TASK TASK_PROCESS_INVENTORY_CHANGES RESUME;
-- ALTER TASK TASK_DAILY_FORECAST RESUME;
-- ALTER TASK TASK_CLEANUP_OLD_ALERTS RESUME;
-- ALTER TASK TASK_REFRESH_STATISTICS RESUME;

-- View task status
CREATE OR REPLACE VIEW V_TASK_STATUS AS
SELECT 
    name AS task_name,
    state,
    schedule,
    warehouse,
    CASE 
        WHEN state = 'started' THEN 'Active'
        ELSE 'Inactive'
    END AS status
FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY())
WHERE database_name = 'INVENTORY_DB'
  AND schema_name = 'INVENTORY_SCHEMA'
ORDER BY created_on DESC;

-- ============================================
-- Monitoring queries
-- ============================================

-- Check task execution history
CREATE OR REPLACE VIEW V_TASK_EXECUTION_HISTORY AS
SELECT 
    name AS task_name,
    state,
    scheduled_time,
    completed_time,
    error_code,
    error_message
FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY())
WHERE database_name = 'INVENTORY_DB'
  AND schema_name = 'INVENTORY_SCHEMA'
ORDER BY scheduled_time DESC
LIMIT 100;

SELECT 'Tasks created successfully! Use ALTER TASK ... RESUME to activate them.' AS status;

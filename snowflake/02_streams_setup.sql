-- ============================================
-- Snowflake Streams for Change Data Capture
-- ============================================

USE DATABASE INVENTORY_DB;
USE SCHEMA INVENTORY_SCHEMA;

-- Stream on inventory snapshots to track changes
CREATE OR REPLACE STREAM INVENTORY_CHANGES_STREAM
    ON TABLE INVENTORY_SNAPSHOTS
    APPEND_ONLY = FALSE;

-- Stream on alert history to track new alerts
CREATE OR REPLACE STREAM ALERT_CHANGES_STREAM
    ON TABLE ALERT_HISTORY
    APPEND_ONLY = TRUE;

-- ============================================
-- Monitoring view for stream activity
-- ============================================

CREATE OR REPLACE VIEW V_STREAM_STATUS AS
SELECT 
    'INVENTORY_CHANGES_STREAM' AS stream_name,
    SYSTEM$STREAM_HAS_DATA('INVENTORY_CHANGES_STREAM') AS has_data
UNION ALL
SELECT 
    'ALERT_CHANGES_STREAM' AS stream_name,
    SYSTEM$STREAM_HAS_DATA('ALERT_CHANGES_STREAM') AS has_data;

-- ============================================
-- Stored procedure to process inventory changes
-- ============================================

CREATE OR REPLACE PROCEDURE PROCESS_INVENTORY_CHANGES()
RETURNS VARCHAR
LANGUAGE SQL
AS
$$
DECLARE
    rows_processed NUMBER DEFAULT 0;
BEGIN
    -- Process critical stock situations from stream
    INSERT INTO ALERT_HISTORY (
        alert_date, location, category, item_name, current_stock,
        alert_type, days_until_stockout, resolved, priority
    )
    SELECT 
        snapshot_date,
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
    FROM INVENTORY_CHANGES_STREAM
    WHERE stock_status IN ('CRITICAL', 'LOW')
      AND METADATA$ACTION = 'INSERT'
      AND NOT EXISTS (
          SELECT 1 FROM ALERT_HISTORY ah
          WHERE ah.location = INVENTORY_CHANGES_STREAM.location
            AND ah.item_name = INVENTORY_CHANGES_STREAM.item_name
            AND ah.resolved = FALSE
            AND ah.alert_date = INVENTORY_CHANGES_STREAM.snapshot_date
      );
    
    rows_processed := SQLROWCOUNT;
    
    -- Mark alerts as resolved when stock is replenished
    UPDATE ALERT_HISTORY
    SET resolved = TRUE,
        resolved_date = CURRENT_DATE()
    WHERE alert_id IN (
        SELECT ah.alert_id
        FROM ALERT_HISTORY ah
        JOIN INVENTORY_CHANGES_STREAM ics
          ON ah.location = ics.location
         AND ah.item_name = ics.item_name
        WHERE ah.resolved = FALSE
          AND ics.stock_status IN ('MODERATE', 'GOOD')
          AND ics.METADATA$ACTION = 'INSERT'
    );
    
    RETURN 'Processed ' || rows_processed || ' inventory changes';
END;
$$;

SELECT 'Streams created successfully!' AS status;

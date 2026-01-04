# Snowflake SQL Scripts

This directory contains SQL scripts for setting up the Snowflake database infrastructure for the Inventory Monitoring System.

## Scripts Overview

Execute these scripts in order:

### 1. Database Setup (`01_database_setup.sql`)
Creates the core database structure:
- Database: `INVENTORY_DB`
- Schema: `INVENTORY_SCHEMA`
- Tables: `INVENTORY_SNAPSHOTS`, `ALERT_HISTORY`, `FORECAST_PREDICTIONS`
- Views: Current inventory, critical items, alerts, trends, location summaries
- Stored procedures for data loading and alert generation
- Indexes for performance optimization

### 2. Streams Setup (`02_streams_setup.sql`)
Implements Change Data Capture (CDC) using Snowflake Streams:
- `INVENTORY_CHANGES_STREAM`: Tracks changes in inventory snapshots
- `ALERT_CHANGES_STREAM`: Tracks new alerts
- Procedures to process inventory changes automatically
- Stream monitoring views

### 3. Tasks Setup (`03_tasks_setup.sql`)
Automates workflows using Snowflake Tasks:
- **TASK_PROCESS_INVENTORY_CHANGES**: Processes inventory changes every 5 minutes
- **TASK_DAILY_FORECAST**: Generates forecast predictions daily at 6 AM UTC
- **TASK_CLEANUP_OLD_ALERTS**: Archives old resolved alerts monthly
- **TASK_REFRESH_STATISTICS**: Refreshes table statistics hourly
- Task monitoring and execution history views

### 4. Cortex Forecasting (`04_cortex_forecasting.sql`)
Implements AI-powered forecasting:
- Time series analysis for consumption prediction
- Stock-out risk assessment
- Anomaly detection in consumption patterns
- Forecast accuracy tracking
- Confidence interval calculations

## Getting Started

### Prerequisites
- Snowflake account with appropriate permissions
- Warehouse named `COMPUTE_WH` (or modify warehouse name in scripts)
- ACCOUNTADMIN or equivalent role

### Execution Steps

1. **Connect to Snowflake**
   ```sql
   -- Using SnowSQL
   snowsql -a <account> -u <username>
   
   -- Or use Snowflake Web UI
   ```

2. **Execute Scripts in Order**
   ```sql
   -- Script 1: Database setup
   !source 01_database_setup.sql
   
   -- Script 2: Streams
   !source 02_streams_setup.sql
   
   -- Script 3: Tasks
   !source 03_tasks_setup.sql
   
   -- Script 4: Cortex forecasting
   !source 04_cortex_forecasting.sql
   ```

3. **Load Sample Data**
   ```sql
   -- Put files into Snowflake stage
   PUT file:///path/to/inventory_data.csv @INVENTORY_STAGE;
   
   -- Load data
   CALL LOAD_INVENTORY_DATA('@INVENTORY_STAGE');
   ```

4. **Activate Tasks**
   ```sql
   ALTER TASK TASK_PROCESS_INVENTORY_CHANGES RESUME;
   ALTER TASK TASK_DAILY_FORECAST RESUME;
   ALTER TASK TASK_CLEANUP_OLD_ALERTS RESUME;
   ALTER TASK TASK_REFRESH_STATISTICS RESUME;
   ```

## Key Features

### Real-time Monitoring
- Streams capture inventory changes automatically
- Tasks process changes every 5 minutes
- Automatic alert generation for critical stock levels

### AI-Powered Forecasting
- 14-day consumption forecasts
- Stock-out risk predictions
- Anomaly detection
- 95% confidence intervals

### Analytics Views
- **V_CURRENT_INVENTORY**: Latest stock status for all items
- **V_CRITICAL_ITEMS**: Items needing immediate attention
- **V_UNRESOLVED_ALERTS**: Open alerts by priority
- **V_STOCK_TRENDS**: 7-day rolling averages
- **V_LOCATION_SUMMARY**: Location-wise inventory health
- **V_FORECAST_ANALYSIS**: Predicted stock levels and risks
- **V_CONSUMPTION_ANOMALIES**: Unusual consumption patterns
- **V_FORECAST_ACCURACY**: Model performance tracking

## Monitoring

### Check Task Status
```sql
SELECT * FROM V_TASK_STATUS;
```

### View Stream Activity
```sql
SELECT * FROM V_STREAM_STATUS;
```

### Check Recent Alerts
```sql
SELECT * FROM V_UNRESOLVED_ALERTS LIMIT 10;
```

### View Forecast Predictions
```sql
SELECT * FROM V_FORECAST_ANALYSIS WHERE stockout_risk = 'HIGH RISK';
```

## Troubleshooting

### Tasks Not Running
```sql
-- Check task state
SHOW TASKS;

-- View execution history
SELECT * FROM V_TASK_EXECUTION_HISTORY;

-- Resume suspended tasks
ALTER TASK <task_name> RESUME;
```

### No Data in Streams
```sql
-- Check if streams have data
SELECT SYSTEM$STREAM_HAS_DATA('INVENTORY_CHANGES_STREAM');

-- View stream contents
SELECT * FROM INVENTORY_CHANGES_STREAM LIMIT 10;
```

### Performance Issues
```sql
-- Recalculate statistics
ALTER TABLE INVENTORY_SNAPSHOTS RECALCULATE STATISTICS;

-- Check query profile in Snowflake UI
-- Use EXPLAIN plan for complex queries
```

## Security Notes

- Adjust role permissions in `01_database_setup.sql` as needed
- Use separate warehouses for different workloads
- Implement row-level security if handling sensitive data
- Enable query auditing and monitoring

## Maintenance

- Tasks automatically clean up old data
- Monitor warehouse credit usage
- Review and optimize queries regularly
- Archive historical data as needed

## Cost Optimization

- Adjust task schedules based on business needs
- Use smaller warehouses for lightweight tasks
- Suspend tasks during off-hours if appropriate
- Enable auto-suspend and auto-resume for warehouses

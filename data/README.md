# Data Directory

This directory contains sample datasets and data generation scripts for the Inventory Monitoring System.

## Files

### Scripts
- **generate_sample_data.py**: Python script to generate realistic sample inventory data

### Generated Datasets
- **inventory_data.csv**: Daily inventory snapshots with stock levels, consumption, and status
- **alert_history.csv**: Historical alerts for low stock and critical situations

## Usage

To generate sample data:

```bash
cd /home/runner/work/ai-stock-dist-snowflake/ai-stock-dist-snowflake
python data/generate_sample_data.py
```

## Data Schema

### inventory_data.csv
- `date`: Date of the snapshot (YYYY-MM-DD)
- `location`: Storage location (hospital, clinic, distribution center)
- `category`: Item category (medicines, food, supplies)
- `item_name`: Name of the item
- `current_stock`: Current quantity in stock
- `consumption`: Daily consumption amount
- `restock_amount`: Amount restocked (if any)
- `restocked`: Boolean indicating if restocking occurred
- `reorder_point`: Threshold for triggering reorder
- `max_stock`: Maximum stock capacity
- `days_until_stockout`: Estimated days until stock runs out
- `stock_status`: Status (CRITICAL, LOW, MODERATE, GOOD)
- `stock_percentage`: Current stock as percentage of max

### alert_history.csv
- `alert_date`: Date when alert was triggered
- `location`: Location where alert occurred
- `category`: Item category
- `item_name`: Name of the item
- `current_stock`: Stock level when alert triggered
- `alert_type`: Type of alert (CRITICAL, LOW)
- `days_until_stockout`: Estimated days until stockout
- `resolved`: Whether alert was resolved
- `priority`: Alert priority (HIGH, MEDIUM)

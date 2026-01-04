# System Architecture

## Overview

The Inventory Monitoring System is an AI-powered solution for tracking and predicting inventory levels of essential goods (medicines, food, supplies) across multiple locations.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Dashboard                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Heatmap  │  │  Alerts  │  │Forecasts │  │  Trends  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Snowflake Data Platform                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                   Analytics Layer                     │  │
│  │  • V_CURRENT_INVENTORY                               │  │
│  │  • V_CRITICAL_ITEMS                                  │  │
│  │  • V_FORECAST_ANALYSIS                               │  │
│  │  • V_CONSUMPTION_ANOMALIES                           │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                 Processing Layer                      │  │
│  │  • Cortex AI Forecasting                             │  │
│  │  • Anomaly Detection                                 │  │
│  │  • Alert Generation                                  │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                 Automation Layer                      │  │
│  │  • Streams (CDC)                                     │  │
│  │  • Tasks (Scheduled Jobs)                            │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                    Data Layer                         │  │
│  │  • INVENTORY_SNAPSHOTS                               │  │
│  │  • ALERT_HISTORY                                     │  │
│  │  • FORECAST_PREDICTIONS                              │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                           ▲
                           │
                    ┌──────┴──────┐
                    │ Data Ingestion│
                    │   (CSV/API)   │
                    └───────────────┘
```

## Components

### 1. Data Layer (Snowflake)

#### Tables
- **INVENTORY_SNAPSHOTS**: Daily inventory records
  - Stores current stock levels, consumption, restock events
  - Indexed by date, location, and status
  - Historical data for trend analysis

- **ALERT_HISTORY**: Stock-out alerts
  - Critical and low stock alerts
  - Priority levels (HIGH, MEDIUM, LOW)
  - Resolution tracking

- **FORECAST_PREDICTIONS**: AI predictions
  - Consumption forecasts
  - Stock-out risk assessments
  - Confidence intervals

#### File Formats & Stages
- CSV_FORMAT: Standard CSV ingestion
- INVENTORY_STAGE: Internal stage for data loading

### 2. Processing Layer (SQL + Snowpark)

#### Stored Procedures
- **LOAD_INVENTORY_DATA**: Bulk data loading from CSV
- **GENERATE_ALERTS**: Alert generation logic
- **PROCESS_INVENTORY_CHANGES**: Stream processing
- **GENERATE_FORECAST_PREDICTIONS**: AI forecasting

#### Views
- **V_CURRENT_INVENTORY**: Latest stock status per item
- **V_CRITICAL_ITEMS**: Items needing immediate attention
- **V_UNRESOLVED_ALERTS**: Open alerts by priority
- **V_STOCK_TRENDS**: 7-day rolling averages
- **V_LOCATION_SUMMARY**: Location-wise health metrics
- **V_FORECAST_ANALYSIS**: Predicted stock levels and risks
- **V_CONSUMPTION_ANOMALIES**: Unusual patterns
- **V_FORECAST_ACCURACY**: Model performance tracking

### 3. AI/ML Layer (Snowflake Cortex)

#### Forecasting Model
- Time series analysis on consumption patterns
- 14-day forward predictions
- Moving averages (7-day, 14-day)
- 95% confidence intervals
- Z-score based anomaly detection

#### Features
- Historical consumption trends
- Seasonal patterns
- Location-specific behavior
- Category-specific consumption rates

#### Outputs
- Predicted daily consumption
- Predicted stock levels
- Stock-out risk (HIGH/MODERATE/LOW)
- Days until stockout
- Model accuracy metrics

### 4. Automation Layer (Streams & Tasks)

#### Streams
- **INVENTORY_CHANGES_STREAM**: Captures inventory updates
- **ALERT_CHANGES_STREAM**: Tracks new alerts

#### Tasks
- **TASK_PROCESS_INVENTORY_CHANGES**: Every 5 minutes
  - Processes inventory updates
  - Generates alerts for critical items
  - Resolves alerts when stock replenished

- **TASK_DAILY_FORECAST**: Daily at 6 AM UTC
  - Runs forecasting models
  - Updates predictions
  - Recalculates risk assessments

- **TASK_CLEANUP_OLD_ALERTS**: Monthly
  - Archives resolved alerts older than 90 days
  - Maintains data hygiene

- **TASK_REFRESH_STATISTICS**: Hourly
  - Updates table statistics
  - Optimizes query performance

### 5. Frontend Layer (Streamlit)

#### Main Application (`app.py`)
- Entry point and orchestration
- Layout management
- Filter controls

#### Components
- **heatmap.py**: Visual inventory heatmap
  - Multiple view modes
  - Interactive filtering
  - Color-coded status

- **alerts.py**: Alert management
  - Priority-based display
  - Timeline visualization
  - Export functionality

- **forecasting.py**: AI predictions
  - Risk assessment
  - Confidence intervals
  - Model performance

- **trends.py**: Historical analysis
  - Time series charts
  - Location comparisons
  - Summary statistics

#### Utilities
- **snowflake_connector.py**: Database connectivity
- **data_processing.py**: Data transformation and demo data

## Data Flow

### Ingestion Flow
```
CSV Files → Snowflake Stage → COPY INTO → Tables → Streams
```

### Processing Flow
```
Streams → Tasks → Procedures → Views → Dashboard
```

### Alert Flow
```
Inventory Update → Stream Capture → Alert Generation → 
Dashboard Display → User Action → Alert Resolution
```

### Forecast Flow
```
Historical Data → Time Series Analysis → Cortex AI → 
Predictions → Risk Assessment → Dashboard Visualization
```

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Database | Snowflake | Data storage, processing |
| AI/ML | Snowflake Cortex | Forecasting, anomaly detection |
| Processing | SQL, Snowpark Python | Data transformation |
| Automation | Streams, Tasks | Real-time processing |
| Frontend | Streamlit | Dashboard UI |
| Visualization | Plotly | Interactive charts |
| Language | Python 3.9+ | Application logic |

## Scalability

### Data Volume
- Handles millions of inventory records
- Efficient aggregation using views
- Partitioning by date for historical data

### Concurrent Users
- Streamlit can serve multiple users
- Snowflake handles concurrent queries
- Read-only views for dashboard access

### Multi-tenancy
- Support for multiple organizations
- Row-level security in Snowflake
- Separate schemas per tenant

## Security

### Data Protection
- Snowflake encryption at rest
- SSL/TLS for data in transit
- Row-level security for sensitive data

### Access Control
- Role-based access in Snowflake
- Separate roles for read/write operations
- Authentication via Streamlit secrets

### Audit
- Snowflake query history
- Task execution logs
- Alert history tracking

## Monitoring

### System Health
- Task execution status
- Stream processing lag
- Warehouse credit usage

### Data Quality
- Forecast accuracy tracking
- Anomaly detection alerts
- Data freshness indicators

### Performance
- Query execution times
- Dashboard load times
- Cache hit rates

## Disaster Recovery

### Backups
- Snowflake Time Travel (90 days)
- Fail-safe for critical data
- Regular data exports

### High Availability
- Snowflake's built-in redundancy
- Multi-AZ deployment
- Automatic failover

## Future Enhancements

- Real-time data streaming (Kafka/Kinesis)
- Mobile app integration
- Advanced ML models (deep learning)
- Multi-language support
- Automated reordering system
- Integration with ERP systems
- Barcode/RFID integration
- Email/SMS notifications

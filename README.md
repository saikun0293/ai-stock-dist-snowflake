# AI-Powered Inventory Management System

## 🧠 **NEW: Snowflake Cortex AI Integration**

This system now includes advanced AI features powered by Snowflake Cortex:

- 💬 **Natural Language Chat** - Ask questions about inventory in plain English
- 🔍 **Anomaly Detection** - Automatically detect unusual stock patterns
- 📈 **AI Forecasting** - Predict future demand with ML models
- 💡 **Auto Insights** - Daily AI-generated recommendations

[**See AI Features Documentation →**](docs/cortex_ai_guide.md)

---

### Snowflake Setup

**What**: Create the backend infrastructure  
**Where**: Snowflake Web UI → Worksheets

First create db and import data following db_setup.sql

**Execute in this order:**

```
1️⃣ snowflake/main_setup.sql (verification script - run Step 1 only to verify data)
   ↓
2️⃣ snowflake/views_heatmap.sql (creates 5 views)
   ↓
3️⃣ snowflake/dynamic_tables.sql (creates 5 auto-refreshing tables)
   ↓
4️⃣ snowflake/streams_tasks.sql (creates automation)
   ↓
5️⃣ 🧠 snowflake/cortex_ai_setup.sql (OPTIONAL: enables AI features)
```

**Expected Results:**

- ✅ 5 Views created (V_STOCK_HEALTH_MATRIX, etc.)
- ✅ 5 Dynamic Tables created (DT_STOCK_HEALTH, etc.)
- ✅ 1 Stream created (INVENTORY_CHANGES_STREAM)
- ✅ 3 Tasks created (TASK_HOURLY_ALERT_CHECK, etc.)
- ✅ 3 New tables (ALERT_HISTORY, REORDER_ACTION_LOG, EXPORT_LOG)

**Verification:**

```sql
SHOW DYNAMIC TABLES;
SELECT COUNT(*) FROM DT_STOCK_HEALTH; -- Should return > 0
```

---

### Dashboard Setup

**What**: Configure and launch the Streamlit dashboard  
**Where**: Your local machine / terminal

**Step 2.1: Create secrets file**

Create file: `streamlit_app/.streamlit/secrets.toml`

```toml
user = "YOUR_USERNAME"
password = "YOUR_PASSWORD"
account = "YOUR_ACCOUNT"  # e.g., "abc12345.us-east-1"
warehouse = "COMPUTE_WH"
database = "inventory_app_db"
schema = "data_schema"
```

**Step 2.2: Install dependencies**

```bash
cd streamlit_app
pip install -r requirements_updated.txt
```

**Step 2.3: Launch dashboard**

```bash
streamlit run app.py
```

**Expected Result:**  
✅ Dashboard opens at http://localhost:8501  
✅ Shows your actual data from Snowflake  
✅ 4 tabs visible: Heatmap, Alerts, Reorder List, Analytics

---

## 📊 Architecture Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     SNOWFLAKE BACKEND                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  📥 inventory_cleaned (your data)                            │
│           ↓                                                   │
│  🔄 INVENTORY_CHANGES_STREAM (CDC)                           │
│           ↓                                                   │
│  ┌──────────────────────────────────────────┐                │
│  │  DYNAMIC TABLES (Auto-refresh)           │                │
│  │  - DT_STOCK_HEALTH (5 min)               │                │
│  │  - DT_ACTIVE_ALERTS (10 min)             │                │
│  │  - DT_REORDER_RECOMMENDATIONS (30 min)   │                │
│  │  - DT_LOCATION_PERFORMANCE (1 hour)      │                │
│  │  - DT_CATEGORY_HEATMAP (15 min)          │                │
│  └──────────────────────────────────────────┘                │
│           ↓                                                   │
│  ⚙️ TASKS (Automated Processing)                             │
│  - TASK_HOURLY_ALERT_CHECK                                   │
│  - TASK_REORDER_RECOMMENDATIONS                              │
│           ↓                                                   │
│  💾 LOGGING TABLES                                           │
│  - ALERT_HISTORY                                             │
│  - REORDER_ACTION_LOG                                        │
│  - EXPORT_LOG                                                │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                         ↓
                    Snowflake
                    Connector
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                   STREAMLIT DASHBOARD                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Tab 1: 🗺️ Heatmap View                                     │
│  - Location x Category matrix                                │
│  - Color-coded by risk score                                 │
│  - Interactive scatter plots                                 │
│                                                               │
│  Tab 2: 🚨 Active Alerts                                     │
│  - Critical item warnings                                    │
│  - Days-until-stockout                                       │
│  - Priority-based sorting                                    │
│                                                               │
│  Tab 3: 📋 Reorder List                                      │
│  - Recommended order quantities                              │
│  - CSV/Excel export                                          │
│  - Supplier information                                      │
│                                                               │
│  Tab 4: 📊 Analytics                                         │
│  - Warehouse performance                                     │
│  - ABC analysis                                              │
│  - Top critical items                                        │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Feature Mapping

| Problem Statement Requirement      | Implementation                                                                                    | Files Involved                                                                           |
| ---------------------------------- | ------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| **"Heatmap by location & item"**   | ✅ Interactive Plotly heatmap with Location x Category matrix                                     | `app.py` (lines 250-350)<br>`views_heatmap.sql`                                          |
| **"Early warnings for stockouts"** | ✅ Days-until-stockout calculations<br>✅ Animated alert cards<br>✅ Hourly task generates alerts | `dynamic_tables.sql` (DT_ACTIVE_ALERTS)<br>`streams_tasks.sql` (TASK_HOURLY_ALERT_CHECK) |
| **"Reorder recommendations"**      | ✅ EOQ-based order quantities<br>✅ Priority scoring (1-10)<br>✅ One-click CSV/Excel export      | `dynamic_tables.sql` (DT_REORDER_RECOMMENDATIONS)<br>`app.py` (lines 450-550)            |
| **"Use Dynamic Tables"**           | ✅ 5 dynamic tables with 5min-1hour refresh                                                       | `dynamic_tables.sql`                                                                     |
| **"Use Streams"**                  | ✅ INVENTORY_CHANGES_STREAM for CDC                                                               | `streams_tasks.sql`                                                                      |
| **"Use Tasks"**                    | ✅ 3 tasks (hourly/daily/weekly)                                                                  | `streams_tasks.sql`                                                                      |
| **"Streamlit dashboard"**          | ✅ 4-tab responsive dashboard with animations                                                     | `app.py`                                                                                 |

## ⚡ Quick Command Cheat Sheet

### Snowflake Commands

```sql
-- Check data exists
SELECT COUNT(*) FROM inventory_cleaned;

-- Check dynamic tables
SHOW DYNAMIC TABLES;
SELECT COUNT(*) FROM DT_STOCK_HEALTH;

-- Manually refresh if needed
ALTER DYNAMIC TABLE DT_STOCK_HEALTH REFRESH;

-- Check tasks
SHOW TASKS;

-- Activate tasks (optional)
ALTER TASK TASK_HOURLY_ALERT_CHECK RESUME;
```

### Terminal Commands

```bash
# Setup
cd streamlit_app
pip install -r requirements_updated.txt

# Run dashboard
streamlit run app.py

# Stop dashboard
Ctrl+C
```

---

## 📞 Quick Help

**Issue**: Dynamic tables have no data  
**Fix**: `ALTER DYNAMIC TABLE DT_STOCK_HEALTH REFRESH;`

**Issue**: Dashboard shows "No Snowflake connection"  
**Fix**: Check `.streamlit/secrets.toml` credentials

**Issue**: Slow dashboard loading  
**Fix**: Add filters to reduce data volume

**Issue**: Tasks not running  
**Fix**: `ALTER TASK TASK_HOURLY_ALERT_CHECK RESUME;`

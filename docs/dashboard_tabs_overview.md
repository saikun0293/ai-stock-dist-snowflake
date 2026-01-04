# 📊 Dashboard Tabs Overview

## Complete Tab Structure

Your Streamlit dashboard now has **7 comprehensive tabs** for inventory monitoring:

### 1. 🗺️ **Heatmap View**

**Purpose**: Visual overview of stock health across locations and categories

**Features**:

- Interactive heatmap showing risk scores
- Location x Category matrix
- Individual item view
- Color-coded by risk level, stock status, or days until stockout

**Best for**: Quick visual identification of problem areas

---

### 2. 🚨 **Active Alerts**

**Purpose**: Critical stockout warnings and urgent items

**Features**:

- Real-time alerts for low stock items
- Priority-based sorting (CRITICAL, HIGH, MEDIUM, LOW)
- Compact card-based display with red gradient for critical items
- Metrics: Days until stockout, stock vs reorder point
- Filters by location and category

**Best for**: Immediate action items and crisis management

---

### 3. 📋 **Reorder List**

**Purpose**: Export-ready procurement recommendations

**Features**:

- Recommended order quantities (EOQ formula)
- Total order value calculations
- Supplier information
- Export to CSV/Excel
- Priority scoring
- Urgent items highlight

**Best for**: Procurement teams and purchase orders

---

### 4. 📊 **Analytics**

**Purpose**: Comprehensive operational metrics and insights

**Features**:

- ABC classification analysis
- Stock status distribution
- Category performance breakdown
- Warehouse performance comparison
- Risk score analysis
- Financial metrics

**Best for**: Management reporting and KPI tracking

---

### 5. 📈 **Forecasting** _(NEW)_

**Purpose**: AI-powered demand prediction and stockout risk assessment

**Features**:

- 14-day consumption forecasts
- Predicted stock levels
- Stockout risk classification (HIGH/MODERATE/LOW)
- Model accuracy metrics (75-95%)
- Confidence intervals for predictions
- Current vs Predicted comparison charts
- Risk distribution by category and location
- Model performance analytics

**Data Source**:

- Demo Mode: Generated from current stock + avg daily sales
- Snowflake Mode: Can integrate with Cortex ML forecasting models

**Best for**: Proactive planning and demand forecasting

---

### 6. 📉 **Trends** _(NEW)_

**Purpose**: Historical analysis and time-series visualization

**Features**:

- Stock level trends over time (7/14/30/60/90 days)
- Consumption pattern analysis
- Category-wise trend charts
- Location performance comparison
- Time period selector
- Area charts for consumption
- Line charts for stock levels

**Data Source**:

- Demo Mode: 30-day historical simulation
- Snowflake Mode: Actual historical data from inventory_cleaned

**Best for**: Pattern recognition and seasonal analysis

---

### 7. 🧠 **AI Insights** _(Snowflake Cortex)_

**Purpose**: Advanced AI-powered analysis and natural language queries

**Features**:

#### 💬 Chat with AI

- Natural language questions about inventory
- Context-aware responses using Cortex LLM (Mistral-Large)
- Example: "Which locations have the most critical alerts?"

#### 🔍 Anomaly Detection

- Statistical analysis of unusual stock movements
- Z-score based detection (>2σ = anomaly)
- Severity levels: NORMAL, MODERATE, SEVERE
- Last 30 days of anomalies

#### 📈 Demand Forecasting (Cortex)

- AI-powered demand prediction
- Volatility analysis
- Forecast confidence levels
- Current vs forecasted comparison

#### 💡 Auto-Generated Insights

- Daily AI analysis and recommendations
- Critical issue summaries
- Category-based priorities
- Quick statistics dashboard

**Requirements**: Requires Snowflake Cortex access

**Best for**: Advanced analytics and decision support

---

## Tab Navigation Flow

```
User Login
    ↓
Dashboard Loads
    ↓
[Filters Applied: Location, Category, ABC Class, Risk Level]
    ↓
┌─────────────────────────────────────────────────────────┐
│  Tab 1: Heatmap    → Quick visual overview              │
│  Tab 2: Alerts     → Immediate actions needed           │
│  Tab 3: Reorder    → Procurement planning               │
│  Tab 4: Analytics  → Performance metrics                │
│  Tab 5: Forecasting→ Future demand prediction           │
│  Tab 6: Trends     → Historical patterns                │
│  Tab 7: AI Insights→ Advanced AI analysis (Cortex)      │
└─────────────────────────────────────────────────────────┘
```

---

## Data Flow

### Forecasting Tab Data

```python
generate_forecast_data(filtered_df)
    ↓
Creates 14-day predictions for:
- predicted_stock
- predicted_consumption
- days_to_stockout
- model_accuracy
- confidence_intervals
- stockout_risk
```

### Trends Tab Data

```python
generate_trends_data(stock_df)
    ↓
Creates 30-day historical data:
- snapshot_date (time series)
- current_stock (daily)
- consumption (daily)
- category/location breakdown
```

### AI Insights Tab Data

```python
display_cortex_features(conn, stock_df, alerts_df)
    ↓
Executes Snowflake Cortex queries:
- SNOWFLAKE.CORTEX.COMPLETE() for chat
- Statistical analysis for anomalies
- ML forecasting queries
- Auto-insight generation
```

---

## Performance Notes

### Tab Loading Speed

- **Fastest**: Heatmap, Alerts (static data)
- **Fast**: Reorder, Analytics (simple aggregations)
- **Medium**: Forecasting, Trends (data generation)
- **Slowest**: AI Insights (Cortex API calls)

### Recommendations

1. **First-time users**: Start with Heatmap and Alerts
2. **Daily operations**: Alerts → Reorder → Analytics
3. **Planning sessions**: Forecasting → Trends → AI Insights
4. **Executive reviews**: Analytics → AI Insights

---

## Future Enhancements

### Forecasting Tab

- [ ] Integration with Snowflake Cortex ML.FORECAST
- [ ] Custom forecast horizons (7/14/30/60 days)
- [ ] Seasonal pattern detection
- [ ] Multi-variate forecasting

### Trends Tab

- [ ] Custom date range selector
- [ ] Download trend reports
- [ ] Comparative trend analysis (YoY, MoM)
- [ ] Trend alerts (unusual patterns)

### AI Insights Tab

- [ ] Voice-enabled queries
- [ ] Automated report scheduling
- [ ] Multi-language support
- [ ] Image analysis for damaged goods

---

## Configuration

### Enable/Disable Tabs

Edit `app.py` tab list to customize:

```python
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🗺️ Heatmap View",     # Can be hidden
    "🚨 Active Alerts",     # Always recommend keeping
    "📋 Reorder List",      # Always recommend keeping
    "📊 Analytics",         # Can be hidden
    "📈 Forecasting",       # NEW - Optional
    "📉 Trends",            # NEW - Optional
    "🧠 AI Insights"        # Requires Cortex
])
```

### Cortex Requirement

Only **Tab 7 (AI Insights)** requires Snowflake Cortex. All other tabs work with standard Snowflake or demo data.

---

## Support & Troubleshooting

### Forecasting Not Loading

- Check `generate_forecast_data()` function
- Verify AVG_DAILY_SALES column exists
- Ensure at least 10 items in filtered dataset

### Trends Not Showing Data

- Check `generate_trends_data()` function
- Verify snapshot_date column format
- Need at least 7 days of historical data

### AI Insights Error

- Verify Cortex access: `SHOW FUNCTIONS LIKE 'CORTEX%' IN SNOWFLAKE;`
- Check privileges: `GRANT USAGE ON SNOWFLAKE.CORTEX TO ROLE your_role;`
- Fall back to other tabs if Cortex unavailable

---

**Last Updated**: January 4, 2026
**Dashboard Version**: 2.0 with Forecasting, Trends, and AI Insights

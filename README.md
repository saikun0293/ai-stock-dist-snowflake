# Inventory Heatmap & Stock-Out Alerts

An AI-powered inventory monitoring system for essential goods (medicines, food, supplies) that helps hospitals, NGOs, and public distribution systems prevent stock-outs and reduce waste.

## 🚀 Features

- **📊 Interactive Heatmap**: Visual inventory monitoring across locations and categories
- **🚨 Smart Alerts**: Automated stock-out warnings with priority levels
- **🤖 AI Forecasting**: 14-day consumption predictions using Snowflake Cortex AI
- **📈 Trend Analysis**: Historical patterns and consumption analytics
- **⚡ Real-time Processing**: Snowflake Streams & Tasks for automation
- **🎯 Risk Assessment**: Stock-out risk predictions (High/Moderate/Low)

## 🏗️ Architecture

**Tech Stack:**
- **Data Platform**: Snowflake
- **Processing**: SQL + Snowpark Python
- **AI/ML**: Snowflake Cortex for forecasting and anomaly detection
- **Frontend**: Streamlit dashboard
- **Visualization**: Plotly
- **Automation**: Snowflake Streams & Tasks

## 📁 Project Structure

```
ai-stock-dist-snowflake/
├── data/                       # Sample datasets & generation scripts
│   ├── generate_sample_data.py # Python script to generate demo data
│   └── README.md
├── snowflake/                  # SQL scripts for database setup
│   ├── 01_database_setup.sql   # Core tables, views, procedures
│   ├── 02_streams_setup.sql    # Change Data Capture (CDC)
│   ├── 03_tasks_setup.sql      # Scheduled automation
│   ├── 04_cortex_forecasting.sql # AI forecasting models
│   └── README.md
├── streamlit_app/              # Dashboard application
│   ├── app.py                  # Main application
│   ├── components/             # UI components (heatmap, alerts, etc.)
│   ├── utils/                  # Helper functions
│   ├── requirements.txt        # Python dependencies
│   └── README.md
├── docs/                       # Documentation
│   ├── system_architecture.md  # Architecture details
│   ├── user_guide.md          # End-user guide
│   └── README.md
├── notebooks/                  # Jupyter notebooks for analysis
│   ├── 01_data_exploration.ipynb
│   └── README.md
└── README.md                   # This file
```

## 🚦 Quick Start

### Prerequisites

- Python 3.8 or higher
- Snowflake account (optional for demo mode)
- pip package manager

### 1. Generate Sample Data

```bash
cd data
python generate_sample_data.py
```

This creates:
- `inventory_data.csv`: 90 days of inventory records
- `alert_history.csv`: Historical alerts

### 2. Setup Snowflake (Optional)

If you have a Snowflake account:

```sql
-- Execute scripts in order using SnowSQL or Snowflake Web UI
!source snowflake/01_database_setup.sql
!source snowflake/02_streams_setup.sql
!source snowflake/03_tasks_setup.sql
!source snowflake/04_cortex_forecasting.sql

-- Load sample data
PUT file:///path/to/inventory_data.csv @INVENTORY_STAGE;
CALL LOAD_INVENTORY_DATA('@INVENTORY_STAGE');

-- Activate tasks
ALTER TASK TASK_PROCESS_INVENTORY_CHANGES RESUME;
ALTER TASK TASK_DAILY_FORECAST RESUME;
```

See [Snowflake README](snowflake/README.md) for detailed setup.

### 3. Run Streamlit Dashboard

```bash
cd streamlit_app
pip install -r requirements.txt
streamlit run app.py
```

The dashboard will open at `http://localhost:8501`

**Demo Mode**: If Snowflake is not configured, the app runs with sample data automatically.

**Snowflake Mode**: To connect to Snowflake, create `.streamlit/secrets.toml`:

```toml
snowflake_user = "your_username"
snowflake_password = "your_password"
snowflake_account = "your_account"
snowflake_warehouse = "COMPUTE_WH"
snowflake_database = "INVENTORY_DB"
snowflake_schema = "INVENTORY_SCHEMA"
```

## 📊 Dashboard Features

### Heatmap View
- Visual inventory status across all locations
- Color-coded by status, percentage, or days until stockout
- Interactive filtering and search
- Detailed table view

### Alerts View
- Real-time stock-out alerts
- Priority-based categorization (High/Medium/Low)
- Location and category breakdowns
- Export functionality

### Forecasts View
- 14-day AI-powered predictions
- Stock-out risk assessment
- Confidence intervals
- Model accuracy tracking

### Trends View
- Historical stock levels
- Consumption patterns
- Location comparisons
- Item-level analysis

## 🤖 AI/ML Capabilities

### Forecasting
- Time series analysis on consumption patterns
- 14-day forward predictions
- 95% confidence intervals
- Stock-out risk predictions

### Anomaly Detection
- Z-score based detection
- Unusual consumption patterns
- Automated alerts

### Model Performance
- Accuracy tracking
- Prediction vs actual comparison
- Continuous improvement

## 🔄 Automation

### Snowflake Streams
- Real-time change data capture
- Automatic alert generation
- Alert resolution tracking

### Snowflake Tasks
- **Every 5 minutes**: Process inventory changes
- **Daily at 6 AM**: Generate forecasts
- **Monthly**: Archive old alerts
- **Hourly**: Refresh statistics

## 📖 Documentation

- [System Architecture](docs/system_architecture.md) - Technical design and components
- [User Guide](docs/user_guide.md) - End-user documentation
- [Snowflake Setup](snowflake/README.md) - Database setup guide
- [Streamlit App](streamlit_app/README.md) - Dashboard documentation
- [Data Generation](data/README.md) - Sample data details

## 🧪 Exploration & Analysis

Jupyter notebooks for data exploration:

```bash
cd notebooks
jupyter notebook 01_data_exploration.ipynb
```

## 🎯 Use Cases

### Hospitals & Clinics
- Monitor medicine inventory
- Prevent critical shortages
- Optimize restocking schedules

### NGOs & Relief Organizations
- Track essential supplies
- Plan distribution efficiently
- Respond to emergencies

### Public Distribution Systems
- Manage food stocks
- Ensure equitable distribution
- Reduce waste

## 🔒 Security

- Snowflake encryption at rest and in transit
- Role-based access control
- Secure credential management
- Audit logging

## 📈 Scalability

- Handles millions of records
- Multi-location support
- Concurrent user access
- Auto-scaling with Snowflake

## 🛠️ Development

### Project Setup
```bash
git clone https://github.com/saikun0293/ai-stock-dist-snowflake.git
cd ai-stock-dist-snowflake
```

### Generate Data
```bash
cd data
python generate_sample_data.py
```

### Run Dashboard
```bash
cd streamlit_app
pip install -r requirements.txt
streamlit run app.py
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is open source and available under the MIT License.

## 📧 Contact

For questions or support, please open an issue on GitHub.

## 🙏 Acknowledgments

- Built with Snowflake Cortex AI
- Powered by Streamlit
- Visualizations by Plotly

---

**Made with ❤️ for better inventory management**
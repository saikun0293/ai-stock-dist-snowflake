# Streamlit App

This directory contains the Streamlit dashboard application for the Inventory Monitoring System.

## Features

### 📊 Interactive Heatmap
- Visual representation of inventory levels across locations and categories
- Multiple view modes: by category or location
- Color coding: by status, percentage, or days until stockout
- Interactive hover details and filtering

### 🚨 Stock-Out Alerts
- Real-time alerts for critical and low stock items
- Priority-based categorization (High, Medium, Low)
- Alert timeline and trends
- Location and category breakdowns
- Export functionality

### 📈 AI-Powered Forecasting
- 14-day consumption predictions using Snowflake Cortex AI
- Stock-out risk assessment (High, Moderate, Low)
- Confidence intervals for predictions
- Model accuracy tracking
- Current vs predicted stock comparisons

### 📉 Trend Analysis
- Historical stock level trends
- Consumption pattern analysis
- Location comparisons
- Item-level detailed views
- Summary statistics

## Installation

### Prerequisites
- Python 3.8 or higher
- Snowflake account (optional, demo mode available)

### Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Snowflake connection (optional)**
   ```bash
   cd .streamlit
   cp secrets.toml.template secrets.toml
   # Edit secrets.toml with your Snowflake credentials
   ```

3. **Run the application**
   ```bash
   streamlit run app.py
   ```

4. **Access the dashboard**
   Open your browser to `http://localhost:8501`

## Usage

### Demo Mode
If Snowflake credentials are not configured, the app automatically runs in demo mode with sample data.

### Snowflake Mode
When connected to Snowflake, the app loads real-time data from:
- `V_CURRENT_INVENTORY` view
- `V_UNRESOLVED_ALERTS` view
- `V_FORECAST_ANALYSIS` view

### Filters
Use the sidebar to filter data by:
- **Location**: Specific hospital, clinic, or distribution center
- **Category**: Medicines, food, or supplies
- **Stock Status**: Critical, Low, Moderate, or Good

## Project Structure

```
streamlit_app/
├── app.py                  # Main application
├── requirements.txt        # Python dependencies
├── .streamlit/
│   ├── config.toml        # Streamlit configuration
│   └── secrets.toml       # Snowflake credentials (not in git)
├── components/
│   ├── heatmap.py         # Heatmap visualization
│   ├── alerts.py          # Alerts component
│   ├── forecasting.py     # Forecasting component
│   └── trends.py          # Trends analysis
└── utils/
    ├── snowflake_connector.py  # Snowflake connection
    └── data_processing.py      # Data utilities
```

## Components

### Heatmap (`components/heatmap.py`)
- Interactive heatmap visualization
- Multiple color schemes
- Detailed table view with search

### Alerts (`components/alerts.py`)
- Alert cards with priority indicators
- Visual analytics (charts, timelines)
- Export functionality

### Forecasting (`components/forecasting.py`)
- AI prediction displays
- Risk assessment
- Model performance metrics

### Trends (`components/trends.py`)
- Time series charts
- Location comparisons
- Item-level analysis

## Configuration

### Theme Customization
Edit `.streamlit/config.toml` to customize colors and appearance.

### Snowflake Connection
Edit `.streamlit/secrets.toml` with your Snowflake credentials:
```toml
snowflake_user = "your_username"
snowflake_password = "your_password"
snowflake_account = "your_account"
snowflake_warehouse = "COMPUTE_WH"
snowflake_database = "INVENTORY_DB"
snowflake_schema = "INVENTORY_SCHEMA"
```

## Deployment

### Local Development
```bash
streamlit run app.py
```

### Streamlit Cloud
1. Push code to GitHub
2. Connect to Streamlit Cloud
3. Add secrets in Streamlit Cloud dashboard
4. Deploy

### Docker
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py"]
```

### Other Platforms
- AWS EC2/ECS
- Google Cloud Run
- Azure App Service
- Heroku

## Performance Tips

1. **Use Snowflake views**: Pre-aggregate data in Snowflake
2. **Enable caching**: Use `@st.cache_data` for expensive operations
3. **Limit data size**: Filter data at the query level
4. **Optimize queries**: Use appropriate indexes in Snowflake

## Troubleshooting

### Connection Issues
- Verify Snowflake credentials in `secrets.toml`
- Check network connectivity to Snowflake
- Ensure warehouse is running

### Performance Issues
- Reduce date range for historical queries
- Use filters to limit data volume
- Check Snowflake warehouse size

### Display Issues
- Clear browser cache
- Update Streamlit: `pip install --upgrade streamlit`
- Check console for JavaScript errors

## Security

- Never commit `secrets.toml` to version control
- Use environment variables in production
- Implement proper authentication for public deployments
- Enable HTTPS for production deployments
- Follow Snowflake security best practices

## Monitoring

The app includes built-in monitoring:
- Last updated timestamp
- Data freshness indicators
- Connection status
- Query performance (in dev mode)

## Support

For issues or questions:
1. Check the main project README
2. Review Streamlit documentation: https://docs.streamlit.io
3. Review Snowflake documentation: https://docs.snowflake.com

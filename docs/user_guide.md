# User Guide

## Getting Started with the Inventory Dashboard

This guide will help you navigate and use the Inventory Monitoring System dashboard effectively.

## Accessing the Dashboard

1. Open your web browser
2. Navigate to the dashboard URL (e.g., `http://localhost:8501` for local setup)
3. The dashboard will load with the latest inventory data

## Dashboard Overview

### Header Section
- **Title**: Displays the system name
- **Last Updated**: Shows when data was last refreshed
- **Key Metrics**: Five main indicators at the top
  - 🔴 Critical Items: Items with less than 10% stock
  - 🟡 Low Stock: Items with 10-25% stock
  - 🟠 Moderate: Items with 25-50% stock
  - 🟢 Good Stock: Items with more than 50% stock
  - ⚠️ Active Alerts: Total number of unresolved alerts

### Sidebar Filters

Use the sidebar to narrow down your view:

1. **Location**: Select a specific location or "All"
   - City Hospital
   - District Clinics
   - NGO Centers
   - Public Distribution Systems

2. **Category**: Filter by item category
   - Medicines
   - Food
   - Supplies

3. **Stock Status**: Show only items with specific status
   - Critical
   - Low
   - Moderate
   - Good

## Main Features

### 📊 Heatmap Tab

The heatmap provides a visual overview of inventory levels.

**View Options:**
- **View by Category**: See all locations for each category
- **View by Location**: See all categories for each location

**Color Coding:**
- **Stock Status**: Red (Critical) → Yellow (Moderate) → Green (Good)
- **Stock Percentage**: Shows % of maximum capacity
- **Days Until Stockout**: Shows urgency

**How to Use:**
1. Select your preferred view and color scheme
2. Hover over cells for detailed information
3. Use the search box below to find specific items
4. Review the detailed table for exact numbers

**Interpreting the Heatmap:**
- 🔴 Red cells = Immediate attention required
- 🟡 Yellow cells = Monitor closely
- 🟢 Green cells = Healthy stock levels

### 🚨 Alerts Tab

View and manage stock-out alerts.

**Alert Priority Levels:**
- **🔴 HIGH**: Critical stock (< 10%), immediate action needed
- **🟡 MEDIUM**: Low stock (10-25%), plan restock soon
- **🟢 LOW**: Moderate stock (25-50%), routine monitoring

**Understanding Alerts:**

Each alert card shows:
- Item name and location
- Current stock level
- Days until stockout
- Priority level

**Alert Analytics:**
- **By Location**: Bar chart showing alerts per location
- **By Category**: Pie chart of alert distribution
- **Timeline**: Daily alert count over time

**Taking Action:**
1. Review high-priority alerts first
2. Note the "Days to Stockout" metric
3. Plan restocking based on urgency
4. Export alerts for offline review

**Exporting Alerts:**
- Click "Download Alerts as CSV" button
- Opens in Excel or other spreadsheet software
- Useful for reports and planning

### 📈 Forecasts Tab

View AI-powered predictions for the next 14 days.

**Key Metrics:**
- **🔴 High Risk**: Items predicted to stock out
- **🟡 Moderate Risk**: Items likely to need restock
- **🟢 Low Risk**: Items with sufficient stock
- **🎯 Model Accuracy**: Average prediction confidence

**Understanding Forecasts:**

**Risk Assessment:**
- **HIGH RISK**: Predicted to run out within 14 days
- **MODERATE RISK**: Will fall below reorder point
- **LOW RISK**: Sufficient stock for 14+ days

**Forecast Details:**
Each item shows:
- Current vs predicted stock
- Predicted daily consumption
- Days until stockout
- Model accuracy (higher is better)
- Confidence interval (range of likely values)

**Using Forecasts:**
1. Focus on HIGH RISK items first
2. Review predicted consumption rates
3. Plan orders based on predictions
4. Consider confidence intervals for safety stock
5. Monitor model accuracy for reliability

**Charts:**
- **Risk by Category/Location**: See where issues concentrate
- **Current vs Predicted**: Compare today to 14 days ahead
- **Model Performance**: Track accuracy over time

### 📉 Trends Tab

Analyze historical patterns and trends.

**Time Period Selection:**
- Choose 7, 14, 30, 60, or 90 days

**Available Charts:**

**1. Category Stock Trends**
- Line chart showing stock levels over time
- One line per category
- Identify seasonal patterns
- Spot unusual changes

**2. Consumption Trends**
- Area chart of daily consumption
- Stacked by category
- Understand demand patterns
- Plan for peak periods

**3. Location Comparison**
- Total stock by location
- Status distribution per location
- Identify locations needing support

**4. Item-Level Analysis**
- Select specific item for deep dive
- View across all locations
- Compare to maximum capacity
- Identify problem locations

**Summary Statistics:**
- Unique items tracked
- Number of locations
- Average stock level
- Items needing restock

## Best Practices

### Daily Operations

**Morning Routine:**
1. Check Active Alerts count
2. Review Critical Items (🔴)
3. Address HIGH priority alerts
4. Check forecast for upcoming issues

**Weekly Planning:**
1. Review Trends tab for patterns
2. Check 14-day forecasts
3. Plan restocking schedules
4. Export alerts for team meeting

**Monthly Review:**
1. Analyze consumption trends
2. Review forecast accuracy
3. Adjust reorder points if needed
4. Identify efficiency improvements

### Interpreting Data

**Stock Percentages:**
- < 10%: Critical - Order immediately
- 10-25%: Low - Order soon
- 25-50%: Moderate - Monitor
- > 50%: Good - Normal operations

**Days Until Stockout:**
- < 3 days: Emergency
- 3-7 days: Urgent
- 7-14 days: Plan order
- > 14 days: Sufficient

**Alert Response Times:**
- HIGH priority: Same day
- MEDIUM priority: Within 2-3 days
- LOW priority: Within a week

### Tips for Efficiency

1. **Use Filters**: Narrow down to relevant items
2. **Check Daily**: Don't let critical items surprise you
3. **Trust Forecasts**: They're based on historical patterns
4. **Export Data**: Share with procurement team
5. **Track Patterns**: Some items may need higher reorder points
6. **Location Focus**: Check problem locations more frequently
7. **Category Awareness**: Different categories have different consumption patterns

## Troubleshooting

### Dashboard Not Loading
- Refresh your browser
- Check internet connection
- Contact system administrator

### Data Looks Outdated
- Check "Last Updated" timestamp
- Wait a few minutes and refresh
- Contact administrator if issue persists

### Numbers Don't Match
- Verify filters are set correctly
- Check time period selection
- Ensure you're looking at the right location/category

### Charts Not Displaying
- Try a different browser
- Clear browser cache
- Update browser to latest version

## Getting Help

- **User Guide**: This document
- **System Admin**: Contact for technical issues
- **Training**: Schedule refresher sessions
- **Feedback**: Report issues or suggest improvements

## Glossary

- **Stock Status**: Health indicator (Critical/Low/Moderate/Good)
- **Stock Percentage**: Current stock as % of maximum
- **Days to Stockout**: Estimated days until item runs out
- **Reorder Point**: Stock level that triggers reorder
- **Forecast Horizon**: Number of days ahead predicted (14 days)
- **Confidence Interval**: Range of likely consumption values
- **Model Accuracy**: How well predictions match actual results
- **Alert**: Notification of low/critical stock
- **Priority**: Urgency level of alert

# 🧠 Snowflake Cortex AI Integration

## Overview

This implementation integrates **Snowflake Cortex AI** capabilities into the inventory monitoring system, providing intelligent insights and predictive analytics powered by Large Language Models (LLMs) and ML functions.

## Prerequisites

Run the following SQL command to enable Cross-Region Inference

```
-- Make sure you're ACCOUNTADMIN
USE ROLE ACCOUNTADMIN;

-- Enable for all regions (most reliable)
ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'ANY_REGION';
```

## 🎯 AI Features Implemented

### 1. **💬 Natural Language Chat Interface**

- Ask questions about your inventory in plain English
- Powered by Cortex's `COMPLETE()` function with Mistral-Large model
- Examples:
  - "Which locations have the most critical alerts?"
  - "What are the top 5 items by inventory value?"
  - "Show me items with less than 3 days of stock"

### 2. **🔍 Anomaly Detection**

- Automatically detects unusual patterns in stock movements
- Uses statistical analysis (Z-score) to identify outliers
- Flags unexpected spikes or drops in inventory levels
- Severity levels: NORMAL, MODERATE, SEVERE

### 3. **📈 AI-Powered Demand Forecasting**

- Predicts future demand based on historical patterns
- Calculates demand volatility and forecast confidence
- Identifies items with high demand variability
- Provides stockout risk assessment

### 4. **💡 Auto-Generated Insights**

- Automated daily analysis using Cortex LLM
- Generates actionable recommendations
- Highlights critical issues and priority actions
- Scheduled via Snowflake Tasks

## 🚀 Getting Started

### Prerequisites

1. **Snowflake Account** with Cortex enabled
2. **Privileges Required**:
   ```sql
   GRANT USAGE ON SNOWFLAKE.CORTEX TO ROLE your_role;
   ```

### Setup Steps

1. **Execute Cortex SQL Setup**:

   ```bash
   # In Snowflake worksheet, run:
   snowflake/cortex_ai_setup.sql
   ```

2. **Run Streamlit App**:

   ```bash
   cd streamlit_app
   streamlit run app.py
   ```

3. **Navigate to AI Insights Tab** 🧠 in the dashboard

## 📊 Available Cortex Functions

### Text Generation

```sql
SELECT SNOWFLAKE.CORTEX.COMPLETE(
    'mistral-large',
    'Analyze this inventory...'
) as insights;
```

### Sentiment Analysis

```sql
SELECT SNOWFLAKE.CORTEX.SENTIMENT(
    'Supplier performance is excellent'
) as sentiment;  -- Returns -1 to 1
```

### Summarization

```sql
SELECT SNOWFLAKE.CORTEX.SUMMARIZE(
    long_text_field
) as summary;
```

### Translation

```sql
SELECT SNOWFLAKE.CORTEX.TRANSLATE(
    'Hello', 'en', 'es'
) as translated;
```

## 🎨 Dashboard Features

### Chat Interface

- Interactive Q&A about inventory data
- Real-time responses using Cortex LLM
- Pre-built example questions
- Context-aware based on current filters

### Anomaly Detection View

- Visual alerts for unusual stock movements
- Color-coded severity (red = severe, orange = moderate)
- Detailed statistics (Z-score, mean, std dev)
- Recent anomalies list

### Demand Forecasting

- Interactive charts showing demand volatility
- Current vs forecasted demand comparison
- Forecast confidence levels
- Detailed forecast table

### Auto Insights

- AI-generated key findings
- Critical issue summary
- Category-based recommendations
- Quick statistics dashboard

## 🔧 Configuration

### Model Selection

Available Cortex models:

- **mistral-large**: Best for complex reasoning (default)
- **mistral-7b**: Fast, good for simple tasks
- **llama2-70b-chat**: Alternative for chat
- **mixtral-8x7b**: Balance of speed and quality

To change model, edit `components/cortex_ai.py`:

```python
query = f"""
SELECT SNOWFLAKE.CORTEX.COMPLETE(
    'mistral-7b',  # Change model here
    '{prompt}'
) as response
"""
```

### Task Scheduling

Auto-generate daily insights:

```sql
-- Schedule: Daily at 8 AM UTC
ALTER TASK TASK_DAILY_AI_INSIGHTS RESUME;

-- View insights
SELECT * FROM AI_DAILY_INSIGHTS
ORDER BY insight_date DESC;
```

## 💡 Use Cases

### 1. Supply Chain Planning

- "What items should I prioritize for ordering today?"
- "Which suppliers have the most critical items?"

### 2. Risk Management

- Detect unusual inventory movements
- Identify potential theft or data errors
- Monitor demand volatility

### 3. Forecasting

- Predict future stockouts
- Plan reorder schedules
- Optimize safety stock levels

### 4. Executive Reporting

- Auto-generate daily summaries
- Get AI-powered recommendations
- Track inventory health trends

## 📈 Performance Tips

1. **Prompt Engineering**

   - Be specific and concise
   - Include relevant context
   - Use structured formats

2. **Token Management**

   - Keep prompts under 2000 tokens
   - Summarize data before sending to LLM
   - Cache frequent queries

3. **Cost Optimization**
   - Use smaller models for simple tasks
   - Batch similar queries
   - Monitor Cortex usage in Snowflake

## 🔒 Security & Privacy

- All data stays within Snowflake environment
- Cortex processing is secure and compliant
- No data leaves Snowflake servers
- Audit trail in `AI_DAILY_INSIGHTS` table

## 🐛 Troubleshooting

### "Cortex not available" Error

```sql
-- Check Cortex availability
SHOW FUNCTIONS LIKE 'CORTEX%' IN SNOWFLAKE;

-- Request access if needed
-- Contact Snowflake support
```

### LLM Returns Empty Response

- Check prompt format (avoid single quotes in text)
- Verify model name is correct
- Ensure sufficient context is provided

### Slow Response Times

- Use smaller models (`mistral-7b`)
- Reduce data context size
- Pre-aggregate data before prompting

## 📚 Additional Resources

- [Snowflake Cortex Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex)
- [Cortex LLM Functions Guide](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions)
- [Best Practices for Prompt Engineering](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-llm-best-practices)

## 🎯 Future Enhancements

- [ ] Image analysis for damaged goods detection
- [ ] Multi-language support for global operations
- [ ] Predictive maintenance alerts
- [ ] Automated report generation with charts
- [ ] Voice-enabled inventory queries
- [ ] Integration with procurement systems

## 💬 Support

For issues or questions:

1. Check Snowflake Cortex documentation
2. Review SQL logs in Snowflake query history
3. Check Streamlit console for Python errors
4. Verify Cortex privileges in your account

---

**Note**: Snowflake Cortex is a premium feature. Ensure your account has access before using these features. Contact your Snowflake account team for pricing and availability.

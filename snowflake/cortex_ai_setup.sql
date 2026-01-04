-- ============================================
-- SNOWFLAKE CORTEX AI INTEGRATION
-- AI-Powered Inventory Analysis
-- ============================================

-- Prerequisites:
-- 1. Snowflake Cortex must be available in your account
-- 2. Required privileges: USAGE on SNOWFLAKE.CORTEX

-- ============================================
-- 1. CORTEX LLM: Generate Inventory Insights
-- ============================================

-- Example: Get AI-generated insights about critical inventory
SELECT SNOWFLAKE.CORTEX.COMPLETE(
    'mistral-large',
    CONCAT(
        'Analyze this inventory situation and provide 3 key recommendations: ',
        'We have ', (SELECT COUNT(*) FROM inventory_cleaned WHERE QUANTITY_ON_HAND <= SAFETY_STOCK)::STRING,
        ' critical items out of ', (SELECT COUNT(*) FROM inventory_cleaned)::STRING, ' total items. ',
        'Average days until stockout is ', 
        (SELECT ROUND(AVG(CASE WHEN AVG_DAILY_SALES > 0 
            THEN QUANTITY_ON_HAND / AVG_DAILY_SALES 
            ELSE 999 END), 1)::STRING FROM inventory_cleaned),
        ' days.'
    )
) as ai_recommendations;


-- ============================================
-- 2. ANOMALY DETECTION: Unusual Stock Movements
-- ============================================

-- Detect unusual inventory changes using statistical methods
CREATE OR REPLACE VIEW V_INVENTORY_ANOMALIES AS
WITH daily_changes AS (
    SELECT 
        SKU_ID,
        SKU_NAME,
        CATEGORY,
        WAREHOUSE_LOCATION,
        AUDIT_DATE,
        QUANTITY_ON_HAND,
        LAG(QUANTITY_ON_HAND) OVER (PARTITION BY SKU_ID ORDER BY AUDIT_DATE) as prev_qty,
        QUANTITY_ON_HAND - LAG(QUANTITY_ON_HAND) OVER (PARTITION BY SKU_ID ORDER BY AUDIT_DATE) as qty_change,
        AVG_DAILY_SALES
    FROM inventory_cleaned
    WHERE AUDIT_DATE >= DATEADD('day', -90, CURRENT_DATE())
),
statistics AS (
    SELECT 
        SKU_ID,
        SKU_NAME,
        CATEGORY,
        WAREHOUSE_LOCATION,
        AUDIT_DATE,
        qty_change,
        AVG_DAILY_SALES,
        AVG(qty_change) OVER (PARTITION BY SKU_ID) as mean_change,
        STDDEV(qty_change) OVER (PARTITION BY SKU_ID) as stddev_change,
        -- Z-score: how many standard deviations from mean
        (qty_change - AVG(qty_change) OVER (PARTITION BY SKU_ID)) / 
            NULLIF(STDDEV(qty_change) OVER (PARTITION BY SKU_ID), 0) as z_score
    FROM daily_changes
    WHERE qty_change IS NOT NULL
)
SELECT 
    SKU_ID,
    SKU_NAME,
    CATEGORY,
    WAREHOUSE_LOCATION,
    AUDIT_DATE,
    qty_change,
    ROUND(mean_change, 2) as avg_change,
    ROUND(stddev_change, 2) as stddev,
    ROUND(z_score, 2) as z_score,
    CASE 
        WHEN ABS(z_score) > 3 THEN 'SEVERE'
        WHEN ABS(z_score) > 2 THEN 'MODERATE'
        ELSE 'NORMAL'
    END as anomaly_severity,
    -- Use Cortex to explain the anomaly
    CASE 
        WHEN qty_change > 0 THEN 'Unusual stock increase detected'
        ELSE 'Unusual stock decrease detected'
    END as anomaly_type
FROM statistics
WHERE ABS(z_score) > 2  -- Flag items with z-score > 2
ORDER BY ABS(z_score) DESC;


-- Query anomalies
SELECT * FROM V_INVENTORY_ANOMALIES
LIMIT 20;


-- ============================================
-- 3. DEMAND FORECASTING VIEW
-- ============================================

CREATE OR REPLACE VIEW V_DEMAND_FORECAST AS
WITH historical_demand AS (
    SELECT 
        SKU_ID,
        SKU_NAME,
        CATEGORY,
        WAREHOUSE_LOCATION,
        ABC_CLASS,
        AVG_DAILY_SALES,
        FORECAST_NEXT_30D,
        QUANTITY_ON_HAND,
        REORDER_POINT,
        SAFETY_STOCK,
        LEAD_TIME_DAYS,
        -- Calculate trend
        AVG(AVG_DAILY_SALES) OVER (
            PARTITION BY SKU_ID 
            ORDER BY AUDIT_DATE 
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) as moving_avg_30d,
        STDDEV(AVG_DAILY_SALES) OVER (
            PARTITION BY SKU_ID 
            ORDER BY AUDIT_DATE 
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) as demand_volatility
    FROM inventory_cleaned
    WHERE AUDIT_DATE >= DATEADD('day', -90, CURRENT_DATE())
)
SELECT DISTINCT
    SKU_ID,
    SKU_NAME,
    CATEGORY,
    WAREHOUSE_LOCATION,
    ABC_CLASS,
    ROUND(AVG(AVG_DAILY_SALES), 2) as avg_daily_demand,
    ROUND(AVG(demand_volatility), 2) as volatility,
    MAX(FORECAST_NEXT_30D) as forecast_30d,
    -- Forecast confidence based on volatility
    CASE 
        WHEN AVG(demand_volatility) / NULLIF(AVG(AVG_DAILY_SALES), 0) < 0.2 THEN 'HIGH'
        WHEN AVG(demand_volatility) / NULLIF(AVG(AVG_DAILY_SALES), 0) < 0.5 THEN 'MEDIUM'
        ELSE 'LOW'
    END as forecast_confidence,
    -- Stockout risk
    CASE 
        WHEN QUANTITY_ON_HAND <= SAFETY_STOCK THEN 'HIGH RISK'
        WHEN QUANTITY_ON_HAND <= REORDER_POINT THEN 'MODERATE RISK'
        ELSE 'LOW RISK'
    END as stockout_risk,
    -- Recommended action
    CASE 
        WHEN QUANTITY_ON_HAND <= SAFETY_STOCK THEN 'URGENT: Order immediately'
        WHEN QUANTITY_ON_HAND <= REORDER_POINT THEN 'WARNING: Plan reorder soon'
        ELSE 'OK: Monitor'
    END as recommendation
FROM historical_demand
GROUP BY 
    SKU_ID, SKU_NAME, CATEGORY, WAREHOUSE_LOCATION, ABC_CLASS,
    QUANTITY_ON_HAND, REORDER_POINT, SAFETY_STOCK
ORDER BY volatility DESC;


-- Query forecasts
SELECT * FROM V_DEMAND_FORECAST
WHERE stockout_risk IN ('HIGH RISK', 'MODERATE RISK')
LIMIT 20;


-- ============================================
-- 4. CORTEX: Natural Language Query Examples
-- ============================================

-- Example 1: Summarize critical inventory status
SELECT SNOWFLAKE.CORTEX.COMPLETE(
    'mistral-large',
    CONCAT(
        'Summarize this inventory data in 3 bullet points: ',
        (SELECT LISTAGG(
            SKU_NAME || ' at ' || WAREHOUSE_LOCATION || ' has only ' || 
            QUANTITY_ON_HAND || ' units left', 
            ', '
        ) WITHIN GROUP (ORDER BY QUANTITY_ON_HAND)
        FROM inventory_cleaned 
        WHERE QUANTITY_ON_HAND <= SAFETY_STOCK 
        LIMIT 10)
    )
) as summary;


-- Example 2: Extract key insights from alerts
SELECT SNOWFLAKE.CORTEX.COMPLETE(
    'mistral-7b',
    'Based on these critical items: ' || 
    (SELECT LISTAGG(DISTINCT CATEGORY, ', ') 
     FROM inventory_cleaned 
     WHERE QUANTITY_ON_HAND <= SAFETY_STOCK) ||
    '. What are the top 2 categories needing immediate attention?'
) as priority_categories;


-- ============================================
-- 5. CREATE TASK: Auto-Generate Daily AI Insights
-- ============================================

-- Create table to store daily AI insights
CREATE OR REPLACE TABLE AI_DAILY_INSIGHTS (
    insight_date DATE,
    critical_count INTEGER,
    total_value FLOAT,
    ai_recommendation STRING,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);


-- Create task to generate daily insights using Cortex
CREATE OR REPLACE TASK TASK_DAILY_AI_INSIGHTS
    WAREHOUSE = compute_wh
    SCHEDULE = 'USING CRON 0 8 * * * UTC'  -- Daily at 8 AM UTC
AS
INSERT INTO AI_DAILY_INSIGHTS (insight_date, critical_count, total_value, ai_recommendation)
SELECT 
    CURRENT_DATE() as insight_date,
    (SELECT COUNT(*) FROM inventory_cleaned WHERE QUANTITY_ON_HAND <= SAFETY_STOCK) as critical_count,
    (SELECT SUM(TOTAL_INVENTORY_VALUE_USD) FROM inventory_cleaned WHERE QUANTITY_ON_HAND <= SAFETY_STOCK) as total_value,
    SNOWFLAKE.CORTEX.COMPLETE(
        'mistral-large',
        CONCAT(
            'As an inventory manager, provide 3 specific actions for today. Current status: ',
            (SELECT COUNT(*) FROM inventory_cleaned WHERE QUANTITY_ON_HAND <= SAFETY_STOCK)::STRING,
            ' critical items worth $',
            (SELECT ROUND(SUM(TOTAL_INVENTORY_VALUE_USD), 0)::STRING FROM inventory_cleaned WHERE QUANTITY_ON_HAND <= SAFETY_STOCK),
            '. Top categories: ',
            (SELECT LISTAGG(DISTINCT CATEGORY, ', ') WITHIN GROUP (ORDER BY CATEGORY)
             FROM (SELECT CATEGORY FROM inventory_cleaned WHERE QUANTITY_ON_HAND <= SAFETY_STOCK LIMIT 5))
        )
    ) as ai_recommendation;


-- Resume the task
ALTER TASK TASK_DAILY_AI_INSIGHTS RESUME;


-- View daily insights
SELECT * FROM AI_DAILY_INSIGHTS
ORDER BY insight_date DESC
LIMIT 7;


-- ============================================
-- 6. SENTIMENT ANALYSIS: Supplier Performance
-- ============================================

-- Example: Analyze supplier notes or performance data
-- (If you have text data like supplier feedback)
/*
SELECT 
    SUPPLIER_NAME,
    SUPPLIER_ONTIME_PCT,
    SNOWFLAKE.CORTEX.SENTIMENT(
        CONCAT('Supplier ', SUPPLIER_NAME, ' has ', SUPPLIER_ONTIME_PCT::STRING, '% on-time delivery rate')
    ) as performance_sentiment
FROM (
    SELECT DISTINCT SUPPLIER_NAME, SUPPLIER_ONTIME_PCT 
    FROM inventory_cleaned
    WHERE SUPPLIER_NAME IS NOT NULL
)
ORDER BY SUPPLIER_ONTIME_PCT DESC;
*/


-- ============================================
-- 7. CHATBOT DATA PREPARATION
-- ============================================

-- Create a summary table optimized for Cortex chat
CREATE OR REPLACE VIEW V_CORTEX_INVENTORY_CONTEXT AS
SELECT 
    -- Item details
    SKU_ID,
    SKU_NAME,
    CATEGORY,
    WAREHOUSE_LOCATION,
    ABC_CLASS,
    
    -- Stock levels
    QUANTITY_ON_HAND,
    REORDER_POINT,
    SAFETY_STOCK,
    
    -- Metrics
    AVG_DAILY_SALES,
    CASE 
        WHEN AVG_DAILY_SALES > 0 THEN ROUND(QUANTITY_ON_HAND / AVG_DAILY_SALES, 1)
        ELSE 999
    END as days_until_stockout,
    
    -- Status
    CASE 
        WHEN QUANTITY_ON_HAND <= 0 THEN 'OUT_OF_STOCK'
        WHEN QUANTITY_ON_HAND <= SAFETY_STOCK THEN 'CRITICAL'
        WHEN QUANTITY_ON_HAND <= REORDER_POINT THEN 'LOW'
        ELSE 'HEALTHY'
    END as stock_status,
    
    -- Financial
    UNIT_COST_USD,
    TOTAL_INVENTORY_VALUE_USD,
    
    -- Supplier
    SUPPLIER_NAME,
    SUPPLIER_ONTIME_PCT,
    LEAD_TIME_DAYS
    
FROM inventory_cleaned
WHERE INVENTORY_STATUS NOT IN ('Discontinued', 'Obsolete')
ORDER BY 
    CASE 
        WHEN QUANTITY_ON_HAND <= 0 THEN 1
        WHEN QUANTITY_ON_HAND <= SAFETY_STOCK THEN 2
        WHEN QUANTITY_ON_HAND <= REORDER_POINT THEN 3
        ELSE 4
    END;


-- ============================================
-- USAGE NOTES
-- ============================================

/*
Available Cortex LLM Models:
- mistral-large: Best for complex reasoning
- mistral-7b: Fast, good for simple tasks
- llama2-70b-chat: Alternative for chat
- mixtral-8x7b: Good balance of speed and quality

Cortex Functions:
1. COMPLETE(model, prompt) - Text generation
2. SENTIMENT(text) - Sentiment analysis (-1 to 1)
3. SUMMARIZE(text) - Text summarization
4. TRANSLATE(text, from_lang, to_lang) - Translation
5. EXTRACT_ANSWER(text, question) - Q&A

Best Practices:
- Keep prompts focused and specific
- Include relevant context in prompts
- Use appropriate model for task complexity
- Monitor token usage and costs
- Cache frequently used results
*/

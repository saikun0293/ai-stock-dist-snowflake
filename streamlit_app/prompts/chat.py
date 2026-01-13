"""
Multi-Agent Chat Prompts
Converts user natural language to SQL, then SQL results to natural language responses
"""

# Database schema information for SQL generation
DATABASE_SCHEMA = """
    DATABASE: inventory_app_db
    SCHEMA: data_schema

    AVAILABLE TABLES AND VIEWS:

    1. DT_STOCK_HEALTH (Dynamic Table - Refreshes every 5 minutes)
    Primary table for current stock status and health metrics
    Columns:
    - SKU_ID (NUMBER) - Unique identifier for SKU
    - SKU_NAME (VARCHAR) - Name of the item
    - CATEGORY (VARCHAR) - Product category (Electronics, Apparel, etc.)
    - LOCATION (VARCHAR) - Warehouse location name
    - WAREHOUSE_ID (NUMBER) - Warehouse identifier
    - ABC_CLASS (VARCHAR) - ABC classification (A, B, or C)
    - QUANTITY_ON_HAND (NUMBER) - Current stock quantity
    - QUANTITY_RESERVED (NUMBER) - Reserved stock
    - QUANTITY_COMMITTED (NUMBER) - Committed stock
    - AVAILABLE_STOCK (NUMBER) - Available for sale = ON_HAND - RESERVED - COMMITTED
    - REORDER_POINT (NUMBER) - When to reorder
    - SAFETY_STOCK (NUMBER) - Minimum safety level
    - LEAD_TIME_DAYS (NUMBER) - Supplier lead time
    - AVG_DAILY_SALES (NUMBER) - Average daily sales rate
    - FORECAST_NEXT_30D (NUMBER) - 30-day demand forecast
    - DAYS_UNTIL_STOCKOUT (NUMBER) - Calculated days until out of stock (999 if no sales)
    - STOCK_STATUS (VARCHAR) - Status: OUT_OF_STOCK, CRITICAL, LOW, MODERATE, HEALTHY
    - RISK_SCORE (NUMBER) - Risk score 0-100 (higher = more critical)
    - UNIT_COST_USD (NUMBER) - Cost per unit in USD
    - TOTAL_INVENTORY_VALUE_USD (NUMBER) - Total value of inventory
    - SUPPLIER_NAME (VARCHAR) - Supplier name
    - SUPPLIER_ID (NUMBER) - Supplier identifier
    - SUPPLIER_ONTIME_PCT (NUMBER) - Supplier on-time delivery percentage
    - LAST_UPDATED (TIMESTAMP) - Last update timestamp

    2. DT_ACTIVE_ALERTS (Dynamic Table - Refreshes every 10 minutes)
    Active inventory alerts and warnings
    Columns:
    - SKU_ID, SKU_NAME, CATEGORY, LOCATION, ABC_CLASS
    - QUANTITY_ON_HAND, REORDER_POINT, SAFETY_STOCK, AVG_DAILY_SALES
    - ALERT_TYPE (VARCHAR) - Type: STOCKOUT, CRITICAL, LOW_STOCK, URGENT, WARNING
    - PRIORITY (VARCHAR) - Priority: CRITICAL, HIGH, MEDIUM, LOW
    - DAYS_UNTIL_STOCKOUT (NUMBER) - Days until stockout
    - LEAD_TIME_DAYS, SUPPLIER_NAME, SUPPLIER_ID
    - UNIT_COST_USD, TOTAL_INVENTORY_VALUE_USD
    - DAYS_SINCE_LAST_RECEIVED (NUMBER) - Days since last receipt
    - ALERT_GENERATED_AT (TIMESTAMP) - When alert was generated

    3. DT_REORDER_RECOMMENDATIONS (Dynamic Table - Refreshes every 30 minutes)
    Items needing reorder with recommendations
    Columns:
    - SKU_ID, SKU_NAME, CATEGORY, LOCATION, WAREHOUSE_ID, ABC_CLASS
    - QUANTITY_ON_HAND, QUANTITY_RESERVED, QUANTITY_COMMITTED, AVAILABLE_STOCK
    - REORDER_POINT, SAFETY_STOCK, LEAD_TIME_DAYS
    - AVG_DAILY_SALES, FORECAST_NEXT_30D
    - RECOMMENDED_ORDER_QTY (NUMBER) - Suggested order quantity
    - ECONOMIC_ORDER_QTY (NUMBER) - EOQ calculation
    - PRIORITY_SCORE (NUMBER) - Priority 1-10 (10 = most urgent)
    - UNIT_COST_USD, ESTIMATED_ORDER_VALUE_USD
    - SUPPLIER_NAME, SUPPLIER_ID, SUPPLIER_ONTIME_PCT
    - DAYS_OF_INVENTORY, ORDER_FREQUENCY_PER_MONTH
    - RECOMMENDATION_GENERATED_AT (TIMESTAMP)

    4. DT_LOCATION_PERFORMANCE (Dynamic Table - Refreshes every 1 hour)
    Aggregated performance by warehouse location
    Columns:
    - LOCATION (VARCHAR) - Warehouse location
    - WAREHOUSE_ID (NUMBER)
    - TOTAL_SKUS (NUMBER) - Total unique SKUs
    - TOTAL_CATEGORIES (NUMBER) - Number of categories
    - TOTAL_UNITS (NUMBER) - Total units in stock
    - TOTAL_VALUE_USD (NUMBER) - Total inventory value
    - OUT_OF_STOCK_COUNT (NUMBER) - Count of out-of-stock items
    - CRITICAL_COUNT (NUMBER) - Count of critical items
    - LOW_STOCK_COUNT (NUMBER) - Count of low stock items
    - HEALTHY_COUNT (NUMBER) - Count of healthy items
    - HEALTH_SCORE (NUMBER) - Overall health score 0-100
    - AVG_DAYS_COVERAGE (NUMBER) - Average days of inventory coverage
    - AVG_SUPPLIER_PERFORMANCE (NUMBER) - Average supplier on-time %
    - AVG_FORECAST_ACCURACY (NUMBER) - Average forecast accuracy %
    - ITEMS_NEEDING_REORDER (NUMBER) - Count of items needing reorder
    - LAST_UPDATED (TIMESTAMP)

    5. DT_CATEGORY_HEATMAP (Dynamic Table - Refreshes every 15 minutes)
    Category-level metrics by location for heatmap visualization
    Columns:
    - LOCATION (VARCHAR)
    - CATEGORY (VARCHAR)
    - TOTAL_SKUS (NUMBER)
    - OUT_OF_STOCK_SKUS, CRITICAL_SKUS, LOW_STOCK_SKUS, HEALTHY_SKUS (NUMBER)
    - TOTAL_UNITS (NUMBER)
    - TOTAL_VALUE_USD (NUMBER)
    - AVG_DAYS_COVERAGE (NUMBER)
    - AVG_RISK_SCORE (NUMBER) - Average risk score
    - OVERALL_STATUS (VARCHAR) - OUT_OF_STOCK, CRITICAL, LOW, HEALTHY
    - LAST_UPDATED (TIMESTAMP)

    6. V_STOCK_HEALTH_MATRIX (View)
    Detailed stock health view with all metrics
    Similar columns to DT_STOCK_HEALTH plus additional calculated fields
    - STOCK_LEVEL_PCT (NUMBER) - Stock level as percentage of reorder point
    - EXPIRY_DATE (DATE) - Product expiry date
    - STOCK_AGE_DAYS (NUMBER) - Age of stock in days
    - INVENTORY_STATUS (VARCHAR) - Inventory status

    IMPORTANT QUERY GUIDELINES:
    - Always use fully qualified names: inventory_app_db.data_schema.TABLE_NAME
    - Use LIMIT clause for safety (max 1000 rows)
    - For aggregations, use appropriate GROUP BY
    - When showing currency, format with ROUND(value, 2)
    - Stock status values: 'OUT_OF_STOCK', 'CRITICAL', 'LOW', 'MODERATE', 'HEALTHY'
    - Alert priorities: 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
    - ABC classes: 'A', 'B', 'C'
    - For "top N" queries, use ORDER BY and LIMIT
    - For counts and sums, use aggregate functions
    - When user asks about "critical" items, use STOCK_STATUS = 'CRITICAL' or ALERT_TYPE = 'CRITICAL'
    - For location-based queries, use LOCATION column
    - For category-based queries, use CATEGORY column
    """


def build_sql_generation_prompt(user_question: str) -> str:
    """
    Agent 1: Convert natural language question to SQL query
    
    Args:
        user_question: User's natural language question
        
    Returns:
        Prompt for LLM to generate SQL query
    """
    prompt = f"""You are a SQL expert specializing in Snowflake query generation for inventory management systems.

    TASK: Convert the user's natural language question into a valid Snowflake SQL query.

    DATABASE SCHEMA:
    {DATABASE_SCHEMA}

    USER QUESTION: {user_question}

    INSTRUCTIONS:
    1. Analyze the user's question and identify what data they need
    2. Select the most appropriate table(s) from the schema above
    3. Generate a valid Snowflake SQL query that answers the question
    4. Use fully qualified table names: inventory_app_db.data_schema.TABLE_NAME
    5. Always include a LIMIT clause (max 1000 rows) unless aggregating
    6. Use appropriate WHERE clauses to filter data
    7. For sorting, use ORDER BY with the most relevant column
    8. If the question is ambiguous, make reasonable assumptions
    9. Return ONLY the SQL query, nothing else

    EXAMPLES:

    Question: "Show me all critical items"
    SQL: SELECT SKU_NAME, LOCATION, CATEGORY, QUANTITY_ON_HAND, STOCK_STATUS, RISK_SCORE 
    FROM inventory_app_db.data_schema.DT_STOCK_HEALTH 
    WHERE STOCK_STATUS = 'CRITICAL' 
    ORDER BY RISK_SCORE DESC 
    LIMIT 100;

    Question: "What's the total value of inventory by location?"
    SQL: SELECT LOCATION, ROUND(SUM(TOTAL_INVENTORY_VALUE_USD), 2) AS TOTAL_VALUE 
    FROM inventory_app_db.data_schema.DT_STOCK_HEALTH 
    GROUP BY LOCATION 
    ORDER BY TOTAL_VALUE DESC;

    Question: "Which locations have the most alerts?"
    SQL: SELECT LOCATION, COUNT(*) AS ALERT_COUNT, 
    COUNT(CASE WHEN PRIORITY = 'CRITICAL' THEN 1 END) AS CRITICAL_ALERTS 
    FROM inventory_app_db.data_schema.DT_ACTIVE_ALERTS 
    GROUP BY LOCATION 
    ORDER BY ALERT_COUNT DESC;

    Question: "Show items that will run out in the next 3 days"
    SQL: SELECT SKU_NAME, LOCATION, CATEGORY, QUANTITY_ON_HAND, DAYS_UNTIL_STOCKOUT, STOCK_STATUS 
    FROM inventory_app_db.data_schema.DT_STOCK_HEALTH 
    WHERE DAYS_UNTIL_STOCKOUT <= 3 AND DAYS_UNTIL_STOCKOUT > 0 
    ORDER BY DAYS_UNTIL_STOCKOUT ASC 
    LIMIT 100;

    Question: "What items need to be reordered urgently?"
    SQL: SELECT SKU_NAME, LOCATION, CATEGORY, QUANTITY_ON_HAND, RECOMMENDED_ORDER_QTY, 
    PRIORITY_SCORE, ROUND(ESTIMATED_ORDER_VALUE_USD, 2) AS ORDER_VALUE 
    FROM inventory_app_db.data_schema.DT_REORDER_RECOMMENDATIONS 
    WHERE PRIORITY_SCORE >= 8 
    ORDER BY PRIORITY_SCORE DESC 
    LIMIT 50;

    Now generate the SQL query for the user's question. Return ONLY the SQL query without any explanation or markdown formatting.

    SQL:"""
        
    return prompt


def build_response_generation_prompt(user_question: str, sql_query: str, sql_results: str, row_count: int) -> str:
    """
    Agent 2: Convert SQL results into natural language response
    
    Args:
        user_question: Original user question
        sql_query: The SQL query that was executed
        sql_results: The results from executing the SQL query (as string)
        row_count: Number of rows returned
        
    Returns:
        Prompt for LLM to generate natural language response
    """
    prompt = f"""You are an inventory management expert helping users understand their inventory data.

    TASK: Convert the SQL query results into a clear, concise, and actionable natural language response.

    USER'S ORIGINAL QUESTION:
    {user_question}

    SQL QUERY EXECUTED:
    {sql_query}

    QUERY RESULTS ({row_count} rows):
    {sql_results}

    INSTRUCTIONS:
    1. Provide a direct answer to the user's question based on the results
    2. Highlight key insights and important numbers
    3. If there are critical issues (stockouts, critical alerts), emphasize them
    4. Use clear formatting with bullet points or numbered lists when appropriate
    5. Include relevant metrics and values from the results
    6. If the query returned no results, explain what that means
    7. Keep the response concise but informative (3-8 sentences typical)
    8. Use professional but conversational tone
    9. If applicable, suggest actionable next steps
    10. Format currency values with $ and commas (e.g., $1,234.56)
    11. Round percentages to 1 decimal place

    RESPONSE STYLE EXAMPLES:

    Example 1 - Critical Items:
    "I found 12 critical items in your inventory that need immediate attention:
    - **Electronics** category has 5 critical items at the Chicago location
    - **Apparel** has 4 critical items at Los Angeles
    - **Home & Garden** has 3 critical items spread across multiple locations

    The most urgent item is 'Premium Laptop Charger' at Chicago with only 2 units left and a risk score of 95. These critical items represent $45,230 in total inventory value. I recommend prioritizing reorders for Class A items first."

    Example 2 - Location Summary:
    "Here's the inventory value breakdown by location:
    - **Chicago**: $2,450,000 (35% of total)
    - **Los Angeles**: $1,890,000 (27%)
    - **New York**: $1,560,000 (22%)
    - **Miami**: $1,100,000 (16%)

    Chicago warehouse holds the highest value inventory and also has the most SKUs (450 items). All locations show healthy inventory levels overall."

    Example 3 - No Results:
    "Good news! There are currently no items projected to run out in the next 3 days. Your inventory levels appear healthy for the short term. However, I recommend monitoring items with 4-7 days of stock remaining to stay ahead of potential stockouts."

    Now generate a clear, helpful response to the user's question based on the SQL results provided.

    RESPONSE:"""
    
    return prompt


def build_error_handling_prompt(user_question: str, sql_query: str, error_message: str) -> str:
    """
    Fallback prompt when SQL query fails
    
    Args:
        user_question: Original user question
        sql_query: The SQL query that failed
        error_message: The error message from Snowflake
        
    Returns:
        Prompt for LLM to explain the error and suggest alternatives
    """
    prompt = f"""You are an inventory management assistant helping a user who encountered an error.

    USER'S QUESTION:
    {user_question}

    SQL QUERY ATTEMPTED:
    {sql_query}

    ERROR MESSAGE:
    {error_message}

    TASK: Provide a helpful, user-friendly explanation of what went wrong and suggest an alternative question or approach.

    INSTRUCTIONS:
    1. Don't show technical SQL errors to the user
    2. Explain in simple terms what might have caused the issue
    3. Suggest 2-3 alternative questions the user could ask
    4. Be apologetic but helpful
    5. Keep it brief (2-4 sentences)

    RESPONSE:"""
    
    return prompt
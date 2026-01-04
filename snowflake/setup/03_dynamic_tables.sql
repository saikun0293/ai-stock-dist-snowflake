-- =====================================================================
-- 03_dynamic_tables.sql
-- Dynamic Tables for AI Stock Distribution - Snowflake
-- Created: 2026-01-04
-- Purpose: Real-time data enrichment, alerting, aggregation, and forecasting
-- =====================================================================

-- =====================================================================
-- 1. INVENTORY ENRICHMENT DYNAMIC TABLE
-- =====================================================================
-- Enriches raw inventory data with product details, locations, and KPIs
-- Refreshes every 5 minutes for near real-time insights

CREATE OR REPLACE DYNAMIC TABLE dt_inventory_enriched
TARGET_LAG = '5 minutes'
WAREHOUSE = compute_wh
AS
SELECT
    inv.inventory_id,
    inv.sku,
    inv.location_id,
    inv.quantity_on_hand,
    inv.quantity_reserved,
    inv.quantity_available,
    inv.last_updated,
    
    -- Product Enrichment
    prod.product_name,
    prod.category,
    prod.subcategory,
    prod.unit_cost,
    prod.retail_price,
    prod.supplier_id,
    
    -- Location Enrichment
    loc.location_name,
    loc.location_type,
    loc.region,
    loc.country,
    loc.warehouse_capacity,
    loc.current_utilization,
    
    -- Supplier Enrichment
    sup.supplier_name,
    sup.lead_time_days,
    sup.reliability_score,
    
    -- Calculated KPIs
    ROUND((inv.quantity_on_hand * prod.unit_cost), 2) AS inventory_value_usd,
    ROUND(inv.quantity_available / NULLIF(inv.quantity_on_hand, 0), 4) AS availability_ratio,
    ROUND(inv.quantity_reserved / NULLIF(inv.quantity_on_hand, 0), 4) AS reservation_ratio,
    
    -- Stock Health Classification
    CASE
        WHEN inv.quantity_available = 0 THEN 'OUT_OF_STOCK'
        WHEN inv.quantity_available < (prod.min_stock_level * 0.5) THEN 'CRITICAL'
        WHEN inv.quantity_available < prod.min_stock_level THEN 'LOW'
        WHEN inv.quantity_available > prod.max_stock_level THEN 'OVERSTOCK'
        ELSE 'NORMAL'
    END AS stock_health_status,
    
    -- Turnover Days
    ROUND(DATEDIFF(day, prod.last_sales_date, CURRENT_DATE()), 0) AS days_since_last_sale,
    
    -- Data Quality Metrics
    CASE WHEN inv.last_updated < CURRENT_TIMESTAMP - INTERVAL '24 hours' THEN 'STALE' ELSE 'FRESH' END AS data_freshness,
    
    CURRENT_TIMESTAMP() AS enriched_at
    
FROM raw_inventory_data inv
LEFT JOIN raw_products prod ON inv.sku = prod.sku
LEFT JOIN raw_locations loc ON inv.location_id = loc.location_id
LEFT JOIN raw_suppliers sup ON prod.supplier_id = sup.supplier_id
WHERE inv.is_active = TRUE
    AND prod.is_active = TRUE
    AND loc.is_active = TRUE;

-- =====================================================================
-- 2. INVENTORY ALERTS DYNAMIC TABLE
-- =====================================================================
-- Generates real-time alerts for stock anomalies, shortages, and anomalies
-- Refreshes every 2 minutes for critical alerting

CREATE OR REPLACE DYNAMIC TABLE dt_inventory_alerts
TARGET_LAG = '2 minutes'
WAREHOUSE = compute_wh
AS
WITH alert_candidates AS (
    SELECT
        inv.inventory_id,
        inv.sku,
        inv.location_id,
        inv.quantity_on_hand,
        inv.quantity_available,
        prod.product_name,
        prod.min_stock_level,
        prod.max_stock_level,
        prod.safety_stock_level,
        loc.location_name,
        prod.unit_cost,
        
        -- Alert Reason Detection
        CASE
            WHEN inv.quantity_available <= 0 THEN 'STOCK_OUT'
            WHEN inv.quantity_available < prod.safety_stock_level THEN 'BELOW_SAFETY_STOCK'
            WHEN inv.quantity_available < prod.min_stock_level THEN 'LOW_STOCK'
            WHEN inv.quantity_on_hand > prod.max_stock_level THEN 'OVERSTOCK'
            WHEN inv.quantity_reserved > inv.quantity_on_hand THEN 'NEGATIVE_AVAILABLE'
            ELSE NULL
        END AS alert_type,
        
        -- Alert Severity
        CASE
            WHEN inv.quantity_available <= 0 THEN 'CRITICAL'
            WHEN inv.quantity_available < (prod.min_stock_level * 0.3) THEN 'HIGH'
            WHEN inv.quantity_available < prod.min_stock_level THEN 'MEDIUM'
            WHEN inv.quantity_on_hand > prod.max_stock_level THEN 'MEDIUM'
            ELSE 'LOW'
        END AS severity_level,
        
        -- Impact Calculation
        ROUND((inv.quantity_available * prod.unit_cost), 2) AS inventory_at_risk_usd
        
    FROM raw_inventory_data inv
    LEFT JOIN raw_products prod ON inv.sku = prod.sku
    LEFT JOIN raw_locations loc ON inv.location_id = loc.location_id
    WHERE inv.is_active = TRUE AND prod.is_active = TRUE
)
SELECT
    inventory_id,
    sku,
    location_id,
    quantity_on_hand,
    quantity_available,
    product_name,
    location_name,
    alert_type,
    severity_level,
    inventory_at_risk_usd,
    
    -- Recommended Action
    CASE alert_type
        WHEN 'STOCK_OUT' THEN 'URGENT: Place emergency order'
        WHEN 'BELOW_SAFETY_STOCK' THEN 'Place replenishment order immediately'
        WHEN 'LOW_STOCK' THEN 'Schedule standard replenishment'
        WHEN 'OVERSTOCK' THEN 'Plan promotions or sales'
        WHEN 'NEGATIVE_AVAILABLE' THEN 'Reconcile inventory records'
        ELSE NULL
    END AS recommended_action,
    
    CURRENT_TIMESTAMP() AS alert_generated_at,
    FALSE AS is_acknowledged
    
FROM alert_candidates
WHERE alert_type IS NOT NULL
ORDER BY severity_level DESC, inventory_at_risk_usd DESC;

-- =====================================================================
-- 3. HEATMAP AGGREGATION DYNAMIC TABLE
-- =====================================================================
-- Aggregates inventory metrics by region, category, and warehouse
-- For visualization and geographic analysis
-- Refreshes every 10 minutes

CREATE OR REPLACE DYNAMIC TABLE dt_heatmap_aggregation
TARGET_LAG = '10 minutes'
WAREHOUSE = compute_wh
AS
SELECT
    -- Dimensions
    loc.region,
    loc.country,
    loc.location_name,
    loc.location_id,
    prod.category,
    prod.subcategory,
    
    -- Aggregated Metrics
    COUNT(DISTINCT inv.inventory_id) AS total_skus,
    SUM(inv.quantity_on_hand) AS total_quantity_on_hand,
    SUM(inv.quantity_available) AS total_quantity_available,
    SUM(inv.quantity_reserved) AS total_quantity_reserved,
    
    -- Inventory Value
    ROUND(SUM(inv.quantity_on_hand * prod.unit_cost), 2) AS total_inventory_value_usd,
    ROUND(SUM(inv.quantity_available * prod.unit_cost), 2) AS available_inventory_value_usd,
    
    -- Stock Health Distribution
    COUNT(CASE WHEN inv.quantity_available = 0 THEN 1 END) AS count_out_of_stock,
    COUNT(CASE WHEN inv.quantity_available < prod.min_stock_level THEN 1 END) AS count_low_stock,
    COUNT(CASE WHEN inv.quantity_on_hand > prod.max_stock_level THEN 1 END) AS count_overstock,
    
    -- Percentages
    ROUND(100.0 * COUNT(CASE WHEN inv.quantity_available = 0 THEN 1 END) / NULLIF(COUNT(DISTINCT inv.inventory_id), 0), 2) AS pct_out_of_stock,
    ROUND(100.0 * COUNT(CASE WHEN inv.quantity_available < prod.min_stock_level THEN 1 END) / NULLIF(COUNT(DISTINCT inv.inventory_id), 0), 2) AS pct_low_stock,
    
    -- Utilization Metrics
    ROUND(SUM(inv.quantity_on_hand) / NULLIF(loc.warehouse_capacity, 0) * 100, 2) AS warehouse_utilization_pct,
    
    -- Performance Metrics
    ROUND(AVG(inv.quantity_available / NULLIF(inv.quantity_on_hand, 0)), 4) AS avg_availability_ratio,
    ROUND(AVG(DATEDIFF(day, prod.last_sales_date, CURRENT_DATE())), 0) AS avg_days_since_sale,
    
    -- Alert Counts
    COUNT(CASE WHEN inv.quantity_available <= 0 THEN 1 END) AS active_alerts_critical,
    COUNT(CASE WHEN inv.quantity_available < (prod.min_stock_level * 0.5) THEN 1 END) AS active_alerts_high,
    
    CURRENT_TIMESTAMP() AS aggregated_at
    
FROM raw_inventory_data inv
LEFT JOIN raw_products prod ON inv.sku = prod.sku
LEFT JOIN raw_locations loc ON inv.location_id = loc.location_id
WHERE inv.is_active = TRUE AND prod.is_active = TRUE
GROUP BY
    loc.region,
    loc.country,
    loc.location_name,
    loc.location_id,
    prod.category,
    prod.subcategory,
    loc.warehouse_capacity;

-- =====================================================================
-- 4. DEMAND FORECASTING DYNAMIC TABLE
-- =====================================================================
-- Predicts future demand based on historical sales trends
-- Incorporates seasonality, growth trends, and velocity
-- Refreshes every 30 minutes (slower due to computational complexity)

CREATE OR REPLACE DYNAMIC TABLE dt_demand_forecasting
TARGET_LAG = '30 minutes'
WAREHOUSE = compute_wh
AS
WITH sales_history AS (
    SELECT
        sku,
        location_id,
        DATE_TRUNC('day', sale_date) AS sale_date,
        SUM(quantity_sold) AS daily_quantity,
        SUM(quantity_sold * unit_price) AS daily_revenue
    FROM raw_sales_data
    WHERE sale_date >= CURRENT_DATE() - INTERVAL '90 days'
    GROUP BY sku, location_id, DATE_TRUNC('day', sale_date)
),
sales_aggregates AS (
    SELECT
        sku,
        location_id,
        COUNT(DISTINCT sale_date) AS days_with_sales,
        SUM(daily_quantity) AS quantity_90d,
        AVG(daily_quantity) AS avg_daily_quantity,
        STDDEV(daily_quantity) AS stddev_daily_quantity,
        MAX(daily_quantity) AS max_daily_quantity,
        MIN(daily_quantity) AS min_daily_quantity,
        
        -- Velocity Calculation (7-day vs 30-day)
        ROUND(SUM(CASE WHEN sale_date >= CURRENT_DATE() - INTERVAL '7 days' THEN daily_quantity ELSE 0 END) / 7.0, 2) AS avg_velocity_7d,
        ROUND(SUM(CASE WHEN sale_date >= CURRENT_DATE() - INTERVAL '30 days' THEN daily_quantity ELSE 0 END) / 30.0, 2) AS avg_velocity_30d,
        
        -- Growth Trend
        ROUND((SUM(CASE WHEN sale_date >= CURRENT_DATE() - INTERVAL '7 days' THEN daily_quantity ELSE 0 END) -
               SUM(CASE WHEN sale_date >= CURRENT_DATE() - INTERVAL '14 days' AND sale_date < CURRENT_DATE() - INTERVAL '7 days' THEN daily_quantity ELSE 0 END)) /
               NULLIF(SUM(CASE WHEN sale_date >= CURRENT_DATE() - INTERVAL '14 days' AND sale_date < CURRENT_DATE() - INTERVAL '7 days' THEN daily_quantity ELSE 0 END), 0) * 100, 2) AS growth_rate_pct
    FROM sales_history
    GROUP BY sku, location_id
),
forecast_data AS (
    SELECT
        sa.sku,
        sa.location_id,
        prod.product_name,
        loc.location_name,
        prod.category,
        
        -- Current Inventory
        inv.quantity_on_hand,
        inv.quantity_available,
        
        -- Historical Metrics
        sa.quantity_90d AS total_sales_90d,
        sa.avg_daily_quantity AS historical_avg_daily_demand,
        sa.avg_velocity_7d,
        sa.avg_velocity_30d,
        ROUND(sa.growth_rate_pct, 2) AS recent_growth_rate_pct,
        
        -- Forecast Components
        ROUND(sa.avg_velocity_30d * 1.15, 2) AS forecast_daily_demand_conservative,  -- Conservative: +15%
        ROUND(sa.avg_velocity_30d * COALESCE((100 + sa.growth_rate_pct) / 100, 1), 2) AS forecast_daily_demand_trend,  -- Trend-based
        ROUND(sa.avg_velocity_7d, 2) AS forecast_daily_demand_current,  -- Current velocity
        
        -- 14-Day Forecast (using average of conservative and trend-based)
        ROUND((sa.avg_velocity_30d * 1.15 + sa.avg_velocity_30d * COALESCE((100 + sa.growth_rate_pct) / 100, 1)) / 2 * 14, 0) AS forecast_14d_quantity,
        
        -- 30-Day Forecast
        ROUND((sa.avg_velocity_30d * 1.15 + sa.avg_velocity_30d * COALESCE((100 + sa.growth_rate_pct) / 100, 1)) / 2 * 30, 0) AS forecast_30d_quantity,
        
        -- Stock Adequacy Analysis
        CASE
            WHEN inv.quantity_available >= ROUND((sa.avg_velocity_30d * 1.15 + sa.avg_velocity_30d * COALESCE((100 + sa.growth_rate_pct) / 100, 1)) / 2 * 30, 0) THEN 'ADEQUATE'
            WHEN inv.quantity_available >= ROUND((sa.avg_velocity_30d * 1.15 + sa.avg_velocity_30d * COALESCE((100 + sa.growth_rate_pct) / 100, 1)) / 2 * 14, 0) THEN 'MODERATE'
            ELSE 'INSUFFICIENT'
        END AS stock_adequacy_30d,
        
        -- Replenishment Recommendation
        CASE
            WHEN inv.quantity_available < ROUND((sa.avg_velocity_30d * 1.15 + sa.avg_velocity_30d * COALESCE((100 + sa.growth_rate_pct) / 100, 1)) / 2 * 14, 0) THEN 'URGENT'
            WHEN inv.quantity_available < ROUND((sa.avg_velocity_30d * 1.15 + sa.avg_velocity_30d * COALESCE((100 + sa.growth_rate_pct) / 100, 1)) / 2 * 30, 0) THEN 'HIGH'
            ELSE 'NORMAL'
        END AS replenishment_priority,
        
        -- Confidence Score (based on sales consistency)
        ROUND(CASE
            WHEN sa.days_with_sales >= 70 THEN 95
            WHEN sa.days_with_sales >= 50 THEN 80
            WHEN sa.days_with_sales >= 30 THEN 65
            WHEN sa.days_with_sales >= 10 THEN 50
            ELSE 25
        END, 2) AS forecast_confidence_score,
        
        CURRENT_TIMESTAMP() AS forecast_generated_at
        
    FROM sales_aggregates sa
    LEFT JOIN raw_products prod ON sa.sku = prod.sku
    LEFT JOIN raw_locations loc ON sa.location_id = loc.location_id
    LEFT JOIN raw_inventory_data inv ON sa.sku = inv.sku AND sa.location_id = inv.location_id
    WHERE prod.is_active = TRUE
)
SELECT * FROM forecast_data
WHERE historical_avg_daily_demand > 0  -- Filter out zero-demand items
ORDER BY replenishment_priority DESC, forecast_confidence_score DESC;

-- =====================================================================
-- 5. SUPPLY CHAIN OPTIMIZATION DYNAMIC TABLE
-- =====================================================================
-- Combines forecasting with supplier metrics for optimal ordering
-- Refreshes every 30 minutes (aligned with forecasting)

CREATE OR REPLACE DYNAMIC TABLE dt_supply_chain_optimization
TARGET_LAG = '30 minutes'
WAREHOUSE = compute_wh
AS
SELECT
    f.sku,
    f.product_name,
    f.location_id,
    f.location_name,
    f.category,
    
    -- Current Situation
    f.quantity_on_hand,
    f.quantity_available,
    
    -- Demand Forecast
    f.forecast_daily_demand_trend,
    f.forecast_14d_quantity,
    f.forecast_30d_quantity,
    f.forecast_confidence_score,
    f.stock_adequacy_30d,
    
    -- Supplier Information
    sup.supplier_id,
    sup.supplier_name,
    sup.lead_time_days,
    sup.reliability_score,
    sup.min_order_quantity,
    sup.unit_cost,
    
    -- Optimal Order Calculation
    GREATEST(
        ROUND(f.forecast_30d_quantity + (f.forecast_daily_demand_trend * sup.lead_time_days) - f.quantity_available, 0),
        sup.min_order_quantity
    ) AS recommended_order_qty,
    
    -- Order Timing
    CASE
        WHEN f.quantity_available < f.forecast_14d_quantity THEN
            ROUND((f.quantity_available / NULLIF(f.forecast_daily_demand_trend, 0)) - sup.lead_time_days, 0)
        ELSE 0
    END AS days_until_order_needed,
    
    -- Cost Analysis
    ROUND(GREATEST(
        ROUND(f.forecast_30d_quantity + (f.forecast_daily_demand_trend * sup.lead_time_days) - f.quantity_available, 0),
        sup.min_order_quantity
    ) * sup.unit_cost, 2) AS estimated_order_cost_usd,
    
    -- Supplier Performance Impact
    ROUND(sup.reliability_score * 100, 2) AS supplier_reliability_pct,
    
    -- Risk Assessment
    CASE
        WHEN f.stock_adequacy_30d = 'INSUFFICIENT' AND sup.lead_time_days > 7 THEN 'HIGH_RISK'
        WHEN f.stock_adequacy_30d = 'INSUFFICIENT' THEN 'MEDIUM_RISK'
        WHEN f.stock_adequacy_30d = 'MODERATE' AND sup.reliability_score < 0.8 THEN 'MEDIUM_RISK'
        ELSE 'LOW_RISK'
    END AS supply_chain_risk_level,
    
    CURRENT_TIMESTAMP() AS optimization_generated_at
    
FROM dt_demand_forecasting f
LEFT JOIN raw_products prod ON f.sku = prod.sku
LEFT JOIN raw_suppliers sup ON prod.supplier_id = sup.supplier_id
WHERE f.replenishment_priority IN ('URGENT', 'HIGH')
ORDER BY f.replenishment_priority DESC, estimated_order_cost_usd DESC;

-- =====================================================================
-- SUMMARY & DOCUMENTATION
-- =====================================================================
/*

DYNAMIC TABLES OVERVIEW:
========================

1. dt_inventory_enriched (5-min refresh)
   - Combines inventory, product, location, and supplier data
   - Calculates inventory value, availability ratios, and stock health
   - Use case: Real-time inventory dashboards, detailed analysis

2. dt_inventory_alerts (2-min refresh)
   - Identifies stock anomalies and critical situations
   - Calculates risk exposure and recommended actions
   - Use case: Alert systems, incident management, critical monitoring

3. dt_heatmap_aggregation (10-min refresh)
   - Aggregates metrics by region, category, and warehouse
   - Provides utilization and health distribution statistics
   - Use case: Geographic heatmaps, regional analysis, capacity planning

4. dt_demand_forecasting (30-min refresh)
   - Predicts 14 and 30-day demand using historical trends
   - Calculates growth rates and stock adequacy
   - Use case: Replenishment planning, demand-driven decisions

5. dt_supply_chain_optimization (30-min refresh)
   - Combines forecasting with supplier data for optimal ordering
   - Calculates order quantities and timing
   - Use case: Purchase order generation, supplier management

PERFORMANCE NOTES:
- Dynamic tables auto-refresh at specified intervals
- Adjust warehouse sizes based on volume
- Monitor system views for refresh performance
- Consider clustering for large fact tables

*/

-- =====================================================================
-- END OF DYNAMIC TABLES SCRIPT
-- =====================================================================

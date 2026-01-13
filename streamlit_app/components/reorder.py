"""
Reorder List Component
Displays and exports reorder recommendations with detailed metrics and explanations
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO


def display_reorder_list(reorder_df, conn, location_filter, category_filter):
    """Display and export reorder recommendations with detailed tooltips and explanations"""
    st.markdown("## 📋 Reorder Recommendations")
    st.markdown("**Export-ready procurement list with recommended order quantities**")
    
    # Add informational expander with definitions
    with st.expander("ℹ️ Understanding Reorder Metrics", expanded=False):
        st.markdown("""
        ### Key Metrics Explained
        
        **📍 Reorder Point (ROP)**
        - The inventory level that triggers a new purchase order
        - **Formula:** `(Average Daily Demand × Lead Time in Days) + Safety Stock`
        - **Example:** If you sell 10 units/day, lead time is 5 days, safety stock is 20:
          - ROP = (10 × 5) + 20 = **70 units**
        - When stock falls to or below 70, place an order
        
        **📦 Recommended Order Quantity**
        - **Current System Formula (Demand-Based Replenishment):**
        ```
        Safety Stock + (Avg Daily Sales × Lead Time × 1.5) - Available Stock
        ```
        
        - **Breakdown:**
          - **Safety Stock**: Minimum buffer inventory (e.g., 50 units)
          - **Avg Daily Sales × Lead Time × 1.5**: Expected demand during lead time + 50% buffer
          - **Available Stock**: Current stock minus reserved/committed units
        
        - **Example Calculation:**
          - Safety Stock: 50 units
          - Avg Daily Sales: 10 units/day
          - Lead Time: 7 days
          - Current Available Stock: 30 units
          - **Calculation:** 50 + (10 × 7 × 1.5) - 30 = 50 + 105 - 30 = **125 units**
        
        - **Why this method?**
          - Ensures you have enough to cover lead time demand
          - Adds 50% safety buffer for demand variability
          - Accounts for already committed/reserved stock
          - Returns to optimal stock level, not just minimum
        
        **🎯 Priority Score (5-10)**
        - **Current System Logic (Rule-Based Scoring):**
        ```
        Score = CASE
            WHEN Stock ≤ 0                    THEN 10 (Out of Stock!)
            WHEN Stock ≤ Safety Stock × 0.5   THEN 9  (Critically Low)
            WHEN Stock ≤ Safety Stock         THEN 8  (Below Safety)
            WHEN Stock ≤ Reorder Point × 0.75 THEN 7  (Approaching ROP)
            WHEN Stock ≤ Reorder Point        THEN 6  (At Reorder Point)
            ELSE 5                                     (Default/Low)
        ```
        
        - **Example:**
          - Safety Stock: 50 units
          - Reorder Point: 100 units
          - Current Stock: 45 units (below safety stock)
          - **Priority Score: 8** (Urgent action needed)
        
        - **Interpretation:**
          - Score **10**: Out of stock - EMERGENCY
          - Score **9**: Critically low (<50% safety) - Order TODAY
          - Score **8**: Below safety stock - Urgent
          - Score **7**: Approaching reorder point - High priority
          - Score **6**: At reorder point - Medium priority
          - Score **5**: Above reorder point - Low priority
        
        **🚨 Urgent Items Definition**
        - Items meeting **either** of these criteria:
          1. Priority Score ≥ 8, OR
          2. Current Stock ≤ Safety Stock
        - These items risk stockout within 3-7 days
        - Require immediate procurement action
        """)
    
    if len(reorder_df) == 0:
        st.success("✅ No items need reordering at this time!")
        return
    
    # Summary metrics with help tooltips
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_items = len(reorder_df)
        st.metric(
            "📦 Items to Reorder", 
            total_items,
            help="Total number of items that have reached or fallen below their reorder point"
        )
    
    with col2:
        if 'ESTIMATED_ORDER_VALUE_USD' in reorder_df.columns:
            total_value = reorder_df['ESTIMATED_ORDER_VALUE_USD'].sum()
        else:
            total_value = (reorder_df['REORDER_POINT'] * reorder_df['UNIT_COST_USD']).sum()
        st.metric(
            "💰 Total Order Value", 
            f"${total_value:,.0f}",
            help="Estimated total cost for all recommended orders (Quantity × Unit Cost)"
        )
    
    with col3:
        if 'PRIORITY_SCORE' in reorder_df.columns:
            urgent = len(reorder_df[reorder_df['PRIORITY_SCORE'] >= 8])
        else:
            urgent = len(reorder_df[reorder_df['QUANTITY_ON_HAND'] <= reorder_df['SAFETY_STOCK']])
        st.metric(
            "🚨 Urgent Items", 
            urgent,
            help="Items with Priority Score ≥ 8 or stock at/below Safety Stock level - require immediate action"
        )
    
    with col4:
        suppliers = reorder_df['SUPPLIER_NAME'].nunique() if 'SUPPLIER_NAME' in reorder_df.columns else 0
        st.metric(
            "🏢 Suppliers Involved", 
            suppliers,
            help="Number of unique suppliers needed to fulfill these orders"
        )
    
    st.markdown("---")
    
    # Add column explanations above the table
    st.markdown("### 📊 Reorder Details")
    
    # Display table
    display_cols = ['SKU_ID', 'SKU_NAME', 'CATEGORY', 'LOCATION', 'QUANTITY_ON_HAND', 'REORDER_POINT']
    if 'RECOMMENDED_ORDER_QTY' in reorder_df.columns:
        display_cols.append('RECOMMENDED_ORDER_QTY')
    if 'PRIORITY_SCORE' in reorder_df.columns:
        display_cols.append('PRIORITY_SCORE')
    if 'UNIT_COST_USD' in reorder_df.columns:
        display_cols.append('UNIT_COST_USD')
    if 'SUPPLIER_NAME' in reorder_df.columns:
        display_cols.append('SUPPLIER_NAME')
    
    available_cols = [col for col in display_cols if col in reorder_df.columns]
    st.dataframe(reorder_df[available_cols].head(100), width="stretch", height=400)
    
    # Add informational expander with definitions
    with st.expander("ℹ️ Understanding Reorder Metrics", expanded=False):
        st.markdown("""
        ### Key Metrics Explained
        
        **📍 Reorder Point**
        - The inventory level that triggers a new purchase order
        - Calculated as: `(Average Daily Sales × Lead Time) + Safety Stock`
        - When stock falls below this level, it's time to reorder
        
        **📦 Recommended Order Quantity**
        - The optimal amount to order based on demand and inventory policies
        - Calculated as: `(Maximum Stock Level - Current Stock) or Economic Order Quantity (EOQ)`
        - Balances ordering costs with holding costs
        
        **🎯 Priority Score**
        - A weighted score (0-10) indicating urgency of reorder
        - **Calculation factors:**
          - Stock level vs. Safety Stock (40% weight)
          - Days until stockout (30% weight)
          - ABC Classification importance (20% weight)
          - Recent demand volatility (10% weight)
        - **Score >= 8**: Critical/Urgent action needed
        - **Score 5-7**: Medium priority
        - **Score < 5**: Low priority monitoring
        
        **🚨 Urgent Items**
        - Items requiring immediate attention
        - **Criteria:** Priority Score >= 8 OR Current Stock <= Safety Stock
        - These items risk stockout within 3-7 days
        """)
    
    # Export section
    st.markdown("### 📥 Export Reorder List")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        export_format = st.selectbox("Format", ["CSV", "Excel"])
    
    with col2:
        include_all = st.checkbox("Include all items", value=True)
    
    with col3:
        st.write("")  # Spacer
    
    # Generate export
    export_df = reorder_df.copy()
    
    if not include_all:
        export_df = export_df.head(100)
    
    # Rename columns for export
    export_df = export_df.rename(columns={
        'SKU_ID': 'SKU ID',
        'SKU_NAME': 'Item Name',
        'CATEGORY': 'Category',
        'LOCATION': 'Location',
        'QUANTITY_ON_HAND': 'Current Stock',
        'REORDER_POINT': 'Reorder Point',
        'RECOMMENDED_ORDER_QTY': 'Recommended Qty',
        'UNIT_COST_USD': 'Unit Cost (USD)',
        'SUPPLIER_NAME': 'Supplier',
        'PRIORITY_SCORE': 'Priority Score'
    })
    
    if export_format == "CSV":
        csv = export_df.to_csv(index=False)
        st.download_button(
            label="⬇️ Download CSV",
            data=csv,
            file_name=f"reorder_list_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            help="Download the reorder list as a CSV file for use in spreadsheets or ERP systems"
        )
    else:
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            export_df.to_excel(writer, sheet_name='Reorder List', index=False)
        
        st.download_button(
            label="⬇️ Download Excel",
            data=buffer.getvalue(),
            file_name=f"reorder_list_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            help="Download the reorder list as an Excel file with formatted columns"
        )
    
    # Log export if connected to Snowflake
    if conn:
        try:
            from utils.snowflake_connector import log_export
            log_export(conn, 'REORDER_LIST', len(export_df), 'dashboard_user', export_format,
                      {'location': location_filter, 'category': category_filter})
        except:
            pass

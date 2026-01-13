"""
Analytics Component
Displays inventory analytics, ABC analysis, and insights
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


def display_analytics(stock_df, location_df):
    """Display analytics and insights"""
    st.markdown("## 📊 Analytics & Insights")
    
    # Location performance
    if location_df is not None and len(location_df) > 0:
        st.markdown("### 📍 Warehouse Performance")
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=location_df['LOCATION'],
            y=location_df['CRITICAL_COUNT'],
            name='Critical Items',
            marker_color='#f5576c'
        ))
        
        fig.add_trace(go.Bar(
            x=location_df['LOCATION'],
            y=location_df['LOW_STOCK_COUNT'],
            name='Low Stock Items',
            marker_color='#ffa500'
        ))
        
        fig.add_trace(go.Bar(
            x=location_df['LOCATION'],
            y=location_df['HEALTHY_COUNT'],
            name='Healthy Items',
            marker_color='#4caf50'
        ))
        
        fig.update_layout(
            barmode='stack',
            title='Stock Health by Location',
            xaxis_title='Location',
            yaxis_title='Number of Items',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    
    # Top Critical Items
    st.markdown("### ⚠️ Top 10 Critical Items")
    
    critical_items = stock_df.nlargest(10, 'RISK_SCORE')[
        ['SKU_NAME', 'LOCATION', 'CATEGORY', 'ABC_CLASS', 'QUANTITY_ON_HAND', 'REORDER_POINT', 'DAYS_UNTIL_STOCKOUT', 'RISK_SCORE']
    ]
    
    # Add value if available
    if 'UNIT_COST_USD' in stock_df.columns:
        critical_items_with_cost = stock_df.nlargest(10, 'RISK_SCORE')[
            ['SKU_NAME', 'LOCATION', 'CATEGORY', 'ABC_CLASS', 'QUANTITY_ON_HAND', 'REORDER_POINT', 
             'DAYS_UNTIL_STOCKOUT', 'RISK_SCORE', 'UNIT_COST_USD']
        ].copy()
        critical_items_with_cost['TOTAL_VALUE'] = (
            critical_items_with_cost['QUANTITY_ON_HAND'] * critical_items_with_cost['UNIT_COST_USD']
        ).round(2)
        st.dataframe(critical_items_with_cost, use_container_width=True, hide_index=True)
    else:
        st.dataframe(critical_items, use_container_width=True, hide_index=True)
        
    st.markdown("---")
    # ABC Analysis
    st.markdown("### 🎯 ABC Analysis")
    
    # Add explanation
    with st.expander("ℹ️ Understanding ABC Classification", expanded=False):
        st.markdown("""
        **ABC Classification** categorizes inventory based on **value and importance**:
        
        - **Class A (20% of items)**: High-value items contributing to ~70-80% of total inventory value
          - Highest unit costs
          - Require tightest control and frequent monitoring
          - Critical to business operations
        
        - **Class B (30% of items)**: Medium-value items contributing to ~15-20% of value
          - Moderate costs and importance
          - Moderate monitoring needed
        
        - **Class C (50% of items)**: Low-value items contributing to ~5-10% of value
          - Lowest unit costs
          - Simple controls acceptable
          - High quantities often maintained
        
        **Key Principle**: Most of your capital should be tied up in Class A items that drive the most value.
        """)
        
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if 'ABC_CLASS' in stock_df.columns:
            a_items = stock_df[stock_df['ABC_CLASS'] == 'A']
            a_critical = len(a_items[a_items['STOCK_STATUS'].isin(['CRITICAL', 'LOW'])])
            a_total = len(a_items)
            a_critical_pct = (a_critical / a_total * 100) if a_total > 0 else 0
            
            st.metric(
                "Class A Items at Risk",
                f"{a_critical} / {a_total}",
                delta=f"{a_critical_pct:.1f}% of Class A",
                delta_color="inverse",
                help="Number of high-value Class A items with critical or low stock"
            )
    
    with col2:
        if 'UNIT_COST_USD' in stock_df.columns:
            avg_cost_overall = stock_df['UNIT_COST_USD'].mean()
            st.metric(
                "Average Item Cost",
                f"${avg_cost_overall:.2f}",
                help="Mean unit cost across all inventory items"
            )
    
    with col3:
        stockout_risk = len(stock_df[stock_df['DAYS_UNTIL_STOCKOUT'] <= 7])
        st.metric(
            "Items at Stockout Risk",
            stockout_risk,
            delta_color="inverse",
            help="Items that will run out within a week"
        )
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Item count distribution
        abc_counts = stock_df['ABC_CLASS'].value_counts().sort_index()
        fig = px.pie(
            values=abc_counts.values,
            names=abc_counts.index,
            title="Distribution by Item Count",
            color_discrete_sequence=px.colors.sequential.Blues_r,
            hole=0.3
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Value distribution - verify ABC classification
        if 'UNIT_COST_USD' in stock_df.columns and 'QUANTITY_ON_HAND' in stock_df.columns:
            # Calculate total value per ABC class
            stock_df_with_value = stock_df.copy()
            stock_df_with_value['TOTAL_VALUE'] = stock_df_with_value['UNIT_COST_USD'] * stock_df_with_value['QUANTITY_ON_HAND']
            
            abc_value = stock_df_with_value.groupby('ABC_CLASS')['TOTAL_VALUE'].sum().sort_index()
            total_value = abc_value.sum()
            abc_value_pct = (abc_value / total_value * 100).round(1)
            
            fig = px.pie(
                values=abc_value.values,
                names=abc_value.index,
                title="Distribution by Total Inventory Value",
                color_discrete_sequence=px.colors.sequential.Reds_r,
                hole=0.3
            )
            fig.update_traces(
                textposition='inside', 
                textinfo='percent+label',
                hovertemplate='Class %{label}<br>Value: $%{value:,.0f}<br>Percentage: %{percent}<extra></extra>'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Add validation message
            if 'A' in abc_value_pct.index:
                a_pct = abc_value_pct['A']
                if a_pct >= 60:
                    st.success(f"✅ **ABC Classification Verified**: Class A items represent {a_pct:.1f}% of total inventory value, confirming proper prioritization.")
                elif a_pct >= 40:
                    st.info(f"ℹ️ Class A items represent {a_pct:.1f}% of inventory value - moderate concentration.")
                else:
                    st.warning(f"⚠️ Class A items only represent {a_pct:.1f}% of value - may need reclassification or review.")
        else:
            st.info("Value distribution requires UNIT_COST_USD and QUANTITY_ON_HAND columns")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Average unit cost by ABC class
        if 'UNIT_COST_USD' in stock_df.columns:
            abc_cost = stock_df.groupby('ABC_CLASS')['UNIT_COST_USD'].agg(['mean', 'median', 'count']).reset_index()
            abc_cost = abc_cost.sort_values('ABC_CLASS')
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=abc_cost['ABC_CLASS'],
                y=abc_cost['mean'],
                name='Average Cost',
                marker_color='#4facfe',
                text=abc_cost['mean'].round(2),
                texttemplate='$%{text:.2f}',
                textposition='outside'
            ))
            
            fig.update_layout(
                title='Average Unit Cost by ABC Class',
                xaxis_title='ABC Class',
                yaxis_title='Average Unit Cost (USD)',
                showlegend=False,
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Display summary table
            st.caption("📋 Cost Summary by ABC Class")
            summary_df = abc_cost.copy()
            summary_df.columns = ['ABC Class', 'Avg Cost ($)', 'Median Cost ($)', 'Item Count']
            summary_df['Avg Cost ($)'] = summary_df['Avg Cost ($)'].round(2)
            summary_df['Median Cost ($)'] = summary_df['Median Cost ($)'].round(2)
            st.dataframe(summary_df, hide_index=True, use_container_width=True)
        else:
            st.info("Cost analysis requires UNIT_COST_USD column")
    
    with col2:
        # Risk score by ABC class
        abc_risk = stock_df.groupby('ABC_CLASS')['RISK_SCORE'].mean().reset_index()
        abc_risk = abc_risk.sort_values('ABC_CLASS')
        
        fig = px.bar(
            abc_risk,
            x='ABC_CLASS',
            y='RISK_SCORE',
            title="Average Risk Score by ABC Class",
            color='RISK_SCORE',
            color_continuous_scale='RdYlGn_r',
            labels={'RISK_SCORE': 'Avg Risk Score', 'ABC_CLASS': 'ABC Class'},
            text='RISK_SCORE'
        )
        
        fig.update_traces(texttemplate='%{text:.1f}', textposition='outside')
        fig.update_layout(
            yaxis_range=[0, 100],
            showlegend=False,
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    


def build_inventory_insights_prompt(aggregated_data):
    """
    Build comprehensive prompt for auto-generated insights
    Uses aggregated data from all dynamic tables and views
    """
    
    context_parts = []
    
    context_parts.append("=== INVENTORY OVERVIEW ===")
    context_parts.append(f"Total Items Tracked: {aggregated_data['total_items']}")
    context_parts.append(f"Total Locations: {aggregated_data['total_locations']}")
    context_parts.append(f"Total Categories: {aggregated_data['total_categories']}")
    context_parts.append(f"Total Inventory Value: ${aggregated_data['total_value']:,.2f}")
    context_parts.append("")
    
    context_parts.append("=== STOCK HEALTH STATUS ===")
    for status, count in aggregated_data['stock_status_breakdown'].items():
        pct = (count / aggregated_data['total_items'] * 100) if aggregated_data['total_items'] > 0 else 0
        context_parts.append(f"{status}: {count} items ({pct:.1f}%)")
    context_parts.append("")
    
    context_parts.append("=== STOCKOUT RISK ANALYSIS ===")
    context_parts.append(f"Items <= 3 days to stockout: {aggregated_data['critical_timing']['3_days']}")
    context_parts.append(f"Items <= 7 days to stockout: {aggregated_data['critical_timing']['7_days']}")
    context_parts.append(f"Items <= 14 days to stockout: {aggregated_data['critical_timing']['14_days']}")
    context_parts.append(f"Average days until stockout: {aggregated_data['avg_days_to_stockout']:.1f} days")
    context_parts.append("")
    
    context_parts.append("=== ABC CLASSIFICATION ===")
    for abc_class, data in aggregated_data['abc_analysis'].items():
        context_parts.append(f"Class {abc_class}: {data['count']} items, ${data['value']:,.0f} value, {data['critical_count']} critical")
    context_parts.append("")
    
    context_parts.append("=== LOCATION PERFORMANCE ===")
    for location in aggregated_data['location_breakdown'][:5]:
        context_parts.append(f"{location['location']}: {location['critical']} critical, {location['low']} low, {location['healthy']} healthy")
    context_parts.append("")
    
    context_parts.append("=== CATEGORY ISSUES ===")
    for category in aggregated_data['category_breakdown'][:5]:
        context_parts.append(f"{category['category']}: {category['critical']} critical items, Avg Risk: {category['avg_risk']:.0f}")
    context_parts.append("")
    
    context_parts.append("=== REORDER RECOMMENDATIONS ===")
    context_parts.append(f"Items requiring reorder: {aggregated_data['reorder_stats']['items_to_reorder']}")
    context_parts.append(f"Urgent items (Priority >= 8): {aggregated_data['reorder_stats']['urgent_items']}")
    context_parts.append(f"Estimated total order value: ${aggregated_data['reorder_stats']['total_order_value']:,.0f}")
    context_parts.append("")
    
    context_parts.append("=== TOP CRITICAL ITEMS ===")
    for idx, item in enumerate(aggregated_data['top_critical_items'][:10], 1):
        context_parts.append(f"{idx}. {item['name']} ({item['location']}) - {item['category']}, Stock: {item['qty']:.0f}, Days: {item['days']:.1f}, Risk: {item['risk']:.0f}")
    
    context = "\n".join(context_parts)
    
    prompt = f"""You are an expert supply chain analyst reviewing inventory health for a healthcare/NGO distribution system handling essential goods (medicines, medical supplies, food, hygiene products).

    **YOUR TASK:** Analyze the comprehensive inventory data below and provide actionable strategic insights.

    **INVENTORY DATA:**
    {context}

    **REQUIRED OUTPUT FORMAT:**

    1. **Executive Summary** (2-3 sentences)
    - Overall inventory health assessment
    - Most urgent concern requiring immediate action

    2. **Critical Issues** (3-4 specific problems)
    - Identify the most pressing inventory risks
    - Include specific numbers, locations, and categories
    - Explain the business impact of each issue

    3. **Root Cause Analysis**
    - Why are these issues occurring?
    - Pattern analysis across locations/categories

    4. **Immediate Actions** (Prioritized list of 5-7 actions)
    - Specific, actionable recommendations
    - Include which items, locations, or categories to focus on
    - Estimated timeline/urgency for each action

    5. **Strategic Recommendations** (2-3 longer-term improvements)
    - Process improvements
    - Inventory policy adjustments
    - Risk mitigation strategies

    **GUIDELINES:**
    - Be specific with numbers, items, and locations
    - Prioritize patient/beneficiary safety (these are essential goods)
    - Consider both immediate risks and systemic issues
    - Use data-driven reasoning
    - Format with clear headers and bullet points
    - Keep total response under 600 words but be thorough

    Provide your analysis:"""
    
    return prompt
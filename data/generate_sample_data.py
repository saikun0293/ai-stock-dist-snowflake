"""
Sample Data Generator for Inventory Monitoring System
Generates realistic inventory data for medicines, food, and supplies
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

# Define categories and items
CATEGORIES = {
    'medicines': [
        'Paracetamol 500mg', 'Amoxicillin 250mg', 'Ibuprofen 400mg',
        'Aspirin 100mg', 'Metformin 500mg', 'Omeprazole 20mg',
        'Ciprofloxacin 500mg', 'Azithromycin 500mg', 'Insulin 100U/ml',
        'Salbutamol Inhaler'
    ],
    'food': [
        'Rice (kg)', 'Wheat Flour (kg)', 'Lentils (kg)', 'Cooking Oil (L)',
        'Sugar (kg)', 'Salt (kg)', 'Milk Powder (kg)', 'Canned Beans',
        'Pasta (kg)', 'Baby Food'
    ],
    'supplies': [
        'Surgical Masks (box)', 'Gloves (box)', 'Hand Sanitizer (L)',
        'Bandages (pack)', 'Syringes (pack)', 'Cotton Swabs (pack)',
        'Thermometers', 'Blood Pressure Monitor', 'First Aid Kit',
        'Disinfectant (L)'
    ]
}

LOCATIONS = [
    'City Hospital - Main', 'City Hospital - Pharmacy', 'City Hospital - Emergency',
    'District Health Center', 'Community Clinic North', 'Community Clinic South',
    'NGO Distribution Center', 'Public Distribution System - Zone A',
    'Public Distribution System - Zone B', 'Rural Health Post'
]

def generate_inventory_data(num_days=90, start_date=None):
    """Generate daily inventory snapshots"""
    if start_date is None:
        start_date = datetime.now() - timedelta(days=num_days)
    
    records = []
    
    for location in LOCATIONS:
        for category, items in CATEGORIES.items():
            for item in items:
                # Initial stock level (varies by location and item)
                base_stock = random.randint(100, 1000)
                current_stock = base_stock
                
                # Define reorder point and max stock
                reorder_point = int(base_stock * 0.25)
                max_stock = int(base_stock * 1.5)
                
                for day in range(num_days):
                    date = start_date + timedelta(days=day)
                    
                    # Daily consumption (varies by item type)
                    if category == 'medicines':
                        consumption = random.randint(5, 30)
                    elif category == 'food':
                        consumption = random.randint(10, 50)
                    else:  # supplies
                        consumption = random.randint(3, 25)
                    
                    # Add some randomness
                    consumption = int(consumption * random.uniform(0.7, 1.3))
                    
                    # Simulate stock movement
                    current_stock -= consumption
                    
                    # Restock if below reorder point
                    if current_stock < reorder_point:
                        restock_amount = max_stock - current_stock
                        current_stock += restock_amount
                        restocked = True
                    else:
                        restock_amount = 0
                        restocked = False
                    
                    # Ensure stock doesn't go negative
                    current_stock = max(0, current_stock)
                    
                    # Calculate days until stockout
                    if consumption > 0:
                        days_until_stockout = current_stock / consumption
                    else:
                        days_until_stockout = 999
                    
                    # Determine stock status
                    stock_percentage = (current_stock / max_stock) * 100
                    if stock_percentage < 10:
                        status = 'CRITICAL'
                    elif stock_percentage < 25:
                        status = 'LOW'
                    elif stock_percentage < 50:
                        status = 'MODERATE'
                    else:
                        status = 'GOOD'
                    
                    record = {
                        'date': date.strftime('%Y-%m-%d'),
                        'location': location,
                        'category': category,
                        'item_name': item,
                        'current_stock': current_stock,
                        'consumption': consumption,
                        'restock_amount': restock_amount,
                        'restocked': restocked,
                        'reorder_point': reorder_point,
                        'max_stock': max_stock,
                        'days_until_stockout': round(days_until_stockout, 2),
                        'stock_status': status,
                        'stock_percentage': round(stock_percentage, 2)
                    }
                    records.append(record)
    
    return pd.DataFrame(records)

def generate_alert_history(inventory_df):
    """Generate alert history based on inventory data"""
    alerts = []
    
    # Filter critical and low stock situations
    critical_records = inventory_df[inventory_df['stock_status'].isin(['CRITICAL', 'LOW'])]
    
    for _, row in critical_records.iterrows():
        alert = {
            'alert_date': row['date'],
            'location': row['location'],
            'category': row['category'],
            'item_name': row['item_name'],
            'current_stock': row['current_stock'],
            'alert_type': row['stock_status'],
            'days_until_stockout': row['days_until_stockout'],
            'resolved': row['restocked'],
            'priority': 'HIGH' if row['stock_status'] == 'CRITICAL' else 'MEDIUM'
        }
        alerts.append(alert)
    
    return pd.DataFrame(alerts)

def main():
    print("Generating sample inventory data...")
    
    # Generate inventory data for the last 90 days
    inventory_df = generate_inventory_data(num_days=90)
    
    # Generate alert history
    alerts_df = generate_alert_history(inventory_df)
    
    # Save to CSV files
    inventory_df.to_csv('data/inventory_data.csv', index=False)
    alerts_df.to_csv('data/alert_history.csv', index=False)
    
    print(f"Generated {len(inventory_df)} inventory records")
    print(f"Generated {len(alerts_df)} alert records")
    print("\nFiles saved:")
    print("  - data/inventory_data.csv")
    print("  - data/alert_history.csv")
    
    # Display summary statistics
    print("\n=== Inventory Summary ===")
    print(f"Date range: {inventory_df['date'].min()} to {inventory_df['date'].max()}")
    print(f"Locations: {inventory_df['location'].nunique()}")
    print(f"Total items: {inventory_df['item_name'].nunique()}")
    print("\nStock Status Distribution:")
    print(inventory_df['stock_status'].value_counts())

if __name__ == "__main__":
    main()

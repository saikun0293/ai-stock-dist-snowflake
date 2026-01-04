"""
Data Processing Utilities
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def load_demo_data():
    """Load demo data from CSV files or generate sample data"""
    
    # Check if demo data exists
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
    inventory_path = os.path.join(data_dir, 'inventory_data.csv')
    alerts_path = os.path.join(data_dir, 'alert_history.csv')
    
    if os.path.exists(inventory_path):
        # Load from CSV
        all_inventory = pd.read_csv(inventory_path)
        all_alerts = pd.read_csv(alerts_path)
        
        # Get most recent date for each item
        all_inventory['date'] = pd.to_datetime(all_inventory['date'])
        inventory_df = all_inventory.sort_values('date').groupby(['location', 'item_name']).tail(1).reset_index(drop=True)
        
        # Filter unresolved alerts
        alerts_df = all_alerts[all_alerts['resolved'] == False].copy()
        if len(alerts_df) > 0:
            alerts_df['alert_date'] = pd.to_datetime(alerts_df['alert_date'])
            alerts_df['days_open'] = (datetime.now() - alerts_df['alert_date']).dt.days
        
    else:
        # Generate sample data
        inventory_df = generate_sample_inventory()
        alerts_df = generate_sample_alerts(inventory_df)
    
    # Generate forecast data
    forecast_df = generate_sample_forecasts(inventory_df)
    
    return inventory_df, alerts_df, forecast_df

def generate_sample_inventory():
    """Generate sample inventory data"""
    locations = ['City Hospital', 'District Clinic', 'NGO Center']
    categories = ['medicines', 'food', 'supplies']
    items = {
        'medicines': ['Paracetamol 500mg', 'Amoxicillin 250mg', 'Ibuprofen 400mg'],
        'food': ['Rice (kg)', 'Wheat Flour (kg)', 'Cooking Oil (L)'],
        'supplies': ['Surgical Masks', 'Gloves', 'Hand Sanitizer']
    }
    
    data = []
    for location in locations:
        for category in categories:
            for item in items[category]:
                stock_pct = np.random.uniform(5, 95)
                max_stock = np.random.randint(500, 1500)
                current_stock = int(max_stock * stock_pct / 100)
                consumption = np.random.randint(10, 50)
                
                if stock_pct < 10:
                    status = 'CRITICAL'
                elif stock_pct < 25:
                    status = 'LOW'
                elif stock_pct < 50:
                    status = 'MODERATE'
                else:
                    status = 'GOOD'
                
                data.append({
                    'location': location,
                    'category': category,
                    'item_name': item,
                    'current_stock': current_stock,
                    'max_stock': max_stock,
                    'stock_percentage': round(stock_pct, 2),
                    'stock_status': status,
                    'days_until_stockout': round(current_stock / consumption, 2) if consumption > 0 else 999,
                    'snapshot_date': datetime.now().strftime('%Y-%m-%d')
                })
    
    return pd.DataFrame(data)

def generate_sample_alerts(inventory_df):
    """Generate sample alerts from inventory data"""
    critical_items = inventory_df[inventory_df['stock_status'].isin(['CRITICAL', 'LOW'])]
    
    alerts = []
    for _, row in critical_items.iterrows():
        alerts.append({
            'alert_id': np.random.randint(1000, 9999),
            'alert_date': datetime.now().strftime('%Y-%m-%d'),
            'location': row['location'],
            'category': row['category'],
            'item_name': row['item_name'],
            'current_stock': row['current_stock'],
            'alert_type': row['stock_status'],
            'days_until_stockout': row['days_until_stockout'],
            'priority': 'HIGH' if row['stock_status'] == 'CRITICAL' else 'MEDIUM',
            'days_open': np.random.randint(1, 5)
        })
    
    return pd.DataFrame(alerts)

def generate_sample_forecasts(inventory_df):
    """Generate sample forecast data"""
    forecasts = []
    
    for _, row in inventory_df.iterrows():
        predicted_consumption = np.random.uniform(10, 50)
        forecast_days = 14
        predicted_stock = max(0, row['current_stock'] - (predicted_consumption * forecast_days))
        
        if predicted_stock == 0:
            risk = 'HIGH RISK'
        elif predicted_stock < row['max_stock'] * 0.25:
            risk = 'MODERATE RISK'
        else:
            risk = 'LOW RISK'
        
        forecasts.append({
            'location': row['location'],
            'category': row['category'],
            'item_name': row['item_name'],
            'current_stock': row['current_stock'],
            'predicted_stock': round(predicted_stock, 2),
            'predicted_consumption': round(predicted_consumption, 2),
            'forecast_horizon_days': forecast_days,
            'stockout_risk': risk,
            'predicted_days_to_stockout': round(row['current_stock'] / predicted_consumption, 1),
            'confidence_interval_lower': round(predicted_consumption * 0.8, 2),
            'confidence_interval_upper': round(predicted_consumption * 1.2, 2),
            'model_accuracy': round(np.random.uniform(75, 95), 2)
        })
    
    return pd.DataFrame(forecasts)

def calculate_stock_metrics(df):
    """Calculate various stock metrics"""
    metrics = {
        'total_items': len(df),
        'critical_count': len(df[df['stock_status'] == 'CRITICAL']),
        'low_count': len(df[df['stock_status'] == 'LOW']),
        'avg_stock_percentage': df['stock_percentage'].mean(),
        'items_below_25_percent': len(df[df['stock_percentage'] < 25])
    }
    return metrics

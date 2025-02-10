from typing import Dict, Any, Optional
from datetime import datetime, timezone
import logging
from ecommerce_calculator.database.operations import load_product_data

logger = logging.getLogger(__name__)

def get_product_demand(product_id: str, start_date: str, end_date: str) -> Optional[Dict[str, Any]]:
    """Get product demand data for date range as monthly time series"""
    logger.info(f"Getting demand data for product: {product_id}")
    product = load_product_data(product_id)
    if not product or 'history' not in product:
        logger.error(f"Product not found or missing history: {product_id}")
        return None
        
    try:
        # Parse dates and ensure they're timezone-aware
        start = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
        end = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)
        
        logger.info(f"Filtering demand history between {start} and {end}")
        
        # Filter demand history to requested date range
        filtered_history = []
        for entry in product['history']:
            entry_date = datetime.fromisoformat(entry['date']).replace(tzinfo=timezone.utc)
            if start <= entry_date <= end:
                filtered_history.append(entry)
        
        # Group data by month
        monthly_data = {}
        for entry in filtered_history:
            date = datetime.fromisoformat(entry['date']).replace(tzinfo=timezone.utc)
            month_key = date.strftime('%Y-%m')  # Format: YYYY-MM
            
            if month_key not in monthly_data:
                monthly_data[month_key] = {
                    'sales': 0,
                    'revenue': 0,
                    'returns': 0,
                    'average_price': 0,
                    'num_transactions': 0
                }
            
            monthly_data[month_key]['sales'] += entry['sales']
            monthly_data[month_key]['revenue'] += entry['sales'] * entry['price']
            monthly_data[month_key]['returns'] += entry.get('returns', 0)
            monthly_data[month_key]['num_transactions'] += 1
        
        # Calculate averages and format time series
        time_series = []
        for month in sorted(monthly_data.keys()):
            data = monthly_data[month]
            avg_price = data['revenue'] / data['sales'] if data['sales'] > 0 else 0
            
            time_series.append({
                'month': month,
                'total_sales': data['sales'],
                'total_revenue': round(data['revenue'], 2),
                'total_returns': data['returns'],
                'average_price': round(avg_price, 2),
                'return_rate': round(data['returns'] / data['sales'], 4) if data['sales'] > 0 else 0
            })
        
        return {
            'time_series': time_series,
            'summary': {
                'total_months': len(time_series),
                'total_sales': sum(m['total_sales'] for m in time_series),
                'total_revenue': round(sum(m['total_revenue'] for m in time_series), 2),
                'average_monthly_sales': round(sum(m['total_sales'] for m in time_series) / len(time_series), 2) if time_series else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Error processing demand data: {e}")
        return None 
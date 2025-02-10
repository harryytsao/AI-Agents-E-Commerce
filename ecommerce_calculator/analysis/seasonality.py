from typing import Dict, Any, List, Optional
from datetime import datetime
from ecommerce_calculator.database.operations import load_product_data

def get_product_seasonality(product_id: str) -> Optional[Dict[str, Any]]:
    """Get product seasonality data"""
    product = load_product_data(product_id)
    if not product or 'history' not in product:
        return None
        
    # Calculate seasonality from history
    seasonality_data = calculate_seasonality_metrics(product['history'])
    
    # Add interpretation
    seasonality_data['interpretation'] = interpret_seasonality(seasonality_data)
    
    return seasonality_data

def calculate_seasonality_metrics(history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate seasonality metrics from sales history"""
    if not history:
        return {'seasonality_patterns': {}}
    
    # Group sales by month
    monthly_patterns = {}
    for entry in history:
        date = datetime.fromisoformat(entry['date'])
        month = date.month
        
        if month not in monthly_patterns:
            monthly_patterns[month] = []
        monthly_patterns[month].append(entry['sales'])
    
    # Calculate average sales for each month
    monthly_averages = {}
    for month, sales in monthly_patterns.items():
        monthly_averages[month] = sum(sales) / len(sales)
    
    # Calculate overall average
    all_sales = [sale for sales_list in monthly_patterns.values() for sale in sales_list]
    overall_average = sum(all_sales) / len(all_sales) if all_sales else 0
    
    # Calculate seasonality index for each month
    seasonality_indices = {}
    for month, avg_sales in monthly_averages.items():
        seasonality_indices[month] = avg_sales / overall_average if overall_average > 0 else 0
    
    # Identify peak and low seasons
    peak_months = [
        month for month, index in seasonality_indices.items()
        if index > 1.1  # 10% above average
    ]
    low_months = [
        month for month, index in seasonality_indices.items()
        if index < 0.9  # 10% below average
    ]
    
    return {
        'seasonality_patterns': {
            'monthly_indices': seasonality_indices,
            'peak_months': peak_months,
            'low_months': low_months,
            'seasonality_strength': calculate_seasonality_strength(seasonality_indices)
        },
        'metrics': {
            'overall_average_sales': overall_average,
            'monthly_averages': monthly_averages
        }
    }

def calculate_seasonality_strength(seasonality_indices: Dict[int, float]) -> float:
    """Calculate the strength of seasonality pattern (0-1)"""
    if not seasonality_indices:
        return 0
    
    # Calculate variance of indices from 1.0 (no seasonality)
    variances = [(index - 1.0) ** 2 for index in seasonality_indices.values()]
    avg_variance = sum(variances) / len(variances)
    
    # Convert to a 0-1 scale with a reasonable maximum variance
    strength = min(1.0, avg_variance * 2)  # Scale factor of 2 means variance of 0.5 gives max strength
    return strength

def interpret_seasonality(seasonality_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate human-readable interpretation of seasonality patterns"""
    patterns = seasonality_data['seasonality_patterns']
    strength = patterns['seasonality_strength']
    
    # Convert month numbers to names
    month_names = {
        1: 'January', 2: 'February', 3: 'March', 4: 'April',
        5: 'May', 6: 'June', 7: 'July', 8: 'August',
        9: 'September', 10: 'October', 11: 'November', 12: 'December'
    }
    
    peak_months = [month_names[m] for m in patterns['peak_months']]
    low_months = [month_names[m] for m in patterns['low_months']]
    
    return {
        'seasonality_type': 'strong' if strength > 0.5 else 'moderate' if strength > 0.2 else 'weak',
        'peak_seasons': peak_months,
        'low_seasons': low_months,
        'confidence_score': min(1.0, strength * 1.5)  # Scale strength to confidence
    } 
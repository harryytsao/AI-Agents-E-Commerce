from typing import Dict, Any, List, Optional
from datetime import datetime
from ecommerce_calculator.database.operations import load_product_data

def get_product_lifecycle(product_id: str) -> Optional[Dict[str, Any]]:
    """Get product lifecycle data and compute current stage based on sales history"""
    product = load_product_data(product_id)
    if not product or 'history' not in product:
        return None
        
    # Calculate lifecycle metrics from history
    history = sorted(product['history'], key=lambda x: x['date'])
    lifecycle_data = calculate_lifecycle_metrics(history)
    
    # Add computed metrics
    lifecycle_data['computed'] = {
        'current_stage': compute_lifecycle_stage(lifecycle_data),
        'days_in_stage': compute_days_in_stage(lifecycle_data),
        'stage_transition_risk': compute_stage_risk(lifecycle_data)
    }
    
    return lifecycle_data

def calculate_lifecycle_metrics(history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate key metrics from sales history"""
    if not history:
        return {'metrics': {}}
    
    # Calculate quarterly sales and growth rates
    quarters = []
    for i in range(0, len(history), 90):  # Approximate quarter (90 days)
        quarter_sales = sum(day['sales'] for day in history[i:i+90])
        quarters.append(quarter_sales)
    
    # Calculate growth rates between quarters
    growth_rates = []
    for i in range(1, len(quarters)):
        if quarters[i-1] > 0:
            growth_rate = (quarters[i] - quarters[i-1]) / quarters[i-1]
            growth_rates.append(growth_rate)
    
    # Calculate metrics
    avg_growth_rate = sum(growth_rates) / len(growth_rates) if growth_rates else 0
    growth_volatility = calculate_volatility(growth_rates)
    
    # Get the most recent metrics
    recent_quarter = quarters[-1] if quarters else 0
    peak_quarter = max(quarters) if quarters else 0
    market_saturation = recent_quarter / peak_quarter if peak_quarter > 0 else 0
    
    return {
        'metrics': {
            'growth_rate': avg_growth_rate,
            'growth_volatility': growth_volatility,
            'market_saturation': market_saturation,
            'competitive_pressure': calculate_competitive_pressure(history),
        },
        'stage_start_date': history[0]['date'] if history else None
    }

def calculate_volatility(rates: List[float]) -> float:
    """Calculate volatility of growth rates"""
    if not rates:
        return 0
    mean = sum(rates) / len(rates)
    variance = sum((r - mean) ** 2 for r in rates) / len(rates)
    return min(1.0, variance ** 0.5)  # Standard deviation, capped at 1.0

def calculate_competitive_pressure(history: List[Dict[str, Any]]) -> float:
    """Calculate competitive pressure based on price changes and returns"""
    if not history:
        return 0
    
    # Calculate price volatility
    prices = [day['price'] for day in history]
    price_changes = [abs(prices[i] - prices[i-1]) / prices[i-1] 
                    for i in range(1, len(prices))]
    price_volatility = sum(price_changes) / len(price_changes) if price_changes else 0
    
    # Calculate return rate
    total_sales = sum(day['sales'] for day in history)
    total_returns = sum(day['returns'] for day in history)
    return_rate = total_returns / total_sales if total_sales > 0 else 0
    
    # Combine metrics
    pressure = (0.7 * price_volatility + 0.3 * return_rate)
    return min(1.0, pressure)

def compute_lifecycle_stage(lifecycle_data: Dict[str, Any]) -> str:
    """Determine current lifecycle stage based on metrics"""
    metrics = lifecycle_data.get('metrics', {})
    growth_rate = metrics.get('growth_rate', 0)
    market_share = metrics.get('market_share', 0)
    
    if growth_rate < 0 and market_share < 0.1:
        return "decline"
    elif growth_rate < 0.05 and market_share >= 0.1:
        return "maturity" 
    elif growth_rate >= 0.05 and market_share >= 0.05:
        return "growth"
    else:
        return "introduction"

def compute_days_in_stage(lifecycle_data: Dict[str, Any]) -> int:
    """Calculate days product has been in current stage"""
    stage_start = lifecycle_data.get('stage_start_date')
    if not stage_start:
        return 0
        
    start_date = datetime.fromisoformat(stage_start)
    days = (datetime.now() - start_date).days
    return max(0, days)

def compute_stage_risk(lifecycle_data: Dict[str, Any]) -> float:
    """Calculate risk of transitioning to next stage"""
    metrics = lifecycle_data.get('metrics', {})
    
    # Risk factors
    growth_volatility = metrics.get('growth_volatility', 0)
    market_saturation = metrics.get('market_saturation', 0)
    competitive_pressure = metrics.get('competitive_pressure', 0)
    
    # Simple weighted risk score
    risk_score = (
        0.4 * growth_volatility +
        0.3 * market_saturation +
        0.3 * competitive_pressure
    )
    
    return min(1.0, max(0.0, risk_score)) 
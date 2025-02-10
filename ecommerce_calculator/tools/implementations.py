import logging
from datetime import datetime
from typing import Dict, Any
from ecommerce_calculator.tools.base import Tool
from ecommerce_calculator.analysis.lifecycle import get_product_lifecycle
from ecommerce_calculator.analysis.seasonality import get_product_seasonality
from ecommerce_calculator.analysis.demand import get_product_demand

logger = logging.getLogger(__name__)

class LifecycleTool(Tool):
    def __init__(self):
        super().__init__(
            name="product_lifecycle",
            description="Analyze product lifecycle stage"
        )
    
    def validate_input(self, product_id: str) -> bool:
        return isinstance(product_id, str) and bool(product_id.strip())
    
    def execute(self, product_id: str) -> Dict[str, Any]:
        try:
            if not self.validate_input(product_id):
                raise ValueError("Invalid input parameters")
                
            result = get_product_lifecycle(product_id)
            success = bool(result)  # Only success if we got actual data
            self.metrics.complete(success=success)
            
            if not success:
                return None
                
            return result
            
        except Exception as e:
            self.metrics.complete(success=False, error=str(e))
            raise

class SeasonalityTool(Tool):
    def __init__(self):
        super().__init__(
            name="product_seasonality",
            description="Analyze product seasonality patterns"
        )
    
    def validate_input(self, product_id: str) -> bool:
        return isinstance(product_id, str) and bool(product_id.strip())
    
    def execute(self, product_id: str) -> Dict[str, Any]:
        try:
            if not self.validate_input(product_id):
                raise ValueError("Invalid input parameters")
                
            result = get_product_seasonality(product_id)
            success = bool(result)  # Only success if we got actual data
            self.metrics.complete(success=success)
            
            if not success:
                return None
                
            return result
            
        except Exception as e:
            self.metrics.complete(success=False, error=str(e))
            raise

class DemandTool(Tool):
    def __init__(self):
        super().__init__(
            name="product_demand",
            description="Analyze product demand patterns"
        )
    
    def validate_input(self, product_id: str, start_date: str, end_date: str) -> bool:
        logger.info(f"Validating input - product_id: {product_id}, start_date: {start_date}, end_date: {end_date}")
        
        if not isinstance(product_id, str) or not bool(product_id.strip()):
            logger.error("Invalid product_id")
            return False
            
        try:
            # Validate date formats
            start = datetime.fromisoformat(start_date)
            end = datetime.fromisoformat(end_date)
            
            # Add validation for start date before end date
            if start > end:
                logger.error("Start date is after end date")
                return False
                
            return True
        except ValueError as e:
            logger.error(f"Date validation error: {e}")
            return False
    
    def execute(self, product_id: str, start_date: str, end_date: str) -> Dict[str, Any]:
        try:
            if not self.validate_input(product_id, start_date, end_date):
                raise ValueError("Invalid input parameters")
                
            result = get_product_demand(product_id, start_date, end_date)
            success = bool(result)  # Only success if we got actual data
            self.metrics.complete(success=success)
            
            if not success:
                return None
                
            return result
            
        except Exception as e:
            self.metrics.complete(success=False, error=str(e))
            raise 
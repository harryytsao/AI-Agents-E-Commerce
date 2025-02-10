from typing import Optional, Literal, Dict, Any, List
from pydantic import BaseModel, Field
from openai import OpenAI
import os
import logging
import json
from datetime import datetime
import psycopg2
import psycopg2.extras

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
model = "gpt-4o-mini"

# --------------------------------------------------------------
# Step 1: Define the data models for routing and responses
# --------------------------------------------------------------

class EcommerceCalculatorRequestType(BaseModel):
    """Router LLM call: Determine the type of ecommerce calculator request"""

    request_type: Literal["analyze_product_lifecycle", "analyze_product_seasonality", "analyze_product_demand", "other"] = Field(
        description="Type of ecommerce calculator request being made"
    )
    confidence_score: float = Field(description="Confidence score between 0 and 1")
    description: str = Field(description="Cleaned description of the request")

class ProductLifecycleDetails(BaseModel):
    """Details for analyzing product lifecycle"""
    
    product_id: str = Field(description="Product identifier")
    current_date: str = Field(description="Current date (ISO 8601)")


class SeasonalityDetails(BaseModel):
    """Details for analyzing product seasonality"""
    
    product_id: str = Field(description="Product identifier")
    date: str = Field(description="Date for seasonality analysis (ISO 8601)")


class DemandDetails(BaseModel):
    """Details for analyzing product demand"""
    
    product_id: str = Field(description="Product identifier")
    start_date: str = Field(description="Start date for analysis (ISO 8601)")
    end_date: str = Field(description="End date for analysis (ISO 8601)")


class EcommerceResponse(BaseModel):
    """Final response format"""
    
    success: bool = Field(description="Whether the operation was successful")
    message: str = Field(description="User-friendly response message")
    analysis_data: Optional[dict] = Field(description="Analysis results if applicable")


# --------------------------------------------------------------
# Step 1.5: Define data access functions
# --------------------------------------------------------------

def load_product_data(product_id: str) -> Optional[Dict[str, Any]]:
    """Load product data from PostgreSQL database"""
    try:
        # Create connection using environment variables
        conn = psycopg2.connect(
            os.getenv('DATABASE_URL')
        )
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Query product data
        cursor.execute("""
            SELECT product_id,
                   name,
                   category,
                   price,
                   attributes,
                   history
            FROM products
            WHERE name = %s
        """, (product_id,))
        
        product = cursor.fetchone()
        
        if not product:
            logger.warning(f"Product not found: {product_id}")
            return None
            
        # Convert to dictionary and ensure JSONB fields are parsed
        result = dict(product)
        # Parse JSONB fields if they're not None
        if result['attributes']:
            result['attributes'] = dict(result['attributes'])
        if result['history']:
            result['history'] = list(result['history'])
            
        return result
        
    except Exception as e:
        logger.error(f"Error loading product data: {e}")
        return None
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

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

def get_product_demand(product_id: str, start_date: str, end_date: str) -> Optional[Dict[str, Any]]:
    """Get product demand data for date range"""
    product = load_product_data(product_id)
    if not product or 'demandHistory' not in product:
        return None
        
    try:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        
        # Filter demand history to requested date range
        filtered_history = [
            entry for entry in product['demandHistory']['monthly']
            if start <= datetime.fromisoformat(entry['date']) <= end
        ]
        
        return {
            'demand_history': filtered_history,
            'metrics': product.get('metrics', {})
        }
    except Exception as e:
        logger.error(f"Error processing demand data: {e}")
        return None

# --------------------------------------------------------------
# Step 2: Define the routing and processing functions
# --------------------------------------------------------------

def route_ecommerce_request(user_input: str) -> EcommerceCalculatorRequestType:
    """Router LLM call to determine the type of ecommerce calculator request"""
    logger.info("Routing ecommerce calculator request")

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": """Determine if this is a request to analyze product lifecycle, seasonality, or demand.
                Return your response as a JSON object with the following fields:
                - request_type: one of ["analyze_product_lifecycle", "analyze_product_seasonality", "analyze_product_demand", "other"]
                - confidence_score: number between 0 and 1
                - description: cleaned description of the request""",
            },
            {"role": "user", "content": user_input},
        ],
        response_format={ "type": "json_object" }
    )
    
    response_json = completion.choices[0].message.content
    result = EcommerceCalculatorRequestType.model_validate_json(response_json)
    
    logger.info(
        f"Request routed as: {result.request_type} with confidence: {result.confidence_score}"
    )
    return result


class ToolMetrics:
    """Track performance metrics for tools"""
    def __init__(self):
        self.start_time = datetime.now()
        self.computation_time = None
        self.success = False
        self.error = None

    def complete(self, success: bool, error: Optional[str] = None):
        self.computation_time = (datetime.now() - self.start_time).total_seconds()
        self.success = success
        self.error = error

class Tool:
    """Base class for all tools"""
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.metrics = ToolMetrics()

    def validate_input(self, **kwargs) -> bool:
        """Validate input types - override in subclasses"""
        return True

    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool - override in subclasses"""
        raise NotImplementedError

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
        if not isinstance(product_id, str) or not bool(product_id.strip()):
            return False
            
        try:
            # Validate date formats
            datetime.fromisoformat(start_date)
            datetime.fromisoformat(end_date)
            return True
        except ValueError:
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

class ToolRepository:
    """Central repository for all available tools"""
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        
    def register_tool(self, tool: Tool):
        """Register a new tool"""
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
        
    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name"""
        return self._tools.get(name)
        
    def list_tools(self) -> List[Dict[str, str]]:
        """List all available tools"""
        return [{"name": t.name, "description": t.description} 
                for t in self._tools.values()]

# Initialize global tool repository
tool_repository = ToolRepository()
tool_repository.register_tool(LifecycleTool())
tool_repository.register_tool(SeasonalityTool())
tool_repository.register_tool(DemandTool())

def handle_lifecycle_analysis(description: str) -> EcommerceResponse:
    """Process a product lifecycle analysis request"""
    logger.info("Processing lifecycle analysis request")

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": """Extract details for analyzing product lifecycle.
                Return your response as a JSON object with the following fields:
                - product_id: string identifier of the product (use spaces, not underscores)
                - current_date: current date in ISO 8601 format""",
            },
            {"role": "user", "content": description},
        ],
        response_format={ "type": "json_object" }
    )
    
    response_json = completion.choices[0].message.content
    details = ProductLifecycleDetails.model_validate_json(response_json)

    # Clean up product ID - replace underscores with spaces
    product_id = details.product_id.replace('_', ' ')

    # Get lifecycle tool from repository
    lifecycle_tool = tool_repository.get_tool("product_lifecycle")
    if not lifecycle_tool:
        return EcommerceResponse(
            success=False,
            message="Lifecycle analysis tool not available",
            analysis_data=None
        )

    try:
        lifecycle_data = lifecycle_tool.execute(product_id=product_id)
        
        # Add check for None result
        if not lifecycle_data:
            return EcommerceResponse(
                success=False,
                message=f"Product '{product_id}' not found",
                analysis_data=None
            )

        return EcommerceResponse(
            success=True,
            message=f"Analyzed lifecycle for product '{product_id}'",
            analysis_data={
                "result": lifecycle_data,
                "metrics": {
                    "computation_time": lifecycle_tool.metrics.computation_time,
                    "success": lifecycle_tool.metrics.success
                }
            }
        )
    except Exception as e:
        logger.error(f"Error in lifecycle analysis: {e}")
        return EcommerceResponse(
            success=False,
            message=f"Error analyzing lifecycle: {str(e)}",
            analysis_data=None
        )


def handle_seasonality_analysis(description: str) -> EcommerceResponse:
    """Process a product seasonality analysis request"""
    logger.info("Processing seasonality analysis request")

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": """Extract details for analyzing product seasonality.
                Return your response as a JSON object with the following fields:
                - product_id: string identifier of the product
                - date: current date in ISO 8601 format""",
            },
            {"role": "user", "content": description},
        ],
        response_format={ "type": "json_object" }
    )
    
    response_json = completion.choices[0].message.content
    details = SeasonalityDetails.model_validate_json(response_json)

    # Clean up product ID - replace underscores with spaces
    product_id = details.product_id.replace('_', ' ')

    # Get seasonality tool from repository
    seasonality_tool = tool_repository.get_tool("product_seasonality")
    if not seasonality_tool:
        return EcommerceResponse(
            success=False,
            message="Seasonality analysis tool not available",
            analysis_data=None
        )

    try:
        seasonality_data = seasonality_tool.execute(product_id=product_id)
        
        if not seasonality_data:
            return EcommerceResponse(
                success=False,
                message=f"Product '{product_id}' not found",
                analysis_data=None
            )

        return EcommerceResponse(
            success=True,
            message=f"Analyzed seasonality for product '{product_id}'",
            analysis_data={
                "result": seasonality_data,
                "metrics": {
                    "computation_time": seasonality_tool.metrics.computation_time,
                    "success": seasonality_tool.metrics.success
                }
            }
        )
    except Exception as e:
        logger.error(f"Error in seasonality analysis: {e}")
        return EcommerceResponse(
            success=False,
            message=f"Error analyzing seasonality: {str(e)}",
            analysis_data=None
        )


def handle_demand_analysis(description: str) -> EcommerceResponse:
    """Process a product demand analysis request"""
    logger.info("Processing demand analysis request")

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": """Extract details for analyzing product demand.
                Return your response as a JSON object with the following fields:
                - product_id: string identifier of the product
                - start_date: start date in ISO 8601 format
                - end_date: end date in ISO 8601 format""",
            },
            {"role": "user", "content": description},
        ],
        response_format={ "type": "json_object" }
    )
    
    response_json = completion.choices[0].message.content
    details = DemandDetails.model_validate_json(response_json)

    # Clean up product ID - replace underscores with spaces
    product_id = details.product_id.replace('_', ' ')

    # Get demand tool from repository
    demand_tool = tool_repository.get_tool("product_demand")
    if not demand_tool:
        return EcommerceResponse(
            success=False,
            message="Demand analysis tool not available",
            analysis_data=None
        )

    try:
        demand_data = demand_tool.execute(
            product_id=product_id,
            start_date=details.start_date,
            end_date=details.end_date
        )
        
        if not demand_data:
            return EcommerceResponse(
                success=False,
                message=f"Product '{product_id}' not found",
                analysis_data=None
            )

        return EcommerceResponse(
            success=True,
            message=f"Analyzed demand for product '{product_id}'",
            analysis_data={
                "result": demand_data,
                "metrics": {
                    "computation_time": demand_tool.metrics.computation_time,
                    "success": demand_tool.metrics.success
                }
            }
        )
    except Exception as e:
        logger.error(f"Error in demand analysis: {e}")
        return EcommerceResponse(
            success=False,
            message=f"Error analyzing demand: {str(e)}",
            analysis_data=None
        )


def process_ecommerce_request(user_input: str) -> Optional[EcommerceResponse]:
    """Main function implementing the routing workflow"""
    logger.info("Processing ecommerce calculator request")

    # Get routing result
    route_result = route_ecommerce_request(user_input)

    # Check confidence threshold
    if route_result.confidence_score < 0.7:
        logger.warning(f"Low confidence score: {route_result.confidence_score}")
        return EcommerceResponse(
            success=False,
            message="Unable to understand request with sufficient confidence",
            analysis_data=None
        )

    # Route to appropriate handler
    if route_result.request_type == "analyze_product_lifecycle":
        return handle_lifecycle_analysis(route_result.description)
    elif route_result.request_type == "analyze_product_seasonality":
        return handle_seasonality_analysis(route_result.description)
    elif route_result.request_type == "analyze_product_demand":
        return handle_demand_analysis(route_result.description)
    else:
        return EcommerceResponse(
            success=False,
            message="Unsupported request type",
            analysis_data=None
        )

def generate_analysis_summary(analysis_data: Dict[str, Any]) -> str:
    """Generate a concise summary of the lifecycle analysis using the LLM"""
    logger.info("Generating analysis summary")
    
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": """You are a helpful ecommerce analyst. Generate a concise, business-friendly summary 
                of the product lifecycle analysis. Focus on the key insights and actionable information.
                Keep the summary to 2-3 sentences."""
            },
            {
                "role": "user", 
                "content": f"Please summarize this product lifecycle analysis data: {json.dumps(analysis_data)}"
            }
        ]
    )
    
    return completion.choices[0].message.content

def main():
    """Main function to run different test scenarios"""
    print("\nEcommerce Calculator Test Suite")
    print("--------------------------------")
    
    while True:
        print("\nSelect a test to run:")
        print("1. Test Product Lifecycle Analysis")
        print("2. Test Product Seasonality Analysis")
        print("3. Test Product Demand Analysis")
        print("4. Test Invalid Request")
        print("5. Test get_product_lifecycle function")
        print("0. Exit")
        
        choice = input("\nEnter your choice (0-5): ")
        
        if choice == "1":
            print("\nTesting lifecycle analysis...")
            lifecycle_input = "What's the lifecycle stage for product 'material can'?"
            result = process_ecommerce_request(lifecycle_input)
            if result:
                print(f"\nSuccess: {result.success}")
                print(f"Message: {result.message}")
                if result.analysis_data:
                    print("\nAnalysis Data:")
                    print(json.dumps(result.analysis_data, indent=2))
                    
                    # Generate and print the summary
                    print("\nSummary:")
                    summary = generate_analysis_summary(result.analysis_data)
                    print(summary)
            else:
                print("\nNo response received")
                
        elif choice == "2":
            print("\nTesting seasonality analysis...")
            seasonality_input = "Is product 'material can' seasonal?"
            result = process_ecommerce_request(seasonality_input)
            if result:
                print(f"\nSuccess: {result.success}")
                print(f"Message: {result.message}")
                if result.analysis_data:
                    print("\nAnalysis Data:")
                    print(json.dumps(result.analysis_data, indent=2))
                    # Generate and print the summary
                    print("\nSummary:")
                    summary = generate_analysis_summary(result.analysis_data)
                    print(summary)
            else:
                print("\nNo response received")
                
        elif choice == "3":
            print("\nTesting demand analysis...")
            demand_input = "What's the demand forecast for product 'Awesome Sausages'?"
            result = process_ecommerce_request(demand_input)
            if result:
                print(f"\nSuccess: {result.success}")
                print(f"Message: {result.message}")
                if result.analysis_data:
                    print("\nAnalysis Data:")
                    print(json.dumps(result.analysis_data, indent=2))
            else:
                print("\nNo response received")
                
        elif choice == "4":
            print("\nTesting invalid request...")
            invalid_input = "What's the weather like today?"
            result = process_ecommerce_request(invalid_input)
            if result:
                print(f"\nSuccess: {result.success}")
                print(f"Message: {result.message}")
            else:
                print("\nRequest not recognized as an ecommerce calculator operation")
                
        elif choice == "5":
            print("\nTesting get_product_lifecycle function directly...")
            test_product_id = "material can"
            result = get_product_lifecycle(test_product_id)
            if result:
                print("\nProduct lifecycle data:")
                print(json.dumps(result, indent=2))
            else:
                print(f"\nNo lifecycle data found for product: '{test_product_id}'")
            
        elif choice == "0":
            print("\nExiting...")
            break
            
        else:
            print("\nInvalid choice. Please try again.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()
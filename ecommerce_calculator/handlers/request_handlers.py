import logging
from datetime import datetime
from typing import Optional
import json
from openai import OpenAI
import os

from ecommerce_calculator.models.request_types import (
    EcommerceCalculatorRequestType,
    ProductLifecycleDetails,
    SeasonalityDetails,
    DemandDetails
)
from ecommerce_calculator.models.response_types import EcommerceResponse
from ecommerce_calculator.tools.base import ToolRepository
from ecommerce_calculator.tools.implementations import LifecycleTool, SeasonalityTool, DemandTool

logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
model = "gpt-4o-mini"  # Update as needed

# Initialize global tool repository
tool_repository = ToolRepository()
tool_repository.register_tool(LifecycleTool())
tool_repository.register_tool(SeasonalityTool())
tool_repository.register_tool(DemandTool())

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
    product_id = details.product_id.replace('_', ' ').lower()

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
                - product_id: string identifier of the product (use spaces, not underscores)
                - date: current date in ISO 8601 format""",
            },
            {"role": "user", "content": description},
        ],
        response_format={ "type": "json_object" }
    )
    
    response_json = completion.choices[0].message.content
    details = SeasonalityDetails.model_validate_json(response_json)

    # Clean up product ID - replace underscores with spaces
    product_id = details.product_id.replace('_', ' ').lower()

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
                - product_id: string identifier of the product (use spaces, not underscores)
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
    product_id = details.product_id.replace('_', ' ').lower()

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
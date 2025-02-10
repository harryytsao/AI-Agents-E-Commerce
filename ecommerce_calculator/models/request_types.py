from typing import Literal
from pydantic import BaseModel, Field

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
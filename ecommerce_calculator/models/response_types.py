from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class EcommerceResponse(BaseModel):
    """Final response format"""
    success: bool = Field(description="Whether the operation was successful")
    message: str = Field(description="User-friendly response message")
    analysis_data: Optional[dict] = Field(description="Analysis results if applicable") 
"""
Pydantic models for JSON data validation and structure.
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class ProcessedResult(BaseModel):
    """Processed extraction result."""
    extracted_fields: Dict[str, Any] = Field(..., description="Extracted key fields")
    validation_status: str = Field(..., description="Validation result")
    processing_notes: str = Field(..., description="Processing notes")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in extraction")
    context: str = Field(..., description="Additional context for downstream processing")


class AgentResponse(BaseModel):
    """Standardized agent response."""
    status: str = Field(..., description="Processing status")
    result: Optional[ProcessedResult] = Field(None, description="Processing result")
    error: Optional[str] = Field(None, description="Error message if any")
    agent_name: str = Field(..., description="Name of processing agent")
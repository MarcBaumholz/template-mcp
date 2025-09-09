"""
Pydantic models for field enhancement and semantic analysis.
"""
from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field


class FieldEnhancement(BaseModel):
    """Enhanced metadata for a single field."""
    field_name: str = Field(..., description="Original field name")
    semantic_description: str = Field(..., description="Detailed semantic description")
    synonyms: List[str] = Field(default=[], description="Alternative names/synonyms")
    possible_datatypes: List[str] = Field(default=[], description="Possible data types")
    possible_values: List[Union[str, int, float, bool]] = Field(default=[], description="Example/possible values")  # <- UNION TYPE
    business_context: str = Field(..., description="Business domain context")


class EnhancementResult(BaseModel):
    """Result of field enhancement processing."""
    original_extraction: Dict[str, Any] = Field(..., description="Original extraction result")
    enhanced_fields: List[FieldEnhancement] = Field(..., description="Enhanced field metadata")
    processing_context: str = Field(..., description="Context used for enhancement")
    enhancement_confidence: float = Field(..., ge=0.0, le=1.0, description="Enhancement quality score")


class EnhancementResponse(BaseModel):
    """Standardized enhancement agent response."""
    status: str = Field(..., description="Processing status")
    result: Optional[EnhancementResult] = Field(None, description="Enhancement result")
    error: Optional[str] = Field(None, description="Error message if any")
    agent_name: str = Field(..., description="Name of processing agent")
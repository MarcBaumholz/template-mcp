"""
Pydantic models for Schema Mapping tool.
Data structures for field mapping, agent insights, and results.
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime


class SourceField(BaseModel):
    """Represents a field from the source API."""
    name: str = Field(description="Field name")
    path: str = Field(description="Full path to the field (e.g., 'user.profile.email')")
    type: str = Field(description="Data type (string, int, object, etc.)")
    description: Optional[str] = Field(default=None, description="Field description")
    context: Optional[str] = Field(default=None, description="Additional context about the field")
    examples: Optional[List[str]] = Field(default=None, description="Example values")


class AgentInsight(BaseModel):
    """Insights from a specific AI agent."""
    agent_name: str = Field(description="Name of the agent")
    insight: str = Field(description="Agent's insight about the field")
    confidence: float = Field(ge=0.0, le=1.0, description="Agent's confidence in the insight")
    reasoning: str = Field(description="Explanation of the agent's reasoning")


class TargetMatch(BaseModel):
    """Represents a potential match in the target API."""
    field_name: str = Field(description="Name of the target field")
    field_path: str = Field(description="Full path to the target field")
    field_type: Optional[str] = Field(default=None, description="Target field type")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Overall confidence score")
    reasoning: str = Field(description="Why this field was matched")
    agent_insights: List[AgentInsight] = Field(default_factory=list, description="Insights from AI agents")
    semantic_similarity: float = Field(ge=0.0, le=1.0, description="Semantic similarity score")
    structural_similarity: float = Field(ge=0.0, le=1.0, description="Structural similarity score")
    context_relevance: float = Field(ge=0.0, le=1.0, description="Context relevance score")


class MappingResult(BaseModel):
    """Complete mapping result for one source field."""
    source_field: SourceField = Field(description="The source field being mapped")
    top_matches: List[TargetMatch] = Field(description="Top 3 matches for this field")
    overall_confidence: float = Field(ge=0.0, le=1.0, description="Overall mapping confidence")
    mapping_recommendation: str = Field(description="Final recommendation for mapping")
    processing_notes: Optional[str] = Field(default=None, description="Additional processing notes")


class SchemaMappingRequest(BaseModel):
    """Request model for schema mapping operation."""
    source_json_path: str = Field(description="Path to source JSON file")
    source_analysis_md_path: Optional[str] = Field(default=None, description="Path to analysis MD file")
    target_collection_name: str = Field(description="Target Qdrant collection name")
    mapping_context: Optional[str] = Field(default=None, description="Context about the mapping purpose")
    max_matches_per_field: int = Field(default=3, ge=1, le=10, description="Maximum matches per field")


class SchemaMappingReport(BaseModel):
    """Complete schema mapping report."""
    request: SchemaMappingRequest = Field(description="Original request")
    mapping_results: List[MappingResult] = Field(description="All mapping results")
    summary_statistics: Dict[str, Any] = Field(description="Summary statistics and insights")
    generated_at: datetime = Field(default_factory=datetime.now, description="Report generation timestamp")
    processing_time_seconds: Optional[float] = Field(default=None, description="Total processing time")


class CognitivePattern(BaseModel):
    """Represents a cognitive matching pattern."""
    pattern_type: str = Field(description="Type of pattern (synonym, abbreviation, etc.)")
    source_pattern: str = Field(description="Source pattern or term")
    target_pattern: str = Field(description="Target pattern or term") 
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in this pattern match")
    explanation: str = Field(description="Explanation of why this pattern applies")


class AgentConfig(BaseModel):
    """Configuration for AI agents."""
    agent_name: str = Field(description="Name of the agent")
    prompt_template: str = Field(description="Prompt template for the agent")
    max_tokens: int = Field(default=500, description="Maximum tokens for response")
    temperature: float = Field(default=0.3, ge=0.0, le=1.0, description="Temperature for generation")
    enabled: bool = Field(default=True, description="Whether this agent is enabled") 
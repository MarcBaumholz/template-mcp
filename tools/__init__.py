"""
Tools package for the MCP Template Server.

This package contains various tools for JSON analysis, RAG operations, and intelligent schema mapping.
"""

from .mapping_models import (
    SourceField,
    AgentInsight,
    TargetMatch,
    MappingResult,
    SchemaMappingRequest,
    SchemaMappingReport,
    CognitivePattern,
    AgentConfig
)

from .cognitive_matcher import CognitiveMatcher
from .ai_agents import (
    BaseAgent,
    FlipInfoAgent,
    WorldKnowledgeAgent,
    CognitiveMatchingAgent,
    MappingCoordinatorAgent
)
from .input_parser import InputParser
from .mapping import SchemaMappingTool
from .report_generator import MarkdownReportGenerator

__all__ = [
    # Data models
    "SourceField",
    "AgentInsight", 
    "TargetMatch",
    "MappingResult",
    "SchemaMappingRequest",
    "SchemaMappingReport",
    "CognitivePattern",
    "AgentConfig",
    
    # Core tools
    "CognitiveMatcher",
    "InputParser",
    "SchemaMappingTool",
    "MarkdownReportGenerator",
    
    # AI Agents
    "BaseAgent",
    "FlipInfoAgent",
    "WorldKnowledgeAgent", 
    "CognitiveMatchingAgent",
    "MappingCoordinatorAgent"
]
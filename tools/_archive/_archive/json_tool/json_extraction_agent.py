"""
Compatibility shim: Provides JsonExtractionAgent alias for FieldExtractionAgent.
This allows legacy imports (tools.json_tool.json_extraction_agent.JsonExtractionAgent)
 to work after refactor.
"""

from .json_agent import FieldExtractionAgent

# Backwards-compatible alias
JsonExtractionAgent = FieldExtractionAgent

__all__ = ["JsonExtractionAgent"] 
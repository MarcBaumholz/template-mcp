"""
Fixed Schema Mapping Tool for intelligent API field mapping.
This version uses structured RAG data instead of string-based RAG.
"""

import asyncio
import logging
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from .mapping_models import (
    SourceField, TargetMatch, MappingResult, SchemaMappingRequest, 
    SchemaMappingReport, AgentInsight
)
from .input_parser import InputParser
from .cognitive_matcher import CognitiveMatcher
from .ai_agents import FlipInfoAgent, WorldKnowledgeAgent, CognitiveMatchingAgent, MappingCoordinatorAgent
from .rag_helper import RAGHelper
from .llm_client import get_llm_response


class FixedSchemaMappingTool:
    """Fixed schema mapping tool using structured RAG data."""
    
    def __init__(self, openai_client=None, debug_dir: Optional[str] = None):
        """
        Initialize the fixed schema mapping tool.
        
        Args:
            openai_client: OpenAI client instance
            debug_dir: Directory for debug output files
        """
        self.logger = logging.getLogger("fixed_schema_mapper")
        
        # Setup debug directory
        if debug_dir:
            self.debug_dir = Path(debug_dir)
        else:
            self.debug_dir = Path("outputs") / "schema_mapping_debug"
        
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"Debug directory: {self.debug_dir}")
        
        # Initialize OpenAI client
        if openai_client:
            self.openai_client = openai_client
        else:
            api_key = os.getenv('OPENROUTER_API_KEY')
            if api_key:
                from openai import OpenAI
                self.openai_client = OpenAI(
                    api_key=api_key,
                    base_url="https://openrouter.ai/api/v1"
                )
            else:
                self.logger.warning("No OpenRouter API key - AI agents will use mock responses")
                self.openai_client = None
        
        # Initialize components
        self.input_parser = InputParser()
        self.cognitive_matcher = CognitiveMatcher()
        self.rag_helper = RAGHelper(str(self.debug_dir))
        
        # Initialize AI agents if we have OpenAI client
        if self.openai_client:
            self.flip_agent = FlipInfoAgent(self.openai_client)
            self.world_agent = WorldKnowledgeAgent(self.openai_client)
            self.cognitive_agent = CognitiveMatchingAgent(self.openai_client)
            self.coordinator_agent = MappingCoordinatorAgent(self.openai_client)
        else:
            # Use mock agents for testing
            self.flip_agent = None
            self.world_agent = None
            self.cognitive_agent = None
            self.coordinator_agent = None
        
        self.logger.info("Fixed schema mapping tool initialized")
    
    async def map_schema(self, 
                        source_json_path: str,
                        target_collection_name: str,
                        mapping_context: str,
                        source_analysis_md_path: Optional[str] = None,
                        max_matches_per_field: int = 3,
                        output_path: Optional[str] = None) -> str:
        """
        Main entry point for schema mapping.
        
        Returns:
            str: Markdown report of the mapping results
        """
        start_time = datetime.now()
        self.logger.info(f"Starting schema mapping for {source_json_path}")
        
        # Save initial mapping request info
        await self._save_md_step("01_mapping_request", {
            "source_json_path": source_json_path,
            "target_collection_name": target_collection_name,
            "mapping_context": mapping_context,
            "source_analysis_md_path": source_analysis_md_path,
            "max_matches_per_field": max_matches_per_field,
            "start_time": start_time.isoformat()
        })
        
        try:
            # Step 1: Parse input files
            self.logger.info("Step 1: Parsing input files")
            source_fields = await self._parse_inputs(source_json_path, source_analysis_md_path)
            
            if not source_fields:
                error_msg = "Failed to parse input files"
                await self._save_md_step("02_parsing_error", {"error": error_msg})
                return f"❌ Error: {error_msg}"
            
            await self._save_md_step("02_source_fields_parsed", {
                "field_count": len(source_fields),
                "fields": [{"name": f.name, "type": f.type, "description": f.description} for f in source_fields]
            })
            
            # Step 2: Find potential matches for each field using RAG
            self.logger.info("Step 2: Finding RAG matches for fields")
            mapping_results = []
            
            for i, field in enumerate(source_fields):
                self.logger.info(f"Processing field {i+1}/{len(source_fields)}: {field.name}")
                
                # Find potential matches using structured RAG
                potential_matches = await self._find_potential_matches_rag(
                    field, target_collection_name, max_matches_per_field
                )
                
                await self._save_md_step(f"03_field_{i+1:02d}_rag_matches", {
                    "field_name": field.name,
                    "matches_found": len(potential_matches),
                    "matches": [
                        {
                            "field_name": m.field_name,
                            "confidence": m.confidence_score,
                            "reasoning": m.reasoning[:100] + "..." if len(m.reasoning) > 100 else m.reasoning
                        } for m in potential_matches
                    ]
                })
                
                # Step 3: Get AI agent insights (if available)
                agent_insights = []
                if self.openai_client and potential_matches:
                    self.logger.info(f"Getting AI agent insights for {field.name}")
                    agent_insights = await self._get_agent_insights(field, potential_matches)
                    
                    await self._save_md_step(f"04_field_{i+1:02d}_agent_insights", {
                        "field_name": field.name,
                        "agent_count": len(agent_insights),
                        "insights": [
                            {
                                "agent": insight.agent_name,
                                "confidence": insight.confidence,
                                "insight": insight.insight[:100] + "..." if len(insight.insight) > 100 else insight.insight
                            } for insight in agent_insights
                        ]
                    })
                
                # Step 4: Create mapping result
                result = await self._create_mapping_result(
                    field, potential_matches, agent_insights, mapping_context
                )
                mapping_results.append(result)
            
            # Step 5: Generate final report
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            final_report = await self._generate_final_report(
                mapping_results, processing_time, mapping_context
            )
            
            await self._save_md_step("05_final_report", {
                "processing_time_seconds": processing_time,
                "total_fields": len(source_fields),
                "successful_mappings": len([r for r in mapping_results if r.top_matches])
            })
            
            self.logger.info(f"Schema mapping completed in {processing_time:.2f} seconds")
            return final_report
            
        except Exception as e:
            error_msg = f"Schema mapping failed: {str(e)}"
            self.logger.error(error_msg)
            await self._save_md_step("error_final", {"error": error_msg})
            return f"❌ {error_msg}"
    
    async def _parse_inputs(self, source_json_path: str, source_analysis_md_path: Optional[str]) -> List[SourceField]:
        """Parse input JSON and optional markdown files."""
        try:
            # Parse JSON file
            json_fields = self.input_parser.parse_json_file(source_json_path)
            if not json_fields:
                self.logger.warning("No fields found in JSON file")
                return []
            
            # Parse markdown analysis if provided
            if source_analysis_md_path:
                md_analysis = self.input_parser.parse_markdown_analysis(source_analysis_md_path)
                return self.input_parser.merge_json_and_analysis(json_fields, md_analysis)
            else:
                return json_fields
                
        except Exception as e:
            self.logger.error(f"Input parsing failed: {e}")
            return []
    
    async def _find_potential_matches_rag(self, 
                                        source_field: SourceField, 
                                        collection_name: str, 
                                        max_matches: int) -> List[TargetMatch]:
        """Find potential matches using structured RAG helper."""
        try:
            # Use RAG helper to find structured matches
            rag_results = self.rag_helper.search_field_matches(
                field_name=source_field.name,
                field_type=source_field.type,
                field_description=source_field.description,
                collection_name=collection_name,
                max_results=max_matches
            )
            
            # Convert RAG results to TargetMatch objects
            target_matches = []
            
            for result in rag_results:
                # Extract field name from the result text
                field_name = self._extract_field_name_from_rag_result(result)
                
                target_match = TargetMatch(
                    field_name=field_name,
                    field_path=result.get('metadata', {}).get('path', field_name),
                    field_type=result.get('metadata', {}).get('type', 'unknown'),
                    confidence_score=result.get('weighted_score', result.get('score', 0.0)),
                    reasoning=f"RAG match (strategy: {result.get('query_strategy', 'unknown')}, score: {result.get('score', 0):.3f})",
                    agent_insights=[],  # Will be filled by agents
                    semantic_similarity=result.get('score', 0.0),
                    structural_similarity=0.5,  # Default value
                    context_relevance=result.get('weighted_score', result.get('score', 0.0))
                )
                
                target_matches.append(target_match)
            
            return target_matches
            
        except Exception as e:
            self.logger.error(f"Failed to find RAG matches: {e}")
            return []
    
    def _extract_field_name_from_rag_result(self, rag_result: Dict) -> str:
        """Extract a meaningful field name from RAG result."""
        text = rag_result.get('text', '')
        metadata = rag_result.get('metadata', {})
        
        # Try to get field name from metadata first
        if 'field_name' in metadata:
            return metadata['field_name']
        
        # Try to extract from path
        if 'path' in metadata:
            path = metadata['path']
            # Look for path parameters like {id}, {employee_id}
            import re
            path_params = re.findall(r'\{([^}]+)\}', path)
            if path_params:
                return path_params[0]
        
        # Fallback: extract from text
        if 'Parameters:' in text:
            params_part = text.split('Parameters:')[1].split('\n')[0].strip()
            if params_part:
                return params_part.split(',')[0].strip()
        
        # Final fallback
        return metadata.get('path', 'unknown_field').replace('/', '_').replace('{', '').replace('}', '')
    
    async def _get_agent_insights(self, 
                                source_field: SourceField, 
                                potential_matches: List[TargetMatch]) -> List[AgentInsight]:
        """Get insights from AI agents (simplified for now)."""
        insights = []
        
        if not self.openai_client:
            # Mock insight for testing
            insights.append(AgentInsight(
                agent_name="MockAgent",
                insight="Mock analysis - configure OpenRouter API key for real insights",
                confidence=0.7,
                reasoning="Mock reasoning for testing purposes"
            ))
            return insights
        
        try:
            # For now, just use a simple LLM call instead of complex agents
            prompt = f"""
            Analyze this field mapping scenario:
            
            Source field: {source_field.name} (type: {source_field.type})
            Description: {source_field.description}
            
            Potential matches from API:
            {chr(10).join([f"- {m.field_name}: {m.reasoning}" for m in potential_matches[:3]])}
            
            Provide a brief analysis of the best match and confidence level (0.0-1.0).
            Format: Best match: [field_name] | Confidence: [0.0-1.0] | Reason: [brief explanation]
            """
            
            response = get_llm_response(prompt, max_tokens=200)
            
            insights.append(AgentInsight(
                agent_name="SimplifiedAgent",
                insight=response[:100] + "..." if len(response) > 100 else response,
                confidence=0.7,  # Default confidence
                reasoning=response
            ))
            
        except Exception as e:
            self.logger.warning(f"Agent insights failed: {e}")
        
        return insights
    
    async def _create_mapping_result(self, 
                                   source_field: SourceField,
                                   potential_matches: List[TargetMatch],
                                   agent_insights: List[AgentInsight],
                                   mapping_context: str) -> MappingResult:
        """Create final mapping result."""
        
        # Add agent insights to matches
        for match in potential_matches:
            match.agent_insights = agent_insights
        
        # Calculate overall confidence
        if potential_matches:
            overall_confidence = potential_matches[0].confidence_score
            if agent_insights:
                agent_confidence = sum(insight.confidence for insight in agent_insights) / len(agent_insights)
                overall_confidence = (overall_confidence + agent_confidence) / 2
        else:
            overall_confidence = 0.0
        
        # Generate recommendation
        if potential_matches and overall_confidence > 0.7:
            recommendation = f"High confidence: {potential_matches[0].field_name}"
        elif potential_matches and overall_confidence > 0.5:
            recommendation = f"Moderate confidence: {potential_matches[0].field_name}"
        elif potential_matches:
            recommendation = f"Low confidence: {potential_matches[0].field_name}"
        else:
            recommendation = "No suitable match found"
        
        return MappingResult(
            source_field=source_field,
            top_matches=potential_matches,
            overall_confidence=overall_confidence,
            mapping_recommendation=recommendation,
            processing_notes=f"Processed with {len(potential_matches)} RAG matches and {len(agent_insights)} agent insights"
        )
    
    async def _generate_final_report(self, 
                                   mapping_results: List[MappingResult],
                                   processing_time: float,
                                   mapping_context: str) -> str:
        """Generate final markdown report."""
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = f"""# 🎯 Schema Mapping Results

**Generated:** {timestamp}  
**Processing Time:** {processing_time:.2f} seconds  
**Context:** {mapping_context}  

## 📊 Summary Statistics

- **Total Fields Analyzed:** {len(mapping_results)}
- **Successful Mappings:** {len([r for r in mapping_results if r.top_matches])}
- **High Confidence:** {len([r for r in mapping_results if r.overall_confidence > 0.7])}
- **Medium Confidence:** {len([r for r in mapping_results if 0.5 < r.overall_confidence <= 0.7])}
- **Low Confidence:** {len([r for r in mapping_results if 0.3 < r.overall_confidence <= 0.5])}

## 🔍 Field Mapping Results

"""
        
        for i, result in enumerate(mapping_results, 1):
            confidence_emoji = "🟢" if result.overall_confidence > 0.7 else "🟡" if result.overall_confidence > 0.5 else "🔴"
            
            report += f"""### {i}. {result.source_field.name} {confidence_emoji}

**Recommendation:** {result.mapping_recommendation}  
**Confidence:** {result.overall_confidence:.2f}  
**Type:** {result.source_field.type}  
**Description:** {result.source_field.description}  

"""
            if result.top_matches:
                report += "**Top Matches:**\n"
                for j, match in enumerate(result.top_matches[:3], 1):
                    report += f"{j}. `{match.field_name}` (score: {match.confidence_score:.3f}) - {match.reasoning}\n"
                report += "\n"
            else:
                report += "No matches found.\n\n"
        
        report += f"""
---
*Generated by Fixed Schema Mapping Tool - Debug files saved to: {self.debug_dir}*
"""
        
        return report
    
    async def _save_md_step(self, step_name: str, data: Dict[str, Any]) -> None:
        """Save a mapping step to markdown file."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{step_name}_{timestamp}.md"
            filepath = self.debug_dir / filename
            
            # Convert data to markdown
            md_content = f"# {step_name.replace('_', ' ').title()}\n\n"
            md_content += f"**Timestamp:** {timestamp}\n\n"
            
            for key, value in data.items():
                md_content += f"## {key.replace('_', ' ').title()}\n\n"
                if isinstance(value, (list, dict)):
                    md_content += f"```json\n{json.dumps(value, indent=2, ensure_ascii=False)}\n```\n\n"
                else:
                    md_content += f"{value}\n\n"
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            self.logger.debug(f"Step saved: {filepath}")
            
        except Exception as e:
            self.logger.warning(f"Failed to save step {step_name}: {e}") 
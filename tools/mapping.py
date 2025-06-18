"""
Main Schema Mapping Tool for intelligent API field mapping.
Orchestrates all components to provide AI-powered field mapping recommendations.
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from openai import OpenAI
import re

from .mapping_models import (
    SourceField, TargetMatch, MappingResult, SchemaMappingRequest, 
    SchemaMappingReport, AgentInsight
)
from .input_parser import InputParser
from .cognitive_matcher import CognitiveMatcher
from .ai_agents import FlipInfoAgent, WorldKnowledgeAgent, CognitiveMatchingAgent, MappingCoordinatorAgent
from .rag_tools import retrieve_from_rag  # Import from existing RAG tools


class SchemaMappingTool:
    """Main tool for intelligent schema mapping using multi-agent AI system."""
    
    def __init__(self, openai_client: Optional[OpenAI] = None):
        """
        Initialize the schema mapping tool.
        
        Args:
            openai_client: OpenAI client instance
        """
        self.logger = logging.getLogger("schema_mapper")
        
        # Initialize OpenAI client
        if openai_client:
            self.openai_client = openai_client
        else:
            api_key = os.getenv('OPENROUTER_API_KEY')
            if not api_key:
                raise ValueError("OPENROUTER_API_KEY environment variable is required")
            
            self.openai_client = OpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1"
            )
        
        # Initialize components
        self.input_parser = InputParser()
        self.cognitive_matcher = CognitiveMatcher()
        
        # Initialize AI agents
        self.flip_agent = FlipInfoAgent(self.openai_client)
        self.world_agent = WorldKnowledgeAgent(self.openai_client)
        self.cognitive_agent = CognitiveMatchingAgent(self.openai_client)
        self.coordinator_agent = MappingCoordinatorAgent(self.openai_client)
        
        self.logger.info("Schema mapping tool initialized successfully")
    
    async def map_schema(self, request: SchemaMappingRequest) -> SchemaMappingReport:
        """
        Main entry point for schema mapping.
        
        Args:
            request: Schema mapping request with all parameters
            
        Returns:
            SchemaMappingReport: Complete mapping report with results
        """
        start_time = datetime.now()
        self.logger.info(f"Starting schema mapping for {request.source_json_path}")
        
        try:
            # Step 1: Parse input files
            source_fields = await self._parse_inputs(request)
            if not source_fields:
                return self._create_error_report(request, "Failed to parse input files", start_time)
            
            # Step 2: Find potential matches for each field
            mapping_results = []
            
            for field in source_fields:
                self.logger.info(f"Processing field: {field.name}")
                
                # Find potential matches using RAG
                potential_matches = await self._find_potential_matches(
                    field, request.target_collection_name, request.max_matches_per_field
                )
                
                if not potential_matches:
                    # Create empty result for fields with no matches
                    result = MappingResult(
                        source_field=field,
                        top_matches=[],
                        overall_confidence=0.0,
                        mapping_recommendation="No suitable matches found",
                        processing_notes="No potential matches discovered in target API"
                    )
                    mapping_results.append(result)
                    continue
                
                # Step 3: Get AI agent insights
                agent_insights = await self._get_agent_insights(field, potential_matches)
                
                # Step 4: Create mapping result
                result = await self._create_mapping_result(
                    field, potential_matches, agent_insights, request.mapping_context
                )
                mapping_results.append(result)
            
            # Step 5: Generate final report
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            report = SchemaMappingReport(
                request=request,
                mapping_results=mapping_results,
                summary_statistics=self._calculate_summary_stats(mapping_results),
                generated_at=end_time,
                processing_time_seconds=processing_time
            )
            
            self.logger.info(f"Schema mapping completed in {processing_time:.2f} seconds")
            return report
            
        except Exception as e:
            self.logger.error(f"Schema mapping failed: {e}")
            return self._create_error_report(request, str(e), start_time)
    
    async def _parse_inputs(self, request: SchemaMappingRequest) -> List[SourceField]:
        """Parse input JSON and markdown files."""
        try:
            # Parse JSON file
            json_fields = self.input_parser.parse_json_file(request.source_json_path)
            if not json_fields:
                self.logger.warning("No fields found in JSON file")
                return []
            
            # Parse markdown analysis if provided
            if request.source_analysis_md_path:
                md_analysis = self.input_parser.parse_markdown_analysis(request.source_analysis_md_path)
                # Merge JSON and markdown data
                return self.input_parser.merge_json_and_analysis(json_fields, md_analysis)
            else:
                return json_fields
                
        except Exception as e:
            self.logger.error(f"Input parsing failed: {e}")
            return []
    
    async def _find_potential_matches(self, 
                                    source_field: SourceField, 
                                    collection_name: str, 
                                    max_matches: int) -> List[TargetMatch]:
        """Find potential matches using RAG system and cognitive matching."""
        try:
            # Create search query from field information
            search_query = self._create_search_query(source_field)
            
            # Query RAG system using existing function
            rag_results = retrieve_from_rag(
                query=search_query,
                collection_name=collection_name,
                limit=max_matches * 2,  # Get more for filtering
                score_threshold=0.3
            )
            
            if not rag_results:
                return []
            
            # Convert RAG results to TargetMatch objects
            target_matches = []
            
            for match in rag_results[:max_matches]:
                # Skip error results
                if 'error' in match:
                    continue
                    
                # Extract field information from RAG text and metadata
                metadata = match.get('metadata', {})
                text = match.get('text', '')
                
                # Try to extract field name from text (simple parsing)
                field_name = self._extract_field_name_from_text(text)
                
                # Calculate cognitive similarity
                cognitive_score = self.cognitive_matcher.calculate_similarity_score(
                    source_field.name, 
                    field_name
                )
                
                # Find cognitive patterns
                patterns = self.cognitive_matcher.find_cognitive_patterns(
                    source_field.name,
                    field_name
                )
                
                target_match = TargetMatch(
                    field_name=field_name,
                    field_path=metadata.get('path', f'{field_name}'),
                    field_type=metadata.get('type', 'unknown'),
                    confidence_score=cognitive_score,
                    reasoning=f"RAG similarity: {match.get('score', 0):.3f}, Cognitive: {cognitive_score:.3f}",
                    agent_insights=[],  # Will be filled by agents
                    semantic_similarity=match.get('score', 0),
                    structural_similarity=cognitive_score,
                    context_relevance=0.5  # Default value
                )
                
                target_matches.append(target_match)
            
            # Sort by combined score
            target_matches.sort(
                key=lambda x: (x.semantic_similarity + x.structural_similarity) / 2, 
                reverse=True
            )
            
            return target_matches[:max_matches]
            
        except Exception as e:
            self.logger.error(f"Failed to find potential matches: {e}")
            return []
    
    async def _get_agent_insights(self, 
                                source_field: SourceField, 
                                potential_matches: List[TargetMatch]) -> List[AgentInsight]:
        """Get insights from all AI agents."""
        insights = []
        
        try:
            # Gather insights from all agents concurrently
            agent_tasks = [
                self.flip_agent.analyze(source_field, potential_matches),
                self.world_agent.analyze(source_field, potential_matches),
                self.cognitive_agent.analyze(source_field, potential_matches)
            ]
            
            agent_results = await asyncio.gather(*agent_tasks, return_exceptions=True)
            
            # Process results and filter out exceptions
            for result in agent_results:
                if isinstance(result, AgentInsight):
                    insights.append(result)
                elif isinstance(result, Exception):
                    self.logger.warning(f"Agent analysis failed: {result}")
            
            # Get coordinator synthesis
            if insights:
                coordinator_insight = await self.coordinator_agent.synthesize_insights(
                    source_field, potential_matches, insights
                )
                insights.append(coordinator_insight)
            
        except Exception as e:
            self.logger.error(f"Failed to get agent insights: {e}")
        
        return insights
    
    async def _create_mapping_result(self, 
                                   source_field: SourceField,
                                   potential_matches: List[TargetMatch],
                                   agent_insights: List[AgentInsight],
                                   mapping_context: str) -> MappingResult:
        """Create final mapping result with agent insights."""
        
        # Add agent insights to matches
        for match in potential_matches:
            match.agent_insights = [
                insight for insight in agent_insights 
                if insight.agent_name != "MappingCoordinatorAgent"
            ]
        
        # Calculate overall confidence
        if agent_insights:
            confidence_scores = [insight.confidence for insight in agent_insights]
            overall_confidence = sum(confidence_scores) / len(confidence_scores)
        else:
            overall_confidence = potential_matches[0].confidence_score if potential_matches else 0.0
        
        # Generate recommendation
        if potential_matches and overall_confidence > 0.7:
            recommendation = f"High confidence match: {potential_matches[0].field_name}"
        elif potential_matches and overall_confidence > 0.5:
            recommendation = f"Moderate confidence match: {potential_matches[0].field_name}"
        elif potential_matches:
            recommendation = f"Low confidence match: {potential_matches[0].field_name}"
        else:
            recommendation = "No suitable match found"
        
        # Processing notes
        notes = f"Analyzed {len(potential_matches)} potential matches with {len(agent_insights)} agent insights"
        if mapping_context:
            notes += f". Context: {mapping_context[:100]}..."
        
        return MappingResult(
            source_field=source_field,
            top_matches=potential_matches,
            overall_confidence=overall_confidence,
            mapping_recommendation=recommendation,
            processing_notes=notes
        )
    
    def _create_search_query(self, source_field: SourceField) -> str:
        """Create optimized search query for RAG system."""
        query_parts = [source_field.name]
        
        if source_field.description:
            query_parts.append(source_field.description)
        
        if source_field.type:
            query_parts.append(f"type:{source_field.type}")
        
        # Add synonyms and variations
        normalized_name = source_field.name.lower()
        if 'employee' in normalized_name or 'emp' in normalized_name:
            query_parts.append("employee staff user person")
        elif 'department' in normalized_name or 'dept' in normalized_name:
            query_parts.append("department division team unit")
        elif 'id' in normalized_name:
            query_parts.append("identifier key uuid number")
        
        return " ".join(query_parts)
    
    def _extract_field_name_from_text(self, text: str) -> str:
        """Extract field name from text using simple parsing."""
        # Look for common patterns in API documentation
        patterns = [
            r'"([a-zA-Z_][a-zA-Z0-9_]*)"',  # Quoted field names
            r'field:\s*([a-zA-Z_][a-zA-Z0-9_]*)',  # "field: name"
            r'property:\s*([a-zA-Z_][a-zA-Z0-9_]*)',  # "property: name"
            r'parameter:\s*([a-zA-Z_][a-zA-Z0-9_]*)',  # "parameter: name"
            r'`([a-zA-Z_][a-zA-Z0-9_]*)`',  # Backtick quoted
            r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b'  # General word pattern
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Return the first reasonable match
                for match in matches:
                    if len(match) >= 2 and not match.lower() in ['the', 'and', 'for', 'this', 'that']:
                        return match
        
        # Fallback: return first few words
        words = text.split()[:3]
        return "_".join(words) if words else "unknown_field"
    
    def _calculate_summary_stats(self, results: List[MappingResult]) -> Dict[str, Any]:
        """Calculate summary statistics for the mapping results."""
        if not results:
            return {"total_fields": 0, "matched_fields": 0, "average_confidence": 0.0}
        
        total_fields = len(results)
        matched_fields = len([r for r in results if r.top_matches])
        confidences = [r.overall_confidence for r in results if r.overall_confidence > 0]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        return {
            "total_fields": total_fields,
            "matched_fields": matched_fields,
            "match_rate": matched_fields / total_fields if total_fields > 0 else 0.0,
            "average_confidence": avg_confidence,
            "high_confidence_matches": len([c for c in confidences if c > 0.7]),
            "moderate_confidence_matches": len([c for c in confidences if 0.5 < c <= 0.7]),
            "low_confidence_matches": len([c for c in confidences if 0.3 < c <= 0.5])
        }
    
    def _create_error_report(self, 
                           request: SchemaMappingRequest, 
                           error_message: str, 
                           start_time: datetime) -> SchemaMappingReport:
        """Create error report when mapping fails."""
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        return SchemaMappingReport(
            request=request,
            mapping_results=[],
            summary_statistics={"error": error_message, "total_fields": 0},
            generated_at=end_time,
            processing_time_seconds=processing_time
        )

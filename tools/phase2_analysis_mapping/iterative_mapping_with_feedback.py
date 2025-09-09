"""
Iterative Mapping System with Feedback Loop (ReAct only)

This module focuses strictly on the ReAct pattern (Think → Act → Observe)
for field mapping. It delegates retrieval (RAG) and verification to existing
tools and avoids duplicating reflection/verification logic.
"""

import json
import logging
from tools.phase2_analysis_mapping.verify_api_specification import (
    get_verifier_instance,
)
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from tools.phase1_data_extraction.upload_api_specification import get_rag_system
from tools.shared_utilities.llm_client import get_llm_response

logger = logging.getLogger(__name__)


# Configuration
MAX_ITERATIONS: int = 5
CONFIDENCE_GOOD_THRESHOLD: float = 0.7
FALLBACK_THRESHOLD: float = 0.3

@dataclass
class MappingIteration:
    """Represents one iteration in the mapping process."""
    iteration: int
    thought: str
    action: Dict[str, Any]
    observation: Dict[str, Any]
    success: bool
    confidence: float


@dataclass
class MappingResult:
    """Final result of iterative mapping."""
    source_field: str
    target_field: str
    confidence: float
    iterations: int
    history: List[MappingIteration]
    final_mapping: Dict[str, Any]
    validation_score: float


class LiveAPIValidator:
    """Deprecated: Live HTTP validation is not part of minimal ReAct agent.

    Kept for backward compatibility in type hints; not used anymore. Use
    APISpecVerifier from verify_api_specification for observation.
    """
    def __init__(self, api_spec_path: str):
        self.api_spec_path = api_spec_path


class ReActMappingAgent:
    """ReAct-based mapping agent (Think-Act-Observe pattern)."""
    
    def __init__(self, rag_system, verifier, api_spec: Dict[str, Any]):
        self.rag = rag_system
        self.verifier = verifier
        self.api_spec = api_spec
        self.history: List[MappingIteration] = []
        self.max_iterations = MAX_ITERATIONS
    
    def _think(self, source_field: str, target_collection: str, iteration: int) -> str:
        """Think phase: Analyze and plan next action."""
        
        # Build context from history
        history_context = ""
        if self.history:
            history_context = "\n\nPrevious attempts:\n"
            for hist in self.history[-2:]:  # Last 2 attempts
                history_context += f"- Thought: {hist.thought}\n"
                history_context += f"- Action: {hist.action}\n"
                history_context += f"- Result: {hist.observation}\n"
        
        # Get RAG results
        rag_results = self.rag.enhanced_query(source_field, target_collection, limit=3)
        
        prompt = f"""
        You are an expert API field mapping agent using the ReAct pattern.
        
        TASK: Map the source field '{source_field}' to the best matching field in the target API.
        
        CURRENT ITERATION: {iteration + 1}/{self.max_iterations}
        
        RAG ANALYSIS RESULTS:
        {json.dumps(rag_results, indent=2)}
        
        {history_context}
        
        THINK: Analyze the current situation and plan your next action.
        Consider:
        1. What have we learned from previous attempts?
        2. What is the best field match based on RAG results?
        3. How should we test this mapping?
        
        Provide your reasoning in 2-3 sentences.
        """
        
        return get_llm_response(prompt, max_tokens=200, tool_name="iterative_mapping_think")
    
    def _act(self, thought: str, source_field: str, target_collection: str) -> Dict[str, Any]:
        """Act phase: Execute the planned action."""
        
        prompt = f"""
        Based on your analysis: {thought}
        
        Execute the mapping action for field '{source_field}'.
        
        Return a JSON object with:
        {{
            "target_field": "best_matching_field_name",
            "confidence": 0.95,
            "reasoning": "why this field matches",
            "test_strategy": "how to validate this mapping"
        }}
        
        Focus on the most promising field match from the RAG results.
        """
        
        try:
            response = get_llm_response(prompt, max_tokens=300, tool_name="iterative_mapping_act")
            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start != -1 and json_end != 0:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            else:
                # Fallback if no JSON found
                return {
                    "target_field": source_field,
                    "confidence": 0.5,
                    "reasoning": "Fallback mapping",
                    "test_strategy": "direct validation"
                }
        except Exception as e:
            logger.error(f"Failed to parse action response: {e}")
            return {
                "target_field": source_field,
                "confidence": 0.3,
                "reasoning": "Error in action parsing",
                "test_strategy": "basic validation"
            }
    
    def _observe(self, action: Dict[str, Any], source_field: str) -> Dict[str, Any]:
        """Observe phase: Validate the action and get feedback."""
        
        target_field = action.get('target_field', source_field)
        
        # Spec-based verification (no HTTP)
        try:
            ver = self.verifier.verify_field_mapping(target_field, self.api_spec, "comprehensive")
            validation_result = {
                'success': bool(ver.found),
                'validation_score': float(ver.confidence or 0.0),
                'endpoint_used': ver.api_path or ver.schema_path,
                'method_used': None,
                'status_code': None,
                'response_data': None,
            }
        except Exception as e:
            validation_result = {
                'success': False,
                'validation_score': 0.0,
                'error': f'Spec verification failed: {str(e)}'
            }
        
        # Enhanced observation with LLM analysis
        prompt = f"""
        Analyze the validation result for mapping '{source_field}' -> '{target_field}':
        
        VALIDATION RESULT:
        {json.dumps(validation_result, indent=2)}
        
        ACTION TAKEN:
        {json.dumps(action, indent=2)}
        
        Provide observation analysis:
        1. Was the mapping successful?
        2. What can we learn from this result?
        3. What should we try next?
        
        Return JSON: {{"success": true/false, "learning": "...", "next_strategy": "..."}}
        """
        
        try:
            observation_analysis = get_llm_response(prompt, max_tokens=200, tool_name="iterative_mapping_observe")
            json_start = observation_analysis.find('{')
            json_end = observation_analysis.rfind('}') + 1
            if json_start != -1 and json_end != 0:
                analysis = json.loads(observation_analysis[json_start:json_end])
            else:
                analysis = {"success": validation_result.get('success', False), "learning": "Basic validation", "next_strategy": "Continue"}
        except:
            analysis = {"success": validation_result.get('success', False), "learning": "Basic validation", "next_strategy": "Continue"}
        
        return {
            **validation_result,
            **analysis
        }
    
    def map_with_react(self, source_field: str, target_collection: str) -> MappingResult:
        """Map a field using the ReAct pattern."""
        
        self.history = []
        best_mapping = None
        best_confidence = 0.0
        
        for iteration in range(self.max_iterations):
            # 1. THINK: Analyze and plan
            thought = self._think(source_field, target_collection, iteration)
            
            # 2. ACT: Execute mapping
            action = self._act(thought, source_field, target_collection)
            
            # 3. OBSERVE: Validate and get feedback
            observation = self._observe(action, source_field)
            
            # Record iteration
            iteration_record = MappingIteration(
                iteration=iteration,
                thought=thought,
                action=action,
                observation=observation,
                success=observation.get('success', False),
                confidence=action.get('confidence', 0.0)
            )
            self.history.append(iteration_record)
            
            # Update best mapping if this is better
            current_confidence = action.get('confidence', 0.0) * observation.get('validation_score', 0.0)
            if current_confidence > best_confidence:
                best_confidence = current_confidence
                best_mapping = {
                    'target_field': action.get('target_field'),
                    'confidence': action.get('confidence', 0.0),
                    'validation_score': observation.get('validation_score', 0.0),
                    'iteration': iteration
                }
            
            # Check if we've found a good mapping
            if observation.get('success', False) and current_confidence > CONFIDENCE_GOOD_THRESHOLD:
                break
        
        # Return final result
        return MappingResult(
            source_field=source_field,
            target_field=best_mapping.get('target_field', source_field) if best_mapping else source_field,
            confidence=best_confidence,
            iterations=len(self.history),
            history=self.history,
            final_mapping=best_mapping or {},
            validation_score=best_mapping.get('validation_score', 0.0) if best_mapping else 0.0
        )


class IterativeMappingSystem:
    """Main system for iterative field mapping with feedback loop."""
    
    def __init__(self, api_spec_path: str):
        self.rag_system = get_rag_system()
        self.verifier = get_verifier_instance()
        try:
            self.api_spec = self.verifier.load_api_spec(api_spec_path)
        except Exception as e:
            raise RuntimeError(f"Failed to load API spec: {str(e)}")
        self.agent = ReActMappingAgent(self.rag_system, self.verifier, self.api_spec)
    
    def iterative_field_mapping(
        self, 
        source_fields: List[str], 
        target_collection: str,
        output_path: Optional[str] = None
    ) -> Dict[str, MappingResult]:
        """Perform iterative mapping for multiple fields."""
        
        results = {}
        
        for field in source_fields:
            logger.info(f"Starting iterative mapping for field: {field}")
            
            # ReAct-based mapping
            mapping_result = self.agent.map_with_react(field, target_collection)
            
            # Fallback to traditional RAG if ReAct failed
            if mapping_result.confidence < FALLBACK_THRESHOLD:
                logger.info(f"ReAct mapping failed for {field}, using fallback RAG")
                fallback_result = self.rag_system.enhanced_query(field, target_collection, limit=1)
                if fallback_result and 'error' not in fallback_result[0]:
                    mapping_result.target_field = fallback_result[0].get('text', field)
                    mapping_result.confidence = 0.5
                    mapping_result.final_mapping['method'] = 'fallback_rag'
            
            results[field] = mapping_result
        
        # Save results if output path provided
        if output_path:
            self._save_mapping_results(results, output_path)
        
        return results
    
    def _save_mapping_results(self, results: Dict[str, MappingResult], output_path: str):
        """Save mapping results to file."""
        try:
            output_dir = Path(output_path)
            output_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"iterative_mapping_results_{timestamp}.json"
            filepath = output_dir / filename
            
            # Convert results to serializable format
            serializable_results = {}
            for field, result in results.items():
                serializable_results[field] = {
                    'source_field': result.source_field,
                    'target_field': result.target_field,
                    'confidence': result.confidence,
                    'iterations': result.iterations,
                    'validation_score': result.validation_score,
                    'final_mapping': result.final_mapping,
                    'history': [
                        {
                            'iteration': h.iteration,
                            'thought': h.thought,
                            'action': h.action,
                            'observation': h.observation,
                            'success': h.success,
                            'confidence': h.confidence
                        }
                        for h in result.history
                    ]
                }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(serializable_results, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Mapping results saved to: {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to save mapping results: {e}")


# Public API functions
def iterative_field_mapping(
    source_fields: List[str],
    target_collection: str,
    api_spec_path: str,
    output_path: Optional[str] = None
) -> str:
    """
    Perform iterative field mapping with feedback loop.
    
    Args:
        source_fields: List of source field names to map
        target_collection: RAG collection name for target API
        api_spec_path: Path to OpenAPI specification for live validation
        output_path: Optional path to save results
    
    Returns:
        JSON string with mapping results
    """
    try:
        mapping_system = IterativeMappingSystem(api_spec_path)
        results = mapping_system.iterative_field_mapping(source_fields, target_collection, output_path)
        
        # Format results for display
        summary = f"# Iterative Mapping Results\n\n"
        summary += f"**Fields Mapped:** {len(results)}\n"
        summary += f"**API Spec:** {api_spec_path}\n"
        summary += f"**Target Collection:** {target_collection}\n\n"
        
        for field, result in results.items():
            summary += f"## {field}\n"
            summary += f"- **Target Field:** {result.target_field}\n"
            summary += f"- **Confidence:** {result.confidence:.3f}\n"
            summary += f"- **Iterations:** {result.iterations}\n"
            summary += f"- **Validation Score:** {result.validation_score:.3f}\n"
            summary += f"- **Success:** {'✅' if result.confidence > 0.5 else '❌'}\n\n"
            
            if result.history:
                summary += f"### Mapping History\n"
                for i, hist in enumerate(result.history):
                    summary += f"**Iteration {i+1}:**\n"
                    summary += f"- Thought: {hist.thought[:100]}...\n"
                    summary += f"- Action: {hist.action.get('target_field', 'N/A')}\n"
                    summary += f"- Success: {hist.success}\n\n"
        
        if output_path:
            summary += f"\n📄 Results saved to: {output_path}"
        
        return summary
        
    except Exception as e:
        return f"❌ Iterative mapping failed: {str(e)}"


def test_iterative_mapping() -> str:
    """Test the iterative mapping system."""
    try:
        # Test with sample data
        test_fields = ["employee_id", "start_date", "status"]
        test_collection = "test_collection"
        test_api_spec = "sample_data/sample_hr_api.json"
        
        result = iterative_field_mapping(
            source_fields=test_fields,
            target_collection=test_collection,
            api_spec_path=test_api_spec,
            output_path="./outputs"
        )
        
        return f"✅ Iterative mapping test completed\n\n{result}"
        
    except Exception as e:
        return f"❌ Test failed: {str(e)}" 
"""
Multi-agent system for intelligent schema mapping.
Each agent has specialized knowledge and reasoning capabilities.
"""

import json
import logging
import os
from typing import List, Dict, Any, Optional
from openai import OpenAI
from .mapping_models import AgentInsight, AgentConfig, SourceField, TargetMatch


class BaseAgent:
    """Base class for all AI agents."""
    
    def __init__(self, client: OpenAI, config: AgentConfig):
        """Initialize base agent with OpenAI client and configuration."""
        self.client = client
        self.config = config
        self.logger = logging.getLogger(f"agent.{config.agent_name}")
    
    async def analyze(self, source_field: SourceField, potential_matches: List[TargetMatch]) -> AgentInsight:
        """Base analysis method to be overridden by specific agents."""
        raise NotImplementedError("Subclasses must implement analyze method")
    
    def _make_llm_call(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """Make a call to the LLM with error handling."""
        try:
            # Use free model from environment variables
            model = os.getenv('OPENROUTER_MODEL', 'deepseek/deepseek-r1-0528-qwen3-8b:free')
            
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens or self.config.max_tokens,
                temperature=self.config.temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"LLM call failed: {e}")
            return f"Error: {str(e)}"


class FlipInfoAgent(BaseAgent):
    """Agent specialized in Flip company domain knowledge."""
    
    def __init__(self, client: OpenAI):
        """Initialize FlipInfoAgent with domain-specific configuration."""
        config = AgentConfig(
            agent_name="FlipInfoAgent",
            prompt_template="flip_analysis",
            max_tokens=500,
            temperature=0.3,
            enabled=True
        )
        super().__init__(client, config)
        
        # Flip-specific domain knowledge
        self.flip_context = {
            "business_model": "HR platform for employee management",
            "core_entities": ["employees", "departments", "positions", "managers"],
            "key_processes": ["onboarding", "performance", "payroll", "termination"],
            "data_patterns": ["hierarchical org structure", "temporal employment data"]
        }
    
    async def analyze(self, source_field: SourceField, potential_matches: List[TargetMatch]) -> AgentInsight:
        """Analyze field mapping from Flip business domain perspective."""
        
        # Create context about potential matches
        matches_context = "\n".join([
            f"- {match.field_name}: {match.reasoning} (confidence: {match.confidence_score:.2f})"
            for match in potential_matches[:3]  # Top 3 matches
        ])
        
        prompt = f"""
As a Flip HR platform domain expert, analyze this field mapping scenario:

SOURCE FIELD: {source_field.name}
- Type: {source_field.type}
- Description: {source_field.description}
- Context: {source_field.context}

POTENTIAL MATCHES:
{matches_context}

Given Flip's HR platform context:
- Business model: {self.flip_context['business_model']}
- Core entities: {', '.join(self.flip_context['core_entities'])}
- Key processes: {', '.join(self.flip_context['key_processes'])}

Provide insights on:
1. Which match best fits Flip's HR domain model?
2. Are there any Flip-specific considerations?
3. What business logic might be affected?

Respond with a JSON object containing:
{{
    "best_match": "field_name",
    "confidence": 0.85,
    "reasoning": "detailed explanation",
    "business_impact": "potential impact description",
    "flip_considerations": "Flip-specific notes"
}}
"""
        
        try:
            response = self._make_llm_call(prompt)
            
            # Try to parse JSON response
            try:
                analysis = json.loads(response)
                reasoning = f"Flip Domain Analysis: {analysis.get('reasoning', 'No reasoning provided')}"
                if analysis.get('business_impact'):
                    reasoning += f" Business Impact: {analysis['business_impact']}"
                
                return AgentInsight(
                    agent_name=self.config.agent_name,
                    insight=analysis.get('best_match', 'No recommendation'),
                    confidence=float(analysis.get('confidence', 0.5)),
                    reasoning=reasoning
                )
            except json.JSONDecodeError:
                # Fallback to text analysis
                return AgentInsight(
                    agent_name=self.config.agent_name,
                    insight="Text analysis fallback",
                    confidence=0.6,
                    reasoning=f"Flip domain analysis: {response[:200]}..."
                )
                
        except Exception as e:
            self.logger.error(f"FlipInfoAgent analysis failed: {e}")
            return AgentInsight(
                agent_name=self.config.agent_name,
                insight="Analysis failed",
                confidence=0.0,
                reasoning=f"Error in Flip domain analysis: {str(e)}"
            )


class WorldKnowledgeAgent(BaseAgent):
    """Agent with broad world knowledge for general field understanding."""
    
    def __init__(self, client: OpenAI):
        """Initialize WorldKnowledgeAgent."""
        config = AgentConfig(
            agent_name="WorldKnowledgeAgent",
            prompt_template="world_knowledge",
            max_tokens=400,
            temperature=0.4,
            enabled=True
        )
        super().__init__(client, config)
    
    async def analyze(self, source_field: SourceField, potential_matches: List[TargetMatch]) -> AgentInsight:
        """Analyze field mapping using general world knowledge."""
        
        matches_context = "\n".join([
            f"- {match.field_name}: {match.reasoning}"
            for match in potential_matches[:3]
        ])
        
        prompt = f"""
As a general knowledge expert, analyze this field mapping:

SOURCE: {source_field.name} ({source_field.type})
Description: {source_field.description}

POTENTIAL MATCHES:
{matches_context}

Using general world knowledge about data structures and common naming conventions:

1. What is the most semantically appropriate match?
2. Are there any standard industry patterns that apply?
3. What are potential data type compatibility issues?

Provide a brief analysis focusing on semantic meaning and industry standards.
"""
        
        try:
            response = self._make_llm_call(prompt)
            
            # Extract key insights from response
            confidence = 0.7  # Default confidence for world knowledge
            if "highly confident" in response.lower():
                confidence = 0.9
            elif "somewhat confident" in response.lower():
                confidence = 0.6
            elif "uncertain" in response.lower():
                confidence = 0.4
            
            return AgentInsight(
                agent_name=self.config.agent_name,
                insight="General knowledge analysis",
                confidence=confidence,
                reasoning=f"World knowledge: {response[:250]}..."
            )
            
        except Exception as e:
            self.logger.error(f"WorldKnowledgeAgent analysis failed: {e}")
            return AgentInsight(
                agent_name=self.config.agent_name,
                insight="Analysis failed",
                confidence=0.0,
                reasoning=f"Error in world knowledge analysis: {str(e)}"
            )


class CognitiveMatchingAgent(BaseAgent):
    """Agent specialized in cognitive pattern recognition."""
    
    def __init__(self, client: OpenAI):
        """Initialize CognitiveMatchingAgent."""
        config = AgentConfig(
            agent_name="CognitiveMatchingAgent",
            prompt_template="cognitive_matching",
            max_tokens=350,
            temperature=0.2,
            enabled=True
        )
        super().__init__(client, config)
    
    async def analyze(self, source_field: SourceField, potential_matches: List[TargetMatch]) -> AgentInsight:
        """Analyze field mapping using cognitive pattern recognition."""
        
        # Focus on the top match for cognitive analysis
        top_match = potential_matches[0] if potential_matches else None
        if not top_match:
            return AgentInsight(
                agent_name=self.config.agent_name,
                insight="No matches to analyze",
                confidence=0.0,
                reasoning="No potential matches provided"
            )
        
        prompt = f"""
Analyze this field mapping using cognitive pattern recognition:

SOURCE: "{source_field.name}"
TARGET: "{top_match.field_name}"

Consider these cognitive patterns:
1. Phonetic similarity (how similar do they sound?)
2. Visual similarity (character patterns)
3. Conceptual similarity (meaning relationship)
4. Structural similarity (naming patterns)
5. Contextual similarity (usage context)

Score the match from 0.0 to 1.0 and explain which cognitive patterns are strongest.
Focus on psychological factors that make humans recognize these as related.
"""
        
        try:
            response = self._make_llm_call(prompt)
            
            # Extract confidence score from response
            confidence = 0.5  # Default
            if "0." in response:
                import re
                scores = re.findall(r'0\.\d+', response)
                if scores:
                    confidence = float(scores[0])
            
            return AgentInsight(
                agent_name=self.config.agent_name,
                insight=f"Cognitive match for {top_match.field_name}",
                confidence=confidence,
                reasoning=f"Cognitive analysis: {response[:200]}..."
            )
            
        except Exception as e:
            self.logger.error(f"CognitiveMatchingAgent analysis failed: {e}")
            return AgentInsight(
                agent_name=self.config.agent_name,
                insight="Analysis failed",
                confidence=0.0,
                reasoning=f"Error in cognitive analysis: {str(e)}"
            )


class MappingCoordinatorAgent(BaseAgent):
    """Coordinator agent that synthesizes insights from all other agents."""
    
    def __init__(self, client: OpenAI):
        """Initialize MappingCoordinatorAgent."""
        config = AgentConfig(
            agent_name="MappingCoordinatorAgent",
            prompt_template="coordination",
            max_tokens=600,
            temperature=0.3,
            enabled=True
        )
        super().__init__(client, config)
    
    async def synthesize_insights(self, 
                                source_field: SourceField, 
                                potential_matches: List[TargetMatch],
                                agent_insights: List[AgentInsight]) -> AgentInsight:
        """Synthesize insights from multiple agents into final recommendation."""
        
        # Prepare agent insights summary
        insights_summary = "\n".join([
            f"- {insight.agent_name}: {insight.insight} (confidence: {insight.confidence:.2f})\n  Reasoning: {insight.reasoning}"
            for insight in agent_insights
        ])
        
        matches_summary = "\n".join([
            f"- {match.field_name}: {match.confidence_score:.2f} - {match.reasoning}"
            for match in potential_matches[:3]
        ])
        
        prompt = f"""
As the mapping coordinator, synthesize these agent insights for field mapping:

SOURCE FIELD: {source_field.name}
Type: {source_field.type}
Description: {source_field.description}

TOP POTENTIAL MATCHES:
{matches_summary}

AGENT INSIGHTS:
{insights_summary}

Your task:
1. Weight each agent's insight based on their confidence and relevance
2. Identify any consensus or conflicts between agents
3. Make a final recommendation with overall confidence score
4. Provide clear reasoning for the decision

Output your final synthesis focusing on the most reliable recommendation.
"""
        
        try:
            response = self._make_llm_call(prompt)
            
            # Calculate overall confidence from agent insights
            if agent_insights:
                avg_confidence = sum(insight.confidence for insight in agent_insights) / len(agent_insights)
                # Weight by agent credibility
                weighted_confidence = min(avg_confidence * 1.1, 1.0)  # Slight boost for synthesis
            else:
                weighted_confidence = 0.5
            
            return AgentInsight(
                agent_name=self.config.agent_name,
                insight="Coordinated recommendation",
                confidence=weighted_confidence,
                reasoning=f"Synthesis of {len(agent_insights)} agents: {response[:300]}..."
            )
            
        except Exception as e:
            self.logger.error(f"MappingCoordinatorAgent synthesis failed: {e}")
            return AgentInsight(
                agent_name=self.config.agent_name,
                insight="Synthesis failed",
                confidence=0.0,
                reasoning=f"Error in coordination: {str(e)}"
            ) 
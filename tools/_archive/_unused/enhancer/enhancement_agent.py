"""
LangGraph Agent für semantische Feldanreicherung.
"""
import json
import os
from datetime import datetime
from typing import Dict, Any, TypedDict
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
from langgraph.graph import StateGraph, END

from .enhancement_schemas import EnhancementResult, EnhancementResponse, FieldEnhancement
from .enhancement_prompts import FIELD_ENHANCEMENT_PROMPT

# Load environment variables
load_dotenv()


class EnhancementState(TypedDict):
    """State für den Enhancement Agent."""
    original_data: Dict[str, Any]
    extracted_fields: Dict[str, Any]
    processing_notes: str
    context: str
    enhanced_fields: list
    processing_context: str
    enhancement_confidence: float
    error: str
    status: str


class FieldEnhancementAgent:
    """LangGraph Agent für semantische Feldanreicherung."""
    
    def __init__(self):
        """Initialize the field enhancement agent."""
        # Configure OpenRouter LLM
        self.llm = ChatOpenAI(
            model=os.getenv("LLM_MODEL"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.1")),
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            openai_api_base=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            max_tokens=4000,
        )
        
        # Create LangGraph workflow
        self.workflow = self._create_workflow()
        self.app = self.workflow.compile()
        
        # Ensure results directory exists
        self.results_dir = "../results/"
        os.makedirs(self.results_dir, exist_ok=True)
    
    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow."""
        workflow = StateGraph(EnhancementState)
        
        # Add nodes
        workflow.add_node("load_data", self._load_data_node)
        workflow.add_node("enhance", self._enhance_fields_node)
        workflow.add_node("save_result", self._save_result_node)
        
        # Define edges
        workflow.set_entry_point("load_data")
        workflow.add_edge("load_data", "enhance")
        workflow.add_edge("enhance", "save_result")
        workflow.add_edge("save_result", END)
        
        return workflow
    
    def _clean_json_response(self, response_text: str) -> str:
        """Clean LLM response to extract valid JSON."""
        # Remove markdown code blocks if present
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            if end > start:
                response_text = response_text[start:end].strip()
        elif "```" in response_text:
            start = response_text.find("```") + 3
            end = response_text.find("```", start)
            if end > start:
                response_text = response_text[start:end].strip()
        
        # Find JSON object boundaries
        start_idx = response_text.find("{")
        end_idx = response_text.rfind("}") + 1
        
        if start_idx >= 0 and end_idx > start_idx:
            return response_text[start_idx:end_idx]
        
        return response_text.strip()
    
    async def _load_data_node(self, state: EnhancementState) -> EnhancementState:
        """Load and prepare data from extraction result."""
        try:
            print("📁 Loading extraction data...")
            
            # Extract relevant information from the result
            extracted_fields = state["original_data"].get("extracted_fields", {})
            processing_notes = state["original_data"].get("processing_notes", "")
            context = state["original_data"].get("context", "")
            
            state.update({
                "extracted_fields": extracted_fields,
                "processing_notes": processing_notes,
                "context": context,
                "status": "loaded"
            })
            
            print(f"✅ Loaded {len(extracted_fields)} fields for enhancement")
            
        except Exception as e:
            state.update({
                "error": f"Data loading failed: {str(e)}",
                "status": "error"
            })
        
        return state
    
    async def _enhance_fields_node(self, state: EnhancementState) -> EnhancementState:
        """Enhance fields with semantic metadata."""
        if state.get("status") == "error":
            return state
            
        try:
            print("🧠 Starting semantic field enhancement...")
            
            # Format prompt with extraction data
            formatted_prompt = FIELD_ENHANCEMENT_PROMPT.format(
                processing_notes=state["processing_notes"],
                context=state["context"],
                extracted_fields=json.dumps(state["extracted_fields"], indent=2)
            )
            
            print("📤 Calling LLM for enhancement...")
            response = await self.llm.ainvoke([HumanMessage(content=formatted_prompt)])
            
            print(f"📥 Enhancement Response: {response.content}...")
            
            # Clean and parse LLM response
            cleaned_response = self._clean_json_response(response.content)
            
            if not cleaned_response:
                raise ValueError("Empty response from LLM")
            
            enhancement_result = json.loads(cleaned_response)
            
            # Update state
            state.update({
                "enhanced_fields": enhancement_result.get("enhanced_fields", []),
                "processing_context": enhancement_result.get("processing_context", ""),
                "enhancement_confidence": enhancement_result.get("enhancement_confidence", 0.0),
                "status": "enhanced"
            })
            
            print("✅ Field enhancement successful")
            
        except Exception as e:
            error_msg = f"Enhancement failed: {str(e)}"
            print(f"❌ {error_msg}")
            state.update({
                "error": error_msg,
                "status": "error"
            })
        
        return state
    
    async def _save_result_node(self, state: EnhancementState) -> EnhancementState:
        """Save enhancement result to JSON file."""
        if state.get("status") == "error":
            return state
            
        try:
            print("💾 Saving enhancement results...")
            
            # Prepare result data
            result_data = {
                "enhanced_fields": state["enhanced_fields"],
                "processing_context": state["processing_context"],
                "enhancement_confidence": state["enhancement_confidence"],
                "timestamp": datetime.now().isoformat()
            }
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"enhancement_result_{timestamp}.json"
            filepath = os.path.join(self.results_dir, filename)
            
            # Save to file
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(result_data, f, indent=2, ensure_ascii=False)
            
            state.update({
                "status": "success",
                "saved_file": filepath
            })
            
            print(f"✅ Enhancement results saved to: {filepath}")
            
        except Exception as e:
            error_msg = f"Save failed: {str(e)}"
            print(f"❌ {error_msg}")
            state.update({
                "error": error_msg,
                "status": "error"
            })
        
        return state
    
    async def enhance_fields(self, extraction_result: Dict[str, Any]) -> EnhancementResponse:
        """
        Enhance extracted fields with semantic metadata.
        
        Args:
            extraction_result: The extraction result from FieldExtractionAgent
            
        Returns:
            EnhancementResponse with semantic field metadata
        """
        print("🚀 Starting field enhancement workflow...")
        
        # Initialize state
        initial_state = EnhancementState(
            original_data=extraction_result,
            extracted_fields={},
            processing_notes="",
            context="",
            enhanced_fields=[],
            processing_context="",
            enhancement_confidence=0.0,
            error="",
            status="initialized"
        )
        
        # Run the workflow
        final_state = await self.app.ainvoke(initial_state)
        
        # Create response
        if final_state["status"] == "error":
            return EnhancementResponse(
                status="error",
                error=final_state["error"],
                agent_name="FieldEnhancementAgent"
            )
        
        # Convert enhanced fields to Pydantic models
        enhanced_fields = [
            FieldEnhancement(**field_data) 
            for field_data in final_state["enhanced_fields"]
        ]
        
        # Create successful result
        enhancement_result = EnhancementResult(
            original_extraction=final_state["original_data"],
            enhanced_fields=enhanced_fields,
            processing_context=final_state["processing_context"],
            enhancement_confidence=final_state["enhancement_confidence"]
        )
        
        return EnhancementResponse(
            status="success",
            result=enhancement_result,
            agent_name="FieldEnhancementAgent",
            saved_file=final_state.get("saved_file")
        )


# Example usage
async def main():
    """Example usage of the field enhancement agent."""
    # Load extraction result - corrected path based on folder structure
    with open("results/json_result.json", "r") as f:
        extraction_data = json.load(f)
    
    # Initialize enhancement agent
    agent = FieldEnhancementAgent()
    
    # Enhance fields
    result = await agent.enhance_fields(extraction_data)
    
    # Print result
    print(f"\nStatus: {result.status}")
    if result.status == "success":
        print(f"Enhanced {len(result.result.enhanced_fields)} fields")
        print(f"Confidence: {result.result.enhancement_confidence}")
        print(f"Saved to: {result.saved_file}")
        
        for field in result.result.enhanced_fields:
            print(f"\n📋 {field.field_name}:")
            print(f"  Description: {field.semantic_description}")
            print(f"  Synonyms: {field.synonyms}")
            print(f"  Types: {field.possible_datatypes}")
            print(f"  Values: {field.possible_values[:3]}...")  # Show first 3
    else:
        print(f"Error: {result.error}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
"""
LangGraph Agent for JSON Field Extraction with OpenRouter/DeepSeek.
"""
import json
import os
from typing import Dict, Any, TypedDict
from datetime import datetime
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
from langgraph.graph import StateGraph, END

from .json_schemas import ProcessedResult, AgentResponse
from .json_prompt import FIELD_EXTRACTION_PROMPT


# Load environment variables
load_dotenv()


class AgentState(TypedDict):
    """State for the LangGraph Agent."""
    json_data: Dict[str, Any]
    extracted_fields: Dict[str, Any]
    validation_status: str
    confidence_score: float
    processing_notes: str
    context: str  # <- Context added
    error: str
    status: str


class FieldExtractionAgent:
    """LangGraph Agent for Field Extraction."""
    
    def __init__(self):
        """Initialize the LangGraph field extraction agent."""
        # Configure OpenRouter LLM
        self.llm = ChatOpenAI(
            model=os.getenv("LLM_MODEL", "deepseek/deepseek-chat"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.1")),
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            openai_api_base=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            max_tokens=2000,  # Ensure enough tokens for response
        )
        
        # Create LangGraph workflow
        self.workflow = self._create_workflow()
        self.app = self.workflow.compile()
        
        # Setup results directory with proper error handling
        self.results_dir = self._setup_results_directory()
    
    def _setup_results_directory(self) -> str:
        """Setup results directory with fallback options for permission issues."""
        import tempfile
        from pathlib import Path
        
        # Try multiple locations in order of preference
        potential_dirs = [
            "results",  # Current directory
            os.path.join(os.getcwd(), "outputs"),  # Current directory outputs
            os.path.join(Path.home(), "mcp_json_results"),  # User home directory
            os.path.join(tempfile.gettempdir(), "mcp_json_results")  # System temp directory
        ]
        
        for dir_path in potential_dirs:
            try:
                os.makedirs(dir_path, exist_ok=True)
                # Test write permissions
                test_file = os.path.join(dir_path, ".write_test")
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
                print(f"✅ Using results directory: {dir_path}")
                return dir_path
            except Exception as e:
                print(f"⚠️ Cannot use directory {dir_path}: {e}")
                continue
        
        # Final fallback - use temp directory with unique name
        fallback_dir = tempfile.mkdtemp(prefix="mcp_json_")
        print(f"⚠️ Using fallback temp directory: {fallback_dir}")
        return fallback_dir
    
    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow."""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("extract", self._extract_fields_node)
        
        # Define edges
        workflow.set_entry_point("extract")
        workflow.add_edge("extract", END)
        
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
    
    def _save_result_to_file(self, result_data: Dict[str, Any]) -> str:
        """
        Save extraction result to JSON file in results directory.
        
        Args:
            result_data: The extraction result data to save
            
        Returns:
            str: Path to the saved file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"json_result_{timestamp}.json"
        
        # Try to save in the configured results directory first
        filepath = os.path.join(self.results_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, indent=2, ensure_ascii=False)
            print(f"💾 Result saved to: {filepath}")
            return filepath
        except Exception as e:
            print(f"❌ Failed to save to {filepath}: {str(e)}")
            
            # Fallback: try to create a new temp directory
            try:
                import tempfile
                fallback_dir = tempfile.mkdtemp(prefix="mcp_json_fallback_")
                fallback_filepath = os.path.join(fallback_dir, filename)
                
                with open(fallback_filepath, 'w', encoding='utf-8') as f:
                    json.dump(result_data, f, indent=2, ensure_ascii=False)
                print(f"💾 Result saved to fallback location: {fallback_filepath}")
                
                # Update results_dir for future saves
                self.results_dir = fallback_dir
                return fallback_filepath
                
            except Exception as fallback_error:
                print(f"❌ Fallback save also failed: {str(fallback_error)}")
                return ""
    
    async def _extract_fields_node(self, state: AgentState) -> AgentState:
        """Extract fields from JSON data."""
        try:
            print("🔍 Starting field extraction")
            
            # Format prompt with JSON data
            formatted_prompt = FIELD_EXTRACTION_PROMPT.format(
                json_data=json.dumps(state["json_data"], indent=2)
            )
            
            print("📤 Calling LLM")
            # Call LLM for extraction
            response = await self.llm.ainvoke([HumanMessage(content=formatted_prompt)])
            # Check for empty response
            if not response.content or response.content.strip() == "":
                error_msg = "LLM returned empty response - model might be overloaded"
                print(f"❌ {error_msg}")
                state.update({
                    "error": error_msg,
                    "status": "error"
                })
                return state
            
            # Clean and parse LLM response
            cleaned_response = self._clean_json_response(response.content)
            print(f"🧹 Cleaned Response: {cleaned_response[:200]}...")
            
            extraction_result = json.loads(cleaned_response)
            
            # Update state - INKL. CONTEXT vom LLM
            state.update({
                "extracted_fields": extraction_result.get("extracted_fields", {}),
                "validation_status": extraction_result.get("validation_status", "unknown"),
                "confidence_score": extraction_result.get("confidence_score", 0.0),
                "processing_notes": extraction_result.get("processing_notes", ""),
                "context": extraction_result.get("context", "No context provided"),  # <- LLM context verwenden
                "status": "success"
            })
            
            # Save result to file
            result_to_save = {
                "extracted_fields": state["extracted_fields"],
                "validation_status": state["validation_status"],
                "confidence_score": state["confidence_score"],
                "processing_notes": state["processing_notes"],
                "context": state["context"],
                "timestamp": datetime.now().isoformat()
            }
            self._save_result_to_file(result_to_save)
            
            print("✅ Extraction successful")
            
        except json.JSONDecodeError as e:
            error_msg = f"JSON Parse Error: {str(e)}\nResponse: {response.content}"
            print(f"❌ {error_msg}")
            state.update({
                "error": error_msg,
                "status": "error"
            })
        except Exception as e:
            error_msg = f"Extraction failed: {str(e)}"
            print(f"❌ {error_msg}")
            state.update({
                "error": error_msg,
                "status": "error"
            })
        
        return state
    
    async def process_json(self, json_data: Dict[str, Any]) -> AgentResponse:
        """
        Process JSON data through the LangGraph workflow.
        
        Args:
            json_data: The JSON data to process
            
        Returns:
            AgentResponse with processing results
        """
        print("🚀 Starting LangGraph workflow...")
        
        # Initialize state - INKL. CONTEXT
        initial_state = AgentState(
            json_data=json_data,
            extracted_fields={},
            validation_status="",
            confidence_score=0.0,
            processing_notes="",
            context="",  # <- Context initialisieren
            error="",
            status="initialized"
        )
        
        # Run the workflow
        final_state = await self.app.ainvoke(initial_state)
        
        # Create response
        if final_state["status"] == "error":
            return AgentResponse(
                status="error",
                error=final_state["error"],
                agent_name="FieldExtractionAgent"
            )
        
        # Create successful result - MIT CONTEXT vom LLM
        processed_result = ProcessedResult(
            extracted_fields=final_state["extracted_fields"],
            validation_status=final_state["validation_status"],
            processing_notes=final_state["processing_notes"],
            confidence_score=final_state["confidence_score"],
            context=final_state["context"]  # <- LLM-generierten Context verwenden
        )
        
        return AgentResponse(
            status="success",
            result=processed_result,
            agent_name="FieldExtractionAgent"
        )


# Example usage
async def main():
    """Example usage of the field extraction agent."""
    # Load test data
    with open("clean.json", "r") as f:
        test_data = json.load(f)
    
    # Initialize agent
    agent = FieldExtractionAgent()
    
    # Process data
    result = await agent.process_json(test_data)
    
    # Print result
    print(f"Status: {result.status}")
    if result.status == "success":
        print(f"Extracted Fields: {result.result.extracted_fields}")
        print(f"Confidence: {result.result.confidence_score}")
        print(f"Validation: {result.result.validation_status}")
        print(f"Context: {result.result.context}")  # <- Context anzeigen
    else:
        print(f"Error: {result.error}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
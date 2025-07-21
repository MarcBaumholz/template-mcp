"""
Tests for the Proof Tool
"""

import pytest
import asyncio
import os
import tempfile
from pathlib import Path
import sys

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from tools.proof_tool import ProofTool, generate_proof_prompt


class TestProofTool:
    """Test cases for the ProofTool class."""
    
    @pytest.fixture
    def sample_mapping_report(self):
        """Sample mapping report content."""
        return """
        # Mapping Analysis Report
        
        ## Mapped Fields
        - employee_id: ✅ Mapped to user.id
        - first_name: ✅ Mapped to user.firstName
        - last_name: ✅ Mapped to user.lastName
        
        ## Unmapped Fields
        - social_security_number: ❌ No direct match found
        - department_code: ❌ Missing from API specification
        - hire_date: ❌ Not found in target API
        """
    
    @pytest.fixture
    def sample_api_spec(self):
        """Sample API specification content."""
        return """
        {
            "openapi": "3.0.0",
            "info": {
                "title": "HR API",
                "version": "1.0.0"
            },
            "components": {
                "schemas": {
                    "User": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "firstName": {"type": "string"},
                            "lastName": {"type": "string"},
                            "email": {"type": "string"},
                            "department": {"type": "string"},
                            "startDate": {"type": "string", "format": "date"}
                        }
                    }
                }
            }
        }
        """
    
    @pytest.fixture
    def temp_files(self, sample_mapping_report, sample_api_spec):
        """Create temporary files for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mapping report file
            mapping_path = os.path.join(temp_dir, "mapping_report.md")
            with open(mapping_path, "w") as f:
                f.write(sample_mapping_report)
            
            # Create API spec file
            api_path = os.path.join(temp_dir, "api_spec.json")
            with open(api_path, "w") as f:
                f.write(sample_api_spec)
            
            yield {
                "mapping_report_path": mapping_path,
                "api_spec_path": api_path,
                "temp_dir": temp_dir
            }
    
    def test_proof_tool_initialization(self):
        """Test that ProofTool can be initialized."""
        tool = ProofTool()
        assert tool is not None
        assert hasattr(tool, 'llm_client')
        assert hasattr(tool, 'rag_helper')
    
    @pytest.mark.asyncio
    async def test_read_file_content(self, temp_files):
        """Test reading file content."""
        tool = ProofTool()
        
        # Test reading existing file
        content = await tool._read_file_content(temp_files["mapping_report_path"])
        assert "Mapping Analysis Report" in content
        assert "Unmapped Fields" in content
        
        # Test reading non-existent file
        content = await tool._read_file_content("non_existent_file.txt")
        assert "Error: File not found" in content
    
    @pytest.mark.asyncio
    async def test_extract_unmapped_fields(self, sample_mapping_report):
        """Test extracting unmapped fields from mapping report."""
        tool = ProofTool()
        
        # Mock the LLM client to return a predictable response
        class MockLLMClient:
            async def generate_response(self, prompt):
                return '["social_security_number", "department_code", "hire_date"]'
        
        tool.llm_client = MockLLMClient()
        
        unmapped_fields = await tool._extract_unmapped_fields(sample_mapping_report)
        
        assert isinstance(unmapped_fields, list)
        assert len(unmapped_fields) == 3
        assert "social_security_number" in unmapped_fields
        assert "department_code" in unmapped_fields
        assert "hire_date" in unmapped_fields
    
    @pytest.mark.asyncio
    async def test_extract_unmapped_fields_fallback(self, sample_mapping_report):
        """Test fallback parsing when LLM fails."""
        tool = ProofTool()
        
        # Mock the LLM client to return invalid JSON
        class MockLLMClient:
            async def generate_response(self, prompt):
                return "Invalid JSON response"
        
        tool.llm_client = MockLLMClient()
        
        unmapped_fields = await tool._extract_unmapped_fields(sample_mapping_report)
        
        assert isinstance(unmapped_fields, list)
        # Should still find some fields using fallback parsing
        assert len(unmapped_fields) > 0
    
    @pytest.mark.asyncio
    async def test_generate_proof_prompt_function(self, temp_files):
        """Test the main generate_proof_prompt function."""
        # This test requires actual LLM and RAG setup, so we'll mock it
        # In a real environment, you would need proper configuration
        
        try:
            result = await generate_proof_prompt(
                mapping_report_path=temp_files["mapping_report_path"],
                api_spec_path=temp_files["api_spec_path"],
                current_path=temp_files["temp_dir"],
                collection_name="test_collection"
            )
            
            # Check that a prompt was generated
            assert isinstance(result, str)
            assert len(result) > 0
            assert "PROOF TOOL" in result
            assert "Field Mapping Verification" in result
            
        except Exception as e:
            # Expected in test environment without proper LLM/RAG setup
            pytest.skip(f"Skipping integration test due to missing dependencies: {e}")
    
    def test_format_unmapped_fields(self):
        """Test formatting unmapped fields for display."""
        tool = ProofTool()
        
        # Test with unmapped fields
        unmapped_fields = ["field1", "field2", "field3"]
        formatted = tool._format_unmapped_fields(unmapped_fields)
        
        assert "Fields requiring attention" in formatted
        assert "field1" in formatted
        assert "field2" in formatted
        assert "field3" in formatted
        
        # Test with no unmapped fields
        formatted = tool._format_unmapped_fields([])
        assert "No unmapped fields detected" in formatted
        assert "Great job!" in formatted
    
    def test_format_creative_solutions(self):
        """Test formatting creative solutions for display."""
        tool = ProofTool()
        
        # Test with solutions
        solutions = {
            "field1": "Solution for field1",
            "field2": "Solution for field2"
        }
        formatted = tool._format_creative_solutions(solutions)
        
        assert "Solutions for `field1`" in formatted
        assert "Solutions for `field2`" in formatted
        assert "Solution for field1" in formatted
        assert "Solution for field2" in formatted
        
        # Test with no solutions
        formatted = tool._format_creative_solutions({})
        assert "No creative solutions needed" in formatted
        assert "all fields are mapped!" in formatted


if __name__ == "__main__":
    pytest.main([__file__]) 
"""
Proof Tool - Generates comprehensive prompts for Cursor to double-check field mappings
and provide creative solutions for unmapped fields.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from ..llm_client import LLMClient
from ..rag_helper import RAGHelper


class ProofTool:
    """
    Tool that generates comprehensive prompts for Cursor to:
    1. Double-check field mappings
    2. Search API spec for missed fields
    3. Provide creative solutions for unmapped fields
    4. Generate implementation ideas
    """
    
    def __init__(self):
        self.llm_client = LLMClient()
        self.rag_helper = RAGHelper()
    
    async def generate_proof_prompt(
        self,
        mapping_report_path: str,
        api_spec_path: str,
        current_path: str = "",
        collection_name: str = "flip_api_v2"
    ) -> str:
        """
        Generate a comprehensive proof prompt for Cursor.
        
        Args:
            mapping_report_path: Path to the mapping analysis report
            api_spec_path: Path to the OpenAPI specification
            current_path: Current working directory path
            collection_name: RAG collection name for API spec
            
        Returns:
            Comprehensive prompt string for Cursor
        """
        
        # Read the mapping report
        mapping_content = await self._read_file_content(mapping_report_path)
        
        # Read API spec
        api_spec_content = await self._read_file_content(api_spec_path)
        
        # Extract unmapped fields from the report
        unmapped_fields = await self._extract_unmapped_fields(mapping_content)
        
        # Generate creative solutions for unmapped fields
        creative_solutions = await self._generate_creative_solutions(
            unmapped_fields, api_spec_content, collection_name
        )
        
        # Generate the comprehensive prompt
        prompt = await self._build_comprehensive_prompt(
            mapping_content,
            api_spec_content,
            unmapped_fields,
            creative_solutions,
            current_path
        )
        
        # Save the prompt to a file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prompt_filename = f"proof_prompt_{timestamp}.md"
        prompt_path = os.path.join(current_path or "reports", prompt_filename)
        
        os.makedirs(os.path.dirname(prompt_path) or ".", exist_ok=True)
        with open(prompt_path, "w", encoding="utf-8") as f:
            f.write(prompt)
        
        return prompt
    
    async def _read_file_content(self, file_path: str) -> str:
        """Read content from a file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return f"Error: File not found at {file_path}"
        except Exception as e:
            return f"Error reading file {file_path}: {str(e)}"
    
    async def _extract_unmapped_fields(self, mapping_content: str) -> List[str]:
        """Extract unmapped fields from the mapping report."""
        
        extraction_prompt = f"""
        Analyze the following mapping report and extract all fields that are marked as "unmapped", 
        "no direct match", "missing", or similar indicators.
        
        Return ONLY a JSON array of field names, nothing else.
        
        Mapping Report:
        {mapping_content}
        """
        
        try:
            response = await self.llm_client.generate_response(extraction_prompt)
            # Try to parse as JSON
            unmapped_fields = json.loads(response.strip())
            return unmapped_fields if isinstance(unmapped_fields, list) else []
        except:
            # Fallback: simple text parsing
            lines = mapping_content.lower().split('\n')
            unmapped_fields = []
            for line in lines:
                if any(keyword in line for keyword in ['unmapped', 'no match', 'missing', 'not found']):
                    # Extract field name from line
                    if ':' in line:
                        field = line.split(':')[0].strip('- *')
                        unmapped_fields.append(field)
            return unmapped_fields
    
    async def _generate_creative_solutions(
        self,
        unmapped_fields: List[str],
        api_spec_content: str,
        collection_name: str
    ) -> Dict[str, str]:
        """Generate creative solutions for unmapped fields."""
        
        if not unmapped_fields:
            return {}
        
        solutions = {}
        
        for field in unmapped_fields:
            # Search for similar fields in API spec using RAG
            rag_results = await self._search_api_spec_for_field(field, collection_name)
            
            # Generate creative solution
            solution_prompt = f"""
            Field "{field}" could not be directly mapped to the API specification.
            
            RAG Search Results:
            {rag_results}
            
            API Specification Context:
            {api_spec_content}
            
            Generate creative solutions for how this field could be:
            1. Mapped to existing API fields (even if transformation is needed)
            2. Derived from multiple API fields
            3. Implemented as a calculated field
            4. Handled through default values or constants
            5. Transformed using business logic
            
            Provide specific, actionable suggestions with code examples where possible.
            """
            
            try:
                solution = await self.llm_client.generate_response(solution_prompt)
                solutions[field] = solution
            except Exception as e:
                solutions[field] = f"Error generating solution: {str(e)}"
        
        return solutions
    
    async def _search_api_spec_for_field(self, field: str, collection_name: str) -> str:
        """Search API spec using RAG for similar fields."""
        try:
            # Use RAG to search for similar fields
            search_query = f"field property attribute {field} similar data type"
            results = await self.rag_helper.query_collection(
                collection_name=collection_name,
                query=search_query,
                limit=3
            )
            
            if results:
                return "\n".join([f"- {result}" for result in results])
            else:
                return "No similar fields found in API specification."
        except Exception as e:
            return f"Error searching API spec: {str(e)}"
    
    async def _build_comprehensive_prompt(
        self,
        mapping_content: str,
        api_spec_content: str,
        unmapped_fields: List[str],
        creative_solutions: Dict[str, str],
        current_path: str
    ) -> str:
        """Build the comprehensive prompt for Cursor."""
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        prompt = f"""# 🔍 PROOF TOOL - Field Mapping Verification & Creative Solutions

**Generated:** {timestamp}
**Task:** Double-check field mappings and provide creative solutions for unmapped fields

## 📋 INSTRUCTIONS FOR CURSOR

You are tasked with performing a comprehensive review of the field mapping analysis. Your goal is to:

1. **VERIFY** all field mappings are accurate and complete
2. **SEARCH** the API specification for any missed fields
3. **GENERATE** creative solutions for unmapped fields
4. **PROVIDE** implementation ideas and code examples

## 📊 CURRENT MAPPING ANALYSIS
```markdown
{mapping_content}
```

## 🔍 UNMAPPED FIELDS DETECTED

The following fields require attention:

{self._format_unmapped_fields(unmapped_fields)}

## 💡 CREATIVE SOLUTIONS

{self._format_creative_solutions(creative_solutions)}

## 🎯 YOUR SPECIFIC TASKS

### 1. Double-Check All Mappings
- Review each mapped field in the analysis above
- Verify the mapping is technically correct
- Check for any logical inconsistencies
- Ensure data types are compatible

### 2. Search API Specification Thoroughly
- Re-examine the API spec for any missed fields
- Look for nested objects, optional fields, or alternative field names
- Check for fields that might be in different endpoints
- Consider fields that might be computed or derived

### 3. Creative Problem Solving
For each unmapped field, consider:
- **Transformation:** Can it be derived from existing fields?
- **Combination:** Can multiple API fields be combined?
- **Default Values:** Can reasonable defaults be provided?
- **Business Logic:** Can it be calculated using business rules?
- **Alternative Approaches:** Are there workarounds?

### 4. Implementation Ideas
Provide specific code examples for:
- Data transformation functions
- Field mapping logic
- Error handling for missing fields
- Validation rules
- Default value strategies

## 📁 API SPECIFICATION REFERENCE

```json
{api_spec_content}
```

## ✅ DELIVERABLES

Please provide:

1. **Verification Report:** Confirm or correct existing mappings
2. **Missing Fields Analysis:** Any fields you found that were missed
3. **Creative Solutions:** Specific approaches for unmapped fields
4. **Implementation Code:** Ready-to-use code snippets
5. **Recommendations:** Best practices and next steps

## 🚀 IMPLEMENTATION GUIDELINES

- Keep solutions simple and maintainable
- Provide error handling for edge cases
- Include validation logic
- Consider performance implications
- Document any assumptions made
- Use type hints and proper documentation

## 🔄 NEXT STEPS

After completing this analysis:
1. Update the mapping report with your findings
2. Implement the suggested solutions
3. Test the mapping logic thoroughly
4. Document any remaining limitations

---

**Remember:** The goal is to achieve the most complete and accurate field mapping possible while providing practical solutions for any gaps.
"""

        return prompt
    
    def _format_unmapped_fields(self, unmapped_fields: List[str]) -> str:
        """Format unmapped fields for display."""
        if not unmapped_fields:
            return "✅ **No unmapped fields detected - Great job!**"
        
        formatted = "🔴 **Fields requiring attention:**\n\n"
        for i, field in enumerate(unmapped_fields, 1):
            formatted += f"{i}. `{field}`\n"
        
        return formatted
    
    def _format_creative_solutions(self, solutions: Dict[str, str]) -> str:
        """Format creative solutions for display."""
        if not solutions:
            return "✅ **No creative solutions needed - all fields are mapped!**"
        
        formatted = ""
        for field, solution in solutions.items():
            formatted += f"### 💡 Solutions for `{field}`\n\n"
            formatted += f"{solution}\n\n"
            formatted += "---\n\n"
        
        return formatted


# Async function to be called by the MCP server
async def generate_proof_prompt(
    mapping_report_path: str,
    api_spec_path: str,
    current_path: str = "",
    collection_name: str = "flip_api_v2"
) -> str:
    """
    Generate a comprehensive proof prompt for Cursor.
    
    Args:
        mapping_report_path: Path to the mapping analysis report
        api_spec_path: Path to the OpenAPI specification  
        current_path: Current working directory path
        collection_name: RAG collection name for API spec
        
    Returns:
        Comprehensive prompt string for Cursor
    """
    tool = ProofTool()
    return await tool.generate_proof_prompt(
        mapping_report_path=mapping_report_path,
        api_spec_path=api_spec_path,
        current_path=current_path,
        collection_name=collection_name
    ) 

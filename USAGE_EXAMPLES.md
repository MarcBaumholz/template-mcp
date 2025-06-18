# MCP Server Usage Examples

This document provides comprehensive usage examples for the RAG API Analysis MCP Server tools.

## 🚀 `analyze_api_fields`

Analyzes a list of fields against an API specification, with optional context for enhanced accuracy.

### Tool Signature
```python
def analyze_api_fields(
    fields_to_analyze: list[str],
    collection_name: str = "flip_api_v2",
    context_topic: str | None = None
) -> str:
```

### Example 1: Basic Field Analysis (No Context)
This example analyzes common fields without providing a business context.

**MCP Call (JSON)**
```json
{
    "method": "tools/call",
    "params": {
        "name": "analyze_api_fields",
        "arguments": {
            "fields_to_analyze": ["start_date", "end_date", "employee_id"]
        }
    }
}
```

**Direct Python Usage**
```python
from tools import analyze_fields_with_rag_and_llm

report = analyze_fields_with_rag_and_llm(
    fields_to_analyze=["start_date", "end_date", "employee_id"],
    collection_name="flip_api_v2"
)
print(report)
```

### Example 2: Enhanced Analysis with Context Topic
This example provides a `context_topic` to get more accurate, business-specific results.

**MCP Call (JSON)**
```json
{
    "method": "tools/call",
    "params": {
        "name": "analyze_api_fields",
        "arguments": {
            "fields_to_analyze": ["absence created", "start date", "end date", "employee id", "reason"],
            "context_topic": "AbsenceRequestCreated",
            "collection_name": "flip_api_v2"
        }
    }
}
```

**Direct Python Usage**
```python
from tools import analyze_fields_with_rag_and_llm

report = analyze_fields_with_rag_and_llm(
    fields_to_analyze=["absence created", "start date", "end date", "employee id", "reason"],
    context_topic="AbsenceRequestCreated",
    collection_name="flip_api_v2"
)
print(report)
```

### Example 3: Payroll Context Analysis
This example demonstrates using a different context topic for payroll-related fields.

**MCP Call (JSON)**
```json
{
    "method": "tools/call",
    "params": {
        "name": "analyze_api_fields",
        "arguments": {
            "fields_to_analyze": ["gross_pay", "net_pay", "tax_deductions"],
            "context_topic": "PayrollProcessed",
            "collection_name": "payroll_api_v1"
        }
    }
}
```

### Benefits of Using `context_topic`
- **Enhanced RAG Queries**: The context topic is added to RAG queries, retrieving more relevant documentation.
- **Improved LLM Prompts**: The LLM receives the context, enabling it to provide more accurate business purpose and data type analysis.
- **Reduced Ambiguity**: Helps distinguish between fields with similar names but different meanings in different contexts (e.g., `id` for an employee vs. an absence request).

---

## 🚀 `upload_api_specification`

Uploads an OpenAPI specification file to the RAG system.

### Tool Signature
```python
def upload_api_specification(
    openapi_file_path: str,
    collection_name: str,
    metadata: dict | None = None
) -> dict:
```

### Example Usage
**MCP Call (JSON)**
```json
{
    "method": "tools/call",
    "params": {
        "name": "upload_api_specification",
        "arguments": {
            "openapi_file_path": "sample_data/api_flip.yml",
            "collection_name": "flip_api_v2"
        }
    }
}
```

**Direct Python Usage**
```python
from tools import upload_api_specification_to_rag

result = upload_api_specification_to_rag(
    openapi_file_path="sample_data/api_flip.yml",
    collection_name="flip_api_v2"
)
print(result)
```

---

## 🚀 `query_api_specification`

Performs a direct query against an API collection to retrieve documentation snippets.

### Tool Signature
```python
def query_api_specification(
    query: str,
    collection_name: str,
    limit: int = 5,
    score_threshold: float = 0.3
) -> list[dict]:
```

### Example Usage
**MCP Call (JSON)**
```json
{
    "method": "tools/call",
    "params": {
        "name": "query_api_specification",
        "arguments": {
            "query": "employee time off endpoints",
            "collection_name": "flip_api_v2"
        }
    }
}
```

**Direct Python Usage**
```python
from tools import query_rag_collection

results = query_rag_collection(
    query="employee time off endpoints",
    collection_name="flip_api_v2"
)
for res in results:
    print(res)
```

---

## Best Practices

- **Use Specific Context Topics**: Be as specific as possible with your `context_topic` for the best results.
- **Match Field Names**: Use field names that are likely to appear in the API documentation.
- **Upload Specs First**: Always use `upload_api_specification` to populate your knowledge base before running analysis.
- **Check Collection Names**: Ensure the `collection_name` exists and matches the one you uploaded your spec to.

## Common Context Topics

| Domain | Context Topics |
|---|---|
| **HR/Absence Management** | "AbsenceRequestCreated", "AbsenceApproved", "AbsenceRejected" |
| **Payroll** | "PayrollProcessed", "PayrollCalculated", "TaxDeductionsApplied" |
| **Employee Management** | "EmployeeOnboarded", "EmployeeTerminated", "EmployeeUpdated" |
| **Time Tracking** | "TimeEntryCreated", "TimesheetSubmitted", "OvertimeCalculated" | 
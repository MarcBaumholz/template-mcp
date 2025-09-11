# 🎯 Dynamic Task Management System Guide

## 📋 Overview

The Dynamic Task Management System automatically updates your task list after each MCP tool execution, creating new tasks based on tool outputs and new information. This provides the dynamic task management you requested, even though it can't directly manipulate Cursor's internal task system.

## 🚀 Key Features

- **Automatic Task Updates**: Tasks are updated after each MCP tool execution
- **Smart Task Generation**: New tasks are generated based on tool outputs and analysis
- **Task Prioritization**: Tasks are automatically renumbered and prioritized
- **Progress Tracking**: Real-time progress tracking with completion rates
- **Integration Ready**: Easy integration with existing MCP tools

## 🏗️ Architecture

```
Dynamic Task Management System
├── DynamicTaskManager          # Core task management
├── TaskUpdateTemplates        # Task generation templates
├── MCPToolIntegration         # MCP tool integration wrapper
└── MCP Tools                  # Actual MCP tool implementations
```

## 📁 File Structure

```
tools/shared_utilities/
├── dynamic_task_manager.py    # Core task management class
├── task_update_templates.py   # Task generation templates
├── mcp_tool_integration.py    # MCP tool integration wrapper
└── mcp_tools.py              # MCP tool imports

TASKS.md                      # Dynamic task list (auto-updated)
STATUS.md                     # Workflow status dashboard
test_dynamic_task_management.py # Test suite
```

## 🔧 Usage

### 1. Basic Usage

```python
from tools.shared_utilities.dynamic_task_manager import update_tasks_after_tool
from tools.shared_utilities.task_update_templates import TaskUpdateTemplates

# After any MCP tool execution
update_tasks_after_tool(
    tool_name="upload_api_specification",
    output_path="outputs/api_spec_uploaded.json",
    analysis="Successfully uploaded Flip API specification",
    new_requirements=TaskUpdateTemplates.get_tool_specific_requirements(
        "upload_api_specification", 
        "outputs/api_spec_uploaded.json", 
        "Successfully uploaded Flip API specification"
    )
)
```

### 2. Integrated MCP Tools

```python
from tools.shared_utilities.mcp_tool_integration import (
    upload_api_spec_with_tasks,
    analyze_fields_with_tasks,
    reasoning_agent_with_tasks,
    generate_mapper_with_tasks,
    quality_suite_with_tasks,
    tdd_validation_with_tasks
)

# Use integrated tools (automatically update tasks)
result = upload_api_spec_with_tasks(
    openapi_file_path="path/to/api.json",
    collection_name="flip_api_v2"
)

result = analyze_fields_with_tasks(
    webhook_json_path="path/to/data.json"
)

result = reasoning_agent_with_tasks(
    source_analysis_path="path/to/analysis.md",
    api_spec_path="path/to/api.json",
    output_directory="outputs/phase2"
)
```

### 3. Manual Task Management

```python
from tools.shared_utilities.dynamic_task_manager import task_manager

# Add manual task
task_manager.add_manual_task("Review generated code and fix issues")

# Get next task
next_task = task_manager.get_next_task()
print(f"Next task: {next_task['content']}")

# Get task summary
summary = task_manager.get_task_summary()
print(f"Completion rate: {summary['completion_rate']:.1%}")
```

## 🎯 Task Generation Logic

### Tool-Specific Requirements

Each MCP tool generates specific new tasks based on its output:

#### Upload API Specification
- Review uploaded API specification
- Validate API specification structure
- Identify key endpoints and data models
- Proceed with field analysis

#### Analyze JSON Fields
- Review field analysis results
- Identify unmapped fields and gaps
- Generate semantic mapping recommendations
- Create field mapping strategy

#### Reasoning Agent
- Review reasoning agent report
- Validate endpoint mappings
- Identify high-confidence vs. low-confidence mappings
- Generate verification checklist

#### Generate Mapping Prompt
- Execute generated mapping prompt
- Review mapping prompt quality
- Test prompt with sample data
- Refine prompt based on results

#### Generate Kotlin Mapper
- Review generated Kotlin mapper
- Run code quality suite
- Execute unit tests
- Perform security review

#### Quality Suite
- Review quality suite results
- Fix identified issues
- Address security vulnerabilities
- Optimize performance

#### TDD Validation
- Review TDD validation results
- Fix failing tests
- Validate business logic
- Prepare for production

## 📊 Task List Format

The system generates a markdown task list with the following structure:

```markdown
# 🎯 Dynamic Task Management System

**Last Updated:** 2024-12-19 15:30:45

## ✅ Completed Tasks
- [x] Bootstrap environment and verify RAG connectivity
- [x] Upload API specifications to RAG system
- [x] Analyze JSON fields and generate mapping recommendations

## 🔄 Current Tasks
- [ ] Review reasoning agent report: outputs/reasoning_agent_report.md
- [ ] Validate endpoint mappings and field correlations
- [ ] Generate verification checklist for manual review

## 🆕 New Tasks Generated
- [ ] Execute generated mapping prompt: outputs/optimized_mapping_prompt.md
- [ ] Review mapping prompt quality and completeness
- [ ] Test prompt with sample data if available

## 📊 Task Statistics
- **Total Tasks:** 8
- **Completed:** 3
- **Current:** 3
- **New:** 2
```

## 🔄 Workflow Integration

### Phase 0 - Bootstrap
```python
# After bootstrap completion
update_tasks_after_tool(
    tool_name="bootstrap_environment",
    output_path="outputs/bootstrap_complete.json",
    analysis="Environment setup completed successfully",
    new_requirements=[
        "Verify environment setup completion",
        "Test RAG system connectivity",
        "Proceed to Phase 1 - Data Extraction"
    ]
)
```

### Phase 1 - Data Extraction
```python
# After uploading API specs
update_tasks_after_tool(
    tool_name="upload_api_specification",
    output_path="outputs/api_spec_uploaded.json",
    analysis="Successfully uploaded Flip API specification",
    new_requirements=TaskUpdateTemplates.get_tool_specific_requirements(
        "upload_api_specification", 
        "outputs/api_spec_uploaded.json", 
        "Successfully uploaded Flip API specification"
    )
)
```

### Phase 2 - Analysis & Mapping
```python
# After field analysis
update_tasks_after_tool(
    tool_name="analyze_json_fields_with_rag",
    output_path="outputs/field_analysis_report.md",
    analysis="Analyzed 23 fields with 85% mapping confidence",
    new_requirements=TaskUpdateTemplates.get_tool_specific_requirements(
        "analyze_json_fields_with_rag",
        "outputs/field_analysis_report.md",
        "Analyzed 23 fields with 85% mapping confidence"
    )
)
```

## 🧪 Testing

Run the test suite to verify the system works correctly:

```bash
python test_dynamic_task_management.py
```

The test will:
1. Create initial task list
2. Simulate MCP tool executions
3. Show task updates after each tool
4. Display final task summary
5. Test task generation templates

## 🔧 Customization

### Custom Task Templates

Create custom task templates for your specific tools:

```python
class CustomTaskTemplates(TaskUpdateTemplates):
    @staticmethod
    def get_custom_tool_requirements(tool_name: str, output_path: str, analysis: str) -> List[str]:
        if 'my_custom_tool' in tool_name.lower():
            return [
                f"Review {tool_name} output: {output_path}",
                "Apply custom business logic",
                "Generate custom reports",
                "Proceed with custom workflow"
            ]
        return super().get_tool_specific_requirements(tool_name, output_path, analysis)
```

### Custom Task Priorities

Modify task priorities based on your workflow:

```python
def custom_task_priorities(tool_name: str, output_path: str) -> List[str]:
    if 'error' in output_path.lower():
        return [
            "🚨 URGENT: Fix tool execution error",
            "Review error logs and identify root cause",
            "Implement error handling improvements"
        ]
    elif 'success' in output_path.lower():
        return [
            "✅ Continue with next workflow step",
            "Validate tool output quality"
        ]
    return []
```

## 📈 Monitoring & Analytics

### Task Progress Tracking

```python
# Get current task progress
summary = task_manager.get_task_summary()
print(f"Completion rate: {summary['completion_rate']:.1%}")

# Get next recommended tool
next_tool = get_next_recommended_tool()
print(f"Next recommended tool: {next_tool}")

# Get execution summary
execution_summary = get_execution_summary()
print(f"Tools used: {execution_summary['tools_used']}")
```

### Status Dashboard

The system automatically updates `STATUS.md` with:
- Last tool execution details
- Task progress statistics
- Next recommended actions
- Workflow status

## 🚨 Error Handling

The system handles errors gracefully:

```python
try:
    result = execute_mcp_tool('upload_api_specification', file_path, collection)
except Exception as e:
    # System automatically creates error tasks
    # Updates task list with error information
    # Logs error details
    print(f"Tool failed: {e}")
```

## 🎉 Benefits

1. **Automatic Task Updates**: No manual task management required
2. **Smart Task Generation**: New tasks based on tool outputs
3. **Progress Tracking**: Real-time progress monitoring
4. **Error Handling**: Automatic error task generation
5. **Integration Ready**: Easy integration with existing MCP tools
6. **Customizable**: Flexible templates and priorities
7. **Monitoring**: Comprehensive analytics and reporting

## 🔄 Next Steps

1. **Integrate with your MCP tools** using the provided wrappers
2. **Customize task templates** for your specific workflow
3. **Monitor task progress** using the built-in analytics
4. **Extend the system** with custom task generation logic
5. **Use in production** for automated workflow management

## 📚 Examples

See `test_dynamic_task_management.py` for complete examples of:
- Task creation and management
- MCP tool integration
- Task update workflows
- Error handling
- Progress monitoring

---

**This system provides the dynamic task management you requested, automatically updating tasks after each MCP tool execution and generating new tasks based on tool outputs and new information.**

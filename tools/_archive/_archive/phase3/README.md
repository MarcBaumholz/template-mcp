# Phase 3 Code Generation Tools

## Overview

The Phase 3 tools are a suite of 4 MCP (Model Context Protocol) tools designed to generate production-ready Kotlin code from Phase 2 mapping reports. These tools work together to create a complete implementation including mappers, converters, complex logic, and comprehensive tests.

All tools use the **free qwen/qwen-2.5-coder:free** model from OpenRouter for LLM operations, making them cost-effective for continuous integration workflows.

## Tool Suite

### 1. Direct Field Mapper (`phase3_generate_direct_mappings`)
Handles simple 1:1 field mappings where source fields directly map to target fields without transformation.

**Features:**
- Generates clean, idiomatic Kotlin code
- Null-safe operations with Kotlin's `?.` and `?:` operators
- Default value handling
- Automatic field grouping and organization

### 2. Type Converter (`phase3_generate_type_conversions`)
Generates data type conversion functions for mappings requiring type transformations.

**Supported Conversions:**
- String to numeric types (Int, Double, Float)
- Date/time format conversions
- Enum mappings
- Boolean conversions
- Custom type transformations

### 3. Complex Logic Mapper (`phase3_generate_complex_mappings`)
Creates functions for fields requiring additional business logic or multi-field operations.

**Handles:**
- Field concatenation/splitting
- Calculated fields (e.g., age from birthdate)
- Conditional logic based on field values
- Lookup tables and transformations
- Business rule validation
- Data enrichment and normalization

### 4. TDD Test Generator (`phase3_generate_tdd_tests`)
Generates comprehensive test suites following Test-Driven Development principles.

**Test Coverage:**
- Unit tests for each mapping
- Edge case tests (null values, boundaries)
- Integration tests for complete flow
- Performance tests for large datasets
- Business rule validation tests

## Installation

1. Ensure you have the required dependencies:
```bash
pip install pydantic openai python-dotenv
```

2. Set up your OpenRouter API key:
```bash
export OPENROUTER_API_KEY="your-api-key-here"
```

Or create a `.env` file:
```env
OPENROUTER_API_KEY=your-api-key-here
OPENROUTER_MODEL=qwen/qwen-2.5-coder:free
```

## Usage

### Via MCP Server

The tools are integrated into the MCP server and can be called directly:

```python
# Example: Generate direct mappings
result = phase3_generate_direct_mappings(
    mapping_report_path="reports/mapping_analysis.md",
    ground_truth_path="reports/ground_truth.json",
    output_directory="outputs/phase3"
)

# Example: Generate type conversions
result = phase3_generate_type_conversions(
    mapping_report_path="reports/mapping_analysis.md",
    output_directory="outputs/phase3"
)

# Example: Generate complex mappings
result = phase3_generate_complex_mappings(
    mapping_report_path="reports/mapping_analysis.md",
    output_directory="outputs/phase3"
)

# Example: Generate TDD tests
result = phase3_generate_tdd_tests(
    mapping_report_path="reports/mapping_analysis.md",
    mapper_code_path="outputs/phase3/CompleteMapper.kt",
    output_directory="outputs/phase3/tests",
    test_all_scenarios=True
)
```

### Programmatic Usage

You can also use the tools directly in Python:

```python
from tools.phase3 import (
    generate_direct_mappings,
    generate_type_conversions,
    generate_complex_mappings,
    generate_tdd_tests
)

# Generate all components for a complete mapper
direct_result = generate_direct_mappings(
    mapping_report_path="path/to/report.md",
    output_directory="output/kotlin"
)

type_result = generate_type_conversions(
    mapping_report_path="path/to/report.md",
    output_directory="output/kotlin"
)

complex_result = generate_complex_mappings(
    mapping_report_path="path/to/report.md",
    output_directory="output/kotlin"
)

test_result = generate_tdd_tests(
    mapping_report_path="path/to/report.md",
    output_directory="output/tests"
)
```

## Workflow Integration

### Recommended Phase 3 Workflow

1. **Phase 2 Output**: Start with a verified mapping report from Phase 2
   - Contains field mappings categorized as direct, type_conversion, or complex_logic
   - Includes ground truth verification data
   - Has endpoint verification status

2. **Generate Direct Mappings**: Create simple 1:1 field mappings
   ```bash
   # Call via MCP
   phase3_generate_direct_mappings(
       mapping_report_path="reports/phase2_report.md",
       output_directory="outputs/phase3"
   )
   ```

3. **Generate Type Conversions**: Add data type transformation functions
   ```bash
   phase3_generate_type_conversions(
       mapping_report_path="reports/phase2_report.md",
       output_directory="outputs/phase3"
   )
   ```

4. **Generate Complex Logic**: Implement business rules and calculations
   ```bash
   phase3_generate_complex_mappings(
       mapping_report_path="reports/phase2_report.md",
       output_directory="outputs/phase3"
   )
   ```

5. **Generate Tests**: Create comprehensive test suite
   ```bash
   phase3_generate_tdd_tests(
       mapping_report_path="reports/phase2_report.md",
       output_directory="outputs/phase3/tests",
       test_all_scenarios=True
   )
   ```

6. **Integration**: Combine all generated components into final implementation

## Output Structure

Each tool generates Kotlin files with timestamp suffixes:

```
outputs/phase3/
├── DirectMapper_20240115_143022.kt       # Direct field mappings
├── TypeConversions_20240115_143045.kt    # Conversion functions
├── TypeConversionMapper_20240115_143045.kt # Integrated converter
├── ComplexFunctions_20240115_143110.kt   # Complex logic functions
├── ComplexLogicMapper_20240115_143110.kt # Integrated complex mapper
└── tests/
    ├── MapperTestSuite_20240115_143135.kt # Complete test suite
    └── TestCases_20240115_143135.json     # Test metadata
```

## Generated Code Examples

### Direct Mapping
```kotlin
class DirectFieldMapper {
    fun mapToTarget(source: SourceDTO): TargetDTO = TargetDTO(
        employeeId = source.employee.id,
        email = source.employee.email ?: "",
        department = source.employee.department
    )
}
```

### Type Conversion
```kotlin
fun String.toLocalDate(): LocalDate {
    return LocalDate.parse(this)
}

fun String.toStatusEnum(): StatusEnum = when (this) {
    "active" -> StatusEnum.ACTIVE
    "inactive" -> StatusEnum.INACTIVE
    else -> StatusEnum.UNKNOWN
}
```

### Complex Logic
```kotlin
fun mapFirstNameToFullName(source: Employee): String {
    return "${source.firstName} ${source.lastName}".trim()
}

fun calculateAge(birthDate: String): Int {
    val birth = LocalDate.parse(birthDate)
    return Period.between(birth, LocalDate.now()).years
}
```

### TDD Tests
```kotlin
@Test
@DisplayName("Should map employee ID correctly")
fun test_employee_id_direct() {
    val source = Employee(id = "123", email = "test@example.com")
    val result = mapper.map(source)
    assertEquals("123", result.employeeId)
    assertEquals("test@example.com", result.email)
}
```

## Configuration

### Environment Variables
- `OPENROUTER_API_KEY`: Your OpenRouter API key (required)
- `OPENROUTER_MODEL`: LLM model to use (default: `qwen/qwen-2.5-coder:free`)

### Tool Parameters

All tools accept these common parameters:
- `mapping_report_path` (required): Path to Phase 2 mapping report
- `ground_truth_path` (optional): Path to verification data
- `output_directory` (optional): Where to save generated files

Additional tool-specific parameters:
- **TDD Generator**:
  - `mapper_code_path`: Path to analyze existing mapper code
  - `test_all_scenarios`: Generate comprehensive vs. minimal tests
  - `package_name`: Kotlin package name for tests

## Testing

Run the test suite to verify tool functionality:

```bash
# Run all Phase 3 tool tests
pytest tests/test_phase3_tools.py -v

# Run specific test classes
pytest tests/test_phase3_tools.py::TestDirectMapper -v
pytest tests/test_phase3_tools.py::TestTypeConverter -v
pytest tests/test_phase3_tools.py::TestComplexMapper -v
pytest tests/test_phase3_tools.py::TestTDDGenerator -v

# Run integration tests
pytest tests/test_phase3_tools.py::TestIntegration -v
```

## Best Practices

1. **Mapping Report Quality**: Ensure Phase 2 reports are complete and verified
2. **Incremental Generation**: Generate and review each component before proceeding
3. **Test Coverage**: Always generate tests, especially for complex mappings
4. **Code Review**: Review generated code for business logic accuracy
5. **Integration Testing**: Test the complete mapper with real data

## Troubleshooting

### Common Issues

1. **LLM API Errors**
   - Verify OPENROUTER_API_KEY is set correctly
   - Check API rate limits and quotas
   - Ensure network connectivity

2. **Parsing Errors**
   - Verify mapping report format matches expected structure
   - Check for valid JSON/YAML in ground truth files

3. **Code Generation Issues**
   - Review mapping categorization in Phase 2 report
   - Ensure field types are correctly specified
   - Check transformation notes for clarity

## Architecture

The Phase 3 tools follow a modular architecture:

```
phase3/
├── phase3_models.py          # Shared Pydantic models
├── phase3_direct_mapper.py   # Direct mapping generator
├── phase3_type_converter.py  # Type conversion generator
├── phase3_complex_mapper.py  # Complex logic generator
├── phase3_tdd_generator.py   # TDD test generator
└── __init__.py               # Package exports
```

Each tool:
- Uses Pydantic for data validation
- Implements lazy loading for performance
- Generates timestamped output files
- Returns structured result objects
- Handles errors gracefully with detailed messages

## Contributing

To add new features or improve existing tools:

1. Follow the existing code structure
2. Use Pydantic models for data structures
3. Add comprehensive tests
4. Update documentation
5. Ensure compatibility with free LLM models

## License

These tools are part of the connector-mcp project and follow the project's licensing terms.


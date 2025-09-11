# 🚀 Enhanced MCP Tools Rules - Configuration-Driven & Domain-Agnostic

## 📋 **Core Principles**

### 1. **No Hardcoded Values**
- ❌ **NEVER** hardcode company names, API endpoints, or field names
- ❌ **NEVER** assume specific business domains (HR, retail, etc.)
- ❌ **NEVER** hardcode LLM models or API keys
- ✅ **ALWAYS** use configuration-driven approaches
- ✅ **ALWAYS** make tools adaptable to any business domain

### 2. **Configuration-First Design**
- Use `tools/shared_utilities/config_manager.py` for all configuration
- Support multiple business domains through `BusinessDomain` enum
- Make LLM providers configurable through `LLMProvider` enum
- Allow runtime configuration changes without code modifications

### 3. **Flexible Field Extraction**
- Use `tools/shared_utilities/field_extractor.py` for field extraction
- Support pattern-based field recognition
- Adapt to any JSON structure without assumptions
- Provide confidence scores and categorization

### 4. **Template-Driven Prompts**
- Use `tools/shared_utilities/prompt_templates.py` for all prompts
- Support domain-specific context injection
- Make prompts configurable and reusable
- Avoid hardcoded prompt text

## 🛠️ **Implementation Guidelines**

### **Phase 1: Data Extraction**
```python
# ✅ CORRECT - Configuration-driven
from tools.shared_utilities.config_manager import get_config, get_collection_name
from tools.shared_utilities.prompt_templates import render_prompt, PromptType

config = get_config()
collection_name = get_collection_name(custom_name)
prompt = render_prompt(PromptType.FIELD_EXTRACTION, business_context=config.business_domain.value)

# ❌ WRONG - Hardcoded values
collection_name = "flip_api_v2"
prompt = "Extract HR fields from JSON data..."
```

### **Phase 2: Analysis & Mapping**
```python
# ✅ CORRECT - Flexible analysis
from tools.shared_utilities.prompt_templates import render_prompt, PromptType

prompt = render_prompt(
    PromptType.API_MAPPING,
    business_context=config.business_domain.value.replace("_", " ").title(),
    source_fields=fields,
    api_spec=spec_content
)

# ❌ WRONG - Domain-specific assumptions
prompt = f"Map HR fields {fields} to StackOne API..."
```

### **Phase 3: Code Generation**
```python
# ✅ CORRECT - Configurable code generation
from tools.shared_utilities.config_manager import get_package_name, get_company_name

prompt = render_prompt(
    PromptType.CODE_GENERATION,
    package_name=get_package_name(custom_package),
    company_name=get_company_name(custom_company),
    language=config.code_generation.default_language
)

# ❌ WRONG - Hardcoded package/company
prompt = f"Generate Kotlin code for com.flip.integrations..."
```

## 📊 **Business Domain Support**

### **Supported Domains**
- `HR` - Human Resources (employees, absences, payroll)
- `RETAIL` - Retail/E-commerce (products, inventory, orders)
- `FINANCE` - Financial services (transactions, accounts, payments)
- `HEALTHCARE` - Healthcare (patients, appointments, records)
- `MANUFACTURING` - Manufacturing (orders, production, quality)
- `EDUCATION` - Education (students, courses, grades)
- `REAL_ESTATE` - Real Estate (properties, listings, transactions)
- `GENERIC` - Generic business data (default)

### **Domain Configuration**
```python
# Set business domain
from tools.shared_utilities.config_manager import update_config, BusinessDomain

update_config(business_domain=BusinessDomain.RETAIL)
# All tools now adapt to retail context
```

## 🔧 **Configuration Management**

### **Environment Variables**
```bash
# LLM Configuration
LLM_MODEL=deepseek/deepseek-chat-v3.1:free
LLM_TEMPERATURE=0.1
OPENROUTER_API_KEY=your_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# Business Domain
MCP_BUSINESS_DOMAIN=retail

# Custom Configuration
MCP_CONFIG_PATH=./custom_config.json
```

### **Configuration File Example**
```json
{
  "business_domain": "retail",
  "llm": {
    "provider": "openrouter",
    "model": "deepseek/deepseek-chat-v3.1:free",
    "temperature": 0.1,
    "max_tokens": 4000
  },
  "field_extraction": {
    "max_depth": 4,
    "exclude_fields": ["pagination", "page", "pageSize", "total"],
    "include_patterns": ["data.*", "items.*", "results.*"]
  },
  "code_generation": {
    "default_language": "kotlin",
    "default_framework": "micronaut",
    "default_package": "com.company.integrations",
    "default_company": "company",
    "default_project": "integrations"
  },
  "rag": {
    "default_collection": "api_specs",
    "chunk_size": 1000,
    "score_threshold": 0.5
  }
}
```

## 🧪 **Testing Requirements**

### **Multi-Domain Testing**
Every tool must be tested with:
- **HR Data**: Employee records, absence requests, payroll data
- **Retail Data**: Product catalogs, inventory, orders, customers
- **Finance Data**: Transactions, accounts, payments, reports
- **Healthcare Data**: Patient records, appointments, medical data
- **Manufacturing Data**: Production orders, inventory, quality control

### **Test Data Structure**
```python
# Create test data for each domain
test_cases = [
    {
        "domain": BusinessDomain.HR,
        "data": {"employees": [...], "absences": [...]},
        "expected_fields": ["employee_id", "name", "department", "status"]
    },
    {
        "domain": BusinessDomain.RETAIL,
        "data": {"products": [...], "inventory": [...]},
        "expected_fields": ["product_id", "sku", "name", "price", "stock"]
    }
    # ... more domains
]
```

## 📝 **Documentation Requirements**

### **Tool Documentation**
Each tool must include:
- **Purpose**: What the tool does
- **Configuration**: How to configure it
- **Input/Output**: Expected data formats
- **Examples**: Usage examples for different domains
- **Limitations**: Known limitations and workarounds

### **API Documentation**
- **Endpoints**: All available endpoints
- **Parameters**: Configuration parameters
- **Responses**: Response formats and examples
- **Error Handling**: Error codes and messages

## 🚨 **Migration Checklist**

### **For Existing Tools**
- [ ] Remove hardcoded company names (flip, stackone)
- [ ] Remove hardcoded field names (absence, employee, etc.)
- [ ] Remove hardcoded API endpoints
- [ ] Remove hardcoded LLM models
- [ ] Add configuration support
- [ ] Add domain flexibility
- [ ] Update prompts to use templates
- [ ] Add multi-domain testing
- [ ] Update documentation

### **For New Tools**
- [ ] Use configuration manager from start
- [ ] Use prompt templates
- [ ] Use flexible field extractor
- [ ] Support all business domains
- [ ] Include comprehensive testing
- [ ] Document configuration options

## 🎯 **Success Metrics**

### **Flexibility Metrics**
- ✅ Tools work with 8+ business domains
- ✅ No hardcoded values in production code
- ✅ Configuration changes don't require code changes
- ✅ New domains can be added without code modifications

### **Quality Metrics**
- ✅ 95%+ field extraction accuracy across domains
- ✅ Consistent prompt quality across domains
- ✅ Proper error handling and fallbacks
- ✅ Comprehensive test coverage

### **Usability Metrics**
- ✅ Clear configuration documentation
- ✅ Easy domain switching
- ✅ Intuitive tool interfaces
- ✅ Helpful error messages

## 🔄 **Continuous Improvement**

### **Regular Reviews**
- Monthly review of hardcoded values
- Quarterly domain coverage assessment
- Annual configuration system review
- Continuous feedback integration

### **Feedback Integration**
- User feedback on domain support
- Performance metrics analysis
- Configuration usage patterns
- Error rate monitoring

---

**Remember**: The goal is to create tools that work seamlessly across any business domain without requiring code changes. Configuration and flexibility are key to achieving this goal.

# MCP RAG Tools Fix - Planning

## 🎯 Goal
Fix all broken and partially working MCP RAG tools to make them fully functional with OpenRouter API and DeepSeek model.

## 🔍 Issues Identified
1. **Missing Dependencies**: sentence-transformers, openai packages
2. **Missing Environment Variables**: OPENAI_API_KEY (need to switch to OPENROUTER_API_KEY)
3. **Technical Bug**: 'CollectionInfo' object has no attribute 'vectors_config'
4. **API Integration**: Switch from OpenAI to OpenRouter with DeepSeek model

## 📋 Tasks Breakdown

### Task 1: Update Dependencies
- [ ] Add missing packages to requirements.txt
- [ ] Update LLM client to use OpenRouter instead of OpenAI
- [ ] Test dependency installation

### Task 2: Fix Environment Configuration
- [ ] Update .env.example with OpenRouter configuration
- [ ] Modify LLM client to use OPENROUTER_API_KEY
- [ ] Configure DeepSeek model as default

### Task 3: Fix Technical Bugs
- [ ] Fix CollectionInfo attribute error in rag_tools.py
- [ ] Update Qdrant client usage to handle collection info properly
- [ ] Test collection listing functionality

### Task 4: Update Server Integration
- [ ] Ensure all tools handle missing dependencies gracefully
- [ ] Update error messages to reflect OpenRouter requirements
- [ ] Test all RAG tools end-to-end

### Task 5: Testing & Validation
- [ ] Create comprehensive test for all RAG tools
- [ ] Verify server starts without errors
- [ ] Test with actual OpenRouter API calls

## 🏗️ Architecture Decisions
- **LLM Provider**: Switch from OpenAI to OpenRouter
- **Model**: Use deepseek/deepseek-r1-0528-qwen3-8b:free
- **Error Handling**: Graceful degradation when API key missing
- **Dependencies**: Keep optional imports with clear error messages

## 🔧 Implementation Order
1. Update requirements.txt
2. Fix LLM client for OpenRouter
3. Fix Qdrant collection bug
4. Update environment configuration
5. Test and validate all tools
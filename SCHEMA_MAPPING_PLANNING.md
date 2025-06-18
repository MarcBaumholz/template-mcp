# Schema Mapping Tool - Planning & Implementation

## 🎯 Goal
Create an intelligent Schema Mapping tool that finds compatible APIs and suggests field mappings with compatibility scoring, using AI agents for enhanced matching.

## 📋 Requirements Analysis

### Input Sources:
1. **clean.json** - Source API fields structure
2. **analyze_api_fields.md** - Detailed field analysis from existing tool
3. **Target API docs** - Stored in Qdrant vector database
4. **Instructions** - Find relevant fields matching from source to target API

### Output:
- **Detailed mapping results** in MD file with:
  - Top 3 matches per field with paths
  - Compatibility scores and reasoning
  - Detailed explanations for each match

## 🏗️ Architecture Design

### Core Components:
1. **Input Parser** - Parse clean.json and MD analysis
2. **Multi-Agent System** - Specialized AI agents for enhanced matching
3. **Qdrant Search Engine** - Vector-based API documentation search
4. **LLM Integration** - OpenRouter API for intelligent analysis
5. **Results Generator** - MD file output with detailed mapping

### AI Agent System:
1. **FlipInfoAgent** - Provides additional Flip API context
2. **WorldKnowledgeAgent** - General API knowledge and patterns
3. **CognitiveMatchingAgent** - Uses cognitive science algorithms for semantic matching
4. **MappingCoordinatorAgent** - Orchestrates all agents and final decisions

## 🔧 Technical Stack

### Dependencies:
- **pydantic** - Data validation and models
- **qdrant-client** - Vector database operations
- **sentence-transformers** - Embeddings for semantic search
- **openai** (via OpenRouter) - LLM calls

### File Structure:
```
tools/
├── mapping.py              # Main mapping tool
├── mapping_models.py       # Pydantic models
├── mapping_agents.py       # AI agents
├── cognitive_matcher.py    # Cognitive matching algorithms
└── mapping_generator.py    # MD output generator
```

## 📝 Implementation Plan

### Phase 1: Core Infrastructure ✅
- [x] Create Pydantic models for data structures
- [x] Implement input parsers (JSON/MD)
- [x] Set up basic Qdrant search functionality
- [x] Create base agent structure

### Phase 2: AI Agents
- [ ] Implement FlipInfoAgent
- [ ] Implement WorldKnowledgeAgent  
- [ ] Implement CognitiveMatchingAgent with semantic algorithms
- [ ] Create MappingCoordinatorAgent for orchestration

### Phase 3: Integration & Testing
- [ ] Integrate multi-agent system with main mapping tool
- [ ] Implement MD results generator
- [ ] Add tool to MCP server.py
- [ ] End-to-end testing with real data

### Phase 4: Optimization
- [ ] Fine-tune matching algorithms
- [ ] Optimize agent interactions
- [ ] Add caching for performance
- [ ] Documentation and examples

## 🧠 Cognitive Matching Algorithms

### Semantic Similarity Patterns:
1. **Synonym Detection** - HR vs Human Resources
2. **Abbreviation Matching** - emp_id vs employee_id
3. **Context Mapping** - department vs dept vs division
4. **Hierarchical Concepts** - address.street vs street_address
5. **Domain-Specific Terms** - onboarding vs orientation

### Scoring Methodology:
- **Exact Match**: 1.0
- **Semantic Similarity**: 0.7-0.95
- **Context Match**: 0.5-0.8
- **Structural Similarity**: 0.3-0.7
- **Domain Knowledge**: 0.2-0.6 
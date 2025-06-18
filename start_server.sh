#!/bin/bash

echo "🚀 Starting MCP JSON Analysis and RAG Server..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo "Please create .env file with your API keys (see .env.example)"
    echo "For RAG functionality, you need: OPENAI_API_KEY"
fi

echo "📋 Available Tools:"
echo "  JSON Analysis Tools:"
echo "    • analyze_json_structure - Analyze JSON structure and schema"
echo "    • extract_json_fields - Extract specific fields using dot notation"
echo "    • flatten_json - Flatten nested JSON objects"
echo ""
echo "  RAG Tools (requires OPENAI_API_KEY):"
echo "    • list_available_api_specs - List all API spec collections"
echo "    • upload_api_specification - Upload OpenAPI spec to RAG system"
echo "    • query_api_specification - Query API documentation"
echo "    • delete_api_specification - Delete API spec collection"
echo "    • analyze_api_fields - Analyze fields using RAG + LLM"
echo "    • enhance_json_fields - Enhance JSON analysis with RAG context"
echo "    • enhance_csv_with_rag - Enhance CSV data with API context"
echo ""

echo "🔧 Starting server..."
python server.py
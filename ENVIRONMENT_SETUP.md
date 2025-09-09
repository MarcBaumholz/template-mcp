# Environment Setup Guide

## Required Environment Variables

Create a `.env` file in the root directory with the following variables:

```bash
# OpenRouter API Configuration
OPENROUTER_API_KEY=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
OPENROUTER_MODEL=deepseek/deepseek-chat

# RAG System Configuration
QDRANT_URL=https://qdrant.flip.com
QDRANT_API_KEY=your_qdrant_api_key_here

# Other Configuration
DEBUG=false
LOG_LEVEL=INFO
```

## Setup Instructions

1. **Create the .env file:**
   ```bash
   touch .env
   ```

2. **Add the environment variables:**
   Copy the configuration above into your `.env` file

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify setup:**
   ```bash
   python test_all_tools.py
   ```

## Security Notes

- Never commit the `.env` file to version control
- The `.env` file is already in `.gitignore`
- API keys should be kept secure and not shared
- Use different API keys for development and production environments

## Troubleshooting

If you get "OPENROUTER_API_KEY environment variable not set" error:
1. Check that the `.env` file exists in the root directory
2. Verify the environment variable name is exactly `OPENROUTER_API_KEY`
3. Restart your terminal/IDE after creating the `.env` file
4. Make sure the `python-dotenv` package is installed

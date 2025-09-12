# Environment Variables Configuration

The `.env.example` file demonstrates all environment variables that can be used to configure TunaCode. These variables provide an alternative method for setting API keys and configuration options.

## File Usage

1. **Copy the example file**:
   ```bash
   cp documentation/configuration/.env.example .env
   ```

2. **Edit with your values**:
   ```bash
   # Set your actual API keys
   ANTHROPIC_API_KEY="sk-ant-api03-your-key-here"
   OPENAI_API_KEY="sk-proj-your-key-here"
   ```

3. **Load the environment**:
   ```bash
   # Load variables in your shell
   source .env

   # Or use with direnv (auto-loading)
   echo "dotenv" > .envrc
   ```

## Environment Variables

### Required API Keys

**Anthropic Claude**
- `ANTHROPIC_API_KEY`: Required for Claude models
- Format: `sk-ant-api03-...`
- Get from: https://console.anthropic.com

**OpenAI**
- `OPENAI_API_KEY`: Required for OpenAI models (GPT-3.5, GPT-4, etc.)
- Format: `sk-proj-...`
- Get from: https://platform.openai.com/api-keys

### Optional API Keys

**Google Gemini**
- `GOOGLE_API_KEY`: For Google Gemini models
- Get from: https://makersuite.google.com/app/apikey

**Perplexity**
- `PERPLEXITY_API_KEY`: For Perplexity AI models
- Format: `pplx-...`
- Get from: https://www.perplexity.ai/settings/api

**Mistral AI**
- `MISTRAL_API_KEY`: For Mistral models
- Get from: https://console.mistral.ai/api-keys

**xAI**
- `XAI_API_KEY`: For xAI models (Grok)
- Get from: https://console.x.ai

**Groq**
- `GROQ_API_KEY`: For Groq's fast inference
- Get from: https://console.groq.com

**OpenRouter**
- `OPENROUTER_API_KEY`: For OpenRouter models
- Get from: https://openrouter.ai/keys

**Azure OpenAI**
- `AZURE_OPENAI_API_KEY`: For Azure OpenAI services
- Requires additional configuration in `tunacode.json` for endpoint

**Ollama**
- `OLLAMA_API_KEY`: For remote Ollama servers requiring authentication
- Local Ollama typically doesn't require a key

**GitHub**
- `GITHUB_API_KEY`: For GitHub import/export features
- Format: `ghp_...` or `github_pat_...`
- Get from: https://github.com/settings/tokens

## Configuration Priority

Environment variables are processed in this order:

1. **Environment variables** (highest priority)
2. **`tunacode.json` configuration file**
3. **Default values** (lowest priority)

Example: If `OPENAI_API_KEY` is set both in `.env` and `tunacode.json`, the `.env` value takes precedence.

## Security Best Practices

### Never Commit `.env` Files
```bash
# Add to .gitignore
.env
.env.local
.env.production
```

### Use Different Files for Different Environments
```
.env                # Local development
.env.staging       # Staging environment
.env.production    # Production environment
```

### Secure Storage
- Use encrypted secrets management in production
- Consider using `direnv` for automatic environment loading
- Use `.env.example` as a template for required variables

### Key Rotation
- Regularly rotate API keys
- Monitor key usage and billing
- Revoke compromised keys immediately

## Usage Examples

### Development Setup
```bash
# Copy and configure
cp documentation/configuration/.env.example .env
echo 'ANTHROPIC_API_KEY="your-key"' >> .env

# Load environment
source .env

# Run tunacode
tunacode --model "anthropic:claude-3-sonnet"
```

### CI/CD Integration
```yaml
# GitHub Actions example
env:
  ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

### Docker Integration
```dockerfile
# Dockerfile
COPY .env.example .env
# Build-time or run-time environment injection
```

## Troubleshooting

### Common Issues

**API Key Not Found**
```bash
# Check if variable is set
echo $ANTHROPIC_API_KEY

# Verify file exists
ls -la .env
```

**Invalid API Key Format**
- Ensure keys start with correct prefix (`sk-`, `pplx-`, etc.)
- Check for extra spaces or quotes
- Verify key hasn't expired

**Permission Issues**
```bash
# Check file permissions
chmod 600 .env
```

### Debug Environment Loading
```bash
# Show all environment variables
env | grep API_KEY

# Test with specific variable
python -c "import os; print(os.getenv('ANTHROPIC_API_KEY', 'NOT SET'))"
```

## Integration with Configuration Files

Environment variables can be referenced in `tunacode.json`:

```json
{
    "env": {
        "ANTHROPIC_API_KEY": "${ANTHROPIC_API_KEY}",
        "OPENAI_API_KEY": "${OPENAI_API_KEY}"
    }
}
```

This allows for flexible configuration management across different deployment environments.

# Using Local Models with TunaCode

TunaCode supports any OpenAI-compatible API, including locally hosted models via LM Studio, Ollama, or other local LLM servers.

## Quick Setup for LM Studio

LM Studio provides an OpenAI-compatible API server for running models locally. Configure TunaCode to use it with this configuration:

```json
{
  "default_model": "openai:model-name-here",
  "env": {
    "OPENAI_API_KEY": "sk-dummy",
    "OPENAI_BASE_URL": "http://localhost:1234/v1"
  }
}
```

## Complete Working Example

Here's a full configuration file (`~/.config/tunacode.json`) for local models:

```json
{
  "default_model": "openai:qwen/qwen3-4b-2507",
  "env": {
    "ANTHROPIC_API_KEY": "",
    "GEMINI_API_KEY": "",
    "OPENAI_API_KEY": "sk-dummy",
    "OPENROUTER_API_KEY": "",
    "OPENAI_BASE_URL": "http://localhost:1234/v1"
  },
  "settings": {
    "max_retries": 10,
    "max_iterations": 40,
    "context_window_size": 200000
  }
}
```

## Key Configuration Points

### Base URL Format
- **Correct**: `http://localhost:1234/v1`
- **Wrong**: `http://localhost:1234/v1/chat/completions`

The base URL must end at `/v1`. TunaCode automatically appends the appropriate endpoint paths.

### Model Name
Use the `openai:` prefix followed by your model name:
- LM Studio: `openai:model-name` (check LM Studio for exact name)
- Ollama: `openai:llama2`, `openai:mistral`, etc.
- Custom: `openai:your-model-id`

### API Key Requirement
Even though local models don't require authentication, the OpenAI client library requires a non-empty API key. Use `"sk-dummy"` or any placeholder value.

## Setup Methods

### Method 1: Direct Configuration
Edit `~/.config/tunacode.json` with the configuration above.

### Method 2: CLI Flags
```bash
tunacode --model "openai:your-model" \
         --baseurl "http://localhost:1234/v1" \
         --key "sk-dummy"
```

### Method 3: Environment Variables
```bash
export OPENAI_BASE_URL="http://localhost:1234/v1"
export OPENAI_API_KEY="sk-dummy"
tunacode --model "openai:your-model"
```

## Compatibility

This configuration works with any OpenAI-compatible API server:
- **LM Studio**: Default port 1234
- **Ollama**: Usually port 11434 (`http://localhost:11434/v1`)
- **LocalAI**: Default port 8080
- **Text Generation WebUI**: With OpenAI extension
- **vLLM**: OpenAI-compatible server mode
- **Any custom OpenAI-compatible implementation**

## Troubleshooting

### Connection Refused
- Ensure your local server is running
- Check the port number matches your server configuration
- Try `curl http://localhost:1234/v1/models` to test connectivity

### Bad Request Errors
- Verify the model name matches what your server expects
- Check the base URL format (must end with `/v1`)
- Ensure the server implements OpenAI's chat completions endpoint

### Model Not Found
- List available models: `curl http://localhost:1234/v1/models`
- Update `default_model` to match an available model

## Performance Tips

- Set `context_window_size` to match your model's capabilities
- Adjust `max_iterations` based on your local compute resources
- Consider reducing `max_retries` for faster failure detection with local models

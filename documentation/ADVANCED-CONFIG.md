# Advanced Configuration

This guide covers advanced configuration options for TunaCode, including provider setup, MCP integration, and customization.

## Configuration File

Your configuration is stored at: `~/.config/tunacode.json`

### Basic Structure

```json
{
  "default_model": "provider:model-name",
  "env": {
    "API_KEY": "your-api-key"
  },
  "mcpServers": {}
}
```

## Model Configuration

### Model Format

Model names must include the provider prefix:

```
provider:model-name
```

### Popular Models

- `openai:gpt-4o` (OpenAI's latest)
- `openai:gpt-4o-mini` (OpenAI's fast model)
- `anthropic:claude-3.5-sonnet` (Claude's latest)
- `anthropic:claude-3-haiku` (Claude's fast model)
- `google-gla:gemini-2.0-flash` (Google's Gemini)
- `openrouter:mistralai/devstral-large` (via OpenRouter)

## Provider Configurations

### OpenAI

```json
{
  "default_model": "openai:gpt-4o",
  "env": {
    "OPENAI_API_KEY": "sk-your-api-key-here"
  }
}
```

### Anthropic Claude

```json
{
  "default_model": "anthropic:claude-3.5-sonnet",
  "env": {
    "ANTHROPIC_API_KEY": "sk-ant-your-api-key-here"
  }
}
```

### Google Gemini

```json
{
  "default_model": "google-gla:gemini-2.0-flash",
  "env": {
    "GOOGLE_API_KEY": "your-google-api-key-here"
  }
}
```

### OpenRouter

[OpenRouter](https://openrouter.ai) provides access to 100+ models through a single API.

**Configuration:**
```json
{
  "default_model": "openrouter:openai/gpt-4o",
  "env": {
    "OPENROUTER_API_KEY": "sk-or-your-api-key-here",
    "OPENAI_BASE_URL": "https://openrouter.ai/api/v1"
  }
}
```

**Popular OpenRouter Models:**
- `openrouter:openai/gpt-4o` (OpenAI GPT-4o via OpenRouter)
- `openrouter:anthropic/claude-3.5-sonnet` (Claude via OpenRouter)
- `openrouter:mistralai/devstral-large` (Mistral's coding model)
- `openrouter:meta-llama/llama-3.3-70b-instruct` (Llama 3.3)

### Custom OpenAI-Compatible API

```json
{
  "default_model": "openai:your-model-name",
  "env": {
    "OPENAI_API_KEY": "your-api-key",
    "OPENAI_BASE_URL": "https://your-api-endpoint.com/v1"
  }
}
```

## MCP (Model Context Protocol) Support

Extend your AI's capabilities with MCP servers. MCP allows you to connect external tools and services to TunaCode, seamlessly integrating with the built-in tool system.

### MCP Integration Features

TunaCode provides robust MCP integration with:

- **Automatic Tool Discovery**: MCP tools are automatically detected and integrated
- **Silent Operation**: MCP server stderr output is suppressed to prevent noise
- **Error Recovery**: Graceful handling of MCP server failures and disconnections
- **Schema Validation**: Full parameter validation using MCP tool schemas
- **Resource Support**: Access to MCP resource protocols for data exchange
- **Seamless UX**: External MCP tools work exactly like built-in tools

### Basic MCP Configuration

```json
{
  "mcpServers": {
    "server-name": {
      "command": "command-to-run",
      "args": ["arg1", "arg2"],
      "env": {
        "ENV_VAR": "value"
      }
    }
  }
}
```

### Example MCP Servers

**Web Fetch Server:**
```json
{
  "mcpServers": {
    "fetch": {
      "command": "uvx",
      "args": ["mcp-server-fetch"]
    }
  }
}
```

**GitHub Integration:**
```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "<YOUR_TOKEN>"
      }
    }
  }
}
```

**File System Server:**
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/directory"]
    }
  }
}
```

### MCP Architecture Integration

TunaCode's MCP integration (`src/tunacode/services/mcp.py`) provides:

**QuietMCPServer**: Suppresses MCP server stderr output for clean operation
```python
class QuietMCPServer(MCPServerStdio):
    """Silences MCP server stderr while preserving JSON-RPC communication"""
```

**Server Lifecycle**:
- MCP servers are loaded during agent initialization
- Automatic connection management with proper cleanup
- Error handling prevents single server failures from affecting other tools

**Tool Integration**:
- MCP tools appear alongside built-in tools in the agent's tool list
- Same confirmation flow and error handling as internal tools
- Full support for parallel execution (read-only MCP tools run concurrently)

### Popular MCP Servers

**Database Access:**
```json
{
  "mcpServers": {
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "DATABASE_URL": "postgresql://user:password@localhost:5432/dbname"
      }
    }
  }
}
```

**SQLite:**
```json
{
  "mcpServers": {
    "sqlite": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sqlite", "/path/to/database.db"]
    }
  }
}
```

**Brave Search:**
```json
{
  "mcpServers": {
    "brave-search": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-brave-search"],
      "env": {
        "BRAVE_API_KEY": "your-brave-api-key"
      }
    }
  }
}
```

Learn more about available MCP servers at [modelcontextprotocol.io](https://modelcontextprotocol.io/)

## Environment Variables

### Setting API Keys via Command Line

```bash
# OpenAI
tunacode --model "openai:gpt-4o" --key "sk-your-openai-key"

# Anthropic Claude
tunacode --model "anthropic:claude-3.5-sonnet" --key "sk-ant-your-anthropic-key"

# OpenRouter
tunacode --model "openrouter:openai/gpt-4o" --key "sk-or-your-openrouter-key"
```

### Manual Environment Variable Configuration

Edit `~/.config/tunacode.json`:

```json
{
  "env": {
    "OPENAI_API_KEY": "sk-...",
    "ANTHROPIC_API_KEY": "sk-ant-...",
    "GOOGLE_API_KEY": "...",
    "OPENROUTER_API_KEY": "sk-or-...",
    "CUSTOM_ENV_VAR": "value"
  }
}
```

## Advanced Settings

### Complete Configuration Example

```json
{
  "default_model": "anthropic:claude-3.5-sonnet",
  "env": {
    "ANTHROPIC_API_KEY": "sk-ant-api-key",
    "OPENAI_API_KEY": "sk-openai-key",
    "OPENROUTER_API_KEY": "sk-or-key",
    "OPENAI_BASE_URL": "https://openrouter.ai/api/v1"
  },
  "mcpServers": {
    "fetch": {
      "command": "uvx",
      "args": ["mcp-server-fetch"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_your_token"
      }
    }
  }
}
```

## Troubleshooting

### Common Issues

1. **API Key Not Found**
   - Ensure the key is in the correct format
   - Check that the environment variable name matches the provider

2. **Model Not Available**
   - Verify the model name includes the provider prefix
   - Check that you have access to the model with your API key

3. **MCP Server Fails to Start**
   - Ensure the command is installed (npm, uvx, etc.)
   - Check that all required environment variables are set
   - Verify the server supports your operating system
   - Check MCP server logs (stderr is suppressed but logged internally)

4. **MCP Tools Not Appearing**
   - Verify the server configuration in `mcpServers` section
   - Check that the MCP server supports tool discovery
   - Use `/refresh` command to reload MCP servers
   - Enable debug mode to see MCP initialization logs

### Debug Mode

Enable verbose logging by setting the environment variable:
```bash
export TUNACODE_DEBUG=1
tunacode
```

### Configuration Validation

Use the `/refresh` command to reload and validate your configuration without restarting TunaCode.

## Security Best Practices

1. **Never commit API keys** to version control
2. **Use environment-specific configs** for different projects
3. **Rotate API keys regularly**
4. **Limit MCP server permissions** to only necessary directories
5. **Review tool confirmations** before approving operations

## Project-Specific Configuration

Create a `TUNACODE.md` file in your project root to provide context:

```markdown
# TUNACODE.md

## Project Configuration

- Language: Python 3.11
- Framework: FastAPI
- Database: PostgreSQL

## Coding Standards

- Use type hints for all functions
- Follow PEP 8 style guide
- Write docstrings for public methods
- Minimum 80% test coverage

## AI Assistant Guidelines

- Always create tests for new features
- Use async/await for database operations
- Follow the existing project structure
```

This file is automatically loaded when TunaCode runs in your project directory.

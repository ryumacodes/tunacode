<!-- This guide explains how to integrate external tools via MCP (Model Context Protocol) servers for extended functionality -->

# MCP (Model Context Protocol) Integration Guide

This guide explains how to integrate external tools into TunaCode using the Model Context Protocol (MCP). MCP allows TunaCode to communicate with external tool servers, extending its capabilities beyond built-in tools.

## MCP Overview

MCP is a protocol for communication between AI assistants and external tool servers. It provides:

- Standardized tool discovery
- Type-safe tool execution
- Async communication via JSON-RPC
- Process lifecycle management
- Error handling and retries

## MCP Architecture in TunaCode

```
┌─────────────────────┐     JSON-RPC      ┌─────────────────────┐
│                     │ ←---------------→  │                     │
│   TunaCode Agent    │                    │    MCP Server       │
│                     │                    │   (Node/Python)     │
│  - Tool Discovery   │                    │                     │
│  - Tool Execution   │                    │  - Tool Registry    │
│  - Result Handling  │                    │  - Implementation   │
│                     │                    │  - Error Handling   │
└─────────────────────┘                    └─────────────────────┘
           ↑                                          ↑
           │                                          │
           └────────── MCPManager ────────────────────┘
                  (Process Management)
```

## Configuring MCP Servers

### 1. Basic Configuration

Add MCP servers to your `~/.config/tunacode/tunacode.json`:

```json
{
    "mcp_servers": {
        "filesystem": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem"],
            "env": {}
        },

        "github": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-github"],
            "env": {
                "GITHUB_TOKEN": "${GITHUB_TOKEN}"
            }
        },

        "custom-tools": {
            "command": "python",
            "args": ["/path/to/your/mcp_server.py"],
            "env": {
                "API_KEY": "${YOUR_API_KEY}"
            }
        }
    }
}
```

### 2. Environment Variables

MCP servers can access environment variables:

```json
{
    "mcp_servers": {
        "my-server": {
            "command": "node",
            "args": ["./my-server.js"],
            "env": {
                "API_KEY": "${MY_API_KEY}",      // From environment
                "BASE_URL": "https://api.example.com",  // Hardcoded
                "TIMEOUT": "30000"
            }
        }
    }
}
```

Environment variables are resolved in this order:
1. From the config's `env` section
2. From system environment variables
3. Default to empty string if not found

### 3. Server Types

#### NPM Package Servers

```json
{
    "mcp_servers": {
        "npm-server": {
            "command": "npx",
            "args": ["-y", "@your-org/mcp-server"],
            "env": {}
        }
    }
}
```

#### Local Script Servers

```json
{
    "mcp_servers": {
        "local-python": {
            "command": "python",
            "args": ["/home/user/scripts/my_mcp_server.py"],
            "env": {
                "PYTHONPATH": "/home/user/lib"
            }
        },

        "local-node": {
            "command": "node",
            "args": ["./servers/custom-server.js"],
            "env": {}
        }
    }
}
```

#### Docker-based Servers

```json
{
    "mcp_servers": {
        "docker-server": {
            "command": "docker",
            "args": [
                "run",
                "--rm",
                "-i",
                "--network", "host",
                "myorg/mcp-server:latest"
            ],
            "env": {}
        }
    }
}
```

## Creating an MCP Server

### Python MCP Server Example

Here's a complete example of a Python MCP server:

```python
#!/usr/bin/env python3
"""
Example MCP server for weather information.
Save as: weather_mcp_server.py
"""

import asyncio
import json
import sys
from typing import Any, Dict, List
import aiohttp

class WeatherMCPServer:
    """MCP server for weather tools"""

    def __init__(self):
        self.api_key = os.environ.get('WEATHER_API_KEY', '')
        self.base_url = "https://api.openweathermap.org/data/2.5"

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle JSON-RPC request"""
        method = request.get('method')
        params = request.get('params', {})
        request_id = request.get('id')

        try:
            if method == 'initialize':
                return self.initialize_response(request_id)
            elif method == 'tools/list':
                return self.list_tools_response(request_id)
            elif method == 'tools/call':
                return await self.call_tool_response(params, request_id)
            else:
                return self.error_response(
                    request_id,
                    -32601,
                    f"Method not found: {method}"
                )
        except Exception as e:
            return self.error_response(
                request_id,
                -32603,
                f"Internal error: {str(e)}"
            )

    def initialize_response(self, request_id: Any) -> Dict[str, Any]:
        """Response to initialization"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocol_version": "0.1.0",
                "capabilities": {
                    "tools": True,
                    "resources": False,
                    "prompts": False
                },
                "server_info": {
                    "name": "weather-server",
                    "version": "1.0.0"
                }
            }
        }

    def list_tools_response(self, request_id: Any) -> Dict[str, Any]:
        """List available tools"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": [
                    {
                        "name": "get_weather",
                        "description": "Get current weather for a city",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "city": {
                                    "type": "string",
                                    "description": "City name"
                                },
                                "country": {
                                    "type": "string",
                                    "description": "Country code (optional)",
                                    "default": ""
                                }
                            },
                            "required": ["city"]
                        }
                    },
                    {
                        "name": "get_forecast",
                        "description": "Get weather forecast for a city",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "city": {
                                    "type": "string",
                                    "description": "City name"
                                },
                                "days": {
                                    "type": "integer",
                                    "description": "Number of days",
                                    "default": 5,
                                    "minimum": 1,
                                    "maximum": 7
                                }
                            },
                            "required": ["city"]
                        }
                    }
                ]
            }
        }

    async def call_tool_response(
        self,
        params: Dict[str, Any],
        request_id: Any
    ) -> Dict[str, Any]:
        """Execute tool and return result"""
        tool_name = params.get('name')
        arguments = params.get('arguments', {})

        if tool_name == 'get_weather':
            result = await self.get_weather(
                arguments.get('city'),
                arguments.get('country', '')
            )
        elif tool_name == 'get_forecast':
            result = await self.get_forecast(
                arguments.get('city'),
                arguments.get('days', 5)
            )
        else:
            return self.error_response(
                request_id,
                -32602,
                f"Unknown tool: {tool_name}"
            )

        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": result
                    }
                ]
            }
        }

    async def get_weather(self, city: str, country: str = "") -> str:
        """Get current weather"""
        if not self.api_key:
            return "Error: WEATHER_API_KEY environment variable not set"

        location = f"{city},{country}" if country else city
        url = f"{self.base_url}/weather"
        params = {
            "q": location,
            "appid": self.api_key,
            "units": "metric"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self.format_weather(data)
                else:
                    return f"Error: Could not get weather for {city}"

    def format_weather(self, data: Dict[str, Any]) -> str:
        """Format weather data"""
        return f"""Weather in {data['name']}, {data['sys']['country']}:
Temperature: {data['main']['temp']}°C (feels like {data['main']['feels_like']}°C)
Conditions: {data['weather'][0]['description']}
Humidity: {data['main']['humidity']}%
Wind: {data['wind']['speed']} m/s"""

    async def get_forecast(self, city: str, days: int) -> str:
        """Get weather forecast"""
        # Implementation similar to get_weather
        return f"Forecast for {city} for {days} days..."

    def error_response(
        self,
        request_id: Any,
        code: int,
        message: str
    ) -> Dict[str, Any]:
        """Format error response"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }

    async def run(self):
        """Main server loop"""
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await asyncio.get_event_loop().connect_read_pipe(
            lambda: protocol, sys.stdin
        )

        while True:
            try:
                # Read line from stdin
                line = await reader.readline()
                if not line:
                    break

                # Parse JSON-RPC request
                request = json.loads(line.decode())

                # Handle request
                response = await self.handle_request(request)

                # Send response
                print(json.dumps(response), flush=True)

            except Exception as e:
                # Log error but continue
                sys.stderr.write(f"Server error: {e}\n")

if __name__ == "__main__":
    import os
    server = WeatherMCPServer()
    asyncio.run(server.run())
```

### Node.js MCP Server Example

```javascript
#!/usr/bin/env node
/**
 * Example MCP server for database operations.
 * Save as: database_mcp_server.js
 */

const readline = require('readline');
const { Pool } = require('pg');

class DatabaseMCPServer {
    constructor() {
        this.pool = new Pool({
            connectionString: process.env.DATABASE_URL
        });

        this.rl = readline.createInterface({
            input: process.stdin,
            output: process.stdout,
            terminal: false
        });
    }

    async handleRequest(request) {
        const { method, params, id } = request;

        try {
            switch (method) {
                case 'initialize':
                    return this.initializeResponse(id);
                case 'tools/list':
                    return this.listToolsResponse(id);
                case 'tools/call':
                    return await this.callToolResponse(params, id);
                default:
                    return this.errorResponse(id, -32601, `Method not found: ${method}`);
            }
        } catch (error) {
            return this.errorResponse(id, -32603, `Internal error: ${error.message}`);
        }
    }

    initializeResponse(id) {
        return {
            jsonrpc: "2.0",
            id,
            result: {
                protocol_version: "0.1.0",
                capabilities: {
                    tools: true,
                    resources: false,
                    prompts: false
                },
                server_info: {
                    name: "database-server",
                    version: "1.0.0"
                }
            }
        };
    }

    listToolsResponse(id) {
        return {
            jsonrpc: "2.0",
            id,
            result: {
                tools: [
                    {
                        name: "query_database",
                        description: "Execute a read-only SQL query",
                        input_schema: {
                            type: "object",
                            properties: {
                                query: {
                                    type: "string",
                                    description: "SQL query to execute"
                                },
                                params: {
                                    type: "array",
                                    description: "Query parameters",
                                    items: {
                                        type: ["string", "number", "boolean", "null"]
                                    },
                                    default: []
                                }
                            },
                            required: ["query"]
                        }
                    },
                    {
                        name: "list_tables",
                        description: "List all tables in the database",
                        input_schema: {
                            type: "object",
                            properties: {
                                schema: {
                                    type: "string",
                                    description: "Schema name",
                                    default: "public"
                                }
                            }
                        }
                    }
                ]
            }
        };
    }

    async callToolResponse(params, id) {
        const { name, arguments: args } = params;

        let result;
        switch (name) {
            case 'query_database':
                result = await this.queryDatabase(args.query, args.params || []);
                break;
            case 'list_tables':
                result = await this.listTables(args.schema || 'public');
                break;
            default:
                return this.errorResponse(id, -32602, `Unknown tool: ${name}`);
        }

        return {
            jsonrpc: "2.0",
            id,
            result: {
                content: [
                    {
                        type: "text",
                        text: result
                    }
                ]
            }
        };
    }

    async queryDatabase(query, params) {
        // Validate query is read-only
        const readOnlyPattern = /^\s*(SELECT|WITH|EXPLAIN|SHOW)\s+/i;
        if (!readOnlyPattern.test(query)) {
            return "Error: Only read-only queries are allowed";
        }

        try {
            const result = await this.pool.query(query, params);
            return this.formatQueryResult(result);
        } catch (error) {
            return `Query error: ${error.message}`;
        }
    }

    formatQueryResult(result) {
        if (result.rows.length === 0) {
            return "No results found";
        }

        // Format as table
        const headers = Object.keys(result.rows[0]);
        const rows = result.rows.map(row =>
            headers.map(h => String(row[h] ?? 'NULL'))
        );

        // Simple text table
        return [
            headers.join(' | '),
            headers.map(h => '-'.repeat(h.length)).join('-+-'),
            ...rows.map(row => row.join(' | '))
        ].join('\n');
    }

    async listTables(schema) {
        const query = `
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = $1
            ORDER BY table_name
        `;

        try {
            const result = await this.pool.query(query, [schema]);
            const tables = result.rows.map(row => row.table_name);
            return `Tables in schema '${schema}':\n${tables.join('\n')}`;
        } catch (error) {
            return `Error listing tables: ${error.message}`;
        }
    }

    errorResponse(id, code, message) {
        return {
            jsonrpc: "2.0",
            id,
            error: { code, message }
        };
    }

    run() {
        this.rl.on('line', async (line) => {
            try {
                const request = JSON.parse(line);
                const response = await this.handleRequest(request);
                console.log(JSON.stringify(response));
            } catch (error) {
                console.error(`Server error: ${error.message}`);
            }
        });
    }
}

// Start server
const server = new DatabaseMCPServer();
server.run();
```

## MCP Server Configuration

### Add to TunaCode Configuration

```json
{
    "mcp_servers": {
        "weather": {
            "command": "python",
            "args": ["/path/to/weather_mcp_server.py"],
            "env": {
                "WEATHER_API_KEY": "${WEATHER_API_KEY}"
            }
        },

        "database": {
            "command": "node",
            "args": ["/path/to/database_mcp_server.js"],
            "env": {
                "DATABASE_URL": "postgresql://user:pass@localhost/db"
            }
        }
    }
}
```

## Using MCP Tools in TunaCode

Once configured, MCP tools are automatically available:

```bash
# Start TunaCode
tunacode

# MCP servers start automatically
# Tools are discovered and available

> Get the current weather in London
# Uses weather.get_weather tool

> Query the users table to find active users
# Uses database.query_database tool
```

## MCP Server Best Practices

### 1. Error Handling

Always handle errors gracefully:

```python
async def call_tool_response(self, params, request_id):
    try:
        # Tool execution
        result = await self.execute_tool(params)
        return self.success_response(result, request_id)
    except ValidationError as e:
        return self.error_response(request_id, -32602, str(e))
    except ExternalAPIError as e:
        return self.error_response(request_id, -32000, f"API error: {e}")
    except Exception as e:
        # Log for debugging
        logger.exception("Unexpected error in tool execution")
        return self.error_response(request_id, -32603, "Internal server error")
```

### 2. Input Validation

Validate all inputs thoroughly:

```python
def validate_tool_input(self, tool_name: str, arguments: Dict) -> None:
    """Validate tool inputs against schema"""
    schema = self.get_tool_schema(tool_name)

    # Check required fields
    for required in schema.get('required', []):
        if required not in arguments:
            raise ValidationError(f"Missing required field: {required}")

    # Validate types
    properties = schema.get('properties', {})
    for key, value in arguments.items():
        if key in properties:
            expected_type = properties[key]['type']
            if not self.check_type(value, expected_type):
                raise ValidationError(
                    f"Invalid type for {key}: expected {expected_type}"
                )
```

### 3. Resource Management

Properly manage resources:

```python
class MCPServer:
    def __init__(self):
        self.resources = []

    async def initialize(self):
        """Initialize server resources"""
        # Open database connections
        self.db = await create_db_pool()
        self.resources.append(self.db)

        # Start background tasks
        self.cleanup_task = asyncio.create_task(self.cleanup_loop())

    async def shutdown(self):
        """Clean shutdown"""
        # Cancel background tasks
        self.cleanup_task.cancel()

        # Close resources
        for resource in self.resources:
            await resource.close()

    async def run(self):
        """Main server loop with cleanup"""
        try:
            await self.initialize()
            await self.main_loop()
        finally:
            await self.shutdown()
```

### 4. Security Considerations

Implement security measures:

```python
class SecureMCPServer:
    def __init__(self):
        # Rate limiting
        self.rate_limiter = RateLimiter(
            max_requests=100,
            window_seconds=60
        )

        # Authentication
        self.api_key = os.environ.get('MCP_API_KEY')

    async def handle_request(self, request):
        # Check rate limits
        client_id = self.get_client_id(request)
        if not self.rate_limiter.allow(client_id):
            return self.error_response(
                request['id'],
                -32000,
                "Rate limit exceeded"
            )

        # Validate authentication if configured
        if self.api_key:
            provided_key = request.get('auth', {}).get('api_key')
            if provided_key != self.api_key:
                return self.error_response(
                    request['id'],
                    -32001,
                    "Authentication required"
                )

        # Process request
        return await self.process_request(request)
```

### 5. Logging and Monitoring

Add comprehensive logging:

```python
import logging
import time

class MonitoredMCPServer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.metrics = {
            'total_requests': 0,
            'errors': 0,
            'tool_calls': {}
        }

    async def handle_request(self, request):
        start_time = time.time()
        request_id = request.get('id')
        method = request.get('method')

        self.logger.info(f"Request {request_id}: {method}")
        self.metrics['total_requests'] += 1

        try:
            response = await self.process_request(request)

            # Log success
            duration = time.time() - start_time
            self.logger.info(
                f"Request {request_id} completed in {duration:.3f}s"
            )

            return response

        except Exception as e:
            self.metrics['errors'] += 1
            self.logger.exception(
                f"Request {request_id} failed: {e}"
            )
            raise
```

## Advanced MCP Features

### 1. Streaming Responses

For long-running operations:

```python
async def call_tool_response(self, params, request_id):
    tool_name = params['name']

    if tool_name == 'analyze_large_dataset':
        # Return streaming response
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": "Starting analysis...",
                        "streaming": True
                    }
                ]
            }
        }

        # Follow up with progress updates
        await self.send_progress_update(
            request_id,
            "Processing 1000/10000 records..."
        )
```

### 2. Resource Management

MCP supports resource URLs:

```python
def list_resources_response(self, request_id):
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "resources": [
                {
                    "uri": "file:///data/report.pdf",
                    "name": "Monthly Report",
                    "description": "Latest monthly report",
                    "mime_type": "application/pdf"
                },
                {
                    "uri": "db://users/table",
                    "name": "Users Table",
                    "description": "User database table"
                }
            ]
        }
    }
```

### 3. Dynamic Tool Registration

Register tools based on configuration:

```python
class DynamicMCPServer:
    def __init__(self, config_file):
        self.tools = self.load_tools_from_config(config_file)

    def load_tools_from_config(self, config_file):
        """Load tool definitions from configuration"""
        with open(config_file) as f:
            config = json.load(f)

        tools = []
        for tool_config in config['tools']:
            tool = {
                'name': tool_config['name'],
                'description': tool_config['description'],
                'input_schema': tool_config['schema'],
                'handler': self.create_handler(tool_config)
            }
            tools.append(tool)

        return tools

    def create_handler(self, tool_config):
        """Create handler function for tool"""
        if tool_config['type'] == 'http':
            return self.create_http_handler(tool_config)
        elif tool_config['type'] == 'script':
            return self.create_script_handler(tool_config)
        # ... more handler types
```

## Debugging MCP Servers

### 1. Enable Debug Logging

In TunaCode:
```bash
LOG_LEVEL=DEBUG tunacode
```

### 2. Test Server Standalone

Test your MCP server:

```bash
# Send test request
echo '{"jsonrpc":"2.0","method":"initialize","id":1}' | python weather_mcp_server.py

# Expected response
{"jsonrpc": "2.0", "id": 1, "result": {"protocol_version": "0.1.0", ...}}
```

### 3. MCP Server Logs

Add logging to your server:

```python
# Log to stderr (visible in TunaCode logs)
sys.stderr.write(f"[MCP] Received: {request}\n")
sys.stderr.write(f"[MCP] Sending: {response}\n")
```

### 4. Common Issues

**Server not starting:**
- Check command path is correct
- Verify script has execute permissions
- Test command manually

**Tools not appearing:**
- Ensure server responds to 'tools/list'
- Check JSON response format
- Verify tool names are unique

**Tool execution failing:**
- Log tool arguments
- Check error responses
- Verify return format

## Production MCP Servers

### 1. Deployment Considerations

- Use process managers (systemd, supervisor)
- Implement health checks
- Add metrics collection
- Use structured logging

### 2. Scaling

- Use worker pools for CPU-intensive operations
- Implement request queuing
- Add caching where appropriate
- Consider horizontal scaling

### 3. Reliability

- Implement circuit breakers
- Add retry logic
- Use timeouts appropriately
- Handle partial failures

## Summary

MCP integration allows TunaCode to:
- Use external tools seamlessly
- Extend functionality without modifying core
- Integrate with existing services
- Scale tool capabilities independently

Start with simple servers and gradually add features as needed. The MCP protocol provides a flexible foundation for building powerful tool integrations.

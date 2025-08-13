# Performance Optimization - Agent Initialization
_Started: 2025-08-13 15:40:56_
_Agent: default

[1] Finding agent creation logic - located in agent_setup.py
[2] Found agent creation logic - line 118 checks if agent exists, creates new if not
[3] Each tool loads XML prompts synchronously on every agent creation - defusedxml parsing
[4] MCP servers loaded on every agent creation with MCPServerStdio(**conf)

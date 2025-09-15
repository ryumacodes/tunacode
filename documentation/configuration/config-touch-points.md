## Configuration Touch Points

### Loading & Validation
- `src/tunacode/utils/user_configuration.py:33-58` - Main config loading
- `src/tunacode/configuration/defaults.py:11-38` - Default values
- `src/tunacode/core/setup/config_setup.py` - Setup wizard & validation

### Distribution Points
- `src/tunacode/core/setup/coordinator.py` - Setup orchestration
- `src/tunacode/core/setup/environment_setup.py:29-49` - Env var export
- `src/tunacode/core/agents/agent_config.py:45-67` - Agent configuration

### Runtime Updates
- `src/tunacode/cli/commands/implementations/model.py:162-170` - Model switching
- `src/tunacode/utils/user_configuration.py:89-97` - Config persistence
- Session state in `StateManager.session.user_config`

### Tool Configuration
- `src/tunacode/tools/base.py:23-41` - Tool schema validation
- `src/tunacode/services/mcp.py:61-108` - MCP server config
- Individual tool settings in `settings.ripgrep`, `tool_ignore`, etc.

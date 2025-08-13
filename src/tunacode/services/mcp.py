"""
Module: sidekick.services.mcp

Provides Model Context Protocol (MCP) server management functionality.
Handles MCP server initialization, configuration validation, and client connections.
"""

import os
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, AsyncIterator, Dict, List, Optional, Tuple

from pydantic_ai.mcp import MCPServerStdio

from tunacode.exceptions import MCPError
from tunacode.types import MCPServers

if TYPE_CHECKING:
    from mcp.client.stdio import ReadStream, WriteStream

    from tunacode.core.state import StateManager

# Module-level cache for MCP server instances
_MCP_SERVER_CACHE: Dict[str, MCPServerStdio] = {}
_MCP_CONFIG_HASH: Optional[int] = None


class QuietMCPServer(MCPServerStdio):
    """A version of ``MCPServerStdio`` that suppresses *all* output coming from the
    MCP server's **stderr** stream.

    We can't just redirect the server's *stdout* because that is where the JSON‑RPC
    protocol messages are sent.  Instead we override ``client_streams`` so we can
    hand our own ``errlog`` (``os.devnull``) to ``mcp.client.stdio.stdio_client``.
    """

    @asynccontextmanager
    async def client_streams(self) -> AsyncIterator[Tuple["ReadStream", "WriteStream"]]:
        """Start the subprocess exactly like the parent class but silence *stderr*."""
        # Local import to avoid cycles
        from mcp.client.stdio import StdioServerParameters, stdio_client

        server_params = StdioServerParameters(
            command=self.command,
            args=list(self.args),
            env=self.env or os.environ,
        )

        # Open ``/dev/null`` for the lifetime of the subprocess so anything the
        # server writes to *stderr* is discarded.
        #
        # This is to help with noisy MCP's that have options for verbosity
        encoding: Optional[str] = getattr(server_params, "encoding", None)
        with open(os.devnull, "w", encoding=encoding) as devnull:
            async with stdio_client(server=server_params, errlog=devnull) as (
                read_stream,
                write_stream,
            ):
                yield read_stream, write_stream


def get_mcp_servers(state_manager: "StateManager") -> List[MCPServerStdio]:
    """Load MCP servers from configuration with caching.

    Args:
        state_manager: The state manager containing user configuration

    Returns:
        List of MCP server instances (cached when possible)

    Raises:
        MCPError: If a server configuration is invalid
    """
    global _MCP_CONFIG_HASH

    mcp_servers: MCPServers = state_manager.session.user_config.get("mcpServers", {})

    # Calculate hash of current config
    current_hash = hash(str(mcp_servers))

    # Check if config has changed
    if _MCP_CONFIG_HASH == current_hash and _MCP_SERVER_CACHE:
        # Return cached servers
        return list(_MCP_SERVER_CACHE.values())

    # Config changed or first load - clear cache and rebuild
    _MCP_SERVER_CACHE.clear()
    _MCP_CONFIG_HASH = current_hash

    loaded_servers: List[MCPServerStdio] = []
    MCPServerStdio.log_level = "critical"

    for server_name, conf in mcp_servers.items():
        try:
            # Check if this server is already cached
            if server_name not in _MCP_SERVER_CACHE:
                # Create new instance
                mcp_instance = MCPServerStdio(**conf)
                _MCP_SERVER_CACHE[server_name] = mcp_instance

            loaded_servers.append(_MCP_SERVER_CACHE[server_name])
        except Exception as e:
            raise MCPError(
                server_name=server_name,
                message=f"Failed to create MCP server: {str(e)}",
                original_error=e,
            )

    return loaded_servers

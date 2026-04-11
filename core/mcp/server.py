"""
MCP server for the sandbox — port 8079, streamable-HTTP transport.

Transport: streamable-HTTP (2025-03-26 MCP spec)
  POST /mcp  — client → server messages
  GET  /mcp  — server → client SSE stream (for notifications)

Legacy SSE clients: use /mcp/sse if your client only supports the 2024-11 spec.

Tools are split into focused modules; each exposes a register(mcp) function.
New capabilities: add a module to tools/ and call register() here.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from tools import files, process, system

mcp = FastMCP(
    name="sandbox",
    instructions=(
        "You are connected to a pesnik/sandbox container. "
        "Use shell_execute for one-shot commands. "
        "Use process_start / process_logs / process_stop for long-running services. "
        "Use sandbox_info to discover installed tools and active modules. "
        "File tools (file_read, file_write, file_list, file_delete) provide direct FS access."
    ),
)

system.register(mcp)
files.register(mcp)
process.register(mcp)

# ASGI app for uvicorn — supervisord runs:
#   uvicorn server:app --host 0.0.0.0 --port 8079
# Streamable-HTTP: POST + GET on /mcp (MCP 2025-03-26 spec)
app = mcp.streamable_http_app()

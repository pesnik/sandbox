"""
REST API for the sandbox — port 8091.

Intentionally minimal: shell execution and file I/O.
Process lifecycle management lives in the MCP server (agent-native interface).

Docs: http://localhost:8080/v1/docs
"""

from __future__ import annotations

import socket
from typing import Any

from fastapi import FastAPI

from routers import files, shell

app = FastAPI(
    title="Sandbox API",
    version="1.0.0",
    docs_url="/v1/docs",
    openapi_url="/v1/openapi.json",
)

app.include_router(shell.router)
app.include_router(files.router)


def _port_open(port: int, timeout: float = 0.5) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=timeout):
            return True
    except OSError:
        return False


@app.get("/v1/status")
async def status() -> dict[str, Any]:
    """Liveness of internal services. Used by /readyz proxy."""
    return {
        "api": True,
        "mcp": _port_open(8079),
    }

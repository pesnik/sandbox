"""
MCP server E2E tests.

Uses raw HTTP against the streamable-HTTP transport endpoint.
The server responds with SSE-encoded JSON-RPC: `event: message\ndata: {...}`.
Session IDs are maintained across calls within each test via the _Session helper.
"""

from __future__ import annotations

import json
import time

import requests


MCP_PATH = "/mcp"


def _parse_sse(text: str) -> dict:
    """Extract JSON from an SSE-encoded response (event: message / data: {...})."""
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("data:"):
            return json.loads(line[len("data:"):].strip())
    raise ValueError(f"no data: line found in SSE response:\n{text[:300]}")


class _Session:
    """Stateful MCP session: tracks session_id for streamable-HTTP."""

    def __init__(self, mcp_url: str):
        self._url = mcp_url.rstrip("/") + MCP_PATH
        self._session_id: str | None = None
        self._seq = 0

    def _next_id(self) -> int:
        self._seq += 1
        return self._seq

    def call(self, method: str, params: dict | None = None) -> dict:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self._session_id:
            headers["Mcp-Session-Id"] = self._session_id

        payload = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": method,
            "params": params or {},
        }
        r = requests.post(self._url, json=payload, headers=headers, timeout=15)
        assert r.status_code in (200, 202), f"HTTP {r.status_code}: {r.text[:200]}"

        # Capture session ID from response header
        sid = r.headers.get("Mcp-Session-Id")
        if sid:
            self._session_id = sid

        return _parse_sse(r.text)

    def initialize(self) -> dict:
        resp = self.call("initialize", {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "0.0.1"},
        })
        assert "result" in resp, f"initialize failed: {resp}"
        return resp

    def tool(self, name: str, arguments: dict | None = None) -> dict:
        resp = self.call("tools/call", {"name": name, "arguments": arguments or {}})
        assert "result" in resp, f"tool call failed: {resp}"
        raw = resp["result"]["content"][0]["text"]
        return json.loads(raw)


def test_mcp_initialize(mcp):
    s = _Session(mcp)
    resp = s.initialize()
    result = resp["result"]
    assert result["serverInfo"]["name"] == "sandbox"
    assert "protocolVersion" in result


def test_mcp_tools_list(mcp):
    s = _Session(mcp)
    s.initialize()
    resp = s.call("tools/list")
    tools = {t["name"] for t in resp["result"]["tools"]}
    assert "shell_execute" in tools
    assert "sandbox_info" in tools
    assert "file_read" in tools
    assert "file_write" in tools
    assert "file_list" in tools
    assert "file_delete" in tools
    assert "process_start" in tools
    assert "process_stop" in tools
    assert "process_status" in tools
    assert "process_logs" in tools
    assert "process_list" in tools


def test_mcp_shell_execute(mcp):
    s = _Session(mcp)
    s.initialize()
    result = s.tool("shell_execute", {"cmd": "echo mcp-ok"})
    assert result["stdout"].strip() == "mcp-ok"
    assert result["exit_code"] == 0


def test_mcp_sandbox_info(mcp):
    s = _Session(mcp)
    s.initialize()
    info = s.tool("sandbox_info")
    assert info["image"] == "pesnik/sandbox"
    assert "python3" in info["installed_tools"]


def test_mcp_process_lifecycle(mcp):
    """Start a process, check status, read logs, stop it."""
    s = _Session(mcp)
    s.initialize()

    # Start
    result = s.tool("process_start", {
        "name": "test-e2e",
        "cmd": "bash -c 'echo started; sleep 60'",
    })
    assert result["status"] == "started"

    time.sleep(0.5)

    # Status
    status = s.tool("process_status", {"name": "test-e2e"})
    assert status["status"] == "running"

    # Logs
    logs = s.tool("process_logs", {"name": "test-e2e", "lines": 10})
    assert any("started" in line for line in logs["lines"])

    # List
    procs = s.tool("process_list")
    names = [p["name"] for p in procs["processes"]]
    assert "test-e2e" in names

    # Stop
    stop = s.tool("process_stop", {"name": "test-e2e"})
    assert stop["status"] == "stopped"

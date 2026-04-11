"""
sandbox-client — stdlib-only Python SDK for pesnik/sandbox.

Quick start:
    from sandbox import SandboxClient

    s = SandboxClient()                    # reads SANDBOX_BASE_URL env, default http://localhost:8091
    result = s.shell.execute("ls /root")
    print(result.stdout)

    s.files.write("/tmp/hello.txt", "hello world")
    print(s.files.read("/tmp/hello.txt"))

    s.process.start("server", "python3 -m http.server 9000", cwd="/var/www")
    import time; time.sleep(1)
    print(s.process.logs("server"))
    s.process.stop("server")
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# HTTP helpers (stdlib only)
# ---------------------------------------------------------------------------

def _post(base: str, path: str, body: dict) -> dict:
    url = base.rstrip("/") + path
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


def _get(base: str, path: str) -> dict:
    url = base.rstrip("/") + path
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read())


def _delete(base: str, path: str) -> dict:
    url = base.rstrip("/") + path
    req = urllib.request.Request(url, method="DELETE")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def _qp(path: str, **kwargs) -> str:
    """Append query parameters to a path."""
    return path + "?" + urllib.parse.urlencode(kwargs)


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class ShellResult:
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool


@dataclass
class FileEntry:
    name: str
    type: str       # "file" | "dir" | "unknown"
    size: int
    modified: float


@dataclass
class ProcessStatus:
    name: str
    status: str     # "running" | "stopped" | "crashed"
    pid: int
    exit_code: int | None
    uptime_s: float
    cmd: str


# ---------------------------------------------------------------------------
# Sub-clients
# ---------------------------------------------------------------------------

class ShellAPI:
    def __init__(self, base: str):
        self._b = base

    def execute(self, cmd: str, cwd: str = "/root", timeout: int = 30) -> ShellResult:
        """Run a shell command. Returns stdout, stderr, exit_code, timed_out."""
        r = _post(self._b, "/v1/shell/execute", {"cmd": cmd, "cwd": cwd, "timeout": timeout})
        return ShellResult(
            stdout=r.get("stdout", ""),
            stderr=r.get("stderr", ""),
            exit_code=r.get("exit_code", -1),
            timed_out=r.get("timed_out", False),
        )


class FilesAPI:
    def __init__(self, base: str):
        self._b = base

    def read(self, path: str) -> str:
        return _get(self._b, _qp("/v1/files/read", path=path))["content"]

    def write(self, path: str, content: str) -> int:
        """Write content to path. Returns bytes written."""
        return _post(self._b, "/v1/files/write", {"path": path, "content": content})["bytes"]

    def list(self, path: str) -> list[FileEntry]:
        return [
            FileEntry(name=e["name"], type=e["type"], size=e["size"], modified=e["modified"])
            for e in _get(self._b, _qp("/v1/files/list", path=path)).get("entries", [])
        ]

    def delete(self, path: str) -> bool:
        return _delete(self._b, _qp("/v1/files/delete", path=path)).get("deleted", False)


class ProcessAPI:
    """
    Thin REST wrapper for MCP process tools.
    Only available when calling the MCP server directly via HTTP (not via MCP protocol).
    For full MCP access use an MCP client pointed at http://<host>:8079/mcp.
    """
    def __init__(self, base: str):
        # Process tools live on the MCP port (8079), not the REST API port (8091).
        # Derive mcp_base from the api base_url by replacing the port.
        parsed = urllib.parse.urlparse(base)
        self._b = parsed._replace(netloc=parsed.hostname + ":8079").geturl()

    def start(self, name: str, cmd: str, cwd: str = "/root") -> dict[str, Any]:
        return _post(self._b, "/v1/process/start", {"name": name, "cmd": cmd, "cwd": cwd})

    def stop(self, name: str) -> dict[str, Any]:
        return _post(self._b, "/v1/process/stop", {"name": name})

    def status(self, name: str) -> dict[str, Any]:
        return _get(self._b, _qp("/v1/process/status", name=name))

    def logs(self, name: str, lines: int = 50) -> list[str]:
        return _get(self._b, _qp("/v1/process/logs", name=name, lines=lines)).get("lines", [])

    def list(self) -> list[dict]:
        return _get(self._b, "/v1/process/list").get("processes", [])


class StatusAPI:
    def __init__(self, base: str):
        self._b = base

    def get(self) -> dict[str, bool]:
        """Return {api: bool, mcp: bool}."""
        return _get(self._b, "/v1/status")

    def is_ready(self) -> bool:
        """True when both API and MCP are up."""
        s = self.get()
        return s.get("api", False) and s.get("mcp", False)


# ---------------------------------------------------------------------------
# Top-level client
# ---------------------------------------------------------------------------

class SandboxClient:
    """
    Python client for pesnik/sandbox.

    Reads SANDBOX_BASE_URL env var (default: http://localhost:8091).

        s = SandboxClient()
        s = SandboxClient("http://myhost:8091")
    """

    def __init__(self, base_url: str | None = None):
        url = (base_url or os.getenv("SANDBOX_BASE_URL", "http://localhost:8091")).rstrip("/")
        self.shell = ShellAPI(url)
        self.files = FilesAPI(url)
        self.process = ProcessAPI(url)
        self.status = StatusAPI(url)
        self._base = url

    def __repr__(self) -> str:
        return f"SandboxClient({self._base!r})"

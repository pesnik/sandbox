"""
Named process management — what no other open-source sandbox has.

Agents can start long-running services (web servers, watchers, compilers),
stream their logs, check status, and stop them — all by name.

The registry is in-memory: processes live for the container's lifetime.
"""

from __future__ import annotations

import asyncio
import collections
import time
from typing import Any

from mcp.server.fastmcp import FastMCP

# name → {proc, logs, cmd, cwd, started_at}
_REGISTRY: dict[str, dict[str, Any]] = {}


async def _drain(stream: asyncio.StreamReader, logs: collections.deque, tag: str) -> None:
    """Background task: read lines from a subprocess stream into the log deque."""
    async for raw in stream:
        line = raw.decode(errors="replace").rstrip()
        logs.append(f"[{tag}] {line}")


def register(mcp: FastMCP) -> None:

    @mcp.tool()
    async def process_start(name: str, cmd: str, cwd: str = "/root") -> dict[str, Any]:
        """
        Start a named long-running process.

        If a process with this name is already running, returns an error.
        Use process_stop first if you need to restart.

        Args:
            name: Unique identifier (e.g. "api-server", "watcher")
            cmd:  Shell command to run
            cwd:  Working directory (default: /root)
        """
        entry = _REGISTRY.get(name)
        if entry and entry["proc"].returncode is None:
            return {"error": f"'{name}' is already running (pid={entry['proc'].pid})"}

        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )
        logs: collections.deque = collections.deque(maxlen=500)
        _REGISTRY[name] = {
            "proc": proc,
            "logs": logs,
            "cmd": cmd,
            "cwd": cwd,
            "started_at": time.time(),
        }
        asyncio.create_task(_drain(proc.stdout, logs, "out"))
        asyncio.create_task(_drain(proc.stderr, logs, "err"))

        return {"name": name, "pid": proc.pid, "status": "started", "cmd": cmd}

    @mcp.tool()
    async def process_stop(name: str, signal: str = "TERM") -> dict[str, Any]:
        """
        Stop a named process gracefully (TERM) or forcefully (KILL).

        Waits up to 5s for TERM; sends KILL if it doesn't exit.
        """
        entry = _REGISTRY.get(name)
        if not entry:
            return {"error": f"no process named '{name}'"}

        proc: asyncio.subprocess.Process = entry["proc"]
        if proc.returncode is not None:
            return {"name": name, "status": "already_stopped", "exit_code": proc.returncode}

        import signal as sig_module
        sig = sig_module.SIGKILL if signal.upper() == "KILL" else sig_module.SIGTERM
        proc.send_signal(sig)

        try:
            await asyncio.wait_for(proc.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()

        return {"name": name, "status": "stopped", "exit_code": proc.returncode}

    @mcp.tool()
    def process_status(name: str) -> dict[str, Any]:
        """
        Get the status of a named process.

        Returns: name, status (running/stopped/crashed), pid, exit_code, uptime_s, cmd.
        """
        entry = _REGISTRY.get(name)
        if not entry:
            return {"error": f"no process named '{name}'"}

        proc: asyncio.subprocess.Process = entry["proc"]
        rc = proc.returncode
        uptime = round(time.time() - entry["started_at"], 1)

        if rc is None:
            status = "running"
        elif rc == 0:
            status = "stopped"
        else:
            status = "crashed"

        return {
            "name": name,
            "status": status,
            "pid": proc.pid,
            "exit_code": rc,
            "uptime_s": uptime,
            "cmd": entry["cmd"],
            "cwd": entry["cwd"],
        }

    @mcp.tool()
    def process_logs(name: str, lines: int = 50) -> dict[str, Any]:
        """
        Return the last N log lines from a named process (stdout + stderr interleaved).

        Logs are buffered up to 500 lines per process. Default: last 50.
        """
        entry = _REGISTRY.get(name)
        if not entry:
            return {"error": f"no process named '{name}'"}

        all_logs = list(entry["logs"])
        tail = all_logs[-lines:] if lines < len(all_logs) else all_logs
        return {"name": name, "lines": tail, "total_buffered": len(all_logs)}

    @mcp.tool()
    def process_list() -> dict[str, Any]:
        """List all known processes and their current status."""
        result = []
        for name, entry in _REGISTRY.items():
            rc = entry["proc"].returncode
            result.append({
                "name": name,
                "status": "running" if rc is None else ("stopped" if rc == 0 else "crashed"),
                "pid": entry["proc"].pid,
                "exit_code": rc,
                "uptime_s": round(time.time() - entry["started_at"], 1),
            })
        return {"processes": result}

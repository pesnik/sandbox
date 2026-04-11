"""
System tools: shell execution + sandbox self-description.

sandbox_info  — what's installed, active modules, resource snapshot
shell_execute — run a shell command, capture stdout/stderr/exit_code
"""

from __future__ import annotations

import asyncio
import os
import shutil
import subprocess
from typing import Any

from mcp.server.fastmcp import FastMCP


def register(mcp: FastMCP) -> None:

    @mcp.tool()
    async def shell_execute(cmd: str, cwd: str = "/root", timeout: int = 30) -> dict[str, Any]:
        """
        Run a shell command. Returns stdout, stderr, exit_code, timed_out.

        Use process_start instead when the command is a long-running service.
        Timeout max is 300s; default is 30s.
        """
        timeout = min(timeout, 300)
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            return {
                "stdout": stdout.decode(errors="replace"),
                "stderr": stderr.decode(errors="replace"),
                "exit_code": proc.returncode,
                "timed_out": False,
            }
        except asyncio.TimeoutError:
            proc.kill()
            await asyncio.wait_for(proc.communicate(), timeout=3.0)
            return {"stdout": "", "stderr": f"timed out after {timeout}s", "exit_code": -1, "timed_out": True}

    @mcp.tool()
    def sandbox_info() -> dict[str, Any]:
        """
        Describe this sandbox environment.

        Returns installed CLI tools, active modules (sidecars), Python version,
        and OS info. Call this first to know what you can do.
        """
        # Interesting binaries agents typically want
        candidates = [
            "python3", "python", "pip3", "pip",
            "node", "npm", "npx",
            "git", "curl", "wget", "jq",
            "vault", "ssh", "rsync",
            "docker", "docker-compose",
        ]
        installed = {b: shutil.which(b) for b in candidates if shutil.which(b)}

        # Active modules = supervisor conf.d entries that aren't built-ins
        builtin_confs = {"nginx.conf", "api.conf", "mcp.conf"}
        module_names: list[str] = []
        conf_dir = "/etc/supervisor/conf.d"
        if os.path.isdir(conf_dir):
            module_names = [
                f[:-5] for f in os.listdir(conf_dir)
                if f.endswith(".conf") and f not in builtin_confs
            ]

        # OS release
        try:
            os_release = subprocess.check_output(
                ["lsb_release", "-ds"], text=True, timeout=3
            ).strip()
        except Exception:
            os_release = "unknown"

        return {
            "image": "pesnik/sandbox",
            "os": os_release,
            "python": os.popen("python3 --version 2>&1").read().strip(),
            "installed_tools": installed,
            "active_modules": module_names,
            "mcp_transport": "streamable-http",
            "api_port": 8091,
            "mcp_port": 8079,
        }

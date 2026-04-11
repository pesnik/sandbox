"""
File system tools: read, write, list, delete.

All paths must be absolute. Parent directories are created automatically on write.
"""

from __future__ import annotations

import os
import stat
from typing import Any

import aiofiles
import aiofiles.os
from mcp.server.fastmcp import FastMCP


def register(mcp: FastMCP) -> None:

    @mcp.tool()
    async def file_read(path: str) -> dict[str, Any]:
        """Read a file and return its content as a string."""
        async with aiofiles.open(path, "r", errors="replace") as f:
            content = await f.read()
        return {"path": path, "content": content}

    @mcp.tool()
    async def file_write(path: str, content: str) -> dict[str, Any]:
        """Write content to a file. Creates parent directories if needed. Returns bytes written."""
        parent = os.path.dirname(path)
        if parent:
            await aiofiles.os.makedirs(parent, exist_ok=True)
        async with aiofiles.open(path, "w") as f:
            await f.write(content)
        return {"path": path, "bytes": len(content.encode())}

    @mcp.tool()
    async def file_list(path: str) -> dict[str, Any]:
        """List directory entries with name, type (file/dir), size, and modified time."""
        names = await aiofiles.os.listdir(path)
        entries = []
        for name in sorted(names):
            full = os.path.join(path, name)
            try:
                st = await aiofiles.os.stat(full)
                entries.append({
                    "name": name,
                    "type": "dir" if stat.S_ISDIR(st.st_mode) else "file",
                    "size": st.st_size,
                    "modified": st.st_mtime,
                })
            except OSError:
                entries.append({"name": name, "type": "unknown", "size": 0, "modified": 0.0})
        return {"path": path, "entries": entries}

    @mcp.tool()
    async def file_delete(path: str) -> dict[str, Any]:
        """Delete a file or empty directory."""
        st = await aiofiles.os.stat(path)
        if stat.S_ISDIR(st.st_mode):
            await aiofiles.os.rmdir(path)
        else:
            await aiofiles.os.remove(path)
        return {"path": path, "deleted": True}

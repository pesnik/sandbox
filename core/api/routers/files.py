"""File I/O — /v1/files/*"""

from __future__ import annotations

import os
import stat
from typing import Any

import aiofiles
import aiofiles.os
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter()


class WriteRequest(BaseModel):
    path: str
    content: str


@router.get("/v1/files/read")
async def files_read(path: str = Query(...)) -> dict[str, Any]:
    try:
        async with aiofiles.open(path, "r", errors="replace") as f:
            content = await f.read()
        return {"path": path, "content": content}
    except FileNotFoundError:
        raise HTTPException(404, f"not found: {path}")
    except IsADirectoryError:
        raise HTTPException(400, f"is a directory: {path}")
    except Exception as exc:
        raise HTTPException(500, str(exc)) from exc


@router.post("/v1/files/write")
async def files_write(req: WriteRequest) -> dict[str, Any]:
    try:
        parent = os.path.dirname(req.path)
        if parent:
            await aiofiles.os.makedirs(parent, exist_ok=True)
        async with aiofiles.open(req.path, "w") as f:
            await f.write(req.content)
        return {"path": req.path, "bytes": len(req.content.encode())}
    except Exception as exc:
        raise HTTPException(500, str(exc)) from exc


@router.get("/v1/files/list")
async def files_list(path: str = Query(...)) -> dict[str, Any]:
    try:
        names = await aiofiles.os.listdir(path)
    except FileNotFoundError:
        raise HTTPException(404, f"not found: {path}")
    except NotADirectoryError:
        raise HTTPException(400, f"not a directory: {path}")
    except Exception as exc:
        raise HTTPException(500, str(exc)) from exc

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
            entries.append({"name": name, "type": "unknown", "size": 0, "modified": 0})
    return {"path": path, "entries": entries}


@router.delete("/v1/files/delete")
async def files_delete(path: str = Query(...)) -> dict[str, Any]:
    try:
        st = await aiofiles.os.stat(path)
        if stat.S_ISDIR(st.st_mode):
            await aiofiles.os.rmdir(path)
        else:
            await aiofiles.os.remove(path)
        return {"path": path, "deleted": True}
    except FileNotFoundError:
        raise HTTPException(404, f"not found: {path}")
    except Exception as exc:
        raise HTTPException(500, str(exc)) from exc

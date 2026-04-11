# sandbox — Agent Guide

## What this is

A lean, MCP-native Docker environment for AI agents.
**Not** a desktop. **Not** a browser. A tool surface.

Image size: ~820MB uncompressed (Ubuntu 22.04 + Vault CLI + mcp[cli] dep tree).
The old agent-sandbox was 2.5GB+ — this is a 3× reduction.
Further reduction is possible by switching base to python:3.12-slim (drops ~300MB)
and using `mcp` without `[cli]` extras. Tracked for v0.2.

Two interfaces to the same container:
- **MCP** (port 8079, streamable-HTTP) — agent-native, rich tooling, process management
- **REST API** (port 8091) — simple, scriptable, SDK-backed

nginx on port 8080 proxies both. `/healthz` and `/readyz` are built in.

---

## Architecture decisions (read before changing anything)

### 1. MCP is primary, REST is secondary
Process lifecycle management (`process_start/stop/logs/status/list`) lives **only** in MCP.
REST has shell + files — nothing more. Reason: keeping REST minimal means the API surface
never breaks. Agents use MCP; scripts/SDK use REST.

### 2. No browser, no VNC, no desktop
Deliberate. Image is ~150MB. Browser automation belongs to a dedicated sidecar
(e.g. Playwright MCP) that connects to this sandbox via the module system.
Do NOT add Chromium, noVNC, xdotool, or xfce to this repo.

### 3. MCP transport: streamable-HTTP (2025-03-26 spec)
`FastMCP.run(transport="streamable-http")` — POST + GET on `/mcp`.
SSE (2024-11 spec) is not exposed. If a client requires SSE, run a separate
SSE-compatible MCP proxy in front. Don't pollute the core with two transports.

### 4. Tools are modules with register(mcp)
Every tool file in `core/mcp/tools/` exposes a single `register(mcp: FastMCP) -> None`.
`server.py` imports and calls them in order. To add a new capability:
1. Create `core/mcp/tools/myfeature.py` with a `register(mcp)` function
2. Add `from tools import myfeature` + `myfeature.register(mcp)` in `server.py`
3. Add tests in `tests/test_mcp.py`
Tool names must be globally unique across all modules.

### 5. Process registry is in-memory, MCP-process-scoped
`tools/process.py` holds a module-level `_REGISTRY` dict. It lives for the lifetime
of the `server.py` Python process. Processes started via MCP are not visible to the
REST API and vice versa (they're separate OS processes). This is correct — pick one
interface and stick with it. Agents use MCP.

### 6. Module system: supervisord conf.d drop-ins
Sidecars that want to run *inside* the core container mount a `.conf` file to
`/sandbox/modules/enabled/`. `entrypoint.sh` copies it into `/etc/supervisor/conf.d/`.
Sidecars that run as separate containers (preferred) just expose `/mcp` on their
own port and are proxied via nginx's `location ~ ^/modules/([^/]+)/` block.
The `sandbox_info` tool lists active modules by reading `/etc/supervisor/conf.d/`.

### 7. Org overlay pattern
`./org/` (gitignored) mounts to `/sandbox/org/` inside the container.
- `org/vault.env` → copied to `/etc/profile.d/vault.sh` for all login shells
- `org/scripts/*` → copied to `/usr/local/bin/` and chmod +x
See `org.example/` for the template. Never commit `org/`.

### 8. Daytona compatibility
`.devcontainer/devcontainer.json` references `ghcr.io/pesnik/sandbox:latest`.
`postStartCommand` calls `/entrypoint.sh` which starts supervisord.
State lives in the `sandbox-home` volume, not the image.

---

## Running locally

```bash
make build          # build image
make up             # start detached
make logs           # tail logs
make shell          # bash into container
make test           # run E2E tests (container must be up)
make ci             # build + up + wait-healthy + test
make down           # stop
make clean          # stop + remove image + volumes
```

---

## Adding a new MCP tool

```python
# core/mcp/tools/myfeature.py
from mcp.server.fastmcp import FastMCP

def register(mcp: FastMCP) -> None:

    @mcp.tool()
    async def my_tool(param: str) -> dict:
        """
        One-line description agents see when choosing tools.

        Longer explanation of behaviour, edge cases, and return shape.
        """
        return {"result": param}
```

Then in `core/mcp/server.py`:
```python
from tools import myfeature
myfeature.register(mcp)
```

---

## Adding a sidecar module

Preferred pattern (separate container):
1. Create `modules/mymodule/docker-compose.yml` that adds a service to `sandbox-net`
2. The service exposes `/mcp` on its own port (e.g. 8082)
3. Agents access it via `http://localhost:8080/modules/mymodule/mcp` (nginx proxies by DNS name)

See `modules/README.md` for the full spec.

---

## Test strategy

Tests in `tests/` are E2E — they hit the running container over HTTP.
No mocks. No unit tests for infrastructure. Reason: the failure modes that matter
are container startup, port binding, and wire protocol correctness.
Run with `make test` (container must be healthy first).

MCP tests (`test_mcp.py`) perform a full JSON-RPC handshake: initialize → tools/list → tools/call.
If a test fails, check `make logs` for the MCP server stderr.

---

## Known sharp edges

1. **Ubuntu 22.04 ships `python3`, not `python`**. All supervisord confs and scripts
   must use `python3`. Do not add a `python` symlink.

2. **process_start tasks leak** if the container restarts — `_REGISTRY` is in-memory.
   Agents should not depend on processes surviving container restarts.

3. **FastMCP.run() does not accept host/port**. Use `mcp.streamable_http_app()` to get
   the ASGI app and run via uvicorn: `uvicorn server:app --host 0.0.0.0 --port 8079`.
   This was discovered against mcp==1.27.0.

4. **FastMCP streamable-HTTP** requires `mcp>=1.3.0`. Earlier versions only have SSE.
   Pin the version in `core/mcp/requirements.txt`.

3. **nginx module proxy** uses Docker's embedded DNS resolver (127.0.0.11).
   This only works inside a Docker network. Direct `docker run` without a network
   will return 502 for `/modules/*` routes — expected behaviour.

4. **org/ directory** must exist on the host (even empty) or the volume mount fails silently.
   `docker compose` creates it as a directory automatically if absent — this is correct.

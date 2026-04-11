# sandbox

A lean, MCP-native Docker environment for AI agents.

**No VNC. No browser. No desktop. Pure tool surface.**
Image: ~820MB uncompressed (3× smaller than agent-sandbox). Roadmap: python:3.12-slim base → ~500MB.

```
┌─────────────────────────────────────────────────────┐
│  pesnik/sandbox                                     │
│                                                     │
│  nginx :8080  ──┬── /v1/    → REST API   :8091     │
│  (gateway)      ├── /mcp    → MCP server :8079     │
│                 ├── /healthz → liveness             │
│                 ├── /readyz  → readiness            │
│                 └── /modules/<name>/mcp → sidecars  │
│                                                     │
│  supervisord                                        │
│    ├── nginx      :8080                             │
│    ├── uvicorn    :8091  (REST API)                 │
│    └── python     :8079  (MCP server)               │
└─────────────────────────────────────────────────────┘
```

## What makes this different

| Feature | This sandbox | Others |
|---|---|---|
| MCP transport | Streamable-HTTP (2025 spec) | SSE only |
| Named process management | `process_start/stop/logs/status` | None |
| Module/sidecar discovery | `sandbox_info` lists active modules | None |
| Image size | ~150MB | 1-3GB |
| Source available | Full source | SDK-only or closed |
| Daytona-ready | `.devcontainer/devcontainer.json` | Varies |

## Quick start

```bash
git clone git@github.com:pesnik/sandbox.git
cd sandbox
make ci          # build + start + test
```

## MCP tools

Connect any MCP client to `http://localhost:8080/mcp`:

| Tool | Description |
|---|---|
| `shell_execute` | Run a shell command, get stdout/stderr/exit_code |
| `sandbox_info` | Discover installed tools, active modules, OS info |
| `file_read` | Read a file |
| `file_write` | Write a file (creates dirs) |
| `file_list` | List a directory |
| `file_delete` | Delete a file or empty dir |
| `process_start` | Start a named long-running process |
| `process_stop` | Stop a named process |
| `process_status` | Get status, pid, uptime of a named process |
| `process_logs` | Get last N log lines from a named process |
| `process_list` | List all known processes |

## REST API

`http://localhost:8080/v1/docs` — interactive Swagger UI.

```bash
# Shell
curl -X POST http://localhost:8091/v1/shell/execute \
  -H 'Content-Type: application/json' \
  -d '{"cmd": "ls /root"}'

# Files
curl -X POST http://localhost:8091/v1/files/write \
  -H 'Content-Type: application/json' \
  -d '{"path": "/tmp/hello.txt", "content": "hello"}'
```

## Python SDK

```python
from sandbox import SandboxClient

s = SandboxClient()                            # SANDBOX_BASE_URL env or http://localhost:8091
result = s.shell.execute("ls /root")
print(result.stdout)

s.files.write("/tmp/test.txt", "hello")
print(s.files.read("/tmp/test.txt"))
```

## Adding modules (sidecars)

See `modules/README.md`. Sidecars join `sandbox-net` and expose `/mcp`.
nginx proxies them at `/modules/<name>/mcp`.

## Org overlay

Private scripts and vault config mount into the container at runtime:

```
org/
  vault.env      # → /etc/profile.d/vault.sh
  scripts/       # → /usr/local/bin/  (chmod +x)
```

Copy `org.example/` to `org/` (gitignored) and customize.

## Daytona

`.devcontainer/devcontainer.json` references `ghcr.io/pesnik/sandbox:latest`.
Any Daytona workspace or GitHub Codespace can use this as a base.

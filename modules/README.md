# Modules

Composable sidecars that extend the sandbox with new capabilities.

## Pattern

Each module is a directory with a `docker-compose.yml` that:
1. Defines a service on `sandbox-net`
2. Exposes an MCP endpoint at `/mcp` on its own port
3. Can optionally mount a supervisord `.conf` into `/sandbox/modules/enabled/`
   if it needs a process managed by the core container's supervisord

## Using a module

```bash
docker compose \
  -f docker-compose.yml \
  -f modules/whatsapp/docker-compose.yml \
  up -d
```

Agents access the module's MCP tools via:
```
http://localhost:8080/modules/<service-name>/mcp
```

nginx resolves `<service-name>` by Docker DNS on `sandbox-net`.

## Writing a module

```
modules/
  mymodule/
    docker-compose.yml     # defines the service
    README.md              # what it does, env vars it needs
```

The service must:
- Join network `sandbox-net` (external: true)
- Expose an MCP endpoint (`/mcp` POST + GET) on some port
- Be named consistently (service name = DNS name = nginx proxy target)

## enabled/

`modules/enabled/` is for supervisord `.conf` drop-ins that run *inside* the
core container. This is for lightweight processes that don't warrant a separate
container. Mount the conf at build time via the compose volumes block.

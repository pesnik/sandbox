# Daytona — Multi-Instance Orchestration

Daytona provisions isolated, on-demand sandbox instances from a snapshot.
Each automation run gets its own instance. No shared state. No concurrency conflicts.

## Install Daytona server (self-hosted on 172.16.5.60)

```bash
# On the remote server
curl -sfL https://download.daytona.io/daytona/install.sh | bash
daytona serve &

# Generate an API key
daytona api-key generate autumn-runner
```

Set on the machine running autumn:
```
DAYTONA_API_KEY=<key>
DAYTONA_SERVER_URL=http://172.16.5.60:3986
```

## Register the sandbox as a Daytona template

```bash
# Push the sandbox image to a registry first
docker tag pesnik/sandbox:latest ghcr.io/pesnik/sandbox:latest
docker push ghcr.io/pesnik/sandbox:latest

# Register template (Daytona reads .devcontainer/devcontainer.json)
daytona template create \
  --name sandbox \
  --repo https://github.com/pesnik/sandbox
```

## Create the browser-auth snapshot

Run this **once** after completing Outlook login manually:

```bash
./daytona/snapshot-browser.sh
```

This creates `sandbox-autumn-v1` — a Daytona snapshot with the Outlook
session baked in via the `playwright-profile` volume.

## Workspace lifecycle per autumn run

```python
from daytona_sdk import Daytona, CreateSandboxParams

daytona = Daytona()

# Each run: fresh isolated instance from snapshot
sandbox = daytona.create(CreateSandboxParams(
    snapshot="sandbox-autumn-v1",
))

try:
    run_lc_report(sandbox)
finally:
    sandbox.stop()  # auto-archives after DAYTONA_AUTO_ARCHIVE_INTERVAL
```

## Snapshot strategy

| Snapshot | Contents | Rebuild when |
|---|---|---|
| `sandbox-base` | Core image only | sandbox image updates |
| `sandbox-autumn-v1` | Core + playwright-profile volume (Outlook auth) | Outlook session expires |

Rebuild `sandbox-autumn-v1` by re-running `snapshot-browser.sh` after re-logging in.

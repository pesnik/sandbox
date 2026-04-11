# modules/playwright

Browser automation via `@playwright/mcp` — Microsoft's official Playwright MCP server.

Exposes all browser tools at `/modules/playwright/mcp` through the sandbox nginx gateway.

## Tools provided

| Tool | Description |
|---|---|
| `browser_navigate` | Navigate to a URL |
| `browser_snapshot` | Accessibility tree — what the agent reads |
| `browser_click` | Click by aria-ref from snapshot |
| `browser_type` | Type text into focused element |
| `browser_screenshot` | Capture PNG screenshot |
| `browser_evaluate` | Run JavaScript in page context |
| `browser_select_option` | Select dropdown value |
| `browser_wait_for_load_state` | Wait for navigation/network |

## Startup

```bash
docker compose \
  -f docker-compose.yml \
  -f modules/playwright/docker-compose.yml \
  up -d
```

## First-time Outlook auth (one-time per snapshot)

1. Start in headed mode so you can see the browser:
   ```bash
   PLAYWRIGHT_HEADED=true docker compose \
     -f docker-compose.yml \
     -f modules/playwright/docker-compose.yml \
     up -d playwright
   ```

2. Use a sandbox MCP client (or `browser_navigate` tool) to open Outlook:
   ```
   browser_navigate → https://outlook.office.com
   ```

3. Complete login manually in the browser window (or via noVNC if run on a remote server).

4. Once logged in, the session is saved in the `playwright-profile` volume.

5. **Create a Daytona snapshot** to bake in this auth state:
   ```bash
   ./daytona/snapshot-browser.sh
   ```

After snapshotting: every new Daytona workspace from `sandbox-autumn-v1` starts with Outlook already logged in.

## Profile persistence

The `playwright-profile` volume stores Chrome's user data directory.
In Daytona, volumes persist for the workspace lifetime and are included in snapshots.

## Headless automation (post-login)

Set `PLAYWRIGHT_HEADED=false` (default) for headless automation.
The browser reuses the saved profile so auth is preserved.

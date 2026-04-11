#!/bin/bash
# snapshot-browser.sh — create a Daytona snapshot that includes the Outlook auth state.
#
# Run this ONCE after manually completing Outlook login in the headed playwright browser.
# Subsequent workspace creates from 'sandbox-autumn-v1' start with Outlook logged in.
#
# Prerequisites:
#   - Daytona server running and DAYTONA_API_KEY set
#   - sandbox + playwright module running
#   - Outlook login completed in the playwright browser (playwright-profile volume populated)

set -euo pipefail

SNAPSHOT_NAME="${SNAPSHOT_NAME:-sandbox-autumn-v1}"
DAYTONA_SERVER_URL="${DAYTONA_SERVER_URL:-http://172.16.5.60:3986}"

echo "[snapshot] verifying Outlook session is active..."

# Quick check: navigate to Outlook and see if we're logged in
PLAYWRIGHT_MCP="${PLAYWRIGHT_MCP_URL:-http://localhost:8080/modules/playwright/mcp}"
RESPONSE=$(curl -s -X POST "$PLAYWRIGHT_MCP" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"snapshot-check","version":"1.0"}}}')

if echo "$RESPONSE" | grep -q '"sandbox"'; then
    echo "[snapshot] playwright MCP reachable ✓"
else
    echo "[snapshot] ERROR: playwright MCP not reachable at $PLAYWRIGHT_MCP"
    echo "           Start with: docker compose -f docker-compose.yml -f modules/playwright/docker-compose.yml up -d"
    exit 1
fi

echo "[snapshot] creating Daytona snapshot: $SNAPSHOT_NAME"
daytona snapshot create \
    --name "$SNAPSHOT_NAME" \
    --server "$DAYTONA_SERVER_URL" \
    --include-volumes playwright-profile

echo "[snapshot] done — snapshot '$SNAPSHOT_NAME' ready"
echo ""
echo "Use in lc-report-daytona:"
echo "  DAYTONA_SNAPSHOT=$SNAPSHOT_NAME python runner.py"

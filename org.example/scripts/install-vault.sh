#!/bin/bash
# Install HashiCorp Vault CLI
#
# Installs to /root/.local/bin/vault — persisted via the sandbox-home volume.
# Runs at every container startup; skips silently if already installed.
#
# Version is pinned; bump VAULT_VERSION to upgrade.
# Supports amd64 and arm64.

set -euo pipefail

VAULT_VERSION="${VAULT_VERSION:-1.18.3}"
VAULT_BIN="/root/.local/bin/vault"

if [ -x "$VAULT_BIN" ]; then
    echo "[vault] already installed: $($VAULT_BIN version | head -1)"
    exit 0
fi

ARCH=$(uname -m)
case "$ARCH" in
    x86_64)  VAULT_ARCH="amd64" ;;
    aarch64) VAULT_ARCH="arm64" ;;
    *)       echo "[vault] unsupported arch: $ARCH"; exit 1 ;;
esac

ZIP="vault_${VAULT_VERSION}_linux_${VAULT_ARCH}.zip"
URL="https://releases.hashicorp.com/vault/${VAULT_VERSION}/${ZIP}"

echo "[vault] installing ${VAULT_VERSION} (${VAULT_ARCH})..."
cd /tmp
wget -q "$URL" -O "$ZIP"
unzip -q "$ZIP" vault
mv vault "$VAULT_BIN"
chmod +x "$VAULT_BIN"
rm -f "$ZIP"
echo "[vault] installed: $($VAULT_BIN version | head -1)"

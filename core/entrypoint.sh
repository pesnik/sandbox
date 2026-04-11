#!/bin/bash
set -euo pipefail

# ---------------------------------------------------------------------------
# Module supervisord confs — drop-ins from /sandbox/modules/enabled/
# Sidecars mount their .conf here; entrypoint copies them into conf.d
# ---------------------------------------------------------------------------
if ls /sandbox/modules/enabled/*.conf 2>/dev/null | grep -q .; then
    cp -f /sandbox/modules/enabled/*.conf /etc/supervisor/conf.d/
    echo "[entrypoint] loaded module configs: $(ls /sandbox/modules/enabled/*.conf | xargs -n1 basename | tr '\n' ' ')"
else
    echo "[entrypoint] no module configs in /sandbox/modules/enabled/"
fi

# ---------------------------------------------------------------------------
# Org overlay — gitignored, private scripts + vault env
# Mount: ./org:/sandbox/org:ro  (see docker-compose.yml)
# ---------------------------------------------------------------------------
if [ -d /sandbox/org/scripts ]; then
    count=0
    for f in /sandbox/org/scripts/*; do
        [ -f "$f" ] || continue
        cp "$f" /usr/local/bin/
        chmod +x "/usr/local/bin/$(basename "$f")"
        count=$((count + 1))
    done
    [ "$count" -gt 0 ] && echo "[entrypoint] installed $count org script(s)"
fi

if [ -f /sandbox/org/vault.env ]; then
    cp /sandbox/org/vault.env /etc/profile.d/vault.sh
    chmod 644 /etc/profile.d/vault.sh
    echo "[entrypoint] vault env → /etc/profile.d/vault.sh"
fi

# ---------------------------------------------------------------------------
# Ensure log dirs exist
# ---------------------------------------------------------------------------
mkdir -p /var/log/nginx /var/run

# ---------------------------------------------------------------------------
# supervisord — foreground, PID 1
# ---------------------------------------------------------------------------
echo "[entrypoint] starting supervisord"
exec /usr/bin/supervisord -n -c /etc/supervisor/supervisord.conf

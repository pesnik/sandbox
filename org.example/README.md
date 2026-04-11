# org.example

Template for your private org overlay. Copy to `org/` (gitignored).

```
cp -r org.example org
```

## Structure

```
org/
  vault.env        # sourced as /etc/profile.d/vault.sh in all login shells
  scripts/
    install-vault.sh   # example: installs vault CLI to /root/.local/bin
    your-script.sh     # any executable — copied to /usr/local/bin at startup
```

## How it works

`entrypoint.sh` at container startup:
1. Copies `org/scripts/*` → `/usr/local/bin/` (chmod +x)
2. Copies `org/vault.env` → `/etc/profile.d/vault.sh`

Scripts run as root, on every container start. Make them idempotent.

## Vault example

`org.example/scripts/install-vault.sh` installs the Vault CLI binary to
`/root/.local/bin/vault`, which persists across restarts via the `sandbox-home`
volume. First startup downloads the binary; subsequent starts skip it.

To use:
```bash
cp -r org.example org
cp org/vault.env.example org/vault.env
# Edit org/vault.env with your VAULT_ADDR
# Copy your vault token:
cp ~/.vault-token org/   # or mount it via docker-compose volumes
```

# Syncthing Vault Sync Setup

For syncing an Obsidian vault between a local machine and a headless server.

## Server-Side Setup

```bash
# Install
sudo apt-get install -y syncthing

# Create vault directory
mkdir -p ~/obsidian-vault

# Start (use absolute paths — tilde expansion fails with --home flag)
syncthing --no-browser --home=/home/user/.config/syncthing
```

## Device Connection

1. Get the server's Device ID from the startup log or `syncthing --device-id`
2. Share it with the user — they add it on their Syncthing GUI as a Remote Device
3. Get the user's Device ID back, add it to `config.xml`:
```xml
<device id="USER-DEVICE-ID" name="User-PC" compression="metadata" introducer="false" skipIntroductionRemovals="false" introducedBy="">
    <address>dynamic</address>
    <paused>false</paused>
    <autoAcceptFolders>true</autoAcceptFolders>
</device>
```

## Pitfalls

- **Tilde expansion:** `--home=~/.config/syncthing` does NOT expand the tilde. Always use the full absolute path.
- **Config location:** cert.pem and config.xml live under `--home` directory, NOT `~/.local/state/`.
- **Relay connections:** When both sides are behind NAT, Syncthing auto-uses relay servers. Connections may drop and reconnect frequently — this is normal and sync still works.
- **Folder auto-accept:** Set `autoAcceptFolders=true` on both device entries so the server auto-accepts folders the user shares.
- **Restart after config change:** Kill the process and restart for config changes to take effect.
- **Background process:** Use `background=true` + no `notify_on_complete` (daemon, never exits).

## Post-Connection

Set `OBSIDIAN_VAULT_PATH=~/obsidian-vault` in `~/.hermes/.env` for automatic vault path resolution.
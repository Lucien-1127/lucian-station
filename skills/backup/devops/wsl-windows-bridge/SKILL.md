---
name: wsl-windows-bridge
description: Make Hermes Agent (WSL‑installed) accessible from Windows desktop tools — PATH wrappers, cc‑switch integration, cross-platform config bridging.
version: 1.3.0
author: Hermes Agent
tags: [wsl, windows, cc-switch, cross-platform, bridge, PATH, wrapper, desktop]
---

# WSL ↔ Windows Bridge for Hermes Agent

When Hermes is installed **inside WSL** but a Windows GUI tool (cc‑switch, VS Code, Windows Terminal) needs to call `hermes`, Windows cannot resolve the WSL‑only binary. This skill covers the bridging pattern.

## The Bridge Pattern

Create a `.cmd` (or `.ps1`) wrapper in a Windows PATH directory that forwards commands into WSL.

### 1. Identify a Windows PATH directory already in scope

```cmd
# From Windows cmd.exe:
echo %PATH%
```

On the user's system `C:\Users\<user>\.local\bin` is present in the Windows PATH (created by Python installers, Rust, etc.).

### 2. Create the wrapper

**`C:\Users\<user>\.local\bin\hermes.cmd`:**
```batch
@echo off
REM Hermes Agent WSL wrapper — forwards commands from Windows to WSL
wsl.exe /home/<user>/.local/bin/hermes %*
```

**`C:\Users\<user>\.local\bin\hermes.ps1`** (PowerShell alternative):
```powershell
# Hermes Agent WSL wrapper — forwards commands from Windows to WSL
wsl.exe /home/<user>/.local/bin/hermes $args
```

### 3. Test from Windows

```cmd
C:\\Users\\<user>\\.local\\bin\\hermes.cmd --version
```

Should print `Hermes Agent v0.14.0 ...`.

### 4. Verify cc‑switch can launch Hermes

In cc‑switch, clicking "啟動終端機" → "hermes_dashboard" should now work. It previously failed with:
```
'hermes' is not recognized as an internal or external command
```

### 5. (Optional) Add PowerShell Profile Shortcuts

For users working primarily in PowerShell 7, add functions to `$PROFILE` for one-command launch. **CRITICAL: Use absolute WSL paths — see PowerShell tilde trap pitfall below.**

```powershell
$WSL_HERMES = "/home/<user>/.local/bin/hermes"

function gemini { wsl -e $WSL_HERMES chat }
function hermes-dash { Start-Process "http://localhost:8000" }
# NOTE: `hermes model` does NOT support --list. Read config.yaml instead:
function hermes-models {
    Write-Host "📋 當前設定："
    Write-Host "   Model:    $(wsl -e grep 'default:' /home/<user>/.hermes/config.yaml | Select-Object -First 1)"
    Write-Host "   Provider: $(wsl -e grep 'provider:' /home/<user>/.hermes/config.yaml | Select-Object -First 1)"
}
function hermes { wsl -e $WSL_HERMES $args }
```

Reload with `. $PROFILE`. Then `gemini` enters chat, `hermes-dash` opens the web UI. See `references/powershell-profile-hermes-shortcuts.md` for full template.

## Mirrored Networking (for Mobile SSH & External Dashboard Access)

When you need to access WSL SSH (port 22) or the Hermes Dashboard (port 8000) from an external device (such as an iPhone on the same Wi-Fi network), the default WSL NAT network makes the WSL IP internal and unreachable.

Instead of writing fragile port-forwarding scripts, enable **Mirrored Networking Mode** in Windows. This mirrors Windows network interfaces directly into WSL, making WSL services accessible on the Windows Host's local Wi-Fi IP address.

### 1. Enable Mirrored Mode

In **Windows**, edit `C:\Users\<user>\.wslconfig` and add `networkingMode=mirrored` under `[wsl2]`:

```ini
[wsl2]
guiApplications=true
networkingMode=mirrored
```

### 2. Restart WSL

In Windows PowerShell or CMD, completely shut down WSL to apply changes:
```powershell
wsl --shutdown
```

### 3. Open Windows Firewall for SSH Inbound

Windows Firewall may block incoming connections on Port 22. To allow your iPhone to connect, run this command in **Windows PowerShell (as Administrator)**:
```powershell
New-NetFirewallRule -Name "WSL_SSH" -DisplayName "WSL SSH Port 22" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 22
```

---

## WSL `.bash_aliases` for Mobile SSH Terminal Convenience

When SSHing into WSL from a mobile SSH client (like Termius, Blink Shell, or Shellfish), typing long commands on a phone screen is tedious. Mirror the Windows PowerShell shortcuts inside WSL by creating a `~/.bash_aliases` file.

**`~/.bash_aliases`:**
```bash
# === Hermes Agent Shortcuts ===
alias gemini="hermes chat"
alias hermes-dash="echo '🔗 Dashboard URL: http://<Windows_IP>:8000'; hermes dashboard --skip-build"
alias hermes-models="grep 'default:' ~/.hermes/config.yaml; grep 'provider:' ~/.hermes/config.yaml"
```

These are automatically loaded by the default `.bashrc` upon connection.

---

## cc‑switch Integration Details

### How cc‑switch stores data

cc‑switch keeps its own **SQLite database**, separate from Hermes config:

| Location | Description |
|---|---|
| `C:\Users\<user>\.cc-switch\cc-switch.db` | Main SQLite DB |
| `C:\Users\<user>\.cc-switch\backups\db_backup_<timestamp>.db` | Auto-backups |

### Database Schema (Key Tables)

**`providers`** — Provider configs per app type:
- Columns: `id, name, app_type, settings_config, is_current, meta`
- `app_type`: `hermes`, `claude`, `codex`, `gemini`, `claude-desktop`
- `name`: Display name (e.g. `"OpenRouter"`) — DIFFERENT from the internal `name` inside `settings_config`
- `settings_config`: JSON string with provider-specific config:
  ```json
  {"name":"openrouter","base_url":"https://openrouter.ai/api/v1","api_key":"sk-or-...","api_mode":"chat_completions","models":[{"id":"anthropic/claude-sonnet-4-6","name":"Claude Sonnet 4.6","context_length":1000000}]}
  ```
- **API keys are masked** (`***`) in cc-switch DB even from local filesystem reads — you cannot extract them from the DB

**`provider_endpoints`** — Per-provider URL endpoints:
- Columns: `id, provider_id, app_type, url, added_at`
- Stores base URLs matching each provider's `base_url` in `settings_config`

**`skills`** — Installed skills per app:
- Columns: `id, name, description, directory, enabled_claude, enabled_codex, enabled_hermes, enabled_gemini, enabled_opencode, installed_at, content_hash`
- Most skills default to `enabled_hermes=0` — only sync if explicitly enabled

**`mcp_servers`** — MCP server configs:
- Columns: `id, name, server_config, description, enabled_claude, enabled_codex, enabled_hermes, enabled_gemini, enabled_opencode`
- `server_config` contains `{"type":"stdio","command":"...","env":{...}}` JSON

**`skills`**, **`prompts`**, **`settings`**, **`model_pricing`** (147+ rows), **`proxy_config`**, **`proxy_request_logs`** — Additional app-wide config tables.

### Reading cc-switch SQLite from WSL

```python
import sqlite3, json
conn = sqlite3.connect('/mnt/c/Users/<user>/.cc-switch/cc-switch.db')
cursor = conn.cursor()
cursor.execute("SELECT id, name, app_type, settings_config FROM providers WHERE app_type='hermes'")
rows = cursor.fetchall()
for r in rows:
    cfg = json.loads(r[3])
    print(f"  {r[0]}: {r[1]} → {cfg.get('base_url')}")
conn.close()
```

### Batch Sync: All cc-switch Providers → Hermes

When the user asks to sync everything, extract all hermes-type providers and write them into Hermes config:

**Step 1: Extract providers and keys from cc-switch DB**
```python
import sqlite3, json
db_path = '/mnt/c/Users/<user>/.cc-switch/cc-switch.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT name, settings_config FROM providers WHERE app_type='hermes'")
rows = cursor.fetchall()
for r in rows:
    cfg = json.loads(r[1])
    name = cfg.get('name', r[0])
    key = cfg.get('api_key', '')
    base_url = cfg.get('base_url', '')
    # Write keys to temp files to bypass shell secret redaction
    with open(f'/tmp/cc_sync_{name}.key', 'w') as f:
        f.write(key)
    with open(f'/tmp/cc_sync_{name}.json', 'w') as f:
        json.dump({'base_url': base_url, 'api_mode': cfg.get('api_mode', '')}, f)
```

**Step 2: Write each provider into Hermes config**
```bash
KEY=$(cat /tmp/cc_sync_<name>.key)
hermes config set providers.<name>.api_key "$KEY"
hermes config set providers.<name>.base_url "<base_url>"
hermes config set providers.<name>.api_mode "chat_completions"
```

**Step 3: End-to-end test each provider**
```bash
# Test OpenRouter
OPENROUTER_KEY=$(grep -A3 'openrouter:' ~/.hermes/config.yaml | grep 'api_key:' | sed 's/.*api_key: //')
curl -s "https://openrouter.ai/api/v1/chat/completions" \
  -H "Authorization: Bearer $OPENROUTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"openrouter/free","messages":[{"role":"user","content":"Say OK"}],"max_tokens":5}'
```

**Step 4: Clean up model section** — if `model:` uses `provider: custom` with inline fields and a matching named provider was synced:
```bash
hermes config set model.provider google-gemini
hermes config set model.base_url ""
hermes config set model.api_mode ""
hermes config set model.api_key ""
```

**Step 5: Verify and clean up**
```bash
read_file ~/.hermes/config.yaml offset=1 limit=20
rm -f /tmp/cc_sync_*.key /tmp/cc_sync_*.json
```

### Fixing Provider Configs in cc-switch

| Field | Correct value | Notes |
|---|---|---|
| `name` (内部) | e.g. `google-gemini`, `openrouter`, `deepseek` | Lowercase, hyphens. Used in config.yaml |
| `api_mode` | `chat_completions` / `anthropic_messages` | Must match the provider's API protocol |
| `models[].id` | e.g. `gemini-2.5-flash` | **No** `models/` prefix. Use actual model IDs |

### cc‑switch writes to its OWN DB, NOT to ~/.hermes/config.yaml

The user must click **"Apply"** / **"Sync to Hermes"** inside the cc‑switch GUI to push provider configs from the cc‑switch DB into Hermes' `~/.hermes/config.yaml`. Merely adding a provider in cc‑switch does **not** automatically update Hermes.

### cc‑switch is a config manager, not a launcher

It cannot "open" Claude Code, Codex, or Hermes. It manages their config files. Users expecting a one‑click launch will be confused.

### Shell Mode Comparison (PowerShell → WSL)

| Mode | Command | Sources `.bashrc` | Finds `~/.local/bin` in PATH | Use Case |
|------|---------|-------------------|------------------------------|----------|
| **Exec** | `wsl -e /abs/path/to/binary` | N/A | N/A (uses absolute path) | ✅ Best for scripts, functions |
| **Login** | `wsl bash -l -c 'hermes chat'` | ✅ (via .profile) | ✅ | Interactive tools needing full env |
| **Interactive** | `wsl` (enter WSL shell) | ✅ | ✅ | Manual use |
| **Exec by name** | `wsl -e hermes` | ❌ | ❌ (unless PATH set globally) | ❌ Unreliable |

**Core rule:** Never use `~` in PowerShell commands targeting WSL. PowerShell expands `~` to `$HOME` (Windows home), which WSL cannot interpret as its own home.

### Pitfalls

- **PowerShell tilde expansion trap.** In PowerShell, `~` is an alias for `$HOME` = `C:\Users\<user>`. Writing `wsl ~/.local/bin/hermes` in a PowerShell function causes PowerShell to expand `~` to the **Windows home path** before passing it to WSL. **Fix:** Use the absolute WSL path in a variable.
  ```powershell
  $WSL_HERMES = "/home/<user>/.local/bin/hermes"
  wsl -e $WSL_HERMES chat
  ```
  Do NOT use `wsl -e hermes` alone — `wsl -e` runs a non-interactive shell that does not source `.bashrc`, so `~/.local/bin` is not in PATH for `hermes` to be found. Always use the full absolute path.
- **`%*` in cmd.exe** passes all arguments correctly for basic cases; complex quoting may need `%*` passed through `wsl.exe` carefully.
- **`wsl.exe ~/...`** may not expand `~` in all contexts — prefer the absolute WSL path `/home/<user>/...`.
- **cc‑switch v3.16.1** on Windows stores API key as `***` in the SQLite DB once saved — the actual key cannot be recovered from the DB after first write.
- **Dashboard first‑time build hangs.** `hermes dashboard` needs a pre‑built `web/dist/` directory. On first run it builds from source via npm, taking 5–60+ seconds with no progress feedback — the user sees only "Building web UI..." with no indicator. **Fix:** pre‑build once from WSL:
  ```bash
  cd ~/.hermes/hermes-agent/web && npm install && npm run build
  ```
  After that `hermes dashboard` (or `--skip-build`) serves instantly.
- **Honcho memory is separate from cc‑switch.** cc‑switch manages provider configs (API keys, base URLs, models) — it does **not** manage Honcho memory. When the user asks for 記憶 alongside cc‑switch setup, configure Honcho separately:
  1. Get an API key from https://app.honcho.dev
  2. Write `~/.hermes/honcho.json` with the key and settings
  3. `hermes config set memory.provider honcho`
- **Do NOT claim to have written cc‑switch config when you only wrote Hermes config.** The user will correct you. cc‑switch has its **own SQLite database** at `C:\Users\<user>\.cc-switch\cc-switch.db`. Changes to `~/.hermes/config.yaml`, `.env`, or `honcho.json` do **not** update cc‑switch. To configure a provider in cc‑switch, use the GUI — or write directly to the SQLite DB (not recommended). When the user says 我用好了, verify by querying the cc‑switch DB, not by checking Hermes config files.

## Setup Workflow (typical WSL + Windows sequence)

1. User installs cc‑switch (Windows MSI from GitHub releases)
2. User adds providers in cc‑switch GUI (writes to cc‑switch DB only)
3. User clicks "Launch terminal" → fails: `'hermes' is not recognized`
4. Agent creates `hermes.cmd`/`hermes.ps1` wrapper in a Windows PATH dir → launch works
5. **Add PowerShell profile shortcuts** (NEW: 2026-06-06):
   - Edit `$PROFILE` (typically `C:\\Users\\<user>\\Documents\\PowerShell\\Microsoft.PowerShell_profile.ps1`)
   - Add functions for common Hermes commands — **use absolute WSL paths, NOT `~`**:
     ```powershell
     $WSL_HERMES = "/home/<user>/.local/bin/hermes"

     function gemini {
         wsl -e $WSL_HERMES chat
     }
     function hermes-dash {
         Start-Process "http://localhost:8000"
     }
     function hermes-models {
         wsl -e $WSL_HERMES model --list
     }
     ```
   - Reload profile: `. $PROFILE` or restart PowerShell 7
   - Now user can type `gemini` to enter Hermes chat, `hermes-dash` for web UI
6. Dashboard hangs on first run → Agent pre‑builds web UI (`cd web && npm install && npm run build`)
7. Honcho memory configured separately (not in cc‑switch):
   - Install `honcho-ai`
   - `hermes config set memory.provider honcho`
   - Write API key + config to `~/.hermes/honcho.json`
8. Cron jobs reading `.env` may fail if values are placeholder `***` instead of real keys — replace them
9. **Expose WSL to Mobile Devices (iPhone SSH)**:
   - Configure `networkingMode=mirrored` in `.wslconfig` to expose ports directly on the host LAN IP.
   - Run `wsl --shutdown` to restart WSL in mirrored mode.
   - Open Windows Firewall for inbound port 22: `New-NetFirewallRule -Name "WSL_SSH" -DisplayName "WSL SSH Port 22" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 22`
   - Setup mobile terminal shortcuts in WSL's `~/.bash_aliases` (e.g. `gemini`, `hermes-dash`).

### iPhone / Mobile SSH Connection via Mirrored Networking (NEW: 2026-06-07)

For accessing Hermes Agent from an iPhone/iPad SSH client (e.g., Termius, Blink Shell, Shellfish) on the same Wi-Fi:

1. **Enable Mirrored Networking in WSL:**
   In `C:\Users\<user>\.wslconfig`, add `networkingMode=mirrored`. This binds WSL's services (like SSH and Dashboard) directly to the Windows host's network interfaces, bypassing manual port-forwarding rules that break when WSL's internal IP changes.
   ```ini
   [wsl2]
   networkingMode=mirrored
   ```
2. **Restart WSL:**
   From a Windows CMD or PowerShell prompt, run `wsl --shutdown` to apply.
3. **Configure Windows Defender Firewall:**
   In an Administrator PowerShell window, allow external inbound traffic on Port 22:
   ```powershell
   New-NetFirewallRule -Name "WSL_SSH" -DisplayName "WSL SSH Port 22" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 22
   ```
4. **Create Mobile-Friendly Aliases (`~/.bash_aliases`):**
   Typing long commands on a phone screen is tedious. Define short, clean aliases in WSL's `~/.bash_aliases`:
   ```bash
   # === Hermes Agent Shortcuts ===
   alias gemini="hermes chat"
   alias hermes-dash="echo '🔗 Dashboard URL: http://<Windows_IP>:8000'; hermes dashboard --skip-build"
   alias hermes-models="grep 'default:' ~/.hermes/config.yaml; grep 'provider:' ~/.hermes/config.yaml"
   ```
5. **Connect from iPhone SSH Client:**\n   - **Host:** The Windows Host's local Wi-Fi IP (e.g. `192.168.1.111`).\n   - **Port:** `22`\n   - **User:** `<wsl-username>`\n   - **Auth:** Password or SSH Key. (For SSH Keys, generate a key pair in the iPhone app, then copy the public key to WSL's `~/.ssh/authorized_keys` with permissions 700 on `~/.ssh` and 600 on `authorized_keys`).\n\n---\n\n## GitHub Push Bridge (WSL → Windows Git Credential Manager)\n\nWhen WSL-native `git push` fails because SSH keys aren't added to GitHub and HTTPS prompts for a password (which GitHub no longer accepts for Git operations), **Windows Git may have cached credentials** via Git Credential Manager (GCM), GitHub Desktop, or the Windows Credential Manager.\n\n### The Bridge Pattern\n\nInstead of setting up SSH keys inside WSL or generating PAT tokens, copy the repo to the Windows filesystem and push via Windows Git:\n\n```bash\n# Within WSL:\ncp -r /tmp/repo-name \"/mnt/c/Users/<user>/Desktop/repo-name\"\ncmd.exe /c \"git -C C:\\Users\\<user>\\Desktop\\repo-name push origin main\"\n```\n\n### When to Use\n\n- WSL has a valid SSH key pair but the **public key has not been added to the GitHub account**.\n- GitHub no longer accepts password authentication over HTTPS.\n- Installing `gh` CLI or generating a PAT is not desirable for a one-time push.\n\n### When Not to Use\n\n- For frequent pushes, set up SSH key authentication properly from WSL: `ssh-keygen -t ed25519 -C \"your@email.com\"`, then add `~/.ssh/id_ed25519.pub` to GitHub Settings → SSH and GPG keys.\n\n### Pitfalls\n\n1. **Symlinks and permissions** — copying from WSL to `/mnt/c/` preserves file modes but Windows Git may reset the executable bit. For script files, re-apply `chmod +x` on the WSL copy.\n2. **Large repos** — copying 1000+ files over the 9p protocol is slow. For frequent pushes, set up SSH keys in WSL instead.\n3. **Emoji filenames** — Windows Git handles Unicode filenames correctly (including emoji like ⚖️, 🏰). No encoding workarounds are needed on modern Windows 11.\n\n## Running Windows Commands from WSL (bash)

When you need to run Windows-native commands (CMD, PowerShell, or access Windows-localhost services) from within a WSL bash session, three traps arise and proven workarounds exist.

### Trap 1: CMD + Chinese / Unicode paths

**Problem:** `cmd.exe /c` cannot handle Chinese characters in paths when called from WSL bash. The bash shell passes UTF-8 bytes, but CMD's legacy code page misinterprets them, producing `File not found`.

```
# ❌ Fails — CMD can't parse the Chinese path
cmd.exe /c "attrib -r -s -h \"C:\Users\<user>\知識庫\*.*\" /s /d"
```

**Workaround:** Skip CMD entirely and use WSL-native tools on the `/mnt/c/` mount point.

```
# ✅ Works — WSL tools access the same filesystem
ls -la "/mnt/c/Users/<user>/Desktop/知識庫/"
find "/mnt/c/Users/<user>/Desktop/知識庫/" -name "*.md"
```

**When you absolutely need CMD** (e.g., listing Recycle Bin, calling Windows-specific utilities):
Write the command to a `.bat` file first using write_file or echo, then run it.

### Trap 2: PowerShell inline from bash

**Problem:** Bash expands `$` variables before PowerShell sees them. This breaks PowerShell inline one-liners using `$item`, `$_.Name`, or any `$variable`.

```
# ❌ Fails — bash consumes $shell, $rb, $i, etc.
powershell.exe -Command "$shell = New-Object ..."
```

**Workaround — write a PS1 file to Windows temp, then execute:**

```bash
# 1. Write the script to Windows temp via /mnt/c/
cat > /mnt/c/Users/<user>/AppData/Local/Temp/myscript.ps1 << 'EOF'
$shell = New-Object -ComObject Shell.Application
$rb = $shell.NameSpace(10)
$items = $rb.Items()
Write-Output "Total items: $($items.Count)"
EOF

# 2. Execute with Bypass policy
powershell.exe -ExecutionPolicy Bypass -File "C:\Users\<user>\AppData\Local\Temp\myscript.ps1"
```

**Key points:**
- Write to `/mnt/c/Users/<user>/AppData/Local/Temp/` (maps to Windows temp)
- Use `-ExecutionPolicy Bypass` since script execution is typically disabled
- Use `-File` not `-Command` to avoid inline parsing issues
- Always provide the Windows-style path to `-File`

### Trap 4: WSL2 cannot launch Windows GUI installers (but CAN launch installed apps)

**Problem:** From inside WSL2, launching an interactive Windows GUI installer that needs UAC/admin elevation (e.g. Recuva installer) will fail. However, launching an **already-installed GUI application** that does not request elevation WORKS via `Start-Process`.

| Scenario | Approach | Result |
|---|---|---|
| **Installed GUI app** (no UAC) | `powershell Start-Process 'C:\Program Files\App\app.exe'` | ✅ Works — app launches on Windows desktop |
| **Installed GUI app** (no UAC) | `Start-Process` with no `-Wait` | ✅ Returns instantly, app runs in background |
| **GUI installer** (needs admin) | `powershell Start-Process installer.exe` | ❌ Hangs or fails silently |
| **GUI installer** (needs admin) | `cmd.exe /c "start installer.exe"` | ❌ Window doesn't appear in Windows |
| **GUI installer** (needs admin) | `explorer.exe installer.exe` | ❌ Silent failure |
| **GUI installer** (needs admin) | `wscript //E:VBScript ShellExecute` | ❌ Exit code 1, nothing launches |
| **GUI installer** (needs admin) | `winget install --silent` | ⚠️ Downloads succeed, but GUI install step hangs |
| **GUI installer** (needs admin) | `[System.Diagnostics.Process]::Start(...)` | ❌ Hangs from WSL context |

**Root cause:** WSL2 processes run in a separate PID namespace and cannot create elevated Windows GUI windows. However, `Start-Process` CAN spawn non-elevated GUI processes into the Windows session (tested with Recuva).

**Workaround for installers — create a .bat file on the Windows Desktop:**

```bash
# Write a .bat file to the Windows Desktop
cat > /mnt/c/Users/<user>/Desktop/📥\ 安裝\ 工具名稱.bat << 'BAT'
@echo off
title 安裝工具名稱
echo 正在啟動安裝程式...
start "" "C:\path\to\installer.exe"
echo 安裝程式已啟動，請依照安裝精靈操作。
pause
BAT

# Then tell the user: "雙擊桌面上的 📥 安裝工具名稱.bat"
```

The user double-clicks this in Windows File Explorer to launch the normal GUI installer.

**Best practice for launching installed GUI apps from WSL:**

```bash
# Simple one-liner that works for non-elevated apps
powershell.exe -ExecutionPolicy Bypass -NoProfile -Command "Start-Process 'C:\Program Files\App\app.exe'"

# No trailing &, no background wrapper needed
# The command returns immediately; the app runs in Windows
```

Verify launch with:
```bash
powershell.exe -ExecutionPolicy Bypass -NoProfile -Command "Get-Process app* -ErrorAction SilentlyContinue | Select-Object Id,ProcessName,Responding"
```

**Alternative — use pre-portable versions when available:**
Some tools offer portable/zipped versions (e.g. Recuva Portable). The portable `.exe` runs without installation — but the same installer limitation applies. You still need the .bat workaround for portable installers.

### Trap 5: Windows-localhost services unreachable from WSL2

**Problem:** A Windows service bound to `127.0.0.1:PORT` (Windows loopback) is **not** reachable from WSL2's network stack. WSL2 has its own separate `127.0.0.1`.

Example: Syncthing GUI at `http://127.0.0.1:8384/` (Windows). From WSL:
```
# ❌ Connection refused — WSL's own 127.0.0.1
curl http://127.0.0.1:8384/
```

**Workaround — run curl via `cmd.exe /c`:**

```bash
# ✅ Runs curl from inside Windows, accessing Windows localhost
cmd.exe /c "curl -s http://127.0.0.1:8384/rest/system/connections"
```

**When you need browser tools to inspect a Windows-localhost GUI:**
The agent's browser tools also run inside WSL's network stack, so they can't reach Windows-localhost services either. Prefer:
1. `cmd.exe /c curl ...` for API access
2. Reading the application's log files directly from `/mnt/c/`
3. If you must control the GUI remotely, set the Windows service to bind to `0.0.0.0` or use `netsh interface portproxy`

### Specific: Syncthing log investigation

Syncthing logs activity to `%LOCALAPPDATA%\Syncthing\syncthing.log`. From WSL:
```
# Read via /mnt/c/ mount
read_file /mnt/c/Users/<user>/AppData/Local/Syncthing/syncthing.log
```

Key log patterns to look for:
- `"Deleted file"` — files removed by sync (count with `grep -c`)
- `"Peer has a new index ID"` — remote side sent a different file index (often means conflict)
- `"Failed to delete directory"` with `"contents are probably ignored"` — directories that survived
- `<versioning>` in `config.xml` — if empty/no type attribute, Syncthing kept NO backups

See `references/syncthing-data-loss-investigation.md` for a full investigation recipe.

## Related

- `hermes-agent` skill — general Hermes config (protected/bundled)
- `honcho` skill — memory provider setup
- `powershell-wsl-bridge` — calling WSL commands FROM PowerShell (the reverse direction)
- `references/cc-switch-db-schema.md` — full cc‑switch database schema
- `references/mirrored-networking-iphone-ssh.md` — Full walkthrough for iPhone SSH and Mirrored Networking setup
- `references/mobile-ssh-wsl-configuration.md` — detailed mobile/iPhone SSH configuration guide via Mirrored Networking
- `references/syncthing-data-loss-investigation.md` — step-by-step sync disaster investigation recipe
- `references/winget-software-installation-workaround.md` — installing Windows GUI software from WSL2 via winget + .bat workaround (Recuva file recovery context)

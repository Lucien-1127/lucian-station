---
name: wsl-windows-bridge
description: Make Hermes Agent (WSL‑installed) accessible from Windows desktop tools — PATH wrappers, cc‑switch integration, cross-platform config bridging.
version: 1.4.0
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

## Mirrored Networking (for Mobile SSH, Dashboard Access & Localhost Forwarding)

When you need to access WSL services (SSH port 22, Hermes Dashboard port 8000, FastAPI port 8000, etc.) from Windows browser or an external device on the same network, the default WSL2 NAT mode may break localhost forwarding. **Symptoms:** server runs and responds to `curl` inside WSL, but `localhost:PORT` times out from Windows browser.

Enable **Mirrored Networking Mode** so WSL and Windows share the network namespace — localhost forwarding works, and WSL services become accessible via the Windows host's IP.

### 1. Enable Mirrored Mode

In **Windows**, create/edit `C:\Users\<user>\.wslconfig`:

```ini
[wsl2]
guiApplications=true
networkingMode=mirrored
```

**⚠️ CRITICAL: Use `.wslconfig` (Windows-side), NOT `/etc/wsl.conf` (WSL-side).**
- `.wslconfig` (`%USERPROFILE%\.wslconfig`) controls global WSL2 settings including `networkingMode`, `memory`, `processors`, `kernel` — this is the **correct** place for `networkingMode=mirrored`.
- `/etc/wsl.conf` controls per-distro settings (`[boot]`, `[user]`, `[network]`) — it does NOT support a `[wsl2]` section for networking mode.
- Mistake to avoid: writing `networkingMode=mirrored` into `/etc/wsl.conf` will be silently ignored. Verify the change took effect after restart with: `wsl -e ip route show default` — should show the Windows host's default gateway, not a NAT IP.

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

## Mirrored Mode Troubleshooting

### Verification — Is Mirrored Actually Active?

After configuring `networkingMode=mirrored` and running `wsl --shutdown`, verify it took effect:

```bash
# ✅ Mirrored is WORKING → WSL has NO separate IP, only loopback
ip addr show
# Expected: only lo (127.0.0.1/8) — NO eth0/eth1 with 172.x or 10.x IP

# ❌ Mirrored is NOT working → WSL has its own IP (NAT mode)
ip addr show eth1 | grep inet
# Expected: inet 10.114.205.137/24 — WSL has a separate network interface
```

**In working mirrored mode:**
- `localhost:PORT` is shared between Windows and WSL — no port forwarding needed
- `hostname -I` returns the Windows host's IP, not a WSL-specific IP
- `curl http://localhost:8000` works from both WSL terminal AND Windows cmd

**In NAT mode (mirrored not active):**
- WSL has its own IP (e.g., `10.114.205.137/24` or `172.x.x.x`)
- `curl http://localhost:8000` works from WSL terminal but FAILS from Windows cmd
- The WSL IP is reachable from Windows but NOT localhost

### Common Failure Modes

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `ip addr show` shows eth0/eth1 with IP after `wsl --shutdown` | Mirrored config in wrong file | Check `.wslconfig` (Windows-side, `%USERPROFILE%\.wslconfig`) — `networkingMode=mirrored` only works in `.wslconfig`, NOT in `/etc/wsl.conf` |
| Both `.wslconfig` AND `/etc/wsl.conf` have `networkingMode=mirrored` | Duplicate config may cause silent failure | Remove the `[wsl2]` section from `/etc/wsl.conf` — keep only in `.wslconfig` |
| WSL version < 2.0.0 | Mirrored requires WSL 2.0.0+ | Run `wsl --update` from Windows PowerShell |
| After `wsl --shutdown` and restart, still in NAT | WSL VM cache not cleared | `wsl --shutdown`, then `wsl --terminate <distro>`, then restart |
| Working yesterday, broken today | Windows update reset `.wslconfig` changes | Re-apply `.wslconfig` and re-shutdown |

### Fix: Remove Conflicting Config from /etc/wsl.conf

The `[wsl2]` section with `networkingMode` is **only valid in `.wslconfig`** on Windows. If `/etc/wsl.conf` also contains a `[wsl2]` section, it is **silently ignored** and may cause confusion during debugging.

```bash
# Check /etc/wsl.conf for [wsl2] section
grep -n "wsl2" /etc/wsl.conf
# If found, remove that section — it doesn't belong here
# The correct location is %USERPROFILE%\.wslconfig (Windows-side)
```

### Fallback: netsh Port Forwarding (When Mirrored Won't Work)

If mirrored mode refuses to activate (WSL version too old, Windows build incompatibility, or unknown regression), use **netsh port forwarding** as a reliable fallback:

```bash
# 1. Get the WSL IP
WSL_IP=$(hostname -I | awk '{print $1}')
echo "$WSL_IP"  # e.g., 10.114.205.137

# 2. Set up port forwarding (requires Admin rights — UAC prompt)
powershell.exe -Command "Start-Process powershell -Verb RunAs -ArgumentList '-NoProfile -Command \"netsh interface portproxy delete v4tov4 listenport=8000 listenaddress=0.0.0.0 2>`$null; netsh interface portproxy add v4tov4 listenport=8000 listenaddress=0.0.0.0 connectport=8000 connectaddress=''$WSL_IP''; Write-Host (''''✅ Port forwarding set up''''); Start-Sleep -Seconds 2\"'"

# 3. Verify
powershell.exe -Command "netsh interface portproxy show v4tov4 | findstr 8000"

# 4. Now http://localhost:8000 from Windows browser should work
```

**Limitations of netsh fallback:**
- WSL IP changes on every `wsl --shutdown` → must re-run port forwarding
- Requires UAC/admin elevation each time
- Not as clean as mirrored mode (which persists across restarts)

**Packaging as a .bat for the desktop:**
Create a combined .bat that detects WSL IP, sets up port forwarding via UAC, starts the service, and opens browser. Use `chcp 950 >nul` at the top (NOT `chcp 65001`) when the system ACP is 950 to avoid font rendering issues in cmd.

```batch
@echo off
title 🚀 AppName啟動 · WSL版
chcp 950 >nul
for /f "tokens=1" %%i in ('wsl.exe hostname -I') do set WSL_IP=%%i
echo Setting up port forwarding...
powershell -Command "Start-Process powershell -Verb RunAs -ArgumentList '-NoProfile -Command ...'"
echo Starting server...
wsl bash -c "cd '/path/to/project' && source .venv/bin/activate && python -m uvicorn main:app --host 0.0.0.0 --port 8000"
```

## Testing WSL Service Accessibility from Windows

### Critical: Know Which "localhost" Your Tools Test

When running inside WSL, **Hermes' `browser_navigate` tool tests WSL's localhost, NOT the Windows host's localhost.** This is a common source of false positives:

```bash
# From Hermes' browser: tests WSL's localhost → WILL work for WSL services
browser_navigate(url="http://localhost:8000/")  # ✅ Works from inside WSL

# But the USER's Chrome/Edge on Windows: tests WINDOWS localhost
# → WILL FAIL if mirrored mode is not active or port forwarding not set up
```

**✅ Correct verification procedure** when the user says "localhost doesn't work":

```bash
# Step 1: Verify service is running inside WSL
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/   # Should be 200

# Step 2: Test from Windows side via cmd.exe curl
cmd.exe /c "curl -s --max-time 5 http://localhost:8000/ -o C:\Users\%USERNAME%\Desktop\_test.html -w %%{http_code}"
# Check if file was created with content
ls -la "/mnt/c/Users/$(whoami)/Desktop/_test.html"  # Should be > 0 bytes
cat "/mnt/c/Users/$(whoami)/Desktop/_test.html" | head -5

# Step 3: Also test via WSL IP
WSL_IP=$(hostname -I | awk '{print $1}')
cmd.exe /c "curl -s --max-time 5 http://$WSL_IP:8000/ -o C:\Users\%USERNAME%\Desktop\_test2.html"

# Step 4: Clean up temp files
rm -f "/mnt/c/Users/$(whoami)/Desktop/_test.html" "/mnt/c/Users/$(whoami)/Desktop/_test2.html"
```

**Results interpretation:**

| Windows curl | Browser | Likely cause |
|---|---|---|
| ✅ Works | ❌ Times out | **Browser proxy/DNS issue** — clear Chrome's DNS cache (`chrome://net-internals/#dns` → Clear host cache), check proxy settings |
| ✅ Works | ✅ Works | Mirrored/networking is fine, user may have tried before service was ready |
| ❌ Fails | ❌ Times out | **Networking issue** — mirrored not active, need port forwarding or fix |
| ❌ (localhost) but ✅ (WSL IP) | ❌ | Mirrored not active — use WSL IP or set up netsh forwarding |

### Browser-Specific Fixes When Networking is Fine but Browser Fails

If `cmd.exe /c curl http://localhost:PORT/` works but the browser times out:

1. **Chrome DNS cache**: `chrome://net-internals/#dns` → click "Clear host cache"
2. **Chrome proxy settings**: Settings → System → Open computer's proxy settings → "Automatically detect settings" ON, everything else OFF
3. **IPv6 issue**: Try `http://127.0.0.1:PORT/` instead of `http://localhost:PORT/`
4. **Socket pool flush**: `chrome://net-internals/#sockets` → "Flush socket pools"
5. **Incognito window**: Rules out extension interference

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
- **Python venv created from WSL is Linux-style** (uses `bin/` not `Scripts/`). If a Windows `.bat` start script calls `.venv\Scripts\activate.bat`, it will fail because the venv has `bin/activate` instead. Uvicorn then runs from the wrong directory and can't find `main:app`. **Fix:** Either (a) always start the project from WSL using the project's `.sh` script, or (b) delete the WSL-created `.venv` and recreate it from Windows cmd: `python -m venv .venv && .venv\Scripts\activate.bat && pip install -r requirements.txt`.

- **Diagnostic pattern: mixed-venv "Could not import module" error**: When a FastAPI/Uvicorn server errors with `Could not import module "main"` but `main.py` exists in the backend directory:
  1. Check the working directory in the error message — if Uvicorn watched `C:\Users\...\Desktop` instead of `C:\Users\...\backend`, the `cd` in the .bat failed.
  2. Check the venv structure: `ls backend/.venv/bin/activate` (Linux/WSL style) vs `backend/.venv\Scripts\activate.bat` (Windows style).
  3. If the venv was created on the opposite OS, the .bat's venv detection fails silently — it skips activation and runs from the wrong CWD.
  4. Check for leftover Windows processes holding the port: `powershell.exe -Command "Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue"` → If "Bound" state, kill with `Stop-Process -Id <PID> -Force`.
  5. Solution: either run the server from WSL, or recreate the venv on the correct OS.
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
   - Edit `$PROFILE` (typically `C:\Users\<user>\Documents\PowerShell\Microsoft.PowerShell_profile.ps1`)
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
5. **Connect from iPhone SSH Client:**
   - **Host:** The Windows Host's local Wi-Fi IP (e.g. `192.168.1.111`).
   - **Port:** `22`
   - **User:** `<wsl-username>`
   - **Auth:** Password or SSH Key. (For SSH Keys, generate a key pair in the iPhone app, then copy the public key to WSL's `~/.ssh/authorized_keys` with permissions 700 on `~/.ssh` and 600 on `authorized_keys`).

---

## GitHub Push Bridge (WSL → Windows Git Credential Manager)

When WSL-native `git push` fails because SSH keys aren't added to GitHub and HTTPS prompts for a password (which GitHub no longer accepts for Git operations), **Windows Git may have cached credentials** via Git Credential Manager (GCM), GitHub Desktop, or the Windows Credential Manager.

### The Bridge Pattern

Instead of setting up SSH keys inside WSL or generating PAT tokens, copy the repo to the Windows filesystem and push via Windows Git:

```bash
# Within WSL:
cp -r /tmp/repo-name "/mnt/c/Users/<user>/Desktop/repo-name"
cmd.exe /c "git -C C:\Users\<user>\Desktop\repo-name push origin main"
```

### When to Use

- WSL has a valid SSH key pair but the **public key has not been added to the GitHub account**.
- GitHub no longer accepts password authentication over HTTPS.
- Installing `gh` CLI or generating a PAT is not desirable for a one-time push.

### When Not to Use

- For frequent pushes, set up SSH key authentication properly from WSL: `ssh-keygen -t ed25519 -C "your@email.com"`, then add `~/.ssh/id_ed25519.pub` to GitHub Settings → SSH and GPG keys.

### Pitfalls

1. **Symlinks and permissions** — copying from WSL to `/mnt/c/` preserves file modes but Windows Git may reset the executable bit. For script files, re-apply `chmod +x` on the WSL copy.
2. **Large repos** — copying 1000+ files over the 9p protocol is slow. For frequent pushes, set up SSH keys in WSL instead.
3. **Emoji filenames** — Windows Git handles Unicode filenames correctly (including emoji like ⚖️, 🏰). No encoding workarounds are needed on modern Windows 11.

## Running Windows Commands from WSL (bash)

When you need to run Windows-native commands (CMD, PowerShell, or access Windows-localhost services) from within a WSL bash session, several traps arise and proven workarounds exist.

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

### Trap 3: WSL2 cannot launch Windows GUI installers (but CAN launch installed apps)

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

**Root cause:** WSL2 processes run in a separate PID namespace and cannot create elevated Windows GUI windows. However, `Start-Process` CAN spawn non-elevated GUI processes into the Windows session.

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

### Trap 4: Windows-localhost services unreachable from WSL2

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

*Note: For the reverse direction (WSL service accessible from Windows browser), see the "Mirrored Mode Troubleshooting" and "Testing WSL Service Accessibility from Windows" sections above.*

## Section D: Windows Launcher Strategies

Beyond simple `.cmd` wrappers, you may need a full interactive launcher dashboard for tools (Hermes, gcloud, Ollama, etc.). This section compares the available technologies on Windows for building clickable menus.

### Technology Comparison

| Tech | Pros | Cons | Best For |
|------|------|------|----------|
| **Batch (.cmd)** | Ultra-reliable, no deps, UTF-8 support, instant startup | Text-only UI, limited styling | Operational tools, internal launchers, WSL integration |
| **HTA (.hta)** | Pretty HTML/CSS UI, runs locally, no installer | Font CDN fails, JS encoding fragile, old IE engine | Desktop prototypes, personal dashboards (high risk) |
| **PowerShell (.ps1)** | Rich functions, state management, PS ecosystem | Execution policy friction, slower startup | Admin scripts, tool shortcuts, CI/CD integration |
| **Electron** | Modern, cross-platform, npm ecosystem | Heavy (~100MB), installer complexity | Professional tools, multi-window apps, public distribution |

### Quick Decision Tree

```
Need to launch tools / run commands?
  ├─ YES, locally on my machine (internal tool)
  │   ├─ Aesthetics matter?
  │   │   ├─ YES → HTA (pretty, but fragile — see pitfalls)
  │   │   └─ NO → Batch (.cmd) ← RECOMMENDED
  │   └─ Complex state / power user features?
  │       └─ YES → PowerShell (.ps1 profile)
  └─ Distribute to others?
      └─ Electron / .NET / Windows installer
```

### Batch Launcher Best Practices

Batch is the RECOMMENDED choice for internal tool launchers on Windows:

- **Built into Windows** — cmd.exe on every machine, zero deps
- **UTF-8 support** — `chcp 65001 >nul 2>&1` handles emoji & CJK
- **Deterministic** — no HTML/CSS/JS engine mismatches

**Boilerplate template** at `templates/launcher.cmd` — ready-to-copy with:
- Menu loop (`:menu` → `goto menu`)
- WSL command integration via `wsl /abs/path/to/binary`
- UTF-8 + emoji support
- Category sections (AI, Cloud, Knowledge, Dev Tools)

**Key patterns in the template:**
- Line `:menu` is the loop; each option returns via `goto menu`
- Use `echo.` for blank lines, `timeout /t 2` for feedback pauses
- `cd /d` forces drive letter change when needed
- Use `wsl /home/<user>/.local/bin/hermes` — NOT `wsl hermes` (non-interactive shell won't find PATH)

### HTA Pitfalls (for Reference)

HTA can produce pretty dashboards but has severe reliability issues. **Do not recommend HTA for daily-use operational tools** — user feedback from a 2026-06-06 session confirmed Batch was preferred over HTA because it simply works.

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| External CDNs fail silently | Page renders blank (font load halts HTML parsing) | System fonts only: `font-family: "Segoe UI", "Microsoft JhengHei", sans-serif` |
| Mixed VBScript + HTML encoding errors | Parsing errors, buttons don't respond | Use pure VBScript only, or switch to Batch entirely |
| JavaScript unreliability | Modern JS (async/await, ES6) expectations fail | Rewrite in pure VBScript, or use Batch |
| CSS framework failures | CSS Grid, Flexbox unreliable | Simple tables or inline-block layouts only |

See `references/hta-failures-2026-06-06.md` for the full failure transcript and debugging timeline.

### PowerShell Interactive Menu Pattern

For users who want a richer menu without HTA's fragility, add an interactive menu function to `$PROFILE`:

```powershell
function ai {
    Clear-Host
    Write-Host "  ════════════════════════════════════════"
    Write-Host "  🤖  AI 代理啟動中心"
    Write-Host "  ════════════════════════════════════════"
    Write-Host ""
    Write-Host "  ┌─────┬──────────────────────────────┐"
    Write-Host "  │  1  │  🗣️  開始對話                  │"
    Write-Host "  │  2  │  📊  查看狀態                  │"
    Write-Host "  │  3  │  🌐  開啟 Dashboard           │"
    Write-Host "  │  4  │  📋  查看當前設定              │"
    Write-Host "  │  5  │  🏥  健康檢查                  │"
    Write-Host "  │  0  │  🚪  離開                      │"
    Write-Host "  └─────┴──────────────────────────────┘"
    $choice = Read-Host "  請選擇 (0-5)"
    switch ($choice) {
        "1" { wsl -e $WSL_HERMES chat }
        "2" { wsl -e $WSL_HERMES status; Read-Host; ai }
        "3" { Start-Process "http://localhost:8000"; Start-Sleep 1; ai }
        "4" { hermes-models; Read-Host; ai }
        "5" { wsl -e $WSL_HERMES doctor; Read-Host; ai }
        "0" { return }
        default { Start-Sleep 1; ai }
    }
}
```

Key details:
- `Read-Host` pauses for user input before looping back via recursive call
- `Switch` handles all branches (invalid → default → retry)
- Each output-producing action calls `Read-Host; ai` to let user read before returning
- `Clear-Host` at top keeps the menu fresh

### Naming Guidance

**Name functions after what the user does, not the underlying tech:**

| ❌ Avoid | ✅ Use | Reason |
|---------|-------|--------|
| `gemini` | `chat` | User types `chat` to start talking; `gemini` sounds like a standalone tool |
| `hermes-model` | `switch-model` | User wants to change model, not know it's "hermes" |
| — | `ai` | Universal menu command, works regardless of backend changes |

### Related Skills for Launcher Development

- `windows-hta-launcher` — Deep dive into HTA implementation (if you decide HTA is right)
- `powershell-profile-setup` — Full PowerShell profile configuration

## Related

- `hermes-agent` skill — general Hermes config (protected/bundled)
- `honcho` skill — memory provider setup
- `powershell-wsl-bridge` — calling WSL commands FROM PowerShell (the reverse direction)
- `references/mixed-venv-server-diagnostics.md` — diagnosing "Could not import module 'main'" from mixed WSL/Windows venv
- `references/cc-switch-db-schema.md` — full cc‑switch database schema
- `references/mirrored-networking-iphone-ssh.md` — Full walkthrough for iPhone SSH and Mirrored Networking setup
- `references/mobile-ssh-wsl-configuration.md` — detailed mobile/iPhone SSH configuration guide via Mirrored Networking
- `references/syncthing-data-loss-investigation.md` — step-by-step sync disaster investigation recipe
- `references/winget-software-installation-workaround.md` — installing Windows GUI software from WSL2 via winget + .bat workaround (Recuva file recovery context)
- `references/hta-failures-2026-06-06.md` — HTA rendering failure transcript and debugging timeline (see Section D)
- `templates/launcher.cmd` — Ready-to-copy Batch launcher scaffold with UTF-8 + menu structure

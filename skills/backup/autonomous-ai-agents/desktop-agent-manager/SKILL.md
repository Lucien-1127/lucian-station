---
name: desktop-agent-manager
description: Configure and sync AI agent settings via desktop GUI tools like cc-switch. Covers provider configs, MCP servers, and skills management through desktop applications that interface with Hermes, Claude, Codex, and Gemini CLI configs.
version: 1.0.0
author: Hermes skill library
tags: [cc-switch, desktop, config-management, provider-sync, MCP, skills-gui]
---

# Desktop Agent Manager Integration

Desktop agent managers (like [cc-switch](https://ccswitch.io)) provide a GUI for configuring multiple AI coding tools from one place. This skill covers how they interact with Hermes Agent and how to sync configurations between the desktop app and Hermes.

## Supported Tools

cc-switch manages: Claude Code, Claude Desktop, Codex, Gemini CLI, OpenCode, OpenClaw, **Hermes Agent**

## Data Storage

cc-switch stores all data in a **local SQLite database**:

| Item | Location |
|------|----------|
| DB file | `~/.cc-switch/cc-switch.db` (on Windows: `C:\Users\<user>\.cc-switch\cc-switch.db`) |
| Tech | SQLite via Tauri 2 backend |
| Hermes configs | Stored in `providers` table with `app_type='hermes'` |

### Database schema (key tables)

| Table | Contains |
|-------|----------|
| `providers` | Provider definitions (name, settings_config JSON, category, sort_index) |
| `mcp_servers` | MCP server configurations |
| `skills` | Skill metadata and per-tool enable flags |
| `settings` | App-level settings (common configs, feature flags) |
| `proxy_config` | Proxy routing and failover config |

## How cc-switch Writes to Hermes

**Important: cc-switch does NOT auto-sync to Hermes config.** It stores configs in its own DB. To apply to Hermes:

1. Open the cc-switch app
2. Select the Hermes provider you want to activate
3. Click **"Apply"** or **"Sync to Hermes"** in the provider panel
4. cc-switch writes the config into `~/.hermes/config.yaml` as a `custom_providers` entry

Without this explicit sync action, the Hermes config remains unchanged even though cc-switch's DB has the data.

### Hermes provider format in cc-switch DB

The `settings_config` JSON column for Hermes providers (`app_type='hermes'`) follows this shape:

```json
{
  "name": "openrouter",
  "base_url": "https://openrouter.ai/api/v1",
  "api_key": "***",
  "api_mode": "chat_completions",
  "models": [
    { "id": "anthropic/claude-sonnet-4-6", "name": "Claude Sonnet 4.6", "context_length": 1000000 }
  ]
}
```

**⚠️ API keys are masked** (`***`) in the cc-switch DB even from local filesystem reads. You cannot extract them from the DB — you must either sync through the GUI or re-enter the key.

## What cc-switch CAN and CANNOT Do

| Capability | Works for Hermes? |
|------------|-------------------|
| Add/switch providers | ✅ Yes, after GUI sync |
| Manage MCP servers | ✅ Yes, bidirectional sync |
| Install/remove skills | ✅ Yes (per-tool enable/disable toggles) |
| System tray quick switch | ✅ Yes |
| Cost tracking dashboard | ✅ Yes |
| **Launch/run agents** | ❌ **No** — config management only |
| Direct Hermes CLI commands | ❌ No |

## Pitfalls

- **"Can't open agents"** — cc-switch is a config manager, not a launcher. Use `hermes chat` or `hermes chat --resume` to start sessions.
- **"cc-switch didn't change Hermes"** — you must click "Apply" or "Sync" in the GUI. Configs stored in the SQLite DB are not auto-written.
- **API keys are invisible** from the DB (masked as `***`). If you need to re-enter a key, paste it in cc-switch's GUI.
- **Skills table may be empty** — cc-switch's skills tab only shows skills installed THROUGH cc-switch, not skills already in `~/.hermes/skills/`. Skills can be synced bidirectionally.
- **Provider config in Hermes may not match** — after syncing from cc-switch, verify with `hermes config show` or check `~/.hermes/config.yaml`.

## Verification

After syncing a provider from cc-switch to Hermes:

```bash
# Check if the provider was written
grep -A5 'custom_providers:' ~/.hermes/config.yaml

# Or check current model/provider
hermes status
```

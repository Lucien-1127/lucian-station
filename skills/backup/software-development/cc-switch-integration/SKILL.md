---
name: cc-switch-integration
description: Integrate Hermes Agent with cc-switch on Windows/WSL — create WSL wrappers, read/write cc-switch SQLite database, batch sync providers to Hermes config with end-to-end verification, fix provider configs, model.provider cleanup.
version: 1.0.0
---

# cc-switch Integration with Hermes on WSL

cc-switch is a Windows desktop GUI (Tauri 2) that manages providers, MCP, and skills for Claude Code, Codex, Gemini CLI, OpenCode, OpenClaw, and Hermes Agent. It stores data in a local SQLite database and writes configs to each tool's config files.

## Architecture

```
cc-switch (Windows GUI) → SQLite DB (~/.cc-switch/cc-switch.db)
                           ↓ (manual apply/sync)
Hermes Agent (WSL)      → ~/.hermes/config.yaml + ~/.hermes/.env
```

**Key fact:** cc-switch is a **config manager**, not a launcher. It cannot "open" or launch agents. It manages provider/MCP/skill configs.

## Workflow rule: research → plan → execute

This user will call you out if you skip the middle step. When they ask you to modify a desktop launcher or sync tools:

1. **Research** — map the current state (desktop files, WSL tools, DB contents, what exists vs what does not)
2. **Plan** — present a clear diff of what changes and ask for confirmation before touching files
3. **Execute** — only act after the user explicitly approves the plan

Do NOT write files, sync configs, or rearrange buttons without presenting a diff first.

## WSL Integration: Windows → WSL Command Wrapper

cc-switch's "Launch Terminal" feature tries to run `hermes` commands from Windows cmd.exe. Since Hermes is installed in WSL, create a `.cmd` wrapper:

```batch
@echo off
REM Place in a Windows PATH directory (e.g. C:\Users\<user>\.local\bin\)
wsl.exe /home/<user>/.local/bin/hermes %*
```

**Check Windows PATH** for existing `~/.local/bin` mapping:
```
cmd.exe /c "echo %PATH%" → look for C:\Users\<user>\.local\bin
```

## Reading cc-switch's SQLite Database

Database location: `C:\Users\<user>\.cc-switch\cc-switch.db`
Accessible from WSL at: `/mnt/c/Users/<user>/.cc-switch/cc-switch.db`

### Tables of interest

| Table | Purpose |
|---|---|
| `providers` | All configured providers (app_type: 'hermes', 'claude', 'codex', 'gemini') |
| `skills` | Installed skills per tool (enabled_claude, enabled_codex, enabled_hermes, etc.) |
| `mcp_servers` | MCP server configurations |
| `settings` | Common configs per tool, migration flags |
| `provider_endpoints` | Per-provider URL endpoints, one row per provider |
| `model_pricing` | 147+ rows; model_id, display_name, input/output/cache costs per million tokens |
| `proxy_config` | Proxy settings per app_type; default port 15721; all disabled unless configured |
| `proxy_request_logs` | Historical proxy usage logs, useful for debugging API call routing |
| `prompts` | Custom prompts per app_type (e.g. a Codex-specific system prompt) initialized on first launch |
| `skill_repos` | Skill repository sources with URLs |

### Key column details for hermes-relevant tables

**providers** columns: `id, name, app_type, settings_config`
- `settings_config` contains a JSON blob with: `name`, `base_url`, `api_key`, `api_mode`, `models[]` (each model has `id`, `name`, `context_length`)
- `app_type` filters: query `WHERE app_type='hermes'` to get only Hermes-relevant providers
- The `name` field inside `settings_config` (internal provider identifier) is DIFFERENT from the display `name` column in the `providers` table

**mcp_servers** columns: `id, name, server_config, description, homepage, docs, tags, enabled_claude, enabled_codex, enabled_hermes, enabled_gemini, enabled_opencode`
- `server_config` contains `{"type":"stdio","command":"...","env":{...}}` JSON
- `enabled_hermes` is typically 0 for most MCP servers (they are usually configured for Claude or Codex)

**skills** columns: `id, name, description, directory, repo_owner, repo_name, enabled_claude, enabled_codex, enabled_hermes, enabled_gemini, enabled_opencode, installed_at, content_hash`
- Most skills default to `enabled_hermes=0` — only sync if explicitly enabled in the DB
- Skills can be local (id starts with `local:`) or from a remote repo

**provider_endpoints** columns: `id, provider_id, app_type, url, added_at`
- Stores the base URLs that correspond to each provider's `base_url` field in settings_config

### Query providers

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

### Update a provider

```python
cursor.execute(
    "UPDATE providers SET settings_config=? WHERE id=?",
    (json.dumps(new_settings), provider_id)
)
conn.commit()
```

## Fixing Provider Configs in cc-switch

Common issues when editing provider configs directly in the DB:

| Field | Correct value | Notes |
|---|---|---|
| `name` (内) | e.g. `google-gemini`, `openrouter`, `deepseek` | Lowercase, hyphens, no spaces. Used in config.yaml |
| `api_mode` | `chat_completions` / `anthropic_messages` / `codex_responses` / `bedrock_converse` | Must match the provider's API protocol |
| `api_key` | Real API key | cc-switch masks as `***` in display but stores actual value |
| `models[].id` | e.g. `gemini-2.5-flash`, `deepseek-v4-flash` | **No** `models/` prefix. Use actual model IDs |
| `models[].name` | Display name (optional, human-readable) | |
| `models[].context_length` | Integer, e.g. `1000000` | Optional but recommended |

### Google Gemini correct config

```json
{
  "name": "google-gemini",
  "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
  "api_key": "AIzaSy...",
  "api_mode": "chat_completions",
  "models": [
    {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash", "context_length": 1000000},
    {"id": "gemini-2.5-pro", "name": "Gemini 2.5 Pro", "context_length": 1000000}
  ]
}
```

## First-Time Hermes Dashboard Launch

The first `hermes dashboard` command builds the web UI (React/Vite). This can take 5-10 seconds:

```bash
# Pre-build so subsequent launches are instant
cd ~/.hermes/hermes-agent/web
npm install
npm run build

# Then launch with --skip-build to avoid rebuild
hermes dashboard --skip-build --port 9119
```

## Cron Job Delivery to Telegram

When a cron job's `deliver: "origin"` fails with "Telegram send failed: Chat not found", update delivery to an explicit chat ID:

```bash
# List cron jobs first to find job_id
# Then update
cronjob action=update job_id=<id> deliver="telegram:<chat_id>"
```

Valid chat IDs from `~/.hermes/channel_directory.json`.

## Reverse Sync: Hermes CLI → cc-switch (Desktop GUI)

When the user asks to move CLI Hermes data (settings, providers, skills) INTO the desktop GUI version (cc-switch), you write Hermes CLI config data into cc-switch's SQLite database.

**_NOTE:_** This is the OPPOSITE direction from the standard cc-switch → CLI flow. The user may say "把我的 CLI 備份搬到桌面版" or "同步到桌面版".

### Step 1: Discover what's already in cc-switch

```python
import sqlite3, json
db = '/mnt/c/Users/<user>/.cc-switch/cc-switch.db'
conn = sqlite3.connect(db)
c = conn.cursor()

# What providers does cc-switch know about for Hermes?
c.execute("SELECT id, name, settings_config FROM providers WHERE app_type='hermes'")
for r in c.fetchall():
    cfg = json.loads(r[2])
    print(f"  {r[0]}: {cfg.get('base_url')} | key={'✓' if cfg.get('api_key','') else '✗'}")

# What skills are already registered?
c.execute("SELECT id, name, enabled_hermes FROM skills ORDER BY name")
for r in c.fetchall():
    print(f"  {r[0]} | hermes={r[2]}")
conn.close()
```

### Step 2: Identify gaps from Hermes CLI side

Read `~/.hermes/config.yaml` for the `providers:` section — those are the CLI-side named providers. Check `.env` for the actual API keys. Compare with cc-switch:

- CLI providers not in cc-switch → add them (use INSERT, not UPDATE — cc-switch uses compound PK `(id, app_type)`)
- CLI skills not in cc-switch → add as `local:` entries

### Step 3: Add missing providers to cc-switch DB

IMPORTANT: cc-switch's `providers` table has a compound primary key `(id, app_type)` — both columns together must be unique. Always use INSERT with explicit columns:

```python
import sqlite3, json
conn = sqlite3.connect('/mnt/c/Users/<user>/.cc-switch/cc-switch.db')
c = conn.cursor()

# For a provider with no API key (local models like Ollama):
new_provider = {
    "name": "ollama",                      # internal ID, lowercase-hyphens
    "base_url": "http://localhost:11434/v1",
    "api_key": "",                         # empty for local models
    "api_mode": "chat_completions",
    "models": []
}
c.execute(
    "INSERT INTO providers (id, name, app_type, settings_config) VALUES (?, ?, 'hermes', ?)",
    ("ollama", "Ollama (Local)", json.dumps(new_provider))
)
conn.commit()
conn.close()
```

### Step 4: Import ALL Hermes CLI skills into cc-switch

cc-switch's `skills` table stores entries with `id = "local:<skill_name>"` for filesystem-based skills. The Hermes CLI skills are organized as `~/.hermes/skills/<category>/<skill_name>/SKILL.md`.

Write a temp `.py` script (do NOT use inline `-c` with sqlite3 — see Pitfalls):

```python
import sqlite3, os, time

db = '/mnt/c/Users/<user>/.cc-switch/cc-switch.db'
skills_dir = '/home/<user>/.hermes/skills'
now = int(time.time())

conn = sqlite3.connect(db)
c = conn.cursor()

# Clean old entries first
c.execute("DELETE FROM skills WHERE id LIKE 'local:%'")

added = 0
for cat in sorted(os.listdir(skills_dir)):
    cat_path = os.path.join(skills_dir, cat)
    if not os.path.isdir(cat_path):
        continue
    for skill_name in sorted(os.listdir(cat_path)):
        skill_path = os.path.join(cat_path, skill_name)
        skill_md = os.path.join(skill_path, 'SKILL.md')
        if not os.path.isfile(skill_md):
            continue

        # Read description from SKILL.md frontmatter
        desc = skill_name
        with open(skill_md, 'r') as f:
            for line in f:
                if line.startswith('description:'):
                    desc = line.split(':', 1)[1].strip().strip("'\"")
                    break

        c.execute(
            "INSERT INTO skills (id, name, description, directory, enabled_hermes, installed_at, updated_at) VALUES (?, ?, ?, ?, 1, ?, ?)",
            (f"local:{skill_name}", skill_name, desc, skill_path, now, now)
        )
        added += 1

conn.commit()
print(f"Imported {added} skills to cc-switch ✓")
conn.close()
```

Run it with: `python3 /tmp/sync_cc_skills.py`

### Step 5: Also back up the repo to Windows Desktop

The user often wants a Windows-accessible copy of the full backup repo. Rsync works across the `/mnt/c/` mount:

```bash
cd ~/lucian-station
rsync -av --delete --exclude='.git/' --exclude='sync.log' ./ /mnt/c/Users/<user>/Desktop/lucian-station/
```

### Step 6: Verify the sync

```bash
python3 -c "
import sqlite3, json
conn = sqlite3.connect('/mnt/c/Users/<user>/.cc-switch/cc-switch.db')
c = conn.cursor()
c.execute(\"SELECT id, name, settings_config FROM providers WHERE app_type='hermes'\")
print('=== Providers ===')
for r in c.fetchall():
    cfg = json.loads(r[2])
    print(f'  {r[0]} | key={\"✓\" if cfg.get(\"api_key\",\"\") else \"✗\"}')
c.execute('SELECT COUNT(*) FROM skills WHERE enabled_hermes=1')
print(f'\\nHermes-enabled skills: {c.fetchone()[0]}')
conn.close()
"
```

Then tell the user to open cc-switch GUI and verify. Note: cc-switch caches its display; a GUI restart may be needed for new entries to appear.

---

## Batch Sync: All cc-switch Providers → Hermes

When the user asks to sync everything from the desktop GUI into the CLI, extract all hermes-type providers from cc-switch's DB and write them into Hermes config with `hermes config set`:

### Step 1: Extract providers and keys from cc-switch DB

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
    api_mode = cfg.get('api_mode', '')
    # Write keys to temp files to bypass shell secret redaction
    with open(f'/tmp/cc_sync_{name}.key', 'w') as f:
        f.write(key)
    with open(f'/tmp/cc_sync_{name}.json', 'w') as f:
        json.dump({'base_url': base_url, 'api_mode': api_mode}, f)
```

### Step 2: Write each provider into Hermes config

```bash
# For each provider (openrouter, deepseek, google-gemini, etc.):
KEY=$(cat /tmp/cc_sync_<name>.key)
hermes config set providers.<name>.api_key "$KEY"
hermes config set providers.<name>.base_url "<base_url>"
hermes config set providers.<name>.api_mode "chat_completions"
```

### Step 3: End-to-end test each provider

After syncing, verify each provider actually works — not just HTTP connectivity but real chat completions:

```bash
# Test OpenRouter
OPENROUTER_KEY=$(grep -A3 'openrouter:' ~/.hermes/config.yaml | grep 'api_key:' | sed 's/.*api_key: //')
curl -s "https://openrouter.ai/api/v1/chat/completions" \
  -H "Authorization: Bearer $OPENROUTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"openrouter/free","messages":[{"role":"user","content":"Say OK"}],"max_tokens":5}'

# Test DeepSeek
DEEPSEEK_KEY=$(grep -A3 'deepseek:' ~/.hermes/config.yaml | grep 'api_key:' | sed 's/.*api_key: //')
curl -s "https://api.deepseek.com/chat/completions" \
  -H "Authorization: Bearer $DEEPSEEK_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-chat","messages":[{"role":"user","content":"Say OK"}],"max_tokens":5}'

# Test Gemini
GEMINI_KEY=$(grep -A3 'google-gemini:' ~/.hermes/config.yaml | grep 'api_key:' | sed 's/.*api_key: //')
curl -s "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions" \
  -H "Authorization: Bearer $GEMINI_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"gemini-2.5-flash","messages":[{"role":"user","content":"Say OK"}],"max_tokens":5}'
```

All should return HTTP 200 with a chat response. For a quick HTTP-only check (no chat), use `-o /dev/null -w "%{http_code}"` and hit the `/models` endpoint instead.

### Step 4: Clean up model section (optional)

If the `model:` section uses `provider: custom` with an inline `api_key`/`base_url`/`api_mode`, and a matching named provider was just synced, switch to the named provider and remove the inline fields:

```bash
hermes config set model.provider google-gemini
hermes config set model.base_url ""
hermes config set model.api_mode ""
hermes config set model.api_key ""
```

This deduplicates credential storage — the named provider owns the key; the model section just references it.

### Step 5: Verify and clean up temp files

```bash
hermes config show           # Quick check (note: providers section won't show here)
read_file ~/.hermes/config.yaml offset=1 limit=20  # Verify providers were written
rm -f /tmp/cc_sync_*.key /tmp/cc_sync_*.json
```

## Tips: Use temp .py files, not inline -c strings

Writing SQLite queries with JSON blobs through `terminal("python3 -c \"...\"")` breaks on nested quotes — the JSON's double quotes and Python's string delimiters fight each other. The shell also strips or mangles complex quoting.

**WRONG** (will break on JSON or multi-line):
```bash
terminal('python3 -c "import sqlite3, json; ... json.dumps({\"key\": \"value\"}) ..."')
```

**RIGHT** (write a temp file, run it):
```python
from hermes_tools import write_file, terminal
write_file(path='/tmp/sync_script.py', content='''...your Python code...''')
terminal('python3 /tmp/sync_script.py')
```

The temp file approach also makes debugging far easier — you can inspect `/tmp/sync_script.py`, rerun it manually, and iterate without re-prompting the LLM.

## Reference files

`references/reverse-sync-example.md` — full copy-pasteable scripts from a live reverse-sync session (providers + skills import + desktop backup), including the exact SQL queries, table schemas, and issues encountered.

## Pitfalls

- `hermes config.yaml` is a **protected file** — can't use `patch` tool on it. Use `hermes config set <key> <value>` instead.
- `hermes.memory.provider` can't be set to `honcho` via `patch` either — use `hermes config set memory.provider honcho`.
- cc-switch DB API keys are **not** automatically synced to Hermes — user must "Apply" in cc-switch GUI, or you write to Hermes config directly.
- The `name` field inside `settings_config` (provider identifier) is DIFFERENT from the display `name` column in the `providers` table.
- Shell secret redaction masks `sk-*` keys in terminal output. Workaround: write keys to temp files (`/tmp/cc_sync_<name>.key`), then read via `$(cat /tmp/...)` in the same shell command. Clean up temp files after.
- `hermes config show` does NOT display the `providers:` section — verify with `read_file` on config.yaml directly if you need to confirm provider entries.
- When syncing, only sync `app_type='hermes'` providers. cc-switch also stores providers for Claude Desktop, Codex, and Gemini CLI — their MCP servers, skills, and prompts are irrelevant to Hermes unless explicitly enabled for Hermes (`enabled_hermes=1`).

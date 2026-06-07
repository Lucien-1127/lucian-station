---
name: line-bot-integration
description: >-
  Build and optimize LINE Bot projects (project name: "Line_boy") with
  multi-AI-backend routing, asynchronous message processing, user access
  control, and cost optimization.
version: 1.1.0
author: 小育 (via agent)
license: MIT
metadata:
  hermes:
    tags: [line, messaging-api, bot, ai-backend, async, whitelist]
    related_skills: [hermes-agent]
---

# LINE Bot Integration (Line_boy)

## Overview

Project name: **Line_boy**. This skill covers patterns for building LINE Messaging API bots with multiple AI backends (OpenRouter, DeepSeek, Gemini, NVIDIA, local Ollama), cost-optimized fallback routing, and production-hardening patterns. The project lives at `~/Desktop/skill/line_bot/`.

## Architecture Patterns

### Multi-Backend AI Routing

A cost-optimized fallback chain ensures availability without burning budget:

```
Primary backend (user-selectable)
  ├── OpenRouter (free $0 models, rate-limited)
  ├── DeepSeek (very cheap API, ~$0.14/M input tokens)
  ├── Gemini 2.5 Flash (generous free tier, 1500 RPD)
  ├── NVIDIA NIM (free credits)
  └── Ollama local (free, ultimate fallback)
```

**Implementation rules in `ai_backends.py`:**
- Each backend gets its own `call_<backend>()` function with the native API format
- The `ask()` function dispatches to the primary backend first, then falls through the chain
- Fallbacks are skipped when the backend's API key is missing
- A `_failed()` helper checks for `"⚠️"` prefix to detect errors
- For OpenRouter (multi-model per backend): iterate through comma-separated model IDs with round-robin retry on rate limits (429), exponential backoff (12s → 24s)

### Async Message Processing

LINE webhook handlers run synchronously; AI inference goes to a `ThreadPoolExecutor`:

```
handle_message(event)
  ├── Reply "⏳ 模型思考中，請稍候..." immediately via Reply API
  ├── Show typing bubble via ShowLoadingAnimation
  └── _executor.submit(process_ai_response, ...)
        ├── build_messages() → ai.ask() → text_filter()
        ├── db.add_message(user, user_text)  ← AFTER AI succeeds (race condition fix!)
        ├── db.add_message(user, assistant_reply)
        └── Push API delivers result
```

### Typing Indicator

```python
from linebot.v3.messaging import ShowLoadingAnimationRequest

line_bot_api.show_loading_animation(
    ShowLoadingAnimationRequest(chat_id=user_id)
)
```

Send before every async AI submission so LINE shows the "typing..." bubble.

## Pitfalls

### 1. Race Condition: Saving User Message Before AI Response

```python
# WRONG — if ai.ask() fails, DB has orphaned user message:
db.add_message(uid, "user", text)       # <- too early!
reply = ai.ask(messages)
db.add_message(uid, "assistant", reply)

# CORRECT — write both messages only after AI succeeds:
reply = ai.ask(messages)
db.add_message(uid, "user", text)       # <- after AI success
db.add_message(uid, "assistant", reply)
```

### 2. OpenRouter 429 Rate Limiting

The 3-round retry pattern with model rotation handles rate limits. After all models fail in a round, wait 12s then 24s. The final fallback message suggests running `/掃描模型` to find available free models.

### 3. Env File Path

Always store `.env` in the parent directory (outside the bot folder) to prevent accidental Git exposure. Use `load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))`.

### 4. Missing Module Import After Refactoring

Refactoring `app.py` (moving `load_dotenv()`, reorganizing imports) can silently drop `import database as db`. The error only surfaces at runtime:

```
NameError: name 'db' is not defined  ← in db.init_db()
```

**Always verify with a dry-run import test after structural changes:**
```bash
python3 -c "import sys; sys.path.insert(0, '.'); import importlib; importlib.import_module('app')" 2>&1
```
A clean import without `NameError` means all local modules resolve.

### 5. Windows + WSL Python Startup

If the Windows host has no Python installed, the `start.ps1` must invoke WSL's Python:

```powershell
# WRONG — no Python on Windows:
Start-Process powershell -ArgumentList @("-NoExit", "-Command", "Set-Location 'dir'; python app.py")

# CORRECT — route through WSL:
Start-Process powershell -ArgumentList @("-NoExit", "-Command",
    "wsl -d Ubuntu --cd 'C:\Users\...\line_bot' -- python3 app.py")
```

The `start.bat` wrapper (which calls `start.ps1` via `powershell -ExecutionPolicy Bypass -File ...`) stays unchanged.

## User Access Control (Whitelist)

**Schema:** `users` table gets `is_active INTEGER DEFAULT 0`.

**Webhook gate:** Before any message processing, check `is_user_active(user_id)`. If inactive and not `BOT_OWNER_ID`, reply "🔒 您尚未獲得使用權限" and return immediately.

**Admin commands:**
- `/allow <user_id>` — activates a user (owner only)
- `BOT_OWNER_ID` env var — owner's LINE user ID, auto-activates on login

## Common Tasks

| Task | Action |
|------|--------|
| Add new AI backend | Create `call_<name>()` function, add env vars, add to `ask()` fallback chain |
| Add model to scanner | Add model ID to `SMART_KEYWORDS` or the per-platform free model lists in `model_scanner.py` |
| Switch backend at runtime | Set `AI_BACKEND` env var + `update_env_key()`, QuickReply menu via `/切換模型` |
| Scan free models | `/掃描模型` (OpenRouter only) or `/掃描全部` (all platforms) |

## Verification Checklist

- [ ] All backends compile: `python3 -c "import py_compile; py_compile.compile('ai_backends.py', doraise=True)"`
- [ ] All modules resolve (catch missing import after refactoring): `python3 -c "import sys; sys.path.insert(0, '.'); import database as db; import ai_backends as ai"`
- [ ] Typing indicator fires before async AI calls
- [ ] User messages stored only after successful AI response
- [ ] Inactive users rejected before processing
- [ ] Fallback chain hits next backend if primary fails

## Reference Files

- `references/lineboy-optimization-session.md` — concrete implementation details from a Line_boy optimization session (cost-optimized routing, whitelist, async fixes, WSL startup)
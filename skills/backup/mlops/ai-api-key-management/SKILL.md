---
name: ai-api-key-management
description: "Manage AI provider API keys across DeepSeek, OpenRouter, OpenAI, and Gemini — encryption vault, connectivity testing, provider-specific troubleshooting."
version: 1.0.0
author: Hermes Agent
tags: [api-keys, providers, gemini, openai, openrouter, deepseek, vault]
---

# AI API Key Management

Manage API keys for AI providers using a Fernet-encrypted vault (`api_manager.py`). Supports conversational key management — user says "update my X key", and the agent handles lookup, decryption, testing, and storage via tools.

## Vault Location

```
C:\Users\ysga1\Desktop\AI API 金鑰管理\api_manager.py
_keys/vault.enc        ← encrypted key store
_keys/.salt            ← PBKDF2 salt
.env.export            ← exported plaintext env file
```

**Master password:** `admin123` (user can change via menu option 7)

## Conversational Workflow (preferred)

User says "update my [provider] key" → agent does this without user running the script:

1. Accept the raw key from user
2. Update vault: `API_MGR_PASSWORD='admin123' python3 api_manager.py --set-key <provider> '<key>' --label '<name>'`
3. Test immediately via Python's urllib against the correct endpoint
4. Optionally sync to `~/.hermes/.env` if needed
5. Report results back

## Provider Reference

### DeepSeek
- **Test URL:** `https://api.deepseek.com/v1/models`
- **Auth:** `Authorization: Bearer {key}`
- **Admin page:** https://platform.deepseek.com/api_keys
- **Key format:** `sk-...`

### OpenRouter
- **Test URL:** `https://openrouter.ai/api/v1/models`
- **Auth:** `Authorization: Bearer {key}`
- **Admin page:** https://openrouter.ai/keys
- **Key format:** `sk-or-v1-...`

### OpenAI
- **Test URL:** `https://api.openai.com/v1/models`
- **Auth:** `Authorization: Bearer {key}`
- **Admin page:** https://platform.openai.com/api-keys
- **Key format:** `sk-proj-...` or `sk-...`

### Gemini (Google)
- **Test URL:** `https://generativelanguage.googleapis.com/v1/models?key={key}` (query param, NOT x-goog-api-key header)
- **Auth:** Query parameter `?key=...`
- **Admin page:** https://aistudio.google.com/app/apikey
- **Key format:** `AIza...` (not `AQ.Ab...`)
- **Active models (2026):** `gemini-2.5-flash`, `gemini-2.5-pro`
- **Deprecated:** `gemini-1.5-flash`, `gemini-2.0-flash`, `gemini-2.0-flash-001`

## Known Failure Patterns

| Error | Meaning | Fix |
|-------|---------|-----|
| Gemini 403 "Lightning dunning decision is deny" | Google Cloud project has unpaid bills | Open https://console.cloud.google.com/billing |
| Gemini 404 "model is no longer available" | Using deprecated model name | Use `gemini-2.5-flash` or check `v1/models` list |
| Gemini 404 "not found for API version" | Using v1beta with wrong model | Use `v1/` not `v1beta/` |
| Any 401/403 | Key invalid or expired | Go to admin page, generate new key |

## CLI Quick Commands (non-interactive)

```bash
# Initialize vault (first time)
API_MGR_PASSWORD='admin123' python3 api_manager.py --init 'admin123'

# Set a key
API_MGR_PASSWORD='admin123' python3 api_manager.py --set-key openai 'sk-xxxx' --label 'primary'

# Test all keys
API_MGR_PASSWORD='admin123' python3 api_manager.py --test

# Check status
API_MGR_PASSWORD='admin123' python3 api_manager.py --status

# Export .env
API_MGR_PASSWORD='admin123' python3 api_manager.py --unlock

# List providers
python3 api_manager.py --list-providers
```

## Testing a Key Programmatically (Python, from execute_code)

For quick testing without the full script, use urllib:

```python
import json, urllib.request

# Example for Gemini (query param auth)
key = 'AIza...'
url = f'https://generativelanguage.googleapis.com/v1/models?key={key}'
req = urllib.request.Request(url, method='GET')
with urllib.request.urlopen(req, timeout=15) as resp:
    data = json.loads(resp.read().decode())

# Example for Bearer auth providers
key = 'sk-...'
url = 'https://api.openai.com/v1/models'
req = urllib.request.Request(url, headers={'Authorization': f'Bearer {key}'}, method='GET')
with urllib.request.urlopen(req, timeout=15) as resp:
    data = json.loads(resp.read().decode())

# Test generateContent on Gemini
url = f'https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={key}'
body = json.dumps({'contents': [{'parts': [{'text': 'Hi'}]}]}).encode()
req = urllib.request.Request(url, data=body, method='POST', headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req, timeout=15) as resp:
    result = json.loads(resp.read().decode())
    text = result['candidates'][0]['content']['parts'][0]['text']
```

## Security

- Keys stored with Fernet encryption (AES-128-CBC) + PBKDF2 key derivation (600K iterations)
- Plaintext `.env.export` files are NEVER committed to git
- getpass has three fallback layers: real TTY → echo input → API_MGR_PASSWORD env var
- Master password can be changed via menu option 7 (destroys old salt)
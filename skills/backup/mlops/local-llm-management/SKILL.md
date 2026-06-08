---
name: local-llm-management
title: Local LLM Management (Ollama on Windows from WSL)
description: Manage Ollama local LLMs installed on Windows while running from WSL. Covers environment variable fixes, model CRUD via API, GGUF import from HuggingFace, and uncensored/heretic model sourcing.
version: 1.0.0
trigger: "User asks about Ollama models, local LLM management, GGUF import, downloading uncensored models, or anything involving running/managing Ollama from WSL."
tags: [ollama, local-llm, gguf, huggingface, wsl, windows, mlops]
platforms: [wsl, windows]
---

# Local LLM Management (Ollama on Windows from WSL)

## Architecture

Ollama is installed on Windows (`C:\Users\ysga1\AppData\Local\Programs\Ollama\ollama.exe`), models stored at `C:\Users\ysga1\.ollama\models\`. Accessed from WSL.

## Critical Pitfall: OLLAMA_MODELS Environment Variable

**Problem**: If `OLLAMA_MODELS` is set to a non-existent path (e.g. `D:\Ollama\models`), `ollama serve` crashes repeatedly with `mkdir D:\Ollama: The system cannot find the path specified`.

**Fix (must use PowerShell for Windows-side env vars)**:
```bash
# Set correct path via PowerShell (User scope — persistent)
cd /mnt/c && powershell.exe -NoProfile -Command \
  "[System.Environment]::SetEnvironmentVariable('OLLAMA_MODELS', 'C:\Users\ysga1\.ollama\models', 'User')"

# Verify
cmd.exe /c "reg query HKCU\Environment /v OLLAMA_MODELS"
```

**Why PowerShell, not cmd.exe**: `cmd.exe /c "set ..."` only affects that one process. `[System.Environment]::SetEnvironmentVariable()` writes to the Windows registry and persists across sessions.

**Pitfall**: Registry changes do NOT take effect for already-running processes. You must restart the process (or the whole terminal session) for the new value to apply. When launching from WSL, the Windows .exe inherits the Windows environment at spawn time.

## Starting Ollama Server from WSL

```bash
# Kill any existing instances first
taskkill.exe /F /IM ollama.exe 2>/dev/null
taskkill.exe /F /IM "ollama app.exe" 2>/dev/null

# Start server (background)
# Use cmd.exe to ensure fresh Windows env var pickup
cmd.exe /c "set OLLAMA_MODELS=C:\Users\ysga1\.ollama\models && C:\Users\ysga1\AppData\Local\Programs\Ollama\ollama.exe serve"

# Or override env var directly for the session
OLLAMA_MODELS="C:\\Users\\ysga1\\.ollama\\models" /mnt/c/Users/ysga1/AppData/Local/Programs/Ollama/ollama.exe serve
```

**Verify server is up**: `curl -s http://localhost:11434/api/tags`

## Model CRUD via API (not CLI)

The `ollama` CLI tries to start its own server, which can conflict. Prefer the REST API when the server is already running:

```bash
# List models
curl -s http://localhost:11434/api/tags | python3 -m json.tool

# Delete a model
OLLAMA_MODELS="C:\\Users\\ysga1\\.ollama\\models" \
  /mnt/c/Users/ysga1/AppData/Local/Programs/Ollama/ollama.exe rm <model:tag>

# Pull a model (from Ollama library)
OLLAMA_MODELS="C:\\Users\\ysga1\\.ollama\\models" \
  /mnt/c/Users/ysga1/AppData/Local/Programs/Ollama/ollama.exe pull <model:tag>
```

## Importing GGUF Models (HuggingFace → Ollama)

For models not in the Ollama library (e.g. uncensored/heretic variants):

### 1. Find the GGUF file on HuggingFace

```bash
# List Q4_K_M files in a repo
curl -s "https://huggingface.co/api/models/<owner>/<repo>" | \
  python3 -c "
import sys, json
data = json.load(sys.stdin)
for s in data.get('siblings', []):
    fn = s.get('rfilename', '')
    if 'Q4_K_M' in fn:
        print(fn)
"
```

### 2. Download the GGUF

```bash
# Direct download (slow for large files)
wget -O /tmp/model.gguf "https://huggingface.co/<owner>/<repo>/resolve/main/<file>.gguf"

# For multimodal models, also download mmproj file
wget -O /tmp/mmproj.gguf "https://huggingface.co/<owner>/<repo>/resolve/main/mmproj-*.gguf"
```

**Speed note**: HuggingFace downloads from WSL can be slow (~300KB/s-1MB/s). For large files (>5GB), consider downloading on Windows directly or using a VPN.

### 3. Create Modelfile and import

```bash
cat > /tmp/Modelfile << 'EOF'
FROM /tmp/model.gguf

# For multimodal models, add projector:
# ADAPTER /tmp/mmproj.gguf

PARAMETER temperature 0.7
PARAMETER num_ctx 8192
EOF

# Import into Ollama
OLLAMA_MODELS="C:\\Users\\ysga1\\.ollama\\models" \
  /mnt/c/Users/ysga1/AppData/Local/Programs/Ollama/ollama.exe create <model-name> -f /tmp/Modelfile
```

## Uncensored / Heretic Model Sources

User prefers uncensored (no safety filter) model variants. Key sources:

| Model | Size | Source | Notes |
|-------|------|--------|-------|
| `zaakirio/gemma-4-12b-it-uncensored-GGUF` | 12B | HuggingFace | Q4_K_M ~7.4GB, heretic/abliterated |
| `nexusriot/Gemma-4-Uncensored-HauhauCS-Aggressive` | 8B | Ollama library | Already available as `:e4b` tag |

**Search pattern**: Look for repos tagged `heretic`, `abliterated`, `uncensored`, `decensored` on HuggingFace.

## User Preferences

- Prefers Q4_K_M quantization (best quality/size balance)
- Prefers keeping only uncensored/heretic model variants
- Wants model management to "just work" without interactive prompts
- Has RTX 2050 (4GB VRAM) + 16GB RAM — large models run on CPU

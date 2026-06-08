---
name: local-llm-ops
title: Local LLM Operations (Ollama)
description: "Manage Ollama local LLMs from WSL: list/delete/run models, import GGUF from HuggingFace via Modelfile, fix model path issues. Covers the WSL→Windows bridge for Ollama CLI/API."
version: 1.0.0
trigger: "User asks about Ollama models, downloading GGUF, importing local models, checking what models are installed, or fixing Ollama path/server issues."
tags: [ollama, gguf, local-llm, mlops, wsl]
platforms: [wsl, linux]
---

# Local LLM Operations (Ollama)

## Philosophy

Ollama runs on the Windows host, accessible from WSL via `localhost:11434` API or the Windows `.exe` CLI. Models live in `C:\Users\<user>\.ollama\models\` by default. The CLI must be invoked via the Windows executable from WSL.

## Quick Reference: Ollama CLI from WSL

```bash
# Must use full path to Windows exe
OLLAMA="/mnt/c/Users/ysga1/AppData/Local/Programs/Ollama/ollama.exe"

# List models (may need to start server first)
$OLLAMA list

# Run a model interactively
$OLLAMA run <model-name>

# Delete a model
$OLLAMA rm <model-name>

# Pull from Ollama library
$OLLAMA pull <model-name>
```

**Pitfall**: The CLI tries to start a server if one isn't running. If the OLLAMA_MODELS env var is wrong, the server will crash in a loop. Always check server health first: `curl -s http://localhost:11434/api/tags`

## API Usage (Preferred for Programmatic Access)

```bash
# List all models
curl -s http://localhost:11434/api/tags

# Delete a model
curl -s -X POST http://localhost:11434/api/delete -d '{"name": "model:tag"}'

# Generate text
curl -s http://localhost:11434/api/generate -d '{"model":"...","prompt":"..."}'
```

The API is more reliable than the CLI from WSL because it doesn't try to spawn a server.

## Importing GGUF Models from HuggingFace

When a model isn't in the Ollama library (e.g. uncensored/heretic variants), download the GGUF file and import it:

### Step 1: Find the GGUF File

```bash
# Use HuggingFace API to list files in a repo
curl -s "https://huggingface.co/api/models/<org>/<repo>" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for s in data.get('siblings', []):
    fn = s.get('rfilename', '')
    if 'Q4_K_M' in fn:  # or whatever quantization you want
        print(fn)
"
```

### Step 2: Download the GGUF

For large files (5GB+), use Python with progress tracking rather than wget (more reliable for HuggingFace CDN):

```python
import urllib.request
url = "https://huggingface.co/<org>/<repo>/resolve/main/<filename>.gguf"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
resp = urllib.request.urlopen(req, timeout=30)
total = int(resp.headers.get('Content-Length', 0))
# Download in chunks with progress...
```

See `references/gguf-download.py` for a complete download script with progress bar.

**Speed note**: HuggingFace download speeds from Taiwan can be slow (~1MB/s). A 7GB file takes ~100 minutes. There is no fast workaround without aria2c (requires sudo).

### Step 3: Create Modelfile

```dockerfile
FROM ./model-name-Q4_K_M.gguf

TEMPLATE """{{- if .System }}{{ .System }}{{ end }}
{{- range .Messages }}
{{- if eq .Role "user" }}<|user|>
{{ .Content }}</|user>
{{- else if eq .Role "assistant" }}<|model|>
{{ .Content }}</|model>
{{- end }}{{- end }}<|model|>
"""

SYSTEM "You are a helpful assistant."

PARAMETER stop "<|user|>"
PARAMETER stop "<|model|>"
PARAMETER stop "<|end|>"
PARAMETER temperature 0.7
PARAMETER num_ctx 8192
```

**TEMPLATE format varies by model family.** Check the model card on HuggingFace for the correct chat template. Common patterns:
- Gemma 4: `<|user|>` / `<|model|>` / `<|end|>`
- Llama 3: `<|begin_of_text|><|start_header_id|>user<|end_header_id|>`
- Qwen: `<|im_start|>user\n`

### Step 4: Import into Ollama

```bash
cd /path/to/gguf/directory
OLLAMA_MODELS="C:\\Users\\ysga1\\.ollama\\models" ollama.exe create <model-name> -f Modelfile
```

This copies the GGUF into Ollama's blob storage and creates the model manifest.

## Model Path Issues

### OLLAMA_MODELS Environment Variable

Ollama looks for `OLLAMA_MODELS` to find where models are stored. If set to a non-existent path, the server crashes with:
```
Error: mkdir D:\Ollama: The system cannot find the path specified.
```

**Fix** (see `windows-host-operations` Pitfall 6 for the env var pattern):
1. Check current value: `reg query HKCU\Environment /v OLLAMA_MODELS`
2. Fix via PowerShell: `[System.Environment]::SetEnvironmentVariable('OLLAMA_MODELS', 'C:\Users\ysga1\.ollama\models', 'User')`
3. Kill all Ollama processes: `taskkill.exe /F /IM ollama.exe`
4. Restart: the new process picks up the registry value

**WSL-specific**: Changes to Windows env vars via PowerShell don't apply to already-running WSL processes. Override inline when launching:
```bash
cmd.exe /c "set OLLAMA_MODELS=C:\Users\ysga1\.ollama\models && ollama.exe serve"
```

### Default Model Path

`C:\Users\<user>\.ollama\models\` — contains `blobs/` and `manifests/` subdirectories. Models are stored as content-addressed blobs.

## Checking Installed Models (Without Server)

If the Ollama server won't start, you can inspect models directly:

```bash
# List model names from manifest directory
ls /mnt/c/Users/ysga1/.ollama/models/manifests/registry.ollama.ai/library/

# List tags for a model
ls /mnt/c/Users/ysga1/.ollama/models/manifests/registry.ollama.ai/library/<model-name>/
```

## Hardware Considerations

For systems with limited VRAM (e.g. RTX 2050 4GB):
- Models >4B params will run on CPU, not GPU
- Q4_K_M quantization: model_size_GB ≈ params_B × 0.6
- 12B Q4_K_M ≈ 7GB — needs ~8GB free RAM
- 8B Q4_K_M ≈ 5GB — needs ~6GB free RAM
- Use `num_ctx` in Modelfile to limit context window and reduce memory usage

## Pitfalls

### Pitfall 1: Ollama CLI from WSL tries to start server
Running `ollama.exe list` or `ollama.exe run` will try to start a server if one isn't running. If the env var is wrong, this creates a crash loop. Always check the API first (`curl localhost:11434/api/tags`) before using the CLI.

### Pitfall 2: Windows env var changes don't propagate to WSL
Changing `OLLAMA_MODELS` via PowerShell registry write doesn't affect processes already running in WSL. Must kill and restart, or override inline with `cmd.exe /c "set VAR=value && program.exe"`.

### Pitfall 3: HuggingFace download speed
Downloads from HuggingFace can be slow (~1MB/s from Asia). For 7GB+ GGUF files, expect 60-100+ minutes. No fast workaround without aria2c (needs sudo).

### Pitfall 4: Modelfile TEMPLATE format
Each model family uses a different chat template. Using the wrong template causes garbage output or errors. Always check the model card for the correct format.

### Pitfall 5: Multimodal models need mmproj
For vision models (Gemma 4, LLaVA), you also need the `mmproj` GGUF file. Import with:
```dockerfile
FROM ./model.gguf
PROJECTOR ./mmproj.gguf
```
Not all Ollama versions support PROJECTOR — check `ollama --help`.

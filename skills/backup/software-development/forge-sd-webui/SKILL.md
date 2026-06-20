---
name: forge-sd-webui
title: Stable Diffusion WebUI Forge — Windows Setup & NSFW Optimization
description: Install, configure, and optimize SD WebUI Forge on Windows with NVIDIA RTX (4GB VRAM). Covers Python version pitfalls, Windows-specific triton/xformers issues, batch file encoding, performance tuning, and NSFW model configuration.
version: 1.0.0
trigger: "User asks to set up, fix, launch, or optimize Forge (stable-diffusion-webui-forge) on Windows. Launch_forge.bat won't open, Forge crashes on startup, Python version errors, xformers/triton errors, or NSFW tuning."
tags: [windows, stable-diffusion, forge, nsfw, nvidia, rtx]
platforms: [wsl, windows]
---

# Stable Diffusion WebUI Forge — Windows Setup & NSFW Optimization

## Prerequisites

- Windows (not Linux/WSL-native — Forge runs on Windows directly)
- NVIDIA GPU with 4GB+ VRAM (RTX 2050, 3050, 3060, etc.)
- Python 3.10.6 (CRITICAL — Forge tests against this exact version)
- Git installed
- Access from WSL via `cmd.exe /c` or PowerShell

## Windows-Specific Pitfalls

### Python Version (MOST COMMON FAILURE)

Forge requires **Python 3.10.6**. If you have Python 3.11/3.12 on PATH, the venv gets created with the wrong version and packages (especially CLIP) will fail to build.

**Fix**: Install Python 3.10.6 from https://www.python.org/downloads/release/python-3106/ and point to it explicitly:

```batch
set PYTHON=C:\Users\<user>\AppData\Local\Programs\Python\Python310\python.exe
```

Or point directly to the venv Python after creating it:
```batch
set PYTHON=C:\AI\stable-diffusion-webui-forge\venv\Scripts\python.exe
```

### xformers + triton (Windows Compatibility)

`--xformers` depends on the `triton` package, which is **Linux-only**. On Windows, pip returns "No matching distribution found for triton".

**Fix**: Remove `--xformers` from COMMANDLINE_ARGS. Use `--opt-sdp-attention` instead — it provides equivalent performance through PyTorch's native SDP (Scaled Dot-Product Attention) on NVIDIA GPUs.

**Note**: Forge loads xformers internally regardless of CLI flags. The `WARNING:xformers:A matching Triton is not available` message is harmless — xformers falls back to its CUDA kernels on Windows and works fine.

### `--medvram` is Deprecated

Forge v1.10+ uses fully automatic VRAM management. The `--medvram` flag is removed. If you pass it, Forge prints:
```
Arg --medvram is removed in Forge. Now memory management is fully automatic.
```

**Fix**: Remove `--medvram` from COMMANDLINE_ARGS entirely.

### No `--language` CLI Flag

Forge does NOT support `--language zh-TW` or similar CLI flags. **This crashes Forge on startup** with:
```
launch.py: error: unrecognized arguments: --language zh-TW
```

**Fix**: Language/localization is configured through the Web UI after startup:
Settings → User Interface → Localization (dropdown)

You must first install the language pack via Extensions or place the `.json` file in the localizations directory, then select it from the dropdown and click "Apply settings" + "Reload UI".

## Launching Forge from WSL

### Batch File Encoding Issue

When you run a Windows batch file from WSL via `cmd.exe /c`, **Chinese characters in the .bat file get garbled**. The WSL→cmd.exe bridge sends UTF-8 bytes but cmd.exe's codepage 437/950 parsing mangles multi-byte characters. This causes REM comments and `echo` statements with Chinese text to be parsed as commands.

**Fix**: Keep batch files pure ASCII. Replace `REM` comments and `echo` statements with English-only text. Set `chcp 65001` at the top of the .bat to switch cmd.exe to UTF-8 codepage.

### Launching GUI Windows from WSL

✅ **Reliable method**: PowerShell Start-Process
```bash
powershell.exe -Command "Start-Process -FilePath 'C:\path\to\launch_forge.bat'"
```

❌ **Does NOT work**:
- `cmd.exe /c start <bat>` — hangs
- `explorer.exe <bat>` — hangs
- Direct `<bat>` — hangs

## Performance Tuning (RTX 2050 4GB)

### Recommended COMMANDLINE_ARGS

```batch
set COMMANDLINE_ARGS=--skip-python-version-check --opt-sdp-attention --cuda-malloc --no-half-vae --theme dark --autolaunch --api
```

| Flag | Why |
|------|-----|
| `--skip-python-version-check` | Suppresses the 3.10.6 version warning (harmless if venv is 3.10.6) |
| `--opt-sdp-attention` | PyTorch native attention (replaces xformers on Windows) |
| `--cuda-malloc` | CUDA memory allocator optimization — Forge recommends this |
| `--no-half-vae` | Prevents black images with some NSFW models |
| `--theme dark` | Dark UI theme |
| `--autolaunch` | Opens browser automatically |
| `--api` | Enables REST API (useful for external tools) |

### When VRAM Runs Low

Forge will show warnings like:
```
[Low GPU VRAM Warning] Your current GPU free memory is 1120.71 MB...
```

**Fix**: In the Web UI, click the "UI" dropdown (top-left) → select "All" → find "GPU Weights" slider at the top of the page → reduce to 0.7–0.8.

## NSFW Configuration

### Key Settings

| Setting | Value | Why |
|---------|-------|-----|
| CLIP skip (CLIP_stop_at_last_layers) | **2** | Better NSFW prompt comprehension for many models |
| Face restoration | **OFF** | Prevents face modification on NSFW content |
| Model | **DreamShaper_8** or similar | Known for NSFW support |
| Safety checker | None in Forge | Forge has no built-in NSFW filter |

### Setting via API

```bash
curl -s -X POST "http://127.0.0.1:7860/sdapi/v1/options" \
  -H "Content-Type: application/json" \
  -d '{"CLIP_stop_at_last_layers": 2}'
```

### Full Model Check

DreamShaper_8 supports NSFW tagging. In the prompt, include tags like `nsfw, nude, explicit` or specific anatomical terms. The model handles these natively.

## References

See `references/windows-forge-debugging.md` for the full troubleshooting transcript from a real RTX 2050 setup session.

## Pitfalls Summary

1. **Python 3.10.6 is mandatory** — do NOT skip this. Any other version causes CLIP/torch build failures.
2. **No `--xformers` on Windows** — use `--opt-sdp-attention` instead.
3. **No `--medvram`** — deprecated in Forge, auto-managed.
4. **No `--language` CLI flag** — set language in the Web UI only.
5. **Chinese .bat filenames crash from WSL** — keep batch files pure ASCII.
6. **`--cuda-malloc` works and is recommended** — Forge itself suggests it on compatible GPUs.
7. **`--no-half-vae` prevents black images** with some NSFW models.

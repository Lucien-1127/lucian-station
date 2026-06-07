---
name: powershell-wsl-bridge
title: PowerShell to WSL Command Bridge
description: Patterns for reliably calling WSL/Linux commands from PowerShell. Covers tilde expansion, PATH resolution, non-interactive shell behaviour, and profile shortcuts.
version: 1.0.0
trigger: "Setting up PowerShell functions that call WSL binaries (Hermes, Claude, custom scripts). Debugging 'command not found' or path errors from PowerShell → WSL."
tags: [powershell, wsl, windows, integration, shell]
---

# PowerShell → WSL Command Bridge

## Context

Calling WSL commands from PowerShell is common for WSL-based tools (Hermes Agent, Claude CLI, etc.), but has several non-obvious pitfalls. This skill documents the reliable patterns.

## Core Rule: Absolute WSL Paths

**Never use `~` in PowerShell commands targeting WSL.**

PowerShell expands `~` to `$HOME` (e.g. `C:\Users\ysga1`), which WSL cannot interpret as its own home (`/home/ysga1`).

### ✅ Correct:
```powershell
$WSL_PATH = "/home/ysga1/.local/bin/hermes"
function chat { wsl -e $WSL_PATH chat }
```

### ❌ Wrong (three flavours):
```powershell
# 1. Tilde expansion: ~ becomes C:\Users\ysga1
function gemini { wsl ~/.local/bin/hermes chat }

# 2. Non-interactive PATH miss: .bashrc not sourced
function hermes { wsl -e hermes chat }

# 3. Ambiguous quoting: PS resolves tilde before WSL sees it
wsl "~/.local/bin/hermes" --version
```

## Shell Mode Comparison

| Mode | Command | Sources `.bashrc` | Finds `~/.local/bin` in PATH | Use Case |
|------|---------|-------------------|------------------------------|----------|
| **Exec** | `wsl -e /abs/path/to/binary` | N/A | N/A (uses absolute path) | ✅ Best for scripts, functions |
| **Login** | `wsl bash -l -c 'hermes chat'` | ✅ (via .profile) | ✅ | Interactive tools needing full env |
| **Interactive** | `wsl` (enter WSL shell) | ✅ | ✅ | Manual use |
| **Exec by name** | `wsl -e hermes` | ❌ | ❌ (unless PATH set globally) | ❌ Unreliable |

## PowerShell Profile Template

Define these in `$PROFILE` (`C:\Users\n\Documents\PowerShell\Microsoft.PowerShell_profile.ps1`):

```powershell
# WSL absolute paths
$WSL_HERMES = "/home/ysga1/.local/bin/hermes"

function chat {
    Write-Host "🗣️  Hermes Agent (Gemini 2.5 Flash)" -ForegroundColor Green
    wsl -e $WSL_HERMES chat
}

function hermes {
    wsl -e $WSL_HERMES $args
}
```

## Pitfalls

### Pitfall 1: Tilde expansion
- **Symptoms**: `wsl ~/bin/tool` → `/bin/bash: line 0: C:Usersname/bin/tool: No such file or directory`
- **Fix**: Use absolute WSL paths.

### Pitfall 2: Non-interactive PATH
- **Symptoms**: `wsl -e hermes` → `execvpe(hermes) failed: No such file or directory`
- **Cause**: `wsl -e` creates a non-interactive, non-login shell. `~/.local/bin/` is added to PATH by `.bashrc`, which only runs for interactive shells.
- **Fix**: Use absolute path: `wsl -e /home/ysga1/.local/bin/hermes`

### Pitfall 3: Single vs Double Quotes
- In PowerShell, single quotes (`'...'`) are literal, double quotes (`"..."`) expand variables.
- For WSL commands: prefer single quotes for literal WSL arguments, double quotes when PS variables needed.
- ✅ `wsl -e $WSL_PATH chat` (PS variable, no quoting needed for simple args)

### Pitfall 4: Profile reloading
- Editing `$PROFILE` requires reload: `. $PROFILE`
- Or restart PowerShell entirely.

## Verification

```powershell
# Test absolute path
wsl -e /home/ysga1/.local/bin/hermes --version

# Test PATH resolution (this should fail if not set up)
wsl -e hermes --version

# Test profile function
. $PROFILE
chat --version
```

## Related Skills
- `windows-launcher-strategies` — Windows GUI launchers (Batch/HTA/PowerShell)
- `hermes-agent` — Hermes Agent configuration and setup

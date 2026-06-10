---
name: windows-launcher-strategies
title: Windows Launcher Strategies
description: Compare HTA vs Batch vs PowerShell for building Windows tool launchers and dashboards. Capture pitfalls and best practices from production use.
version: 1.0.0
trigger: "Building a Windows UI launcher, dashboard, menu, or desktop tool. Need to decide between HTA, Batch, PowerShell, or Electron."
tags: [windows, gui, launcher, deployment, reliability]
---

# Windows Launcher Strategies

When building a clickable dashboard or menu system for Windows, choose your technology carefully. This skill compares trade-offs and captures lessons from production use.

## Quick Decision Tree

```
Need to launch tools / run commands?
  ├─ YES, locally on my machine (internal tool)
  │   ├─ Aesthetics matter?
  │   │   ├─ YES → HTA (pretty, but see pitfalls)
  │   │   └─ NO → Batch (.cmd) ← RECOMMENDED
  │   └─ Complex state / power user features?
  │       └─ YES → PowerShell (.ps1 profile)
  └─ Distribute to others?
      └─ Electron / .NET / Windows installer
```

## Technology Comparison

| Tech | Pros | Cons | Best For |
|------|------|------|----------|
| **Batch (.cmd)** | Ultra-reliable, no deps, UTF-8 support, instant startup | Text-only UI, limited styling | Operational tools, internal launchers, WSL integration |
| **HTA (.hta)** | Pretty HTML/CSS UI, runs locally, no installer | Font CDN fails, JS encoding fragile, old IE engine | Desktop prototypes, personal dashboards (if you accept risk) |
| **PowerShell (.ps1)** | Rich functions, state management, PS ecosystem | Execution policy friction, slower startup | Admin scripts, tool shortcuts, CI/CD integration |
| **Electron** | Modern, cross-platform, npm ecosystem | Heavy (~100MB), installer complexity | Professional tools, multi-window apps, public distribution |

## HTA Pitfalls (Production Lessons from 2026-06-06)

### Pitfall 1: External CDNs fail silently
- **What**: `@import url('https://fonts.googleapis.com/...')` does NOT load
- **Result**: Page renders blank (font load halts HTML parsing)
- **Fix**: System fonts only: `font-family: "Segoe UI", "Microsoft JhengHei", sans-serif`
- **Why**: HTA uses IE 11 engine; CDN load reliability is broken

### Pitfall 2: Mixed VBScript + HTML encoding errors
- **What**: Mixing `<script language="VBScript">` + `<script>` JavaScript causes parsing failures
- **Result**: "馬錯誤" (parsing errors), page stops rendering, buttons don't respond
- **Fix**: Use pure VBScript only, or switch to Batch entirely
- **Why**: HTA doesn't normalize character encodings across mixed script blocks

### Pitfall 3: JavaScript unreliability
- **What**: Modern JS (async/await, ES6) expectations fail
- **Why**: HTA's IE-based engine is outdated (~IE 11 level)
- **Fix**: Rewrite in pure VBScript, or use Batch

### Pitfall 4: CSS framework failures
- **What**: CSS Grid, Flexbox don't work reliably
- **Fix**: Simple tables or inline-block layouts only

### Pitfall 5: PowerShell `~` tilde expands to Windows home in WSL contexts
- **What**: In PowerShell functions/scripts, `~/.local/bin/hermes` becomes `C:\Users\name/.local/bin/hermes` instead of `/home/name/.local/bin/hermes`. WSL then fails with "No such file or directory".
- **Root cause**: PowerShell expands `~` to `$HOME` (Windows user dir) before passing to WSL. `wsl -e hermes` also fails because non-interactive shell doesn't source `.bashrc` (PATH missing).
- **Fix**: Define an absolute WSL path variable in the PowerShell profile:
  ```powershell
  $WSL_HERMES = "/home/ysga1/.local/bin/hermes"
  function chat { wsl -e $WSL_HERMES chat }
  ```
- **Verification**: `pwsh -NoProfile -Command "wsl -e /home/name/.local/bin/hermes --version"` should work.
- **What NOT to do**: Don't use `~` in PowerShell WSL commands. Don't rely on `wsl -e hermes` (won't find PATH in non-interactive shell).

### User Feedback (2026-06-06)
User rejected HTA v3.0-3.2 after it rendered blank (font CDN + encoding issues). Immediately accepted pure Batch alternative. **Implicit preference: reliability > aesthetics for operational tools.**

## Batch Launcher Best Practices

**Why Batch is reliable**:
- Built into Windows (cmd.exe on every machine)
- Zero external dependencies
- UTF-8 support: `chcp 65001 >nul 2>&1` (handles emoji & CJK)
- Deterministic command execution

**Boilerplate** (see `templates/launcher.cmd`):
```batch
@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

:menu
cls
echo.
echo   ════════════════════════════════════════════
echo   🚀  Tool Launcher
echo   ════════════════════════════════════════════
echo.
echo   【 AI 代理 】
echo     1. Hermes Agent (聊天)
echo     2. Hermes Dashboard
echo.
echo   【 工具 】
echo     3. Google Cloud CLI
echo.
set /p choice=   請輸入選數 (1-3):

if "%choice%"=="1" goto hermes_cli
if "%choice%"=="2" goto hermes_dash
if "%choice%"=="3" goto gcloud
echo Invalid choice
timeout /t 2 >nul
goto menu

:hermes_cli
echo ⏳ Launching Hermes...
wsl /home/ysga1/.local/bin/hermes chat
goto menu

:hermes_dash
echo ⏳ Opening Hermes Dashboard...
start http://localhost:8000
timeout /t 2 >nul
goto menu

:gcloud
echo ⏳ Launching gcloud...
cd /d "%LOCALAPPDATA%\Google\Cloud SDK"
call cloud_env.bat
goto menu
```

**Key details**:
- Line `:menu` is the loop; each option returns via `goto menu`
- Use `echo.` for blank lines (readability)
- Use `timeout /t 2` for feedback delays
- `cd /d` forces drive letter change if needed
- Supports WSL commands directly: `wsl <command>`

## PowerShell Profile Shortcuts

For lightweight tool shortcuts (not a full menu), add to `$PROFILE`:

**⚠️ CRITICAL:** In PowerShell, `~` expands to `C:\Users\<user>` (Windows home), NOT `/home/<user>` (WSL home). Always use the absolute WSL path or a variable. See `wsl-windows-bridge` skill for full details on the tilde trap.

```powershell
# File: C:\Users\<username>\Documents\PowerShell\Microsoft.PowerShell_profile.ps1

# WSL absolute path variable (avoid PowerShell ~ expansion trap)
$WSL_HERMES = "/home/<user>/.local/bin/hermes"

# Hermes shortcuts
function chat { wsl -e $WSL_HERMES chat }
function hermes-dash { Start-Process "http://localhost:8000" }
# NOTE: hermes model does NOT support --list, use grep instead
function hermes-models {
    Write-Host "📋 當前設定："
    Write-Host "   Model:    $(wsl -e grep 'default:' /home/<user>/.hermes/config.yaml | Select-Object -First 1)"
    Write-Host "   Provider: $(wsl -e grep 'provider:' /home/<user>/.hermes/config.yaml | Select-Object -First 1)"
}
function hermes { wsl -e $WSL_HERMES $args }

# Other tools — also use absolute WSL paths
function claude { wsl -e /home/<user>/.local/bin/claude }
function gcloud-init { cd "$env:LOCALAPPDATA\Google\Cloud SDK"; & .\cloud_env.bat }
```

**Activation**: 
- Restart PowerShell (automatic reload), OR
- Run `. $PROFILE` immediately to reload

## 💡 Naming Guidance (PowerShell Functions)

**Name functions after what the user does, not the underlying tech.**

| ❌ Avoid | ✅ Use | Reason |
|---------|-------|--------|
| `gemini` | `chat` | User types `chat` to start talking; `gemini` sounds like a standalone tool |
| `hermes-model` | `switch-model` | User wants to change model, not know it's "hermes" |
| — | `ai` | Universal menu command, works regardless of backend changes |

### Interactive Menu Pattern (for users who don't want to remember commands)

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
- `Switch` handles all branches (including invalid input → default → retry)
- Each action that produces output calls `Read-Host; ai` to let user read before returning to menu
- `Clear-Host` at the top keeps the menu fresh

## When to Use Each Technology

### Use Batch if:
- Internal tool (no distribution needed)
- Reliability is critical (daily use)
- You want zero dependencies
- CJK characters (emoji, Chinese) in UI

### Use HTA if:
- Single-machine deployment
- You need HTML/CSS prettiness
- You accept fragility trade-off
- You follow ALL pitfalls above
- You test weekly or more

### Use PowerShell if:
- Quick shortcuts (not a full launcher)
- Power users (OK with execution policy friction)
- Admin scripts / CI/CD integration

### Use Electron if:
- Distributing to others
- Multiple windows / complex UI
- Cross-platform support needed

## HTA Implementation Patterns (for reference)

If you still choose HTA despite the pitfalls, here are the key patterns:

### Common Launch Patterns

| Target | Pattern |
|--------|---------|
| Windows CLI tool | `sh.Run('%COMSPEC% /k "' + path + '"', 1, false)` |
| Windows GUI app | `sh.Run('"' + path + '"', 1, false)` |
| WSL tool (CLI) | `sh.Run('wsl.exe -e hermes', 1, false)` |
| Protocol URI | `sh.Run("obsidian://open?vault=知識庫", 0, false)` |

Note: `1` = SW_SHOWNORMAL, `0` = SW_HIDE, `false` = don't wait.

### Handling `.lnk` Shortcut Targets
```powershell
powershell.exe -Command "$sh = New-Object -ComObject WScript.Shell; $sc = $sh.CreateShortcut('C:\path\file.lnk'); Write-Host $sc.TargetPath $sc.Arguments"
```

### Google Cloud SDK Launch
Do NOT run `gcloud.cmd` directly — use `cloud_env.bat`:
```javascript
var env = home() + "\\AppData\\Local\\Google\\Cloud SDK\\cloud_env.bat";
sh.Run('%COMSPEC% /k ""' + env + '""', 1, false);
```

## References & Templates

- `references/hta-failures-2026-06-06.md` — Transcript of HTA rendering failure and debugging steps
- `templates/launcher.cmd` — Ready-to-copy Batch launcher scaffold with UTF-8 + menu structure
- `templates/launcher.ps1` — PowerShell profile function set

## Related Skills

- `windows-hta-launcher` — Deep dive into HTA implementation (if you decide HTA is right)
- `powershell-profile-setup` — Full PowerShell profile configuration

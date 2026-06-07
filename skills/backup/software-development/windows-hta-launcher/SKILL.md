---
name: windows-hta-launcher
description: Manage 工具啟動台.hta — Windows HTML Application desktop launcher with JScript/ActiveX buttons. Add/modify tool buttons, fix launch paths, add WSL-based tools (Hermes, Claude CLI) to the Windows shortcut dashboard.
version: 1.0.0
---

# Windows HTA Desktop Tool Launcher (工具啟動台)

The user's desktop has a `工具啟動台.hta` — an HTML Application (HTA) that acts as a dashboard with buttons to launch various tools. It uses JScript + ActiveX (`WScript.Shell`, `Scripting.FileSystemObject`).

**⚠️ CRITICAL (2026-06-06):** HTA + external font imports fail silently with blank rendering. For this user, **Batch-based menu is now the standard solution.** See `references/hta-rendering-failures-2026.md` for incident details and workarounds.

## Architecture

```
工具啟動台.hta (Windows desktop)
  ├── HTML buttons with onclick handlers
  ├── JScript functions using ActiveX objects
  │   ├── WScript.Shell → sh.Run(path, 1, false)
  │   └── Scripting.FileSystemObject → fso.FileExists(path)
  └── Status bar showing launch results
```

## Common Launch Patterns

| Target | Pattern | Example |
|--------|---------|---------|
| Windows CLI tool | `sh.Run('%COMSPEC% /k "' + path + '"', 1, false)` | Claude CLI, CCB |
| Windows GUI app | `sh.Run('"' + path + '"', 1, false)` | Shortcuts (.lnk), .exe |
| WSL tool (CLI) | `sh.Run('wsl.exe -e hermes', 1, false)` | Hermes Agent CLI |
| WSL tool (dashboard) | `sh.Run('wsl.exe -e hermes dashboard', 1, false)` | Hermes Web UI |
| Protocol URI | `sh.Run("obsidian://open?vault=知識庫", 0, false)` | Obsidian vault |
| Google Cloud SDK | `sh.Run('%COMSPEC% /k ""' + envPath + '""', 1, false)` | cloud_env.bat (not gcloud.cmd directly) |

Note: `1` = SW_SHOWNORMAL (show window), `0` = SW_HIDE (no window), `false` = don't wait.

## How to Read an .hta File

Use `read_file` to get the full content. Key sections:

1. **HTA directives** — `<HTA:APPLICATION ...>` block at the top controls window style, size, scroll
2. **CSS styles** — dark gold theme (#0a0a0a bg, #e0c97f text, #3c3214 borders)
3. **Button HTML** — each `.btn` div has an `onclick` handler, icon, title, and description
4. **JScript functions** — `<script language="JScript">` at the bottom contains all launch logic

## Handling `.lnk` Shortcut Targets

Windows shortcuts are binary files. To discover what a `.lnk` actually runs, use PowerShell:

```powershell
powershell.exe -Command "
\$sh = New-Object -ComObject WScript.Shell
\$shortcut = \$sh.CreateShortcut('C:\path\to\file.lnk')
Write-Host 'Target: ' \$shortcut.TargetPath
Write-Host 'Args: ' \$shortcut.Arguments
Write-Host 'WorkDir: ' \$shortcut.WorkingDirectory
"
```

## Fixing Google Cloud SDK Launch (common issue)

The gcloud SDK installs a `cloud_env.bat` at `%LOCALAPPDATA%\Google\Cloud SDK\cloud_env.bat`. **Do NOT** run `gcloud.cmd` directly from the HTA — it will just show help and exit. Use cloud_env.bat:

```javascript
function launchGCloud() {
  try {
    var env = home() + "\\AppData\\Local\\Google\\Cloud SDK\\cloud_env.bat";
    if (fileExists(env)) {
      sh.Run('%COMSPEC% /k ""' + env + '""', 1, false);
      ok("✅ Google Cloud CLI 已啟動（環境就緒）");
    }
  }
}
```

This sets PATH, CD's to SDK dir, shows welcome message, and keeps the terminal open for interactive use.

## Adding WSL Tools to the Launcher

For Hermes (or any WSL CLI tool), verify the command exists in WSL first, then launch via `wsl.exe -e`:

```javascript
function launchHermes() {
  try {
    if (!wslCommandExists("hermes")) { err_("❌ WSL 中找不到 hermes"); return; }
    sh.Run('wsl.exe -e hermes', 1, false);
    ok("✅ Hermes Agent 已啟動（CLI 模式）");
  } catch(e) { err_("❌ 啟動失敗: " + e.message); }
}
```

The `wslCommandExists` helper:
```javascript
function wslCommandExists(cmd) {
  try { return (sh.Run('wsl.exe sh -lc "command -v ' + cmd + ' >/dev/null 2>&1"', 0, true) === 0); }
  catch(e) { return false; }
}
```

## Checking Actual File Paths

Before writing launch functions, verify every path referenced in the HTA actually exists. Common checks:

```bash
ls -la "/mnt/c/Users/<user>/AppData/Local/Programs/Claude/Claude.exe"
ls -la "/mnt/c/Users/<user>/.local/bin/claude.exe"
ls -la "/mnt/c/Users/<user>/AppData/Local/Google/Cloud SDK/google-cloud-sdk/bin/gcloud.cmd"
```

## Rendering Issues & Migration to Batch (Critical Lesson: 2026-06-06)

### HTA + External Fonts = Silent Rendering Failure

When designing v3.0–3.2 of the launcher with `@import url('https://fonts.googleapis.com/...')`, the HTA rendered completely blank — no buttons, no text, only white void. **Root cause: HTA's Internet Explorer 11 rendering engine cannot reliably load external font URLs over HTTPS.** The page fails silently without error messages or console warnings.

**For this user, the canonical solution is: migrate to Batch file menu (`工具啟動台.cmd`).** Batch provides:
- Zero external dependencies (no fonts, no CDN calls)
- Perfect UTF-8 Chinese character support
- Instant launch, no rendering engine involved
- Trivial debugging (it's just a numbered menu)
- Works identically on every Windows version

### When to Use Batch vs. HTA

| Goal | Recommended | Why |
|------|---|---|
| Interactive menu on Windows | **Batch** | 100% reliable, UTF-8 native, no rendering issues, instant startup |
| GUI buttons with icons | HTA | Only if using system fonts (`Segoe UI`, `Microsoft JhengHei`), NO external `@import` or `<link>` |
| Admin tasks (UAC prompt) | Batch + `runas` | HTA cannot properly handle UAC elevation |
| WSL tool launcher dashboard | Batch | Simpler, fewer cross-platform font issues |

**Batch Template (9-tool launcher):**
```batch
@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

:menu
cls
echo.
echo   🚀  工具啟動台 v4.0  (Batch Edition)
echo   ════════════════════════════════════
echo     1. Hermes Agent
echo     2. Hermes Dashboard
echo   [etc]
echo   0. 結束
set /p choice=請輸入選數:

if "%choice%"=="1" goto hermes_chat
[etc]
if "%choice%"=="0" exit /b 0
echo ❌ 選擇無效
timeout /t 2 >nul
goto menu

:hermes_chat
echo ⏳ 正在啟動...
cmd /c cd /d C:\Users\ysga1 && wsl hermes chat
goto menu
```

## Workflow: Research → Plan → Execute

This user requires you to investigate the current state before making any changes:

1. **Research** — list the desktop directory, check which shortcuts and .bat files exist, verify WSL commands, check the existing HTA content
2. **Plan** — present the proposed changes as a clear diff (what's removed, added, changed) and ask for confirmation
3. **Execute** — only act after the user explicitly approves

Do NOT write the HTA file directly without presenting the plan first. This user will call you out.

## Pitfalls

- **HTA + external fonts = silent rendering failure.** `@import url()` or `<link href="">` to Google Fonts, CDNs, or HTTPS URLs result in blank page. Use system fonts only or migrate to Batch.
- `.hta` files have NO linter — verify manual HTML syntax and JScript function names match onclick handlers
- JScript is case-sensitive for ActiveX method names (`FileExists` not `fileExists`, `ExpandEnvironmentStrings` not `expandEnv`)
- `sh.Run` with `%COMSPEC% /k` opens a visible cmd window; pass `0` as second arg to hide it
- Windows paths use backslashes — escape them correctly in JavaScript strings (use raw backslashes, not escaped)
- The HTA `INNERHEIGHT` attribute controls window height — too many buttons without tabs will clip
- Always backup the original file before writing: `cp original.hta original_v2_backup.hta`
- Claude Desktop GUI (`Claude.exe` in `%LOCALAPPDATA%\Programs\Claude\`) may not be installed — always check and fall back to CLI
- `wsl.exe -e <command>` runs the command directly without a shell — PATH depends on default WSL distro config; test before assuming it works
- **For this user (小育老闆), Batch menu is now the standard.** Multiple HTA versions (v3.0–3.2) all failed with rendering errors; Batch v4.0 works immediately.

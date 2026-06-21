---
name: windows-host-operations
title: Windows Host Operations from WSL
description: Patterns for performing Windows-side operations from WSL — software installation, file management, GUI process launch, system investigation, and file recovery. Complements powershell-wsl-bridge (which covers WSL→PowerShell) with the reverse direction.
version: 1.1.0
trigger: "User asks you to install, investigate, or modify something on the Windows host while you are running inside WSL. Downloading software, reading Windows app logs/configs, launching GUI tools, performing file recovery, or cleaning up Windows files."
tags: [wsl, windows, devops, cross-platform, administration]
platforms: [wsl, linux]
---

# Windows Host Operations from WSL

## Philosophy

When running inside WSL, the Windows filesystem is mounted at `/mnt/c/`. You can access Windows files directly, but launching GUI programs, installing software, and handling non-ASCII filenames have pitfalls.

## Software Installation (Windows → WSL)

### Preferred: winget (Microsoft Package Manager)

```bash
# Search for a package
cmd.exe /c "winget search <query>"

# Install silently
cmd.exe /c "winget install --id <Publisher.Package> --silent --accept-package-agreements"

# Uninstall
cmd.exe /c "winget uninstall --id <Publisher.Package> --silent"
```

**When to use**: Windows software with winget manifests. ✅ Most reliable.

### Fallback: Download + Manual GUI Install

```bash
# Download installer via PowerShell (handles redirects better than curl)
powershell.exe -Command "(New-Object System.Net.WebClient).DownloadFile('<url>', '<dest-path>')"

# Launch GUI installer (user must click through)
powershell.exe -Command "Start-Process '<exe-path>'"
```

**When to use**: No winget manifest, or interactive GUI install needed.

### Direct URL Download via curl

```bash
curl -L -o /mnt/c/Users/<user>/Downloads/file.exe "<download-url>"
```

**Pitfall**: Many download pages use JavaScript redirects or CDN gateways — curl doesn't execute JS. Use the browser tool to navigate the download page and extract the real URL.

## Launching Windows GUI from WSL

### ✅ PowerShell Start-Process (works — this is the ONLY reliable method)

```bash
powershell.exe -ExecutionPolicy Bypass -NoProfile -Command "Start-Process '<path-to-exe>'"
```

Key rules:
- Use **`-NoProfile`** and **no extra wrappers** — no `& { }`, no `-File`, no script blocks
- The process launches asynchronously — PowerShell exits instantly, WSL returns `exit 0`
- Verify the process started: `powershell.exe -NoProfile -Command "Get-Process <name>"`

**Contrast with what DOES NOT work** (see below): the difference is that `Start-Process` with bare args exits immediately, while wrappers like `& { ... }` or `-File script.ps1` cause the WSL→PowerShell bridge to hang.

### ❌ What DOES NOT work

- `cmd.exe /c start "<exe>"` — hangs or silently fails
- `explorer.exe "<exe>"` — hangs
- Direct `./some_gui_installer.exe` from WSL shell — hangs
- `wscript.exe //B CreateObject(...)` — hangs or errors

### ❌ Silent/Unattended GUI Installers

InnoSetup installers (`.exe` with `/VERYSILENT` or `/SILENT`) often hang from WSL because the installer process tree is broken across the WSL/Windows boundary. **Do not attempt silent install** — either use winget or launch the GUI installer for the user.

## File Operations on Windows Files

### Handling Chinese / Emoji Filenames

**cmd.exe cannot handle Chinese or emoji characters in file paths when called from WSL.** The path gets garbled.

### ✅ Use PowerShell for file operations with non-ASCII paths:

```bash
# Delete files/folders
powershell.exe -Command "Remove-Item '<path>' -Recurse -Force"

# List directory with non-ASCII names
powershell.exe -Command "Get-ChildItem '<dir>' | Select-Object Name"

# Read file content
powershell.exe -Command "Get-Content '<file>' -Encoding UTF8"
```

### ✅ Use WSL paths for non-ASCII files (mount at /mnt/c/):

```bash
# This works because WSL handles UTF-8 natively
rm -rf "/mnt/c/Users/ysga1/Desktop/知識庫/一些檔案.md"
ls "/mnt/c/Users/ysga1/Desktop/知識庫/"
```

### Security Blocks on rm -rf from WSL

WSL's `rm -rf` on `/mnt/c/` paths may trigger Windows security prompts (especially for large directories). If blocked, fall back to PowerShell `Remove-Item`.

## Investigating Windows Applications

### Reading Windows Application Configs

Windows apps store config in:
- `%APPDATA%` → `/mnt/c/Users/<user>/AppData/Roaming/`
- `%LOCALAPPDATA%` → `/mnt/c/Users/<user>/AppData/Local/`
- `%PROGRAMDATA%` → `/mnt/c/ProgramData/`

### Checking Windows Processes

```bash
powershell.exe -Command "Get-Process <name> | Select-Object Id,ProcessName,StartTime,Responding"
```

### Killing Windows Processes Holding a Specific Port

WSL's `fuser`/`lsof`/`ss` cannot see processes running on the Windows side. When port 8000 (or any port) is "already in use" but WSL tools show nothing, the process is likely a Windows-side Python/Node/whatever process.

**Step 1: Find the offender**
```bash
powershell.exe -Command "Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object LocalAddress, LocalPort, State, OwningProcess, @{N='ProcessName';E={(Get-Process -Id \$_.OwningProcess -ErrorAction SilentlyContinue).Name}}"
```

**Step 2: Kill it**
```bash
powershell.exe -Command "Stop-Process -Id <PID> -Force"
```

**Step 3: Verify the port is free**
```bash
powershell.exe -Command "Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue"
# Empty output = port is free
```

**Common scenario**: A Uvicorn/FastAPI server started from Windows that crashed or was Ctrl+C'd, but the process still holds the port in "Bound" state. WSL's `pkill -f uvicorn` won't touch it because it's a Windows process.

### Syncthing-Specific Investigation

See `references/syncthing-forensics.md` for the pattern of investigating a sync disaster — reading config, parsing the log, determining root cause, and recovery options.

## Fixing Windows CMD Garbled Chinese Text & Crashes

### Symptom

Windows Command Prompt (cmd.exe) shows garbled Chinese characters (mojibake) or crashes immediately when running `.bat` scripts with Chinese/emoji content. Programs that worked before now display `?` boxes, squares, or scrambled text.

### Root Cause: UTF-8 Beta Setting

Windows has a hidden "Beta: Use Unicode UTF-8 for worldwide language support" setting that changes the system ANSI code page (ACP) from the locale's default (950 = Big5 for zh-TW) to 65001 (UTF-8). While this helps some apps, it breaks many Traditional Chinese cmd tools and `.bat` scripts that expect Big5 encoding.

**Where to check:**
```
Control Panel → Region → Administrative → Change system locale
→ "Beta: Use Unicode UTF-8 for worldwide language support"
```

**Registry check:**
```powershell
# If ACP = 65001 → UTF-8 Beta is ON
Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Nls\CodePage' -Name ACP
```

### Fix: Disable UTF-8 Beta (Requires Admin + Reboot)

```powershell
# Run as Administrator
Set-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\Nls\CodePage' -Name 'ACP' -Value '950'
Set-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\Nls\CodePage' -Name 'OEMCP' -Value '950'
Set-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\Nls\CodePage' -Name 'MACCP' -Value '950'
```

After reboot:
- ACP = 950 (Big5, standard for zh-TW)
- OEMCP = 950
- cmd displays Chinese text correctly
- `chcp` shows 950 by default

**.bat files that need UTF-8 still work** — add `chcp 65001 >nul` at the top of the script to switch code page at runtime.

### Pitfall: Scripts already assume UTF-8

Some modern .bat scripts (like `🚀 智研SaaS啟動.bat`) already have `chcp 65001 >nul` at the top. These will continue to work fine because they explicitly set the code page before displaying Chinese text. The fix only affects scripts that implicitly rely on the system default code page.

### 🔴 CRITICAL Pitfall: Fix scripts must be pure English

When ACP=65001, **the user's CMD displays ALL Chinese characters as garbled text**. This means:

- The fix script itself **must not contain any Chinese characters** — the user cannot read them
- Instructions like "按「是(Y)」" or "重新開機" show as unreadable squares/boxes
- The filename should use English + emoji (Explorer renders emoji correctly), not Chinese characters

**Correct approach:**

1. Use `chcp 437 >nul` at the top of the fix script (switch to US English code page)
2. Write ALL instructions in English
3. Call `powershell` directly (NOT `wsl powershell.exe`) — `.bat` files run in Windows cmd context
4. See `references/cmd-fix-pure-english-script.md` for the correct template

**Common error: `wsl powershell.exe` prefix**

From a `.bat` file running in Windows cmd, do NOT use `wsl powershell.exe -Command "..."`. The `wsl` prefix causes the command to run inside WSL instead of Windows, which either fails silently or runs the wrong script. Just use `powershell -Command "..."` directly.

**Common error: `chcp 65001` in the fix script**

Do NOT use `chcp 65001` in the fix script itself. The console font (PMingLiU) renders Chinese poorly under UTF-8. Use `chcp 437` for pure English output, or `chcp 950` only AFTER the fix has been applied and system ACP is back to 950.

### chcp 65001 in .bat while ACP=65001 (double UTF-8 conflict)

**When ACP is already 65001** (UTF-8 mode), adding `chcp 65001 >nul` inside a .bat file is redundant and can make display **worse**: the default cmd console font (新細明體/PMingLiU) does not render all Chinese characters correctly in UTF-8 code page 65001 mode. Characters may show as `?`, boxes, or scattered glyphs even though the encoding is technically correct.

**Fix in the .bat file**: Replace `chcp 65001 >nul` with `chcp 950 >nul` (Big5) when the script runs Chinese text that must display correctly in cmd. The Big5 code page matches the console font and renders all Traditional Chinese characters properly.

Alternatively, omit `chcp` entirely — after the UTF-8 Beta fix, the system default will be 950, which works correctly.

## File Recovery on Windows

### Option 1: Recuva (GUI — easiest)

Install via winget:
```bash
cmd.exe /c "winget install --id Piriform.Recuva --accept-package-agreements"
```

Then launch for the user:
```bash
powershell.exe -Command "Start-Process 'C:\Program Files\Recuva\recuva64.exe'"
```

Recovery settings for deleted files (not in Recycle Bin):
- File type: "All Files"
- Location: Specific folder path
- **Enable Deep Scan** (critical for files deleted by sync tools)
- Restore to a different location than original

### Option 2: PhotoRec (CLI — more powerful)

Requires raw disk access, which needs sudo in WSL. If sudo is not available, use Recuva instead.

### Option 3: Windows File Recovery (winfr — Microsoft CLI)

Microsoft's command-line recovery tool. Install via Microsoft Store.

## Syncthing Disaster Recovery (Quick Reference)

When a user reports "files disappeared after Syncthing sync":

1. **Stop Syncthing immediately** to prevent further overwrites
2. **Check Recycle Bin** — Syncthing deletions typically DO NOT go to Recycle Bin
3. **Read Syncthing log** at `C:\Users\<user>\AppData\Local\Syncthing\syncthing.log`
   - Look for "Deleted file" entries — each line shows filename and folder
   - Count deletions: `grep -c "Deleted file" /mnt/c/.../syncthing.log`
4. **Read Syncthing config** at `C:\Users\<user>\AppData\Local\Syncthing\config.xml`
   - Check `ignoreDelete` — if `false` (default), deletions propagate
   - Check `versioning` type — if empty, NO versioned backups exist
   - Check folder type (`sendreceive` vs `sendonly`)
5. **Root cause**: Remote device with "new index ID" + empty folder + `sendreceive` mode → deletions propagate everywhere
6. **Recovery**: File recovery software with Deep Scan (Recuva, PhotoRec). The sooner the better before disk space is overwritten.

For comprehensive Syncthing prevention, versioning setup, and backup strategy → load the **`data-backup`** skill.
See also `references/syncthing-forensics.md` for the full investigation transcript.

## Pitfalls

### Pitfall 1: Path encoding for Chinese/Japanese/Korean filenames

`cmd.exe` cannot handle Unicode paths properly when called from WSL. Always use PowerShell or direct WSL paths for non-ASCII filenames.

### Pitfall 2: winget silent install

Some GUI installers (InnoSetup) do not properly support `/VERYSILENT` when launched from WSL context. Prefer winget for fully automated installs.

### Pitfall 3: PowerShell commands timing out

Long-running PowerShell commands from WSL may appear to "hang." This is because WSL waits for the PowerShell process to exit. Use `-NoProfile` for faster startup, and accept that GUI-launch commands will return quickly (the GUI runs asynchronously).

### Pitfall 4: rm -rf security blocks

Windows Defender/Security may intercept bulk deletion on `/mnt/c/` from WSL. If `rm -rf` returns an empty error, try PowerShell `Remove-Item` instead.

### Pitfall 5: Syncthing file versioning not configured by default

If the `<versioning>` section in `config.xml` has no `type` attribute, there is NO versioned backup. Users must enable "File Versioning" in Syncthing settings to protect against deletion propagation.

### Pitfall 6: Windows environment variable changes don't apply to running processes

When you change a Windows environment variable via `powershell.exe -Command "[System.Environment]::SetEnvironmentVariable(...)"`, the change is written to the registry but does NOT take effect for already-running processes. Any .exe launched from WSL inherits the environment from when WSL (or that process) was spawned.

**Fix**: After changing an env var, you must either:
1. Kill and restart the target process, OR
2. Override the var inline when launching: `cmd.exe /c "set VAR=value && program.exe"`

**Example**: Ollama's `OLLAMA_MODELS` pointing to a non-existent path causes server crashes. Changing the registry value requires restarting Ollama.

→ For full Ollama model management (import, delete, GGUF workflow), load the **`local-llm-ops`** skill.

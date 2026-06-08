---
name: windows-host-operations
title: Windows Host Operations from WSL
description: Patterns for performing Windows-side operations from WSL — software installation, file management, GUI process launch, system investigation, and file recovery. Complements powershell-wsl-bridge (which covers WSL→PowerShell) with the reverse direction.
version: 1.0.0
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

### Syncthing-Specific Investigation

See `references/syncthing-forensics.md` for the pattern of investigating a sync disaster — reading config, parsing the log, determining root cause, and recovery options.

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

---
name: data-backup
description: "Data backup strategies, disaster recovery, and sync best practices — Syncthing, file recovery, skills backup, and restoration workflows."
version: 1.0.0
author: Lucien
license: MIT
metadata:
  hermes:
    tags: [backup, disaster-recovery, syncthing, file-recovery, Recuva, PhotoRec, skills-backup]
    related_skills: [obsidian-vault-maintenance, github-repo-management, vm-sync, windows-host-operations]
---

# Data Backup & Recovery

## Overview

Class-level skill for backup strategy, disaster investigation, and file recovery. Covers both **prevention** (proper backup/sync setup) and **reaction** (investigating data loss, choosing recovery tools, knowing when to give up and restore from backup).

## When to Use

Use this skill when the user mentions:
- 「同步出問題」「檔案不見」「被覆蓋」「同步衝突」
- 「Syncthing」「救援」「復原」「備份還原」
- 「技能備份」「Hermes 備份」
- Data loss, sync issues, file recovery, backup setup

## Core Principles

1. **Prevention > Recovery** — Proper versioning and backup config is worth more than any recovery tool.
2. **If backup exists, skip recovery** — Once the user confirms they have a backup, stop all investigation/scanning and pivot to cleanup + restore. Do NOT continue pursuing recovery tools.
3. **Investigate before acting** — Check logs (Syncthing, file system), understand what happened, then choose the right approach.
4. **Recovery time window is narrow** — Deleted files on SSDs/HDDs can be overwritten quickly. Act fast or don't bother.

---

## Section A: Syncthing — Investigation & Prevention

### Syncthing Log Analysis

Syncthing logs are at:
- **Windows**: `%LOCALAPPDATA%\Syncthing\syncthing.log` (e.g., `C:\Users\<user>\AppData\Local\Syncthing\`)
- **Config**: `%LOCALAPPDATA%\Syncthing\config.xml`

### Key Config Settings to Check

| Setting | Default | Risk if Wrong |
|---------|---------|---------------|
| `<type>sendreceive</type>` | sendreceive | Bidirectional — deletions propagate both ways |
| `<ignoreDelete>false</ignoreDelete>` | false | **CRITICAL**: false means remote deletions delete local files |
| `<versioning>` | empty (no type) | **CRITICAL**: no versioning means no `.stversions` backup |
| `<markerName>.stfolder</markerName>` | .stfolder | Marker file — presence indicates folder is under sync |

### Investigation Workflow

When user reports data loss after Syncthing sync:

1. **Check the log for "Deleted file" entries:**
   ```bash
   grep "Deleted file" "/mnt/c/Users/<user>/AppData/Local/Syncthing/syncthing.log" | wc -l
   ```
   
2. **Identify deletion time and remote device:**
   ```bash
   grep "Deleted file" "/mnt/c/Users/<user>/AppData/Local/Syncthing/syncthing.log" | head -3
   ```
   
3. **Check connection history:**
   - Look for `"Established secure connection"` before deletions
   - Look for `"Peer has a new index ID"` — remote had a different index state
   - Look for `"Folder failed to sync, will be retried"` — partial deletion

4. **Check if versioning was enabled** (look for `.stversions` folder):
   ```bash
   ls -la "/mnt/c/Users/<user>/path/to/folder/.stversions" 2>/dev/null || echo "No versioning folder"
   ```

### Why Files Disappear

| Root Cause | Log Signal | Fix |
|-----------|-----------|-----|
| Remote device had empty/new folder | `Peer has a new index ID` + mass deletions | Set `ignoreDelete=true`, enable versioning |
| sendreceive mode on both sides | Deletions propagate bidirectionally | Use `sendonly` for one-way, or versioning |
| Fresh GCP VM instance | Device name like `instance-YYYYMMDD-HHMMSS` | Pause folder on fresh VMs until data is present |

### Prevention Checklist

- [ ] **Enable file versioning** in Syncthing (Simple File Versioning, 5 copies minimum)
- [ ] Set `ignoreDelete=true` on critical folders that should never lose data
- [ ] For sendreceive folders on VMs: PAUSE the folder until the initial sync completes correctly
- [ ] Do NOT connect fresh VM instances with sendreceive mode to folders that already have data
- [ ] Consider `sendonly` on the primary machine, `receiveonly` on secondary

### Recycle Bin Check

Syncthing deletions do NOT go through the Windows Recycle Bin — deleted files bypass it entirely. Do NOT waste time checking the Recycle Bin for Syncthing-deleted files.

---

## Section B: File Recovery Tools

### When NOT to Recover

If the user says they have a backup → **stop immediately and clean up**. Do not:
- Download recovery tools
- Run scans
- Investigate further
Just clean up the mess and tell them to restore from backup.

### Recuva (Windows GUI — Preferred)

Best tool for non-technical users. Free version supports deep scan.

**Installation:**
```powershell
# Via winget (preferred — works from WSL cmd.exe)
winget install --id Piriform.Recuva --accept-package-agreements
```

**Launch** (from WSL — confirmed working):
```powershell
powershell.exe -ExecutionPolicy Bypass -NoProfile -Command "Start-Process 'C:\Program Files\Recuva\recuva64.exe'"
```
Key: use `-NoProfile` and bare `Start-Process` with **no** `& { }` wrapper, no `-File` flag. PowerShell exits instantly; the GUI opens on Windows.

**If launch fails:**
1. Verify install path: `Get-ChildItem 'C:\Program Files\Recuva\'`
2. Try `recuva64.exe` (64-bit) vs `recuva.exe` (32-bit)
3. Last resort: create a `.bat` on Desktop: `start "" "C:\Program Files\Recuva\recuva64.exe"`

**Do NOT attempt from WSL:**
- `cmd.exe /c start "..."` — hangs with path encoding
- `explorer.exe "..."` — timeout
- `wscript.exe` Shell.Application — hangs

**Recuva Recovery Steps:**
1. File type: "All Files"
2. Location: Specific path → the affected folder
3. Enable "Deep Scan"
4. After scan: select green-status files → Recover to a DIFFERENT location
5. Do NOT recover back to the original path

### PhotoRec / TestDisk (CLI — Requires sudo on Linux)

More powerful, command-line-based. Works on raw disk sectors.

```bash
# Install (Linux)
sudo apt-get install -y testdisk

# Uses photorec — reads raw disk, finds deleted files by content signature
sudo photorec
```

**Limitations:**
- Needs sudo/root for raw disk access
- Cannot access raw NTFS from WSL without special config
- Recovery output is raw files without filenames (numbered)

### Recuva vs PhotoRec

| Tool | Best For | Limitations |
|------|----------|-------------|
| Recuva | GUI, filename recovery, quick scan | Windows only, GUI from WSL unreliable |
| PhotoRec | Deep raw-sector recovery | No filenames, needs sudo, slow |

### WSL-to-Windows GUI Limitation

When working from WSL, you CANNOT reliably launch Windows GUI applications:
- `Start-Process` from PowerShell → may time out
- `cmd.exe /c start "program.exe"` → encoding issues with Chinese paths
- `explorer.exe` → timeouts
- `wscript.exe` → fails to create Shell.Application object

**Workaround:** Write a `.bat` or `.ps1` file to the Windows Desktop and tell the user to double-click it. Use `skill_manage(action='write_file')` with `file_path` under the skill's references/ to store the batch file template.

---

## Section C: Hermes Skills Backup to Git

### Architecture

Hermes skills live at `~/.hermes/skills/` (or `$HERMES_HOME/skills/`). To back them up to a GitHub repo:

```
Local:  ~/.hermes/skills/<category>/<skill>/SKILL.md
Git:    <repo>/skills/backup/<category>/<skill>/SKILL.md
```

The backup structure adds one level of nesting (`backup/`) to keep the repo organized.

### Setup Steps

1. **Clone the backup repo:**
   ```bash
   git clone "https://github.com/<user>/<repo>.git" ~/<repo-name>
   ```

2. **Create a sync script** at `<repo>/sync_hermes_skills.sh`:
   - Pulls latest from GitHub
   - Copies new/changed local skills to `backup/`
   - Applies any new skills from `backup/` to local
   - Updates `inventory.txt`
   - Commits and pushes

3. **Set a cron job** to run the script periodically:
   ```bash
   # Runs hourly during working hours
   0 */4 * * * cd ~/<repo> && bash sync_hermes_skills.sh
   ```

### Sync Script Patterns

The script needs to handle two structural patterns:

**Standard structure** (skill in subdirectory):
```
~/.hermes/skills/<cat>/<skill_name>/SKILL.md
~/.hermes/skills/<cat>/<skill_name>/references/...
~/.hermes/skills/<cat>/<skill_name>/scripts/...
```

**Flat structure** (SKILL.md in category directory):
```
~/.hermes/skills/<cat>/SKILL.md
~/.hermes/skills/<cat>/DESCRIPTION.md
```

### Authentication

| Method | Setup |
|--------|-------|
| **SSH key** | `ssh-keygen` → add to https://github.com/settings/keys |
| **HTTPS + token** | `git remote set-url origin https://<user>:<token>@github.com/<user>/<repo>.git` |
| **gh CLI** | `gh auth login` (not always available in WSL) |

### Pitfalls

1. **SSH on first push** — `git push` with SSH requires the key to be added to GitHub first. Show the public key to the user.
2. **Git identity** — must be set before the first commit: `git config user.name/email`
3. **WSL git push with SSH** — ensure `~/.ssh/config` is set up or the default key works
4. **Large repos** — skills with embedded scripts (`.py`, `.js` files) can bloat the repo. Add `*.js, *.py` to `.gitignore` for the scripts/ directories if not needed in backup.

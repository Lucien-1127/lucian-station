---
name: obsidian-vault-maintenance
description: Audit and restructure Obsidian vaults — batch frontmatter injection, orphan-link resolution, cross-note wikilink healing, and index/MOC generation. Use when the user wants to clean up, reorganize, or audit their vault's structural integrity.
version: 2.3.0
author: 小育 (via agent)
license: MIT
metadata:
  hermes:
    tags: [obsidian, vault, cleanup, frontmatter, wikilinks, orphans, structure]
    related_skills: [obsidian]
---

# Obsidian Vault Maintenance

## Overview

Phase-based approach to Obsidian vault structural cleanup, tested on vaults of 150–215 notes. Each phase is independent — the user can choose to stop after any phase. Designed for vaults with 50–500 notes organized by directory.

## When to Use

Use this skill when the user asks to:
- 「整理知識庫」「優化資料庫」「結構整理」
- 「補 frontmatter」「補 metadata」「補屬性」
- 「建索引」「補連結」「孤兒筆記」
- 「wikilinks 檢查」「標籤統一」「tag 分類」
- 「屬性錯誤」「YAML 錯誤」
- 「命名統一」「加上 emoji 前綴」「分類整理」
- 「重複合併」「目錄合併」「整併」
- Clean up, reorganize, or audit their vault's structural integrity
- Create templates, MOC index pages, or tag taxonomies
- Normalize file/directory naming with consistent emoji prefixes
- Merge duplicate directories or near-identical files
- Distinguish project-source directories from vault-note directories

Do NOT use for:
- One-off note creation or editing (use the `obsidian` skill)
- Content-level review or fact-checking (use `llm-wiki`)

## Vault Path Resolution

Always resolve the vault path first. **Do NOT trust `OBSIDIAN_VAULT_PATH` from `.env` alone** — it may be stale or point to a backup directory, not the live vault.

On Windows, verify the vault path by checking Obsidian's own config:

```bash
# Check Obsidian's official vault registry (Windows)
cmd.exe /c "type C:\Users\%USERNAME%\AppData\Roaming\obsidian\obsidian.json" 2>nul

# Look for the vault with "open": true — that's the currently active vault
# Example output:
# {
#   "vaults": {
#     "da2550d...": {"path": "C:\\Users\\ysga1\\Desktop\\知識庫", "ts": ...},
#     "6966e9f...": {"path": "C:\\Users\\ysga1\\Documents\\Lunian", "ts": ..., "open": true}
#   }
# }
```

Resolution order:

1. Obsidian's `obsidian.json` → `"open": true` vault (most reliable on Windows)
2. `OBSIDIAN_VAULT_PATH` environment variable (may be stale — verify it matches #1)
3. User's known vault path from memory
4. Fallback: `~/Documents/Obsidian Vault`

### Cross-Check on WSL

```bash
# WSL path for a Windows Obsidian vault at C:\Users\ysga1\Documents\Lunian
VAULT="/mnt/c/Users/ysga1/Documents/Lunian"

# Verify: check for .obsidian directory
test -d "$VAULT/.obsidian" && echo "VAULT CONFIRMED" || echo "NO .obsidian — wrong path"
```

## Phase — Vault Restoration from Backup

Use this when the vault's `.obsidian/` directory or its note content is missing and must be restored from a known backup. This is the **pre-phase** that runs before any structural cleanup.

### Discovery

When a vault is empty or has lost its `.obsidian/` config, check for backups:

```bash
# Find backup directories
find "$(dirname "$VAULT")" -maxdepth 4 -name ".obsidian" -type d 2>/dev/null
find "$(dirname "$VAULT")" -maxdepth 4 -name "community-plugins.json" -type f 2>/dev/null
find "$(dirname "$VAULT")" -path "*backup*" -maxdepth 4 -type d 2>/dev/null
```

Common backup locations:
- A `_cleanup_archive/` directory at the same level as the vault
- A `知識庫_backup_YYYYMMDD/` directory from previous maintenance runs
- The user's Desktop or Downloads folder

### Validate the Backup

Before restoring, check what the backup contains:

```bash
# Check file count, vault structure, .obsidian presence
BACKUP="/path/to/backup"
echo "Files: $(find "$BACKUP" -type f | wc -l)"
echo "Has .obsidian: $(test -d "$BACKUP/.obsidian" && echo YES || echo NO)"
echo "Has plugins: $(ls "$BACKUP/.obsidian/plugins/" 2>/dev/null | wc -l)"
```

Look for:
- **Nested vault structure** — a backup may have the vault root at the top level AND a subfolder also named `知識庫/` with another `.obsidian`. Only the ROOT `.obsidian/` matters.
- **Plugin folders** — verify the expected plugins are present (check `community-plugins.json`).
- **Config files** — verify `app.json`, `appearance.json`, `core-plugins.json`, `community-plugins.json`.

### Restore

```bash
BACKUP="/path/to/backup"
TARGET="/path/to/live/vault"
rsync -av --progress "$BACKUP/" "$TARGET/"
```

This copies everything (including hidden `.obsidian/`) but preserves any files already in the target that the backup doesn't have (e.g., notes written after the backup).

### Post-Restore Checks

- [ ] `.obsidian/app.json` exists and has valid JSON
- [ ] `.obsidian/community-plugins.json` lists all expected plugins
- [ ] `.obsidian/plugins/<name>/data.json` exists for each listed plugin
- [ ] Template files referenced in plugin configs actually exist at the expected paths
- [ ] The homepage (`🏠 知識庫首頁.md` or similar) is present
- [ ] Note count matches expectations (compare with backup file count)

### Vault Merging

Merging two copies of the same vault (e.g., merging a restored backup into the live vault, or merging two devices' copies). This is **not** the same as Phase E's intra-vault dedup — we're combining two complete vault populations where most files overlap.

#### Identification

Signals to look for:
- User says "把其他地方散落的知識庫都合併到這"
- You know of a second vault directory with similar content
- A restored backup needs its unique files folded into the live vault
- Two copies of a vault diverged due to Syncthing issues

#### Strategy: rsync --ignore-existing

The safest one-way merge uses `rsync --ignore-existing` — it copies files from source to destination ONLY if they don't already exist at the destination:

```bash
SRC="/path/to/source/vault/知識庫"
DST="/path/to/dest/vault/知識庫"

# Preview: what's new in source that dest doesn't have?
cd "$SRC"
find . -type f | while read f; do
  if [ ! -f "$DST/$f" ]; then
    echo "  NEW: $f"
  fi
done | head -30

# Execute merge (no overwrite)
rsync -av --ignore-existing "$SRC/" "$DST/"
```

**Count-check after merge:**
```bash
echo "Source: $(find "$SRC" -name '*.md' -type f | wc -l)"
echo "Dest:   $(find "$DST" -name '*.md' -type f | wc -l)"
```

After merging, both vaults should converge to the same total (assuming the merge was one-way from the larger to the smaller).

#### Bidirectional Merge (Sync After Merge)

If you want both vaults to be equal after the merge, run the reverse direction too:

```bash
# After SRC→DST, also run DST→SRC so both vaults are identical
rsync -av --ignore-existing "$DST/" "$SRC/"
```

This ensures the source vault also gains any files the destination had that source didn't (e.g., newly created Dataview dashboards, maintenance records).

#### Pitfalls

1. **Which vault is authoritative?** Bi-directional rsync (`sendreceive` pattern) works when both vaults started from the same backup. If one has user-generated content the other doesn't, run src→dst first, then dst→src.
2. **Conflicting .obsidian config** — Do NOT merge `.obsidian/` between vaults. Each vault has its own plugin config, theme, and workspace. The rsync command above targets `知識庫/` (notes subdirectory), not the vault root.
3. **Orphaned directories in source** — The source vault may have dustbin directories (e.g., `智研AI法律/` without emoji prefix alongside the canonical `⚖️智研AI法律/`). These get copied as new folders, inflating the dest vault. Either clean them from source first, or do a post-merge dedup pass.
4. **Git status after merge** — Merging adds files. Run `git add -A && git commit -m "📚 merge from <source>"` afterward so Git tracks the additions.
5. **Inbox consolidation** — If both vaults have a `☁️收件夾/`, merge them manually: `cp -n "$SRC_INBOX/"* "$DST_INBOX/"`. There's no automatic dedup by content; duplicates will just appear twice. Let the user sort them.

### Git Init (for Obsidian Git plugin)

After restoring the vault, initialize a Git repository so the Obsidian Git plugin works:

```bash
cd "$VAULT"

# Create .gitignore
cat > .gitignore << 'GITEOF'
.obsidian/workspace*
.obsidian/cache/
.obsidian/plugins/copilot/copilot-index/
知識庫/copilot/copilot-conversations/
*.excalidraw
.DS_Store
Thumbs.db
GITEOF

git init
git config user.name "$USER"
git config user.email "$USER@local"
git add -A
git commit -m "🎉 vault init: restore from backup"
```

**Pitfall:** If the user has Syncthing syncing the vault, pause Syncthing BEFORE `git init` and the initial commit — the mass file changes can trigger a sync storm.

---

## Pre-Phase — Root-Level Consolidation

Move scattered files at the vault root into the proper `知識庫/` subdirectory structure. This runs **before** any frontmatter or structural work — the files need to be in the right folders first.

### When to Use

Run this when the vault root contains `.md` files outside of the main notes subdirectory. Symptoms:
- `ls "$VAULT"/*.md` returns files (beyond `.gitignore` and `.stignore`)
- Root-level folders like `Google Cloud/`, `☁️收件夾/`, `copilot/` exist alongside `知識庫/`
- Templater's `newFileFolderPath` points to a path inside `知識庫/` that doesn't exist yet

### Identify Root Files and Folders

```bash
VAULT="/path/to/vault"
echo "=== Root .md files ==="
ls "$VAULT"/*.md 2>/dev/null
echo "=== Root folders (non-hidden) ==="
find "$VAULT" -maxdepth 1 -type d ! -name ".*" | sort
```

### Classify Files by Content

Read the first 3–5 lines of each root-level file to determine its domain:

```bash
for f in "$VAULT"/*.md; do
  echo "=== $(basename "$f") ==="
  head -5 "$f"
  echo ""
done
```

### Common Classification Map (for a Chinese AI-agent vault)

| Content Signal | Target Directory |
|--------|------------------|
| SSH keys, Windows admin, GCP/KVM infra | `🔧代理管理/` |
| Hermes/OpenClaw install, Agent architecture | `🔧代理管理/` or `🦞AI代理/` |
| Prompt engineering, prompt libraries | `🔧提示詞庫/` |
| Legal/tax/fraud documents | `⚖️法律/` |
| Recipes, misc hobbies | `📦其他/` |
| Unnamed/Untitled placeholders | `☁️收件夾/` (for user review) |
| AI Agent concepts, cognitive architecture | `🦞AI代理/` |
| System audits, dashboards | `🔧代理管理/` |

### Execute the Move

```bash
INNER="$VAULT/知識庫"
mkdir -p "$INNER/☁️收件夾"

# → Target directory
mv "$VAULT/🔑 SSH.md" "$INNER/🔧代理管理/"
mv "$VAULT/未命名.md" "$INNER/☁️收件夾/"
# ... repeat per file
```

### Merge Root Folders into Inner Structure

Root folders like `Google Cloud/`, `☁️收件夾/`, `copilot/` should be merged:

```bash
# Move contents of root inbox into inner inbox
mv "$VAULT/☁️收件夾/"* "$INNER/☁️收件夾/"

# Merge copilot (overwrite with -n to not clobber)
cp -n "$VAULT/copilot/"* "$INNER/copilot/"

# Remove empty root folders
rm -rf "$VAULT/☁️收件夾" "$VAULT/Google Cloud" "$VAULT/copilot"
```

### Second Pass: Classify Inbox → Domain Folders

After all files land in the inbox, do a second pass to move the clearly-destined ones:

| Inbox File | Target | Reason |
|-----------|--------|--------|
| Hermes install guide | `🔧代理管理/` | System management |
| System info / audit | `🔧代理管理/` | System records |
| Agent dashboard | `🔧代理管理/` | Dashboard |
| Fraud/legal analysis | `⚖️法律/` | Legal content |
| AI Agent concepts | `🦞AI代理/` | AI Agent domain |
| Recipe | `📦其他/` | Miscellaneous |

What stays in inbox: unnamed placeholders, finance dashboards, anything needing user attention.

### Pitfalls

1. **Check Templater paths first** — if Templater's `newFileFolderPath` points to `知識庫/☁️收件夾` but that inner folder doesn't exist (`知識庫/知識庫/☁️收件夾`), create it. The root-level inbox may be the real inbox.
2. **Copilot at root vs. inner** — The Obsidian Copilot plugin stores conversations inside the vault. There may be root-level AND inner-level `copilot/` directories. Merge the root's shared prompts into the inner one, keep conversations separate.
3. **Nested `.obsidian/`** — Backups sometimes produce `知識庫/知識庫/.obsidian/` (17MB+ with its own plugin copies). Remove it — only the vault ROOT `.obsidian/` matters.
4. **Nested `.stfolder`** — An inner `知識庫/知識庫/.stfolder` causes Syncthing nested-sync issues. Remove it.
5. **Do NOT move `.gitignore`, `.stignore`, `.obsidian/`** — These belong at the vault root.
6. **Commit after consolidation** — `cd "$VAULT" && git add -A && git commit -m "📂 vault consolidation"` so Git tracks the paths correctly before any structural work.
7. **Root-level inbox path in Omnisearch exclusions** — After moving the inbox from root to inner, Omnisearch's `excludedFolders` may still reference the old root path. Check and update if needed.

---

## Pre-Phase — Rename Unnamed Files

Before any frontmatter work, scan for generic filenames and rename them based on content.

### Scan Targets

| Pattern | Suggested Rename |
|---------|-----------------|
| `未命名.md` or `Untitled.md` | Extract first `# Heading` → use that as filename |
| Files with only generic placeholders | Same approach |

### Script Pattern

```bash
VAULT="/path/to/vault"
find "$VAULT" -name '未命名.md' -not -path '*/.obsidian/*' | while IFS= read -r fp; do
    heading=$(head -1 "$fp" | sed -n 's/^# //p')
    if [ -n "$heading" ]; then
        dir=$(dirname "$fp")
        safe_name=$(echo "$heading" | tr '/\n' '_-' | sed 's/ *$//')
        mv "$fp" "$dir/$safe_name.md"
        echo "Renamed → $safe_name.md"
    fi
done
```

### Pitfalls

1. **Also check `Untitled.md`, `index.md` in inbox folders** — these are often placeholder names.
2. **Use first `# Heading`** not the title in frontmatter (frontmatter won't exist yet).
3. **Sanitize filenames** — strip `/`, `\n`, `:`, and trailing spaces before renaming.

## Phase A — Batch Frontmatter Injection

### Strategy

Scan every `.md` file (excluding `.obsidian/` and `copilot/`). If it lacks a `---` frontmatter block, inject one with `title` and `tags`.

### Approach Selection: Auto vs. Curated

| Frontmatter Coverage | Recommended Approach |
|---------------------|---------------------|
| < 60% | Auto-map tags from directory (see Tag Mapping below) |
| 60–90% | Auto-map with manual review of edge cases |
| **> 90%** | **Curated — manually tag each remaining file with context-appropriate tags** |

When coverage is already high (90%+), the remaining files are often edge cases (directory indexes, inbox captures, archives) that benefit from hand-curation rather than a one-size-fits-all tag map.

### Directory Index (MOC) File Convention

`📋 目錄索引.md` files should get special frontmatter:

```yaml
---
title: "⚖️ 領域名稱 目錄索引"
tags:
  - 目錄索引
  - 領域名稱
  - 知識庫管理
---
```

This distinguishes them from content files and makes them searchable as structural nodes.

### Tag Mapping Convention (for auto-mode)

Map directory names to tags. Use a dictionary in the script:

```python
DIR_TAGS = {
    "00_入口與總覽":    ["法律/AI", "智研", "入口"],
    "10_核心控制層":    ["法律/AI", "智研", "核心"],
    "⚖️法律":           ["法律"],
    "🔧提示詞庫":        ["提示詞"],
    "🪴自我成長":        ["自我成長"],
    # ... etc
}
```

For manual curation mode, build a file-by-file mapping instead:

```python
# Curated mode — hand-pick tags per file
files_fm = {
    "☁️收件夾/My Article.md":
        (["寫手", "文章"], "My Article Title"),
    "🔧提示詞庫/終極提示詞工廠5.0.md":
        (["提示詞工廠", "提示詞生成"], "終極提示詞工廠 5.0"),
    # ...
}
```

**Important:** Do NOT modify the file content below the frontmatter — only prepend the `---` block. Extract `title` from the first `#` heading in the body, or fall back to the cleaned-up filename if no heading exists.

### Title Extraction

```python
m = re.search(r'^# (.+)', content, re.MULTILINE)
if m:
    title = m.group(1).strip()
else:
    name = os.path.splitext(filename)[0]
    name = re.sub(r'^\d+_', '', name)  # strip numeric prefixes like 10_
    title = name.replace('_', ' ').strip()
```

### Verification After Phase A

Run `python3 scripts/vault-audit.py` (or `VAULT_PATH=/path python3 scripts/vault-audit.py`). Target: 100% frontmatter coverage.

## Phase B — Orphan Wikilink Resolution

### Strategy

1. **Scan**: collect all `[[wikilink]]` targets across the vault
2. **Find orphans**: pages whose `basename` appears in NO `[[wikilink]]` in any other file
3. **Group by directory**: batch-fix per subdirectory

### Repair Patterns

| Orphan Type | Fix |
|-------------|-----|
| Same-directory peers | Append `## 📋 相關文件` block with `[[wikilink|Title]]` list of all siblings |
| Version-history files | Cross-link all versions, link main doc to history dir |
| Entry/index pages | Link to all core-control files they should reference |
| Home page | Link to templates, recent updates, key index pages |
| Cross-domain peers (e.g. legal notes) | Link all law-related files to each other |

### Script Structure

For each directory group:

```python
for fp in files_in_subdir:
    siblings = [f for f in all_dir_files if f != fp]
    need_link = [f for f in siblings
                 if os.path.splitext(os.path.basename(f))[0] not in existing_links]
    if need_link:
        links_text = build_wikilink_list(need_link, vault)
        new_content = append_section(content, "📋 相關文件", links_text)
        write_file(fp, new_content)
```

### Caution: Avoid Section Duplication

Check `has_section()` before appending — skip if section already exists (e.g. concept index files with structured listings).

### Verification After Phase B

Run `python3 scripts/vault-audit.py` and check the orphan count dropped significantly.

## Phase C — Index Pages + Tag Taxonomy

After frontmatter and wikilinks are in order, create structural index pages to make navigation searchable.

### Per-Directory MOC Index

Create a `📋 目錄索引.md` in each top-level directory:

```markdown
# ⚖️ 智研AI法律 — 系統總覽
> Description of the directory
最後更新：YYYY-MM-DD ｜ 共 N 筆筆記

## 📂 Subdirectory Name — Description
- [[file-name|File Title]]
- ...
```

Use the directory name's emoji prefix in the MOC title. Tag pattern for MOCs: `[目錄索引, 領域名, 知識庫管理]`.

### Homepage Update

Append a 「🗺️ 領域索引」table to the vault's root homepage, linking to each MOC:

```markdown
## 🗺️ 領域索引
| 領域 | 說明 | 筆記數 |
|------|------|--------|
| [[link/to/index|⚖️ 智研AI法律]] | Description | 84 |
```

Do this last — after all other changes — so the index is accurate.

### Tag Taxonomy Reference

Create a `🏷️ 標籤系統總覽.md` with:
- Tree-style visual of the tag hierarchy
- Optional Dataview query for tag usage counts

### Syncthing & Sync Disaster Prevention

If the Obsidian vault is synced with Syncthing (look for `.stfolder` in the vault root):

1. **CHECK SYNC SETTINGS FIRST** before any bulk operation — mass file changes during vault maintenance can trigger a sync storm that propagates deletions.
2. **`ignoreDelete=true`** — If the vault is under Syncthing, recommend setting `ignoreDelete=true` for the folder. Otherwise, a remote device connecting with an empty folder will wipe the entire vault.
3. **Enable versioning** — Syncthing's Simple File Versioning (5 copies, 1-hour cleanup) creates `.stversions` as a safety net.
4. **Pause Syncthing during maintenance** — Before running any bulk rename/merge operation, tell the user to pause Syncthing on ALL connected devices. Resume only after the vault is stable.
5. **Sendreceive is dangerous** — Two-way sync means deletions on any connected device propagate everywhere. Prefer `sendonly` (primary) + `receiveonly` (secondary) for mission-critical vaults.
6. **Fresh VMs wipe data** — Never connect a new VM instance in sendreceive mode to a folder that already has data. The VM's empty state overwrites the local data.

### `.stfolder` Recovery (Critical)

The `.stfolder` marker file tells Syncthing which directories are synced folders. If it's accidentally deleted (e.g., during vault cleanup), Syncthing stops recognizing the vault and will NOT sync any changes — potentially causing data loss on remote devices.

**Detection:**
```bash
find "$VAULT" -name ".stfolder" -maxdepth 1 2>/dev/null || echo "MISSING — Syncthing will not sync this folder"
```

**Recovery:**
```bash
mkdir -p "$VAULT/.stfolder"
```

**Do NOT add `.stfolder` to `.stignore`.** Each SyncThing device creates its own local `.stfolder` marker — it is NEVER synced between devices. Adding it to `.stignore` would prevent the local marker from being detected.

**Nested vault issue:** If a backup restoration created an inner `知識庫/.stfolder/` alongside the root `.stfolder/`, Syncthing may treat the inner folder as a separate sync target. Remove the inner one:
```bash
rm -rf "$VAULT/知識庫/.stfolder"   # only remove the INNER one
```

**Post-recovery verification:**
```bash
# SyncThing should show the folder as "Up to Date" again
cat /mnt/c/Users/$USER/AppData/Local/Syncthing/syncthing.log | grep -i "folder.*obsidian" | tail -5
```

See `data-backup` skill for full Syncthing disaster recovery workflow.

## Phase D — Template Creation (Informed by Existing Structure)

After structural cleanup, the user may want templates that match their actual vault organization. **Do not create templates in isolation — audit existing ones first.**

### Step 1: Audit Existing Templates

```bash
TEMPLATES="$VAULT/🎛️模板"
for tmpl in "$TEMPLATES"/*.md; do
    echo "--- $(basename "$tmpl") ---"
    head -20 "$tmpl"
done
```

### Step 2: Identify Gaps

Compare existing templates against the vault's content *types*:

| Content Type | Found In Directories | Has Template? |
|-------------|---------------------|---------------|
| General notes | All directories | ✅ (一般筆記模板) |
| Quick captures | ☁️收件夾 | ✅ (收件夾快速捕捉) |
| Domain-specific specs | ⚖️智研AI法律 | ✅ (智研功能規格) |
| Domain-specific concepts | ⚖️智研AI法律 | ✅ (智研概念詞條) |
| Learning/research notes | 📚提示詞工程, 🤖多模型委員會, 🦞AI代理 | ❌ Gap |
| Development notes | 💎磐石技能開發, 🔧提示詞庫 | ❌ Gap |
| Personal growth | 🪴自我成長 | ❌ Gap |
| MOC index pages | Every directory | ❌ Gap |

### Step 3: Offer Staged Template Creation

Present as clear A→B→C options, not a single plan:

- **A. Universal template** — one template that covers all note types (simplest)
- **B. Per-domain template series** — 3–5 templates targeting the identified gaps
- **C. Full template suite** — universal + per-domain + MOC template (full coverage)

### Step 4: Template Frontmatter Conventions

Match the vault's existing naming conventions:
- **Tag format**: block-list YAML (`tags:\n  - tagname`), NOT inline `[tagname]`
- **status values**: `draft`, `inbox`, `active`, `published`, `archived`
- **type values**: `note`, `capture`, `concept`, `agent-spec`, `learning`, `development`, `growth`, `moc`
- **dir emoji prefix**: match the directory's emoji in filenames (e.g., `📚`, `🤖`, `🪴`)

### Verification After Phase D

- [ ] New templates match the naming conventions observed in the vault
- [ ] Templates use Obsidian-compatible frontmatter (`tp.date.now`, `tp.file.title` as Metadata Menu placeholders)
- [ ] Tags in templates align with tags used throughout the vault

## Phase E — Structure Normalization (Emoji Prefix + Deduplicate + Boundary)

Apply this phase AFTER frontmatter and indexing are complete (Phases A–D). It is the polishing pass that makes the vault visually consistent and eliminates structural waste.

### Step 0: Read the Current Triggers

The user will usually say something like:
- 「命名統一化」
- 「加上 emoji 符號」
- 「重複的內容進行合併」
- 「全面盤查」

Always offer this as a single comprehensive phase (not A→B→C sub-options) since the steps interlock — renaming shifts paths, dedup removes files, and both break any wikilinks that haven't been healed already.

### Step 1: Boundary Identification — Vault Notes vs. Project Source

Before any rename or merge, identify directories that are **source code / project directories**, not vault notes. These should be excluded from emoji normalization and structural restructuring:

| Signal | Example | Action |
|--------|---------|--------|
| Contains `src/`, `tests/`, `examples/` | `zhiyan-legal/` | ⛔ Do not rename |
| Contains `.py`, `.js`, `.json` source files | Skill project repos | ⛔ Do not rename |
| Contains `README.md` with code documentation | Any Hermes skill | ⛔ Do not rename |
| Contains `copilot/` | Obsidian Copilot data | ⛔ Never touch |
| Contains `.obsidian/` | Obsidian system config | ⛔ Never touch |

**Pattern** — check for `src/`, `tests/`, or non-markdown code files in the root before operating on a directory:

```python
EXCLUDED_DIRS = {".obsidian", "copilot"}
PROJECT_DIRS = set()  # populated dynamically

for d in os.listdir(vault):
    dp = os.path.join(vault, d)
    if not os.path.isdir(dp): continue
    if d in EXCLUDED_DIRS: continue
    has_src = os.path.isdir(os.path.join(dp, "src"))
    has_tests = os.path.isdir(os.path.join(dp, "tests"))
    has_code_files = any(f.endswith((".py", ".js", ".json")) for f in os.listdir(dp) if os.path.isfile(os.path.join(dp, f)))
    if has_src or has_tests or has_code_files:
        PROJECT_DIRS.add(d)
        print(f"🔒 Identified project source dir: {d}")
```

### Step 2: Emoji Prefix Normalization

Scan all top-level directories (excluding those identified in Step 1). Ensure each has a consistent emoji prefix.

**Convention table** (example from a Chinese-language AI-agent vault):

| Domain | Emoji Prefix | Example Dir Name |
|--------|:-----------:|------------------|
| Legal AI System | ⚖️ | ⚖️智研AI法律 |
| Legal Essays | ⚖️ | ⚖️法律 |
| Writer Prompts | ✍️ | ✍️寫手提示詞 |
| Skills / Dev | 💎 | 💎磐石技能開發 |
| Learning Notes | 📚 | 📚提示詞工程(學習） |
| Prompt Library | 🔧 | 🔧提示詞庫 |
| Agent Config | 🔧 | 🔧代理管理 |
| Multi-Model | 🤖 | 🤖多模型委員會開發 |
| AI Agents | 🦞 | 🦞AI代理 |
| Personal Growth | 🪴 | 🪴自我成長 |
| Other / Misc | 📦 | 📦其他 |
| Templates | 🎛️ | 🎛️模板 |
| Inbox | ☁️ | ☁️收件夾 |

**Script pattern** for detecting emoji-less directories:

```python
import unicodedata

def has_emoji_prefix(name):
    if len(name) == 0: return False
    first = name[0]
    if '\u2000' <= first <= '\u27ff': return False
    if '\u2e80' <= first <= '\uffef': return False
    cp = ord(first)
    return (
        0x2600 <= cp <= 0x27BF or
        0x1F300 <= cp <= 0x1F9FF or
        0x2702 <= cp <= 0x27B0
    )
```

For directories without an emoji prefix, present the user with a mapping and execute the rename:

```python
EMOJI_MAP = {
    "智研AI法律": "⚖️智研AI法律",
    "提示詞庫": "🔧提示詞庫",
    # ...
}
for old_name, new_name in EMOJI_MAP.items():
    old_path = os.path.join(vault, old_name)
    new_path = os.path.join(vault, new_name)
    if os.path.exists(old_path) and not os.path.exists(new_path):
        os.rename(old_path, new_path)
```

### Step 3: Detect and Merge Duplicate Directories

A duplicate directory exists when TWO top-level folders contain the same numbered subdirectory structure (e.g., both have `00_入口與總覽`, `10_核心控制層`, etc.).

**Detection pattern:**

```python
def get_subdir_signature(dpath):
    sig = set()
    for root, dirs, files in os.walk(dpath):
        for d in sorted(dirs):
            rel = os.path.relpath(os.path.join(root, d), dpath)
            sig.add(rel)
        break
    return frozenset(sig)

dirs = [d for d in os.listdir(vault) if os.path.isdir(os.path.join(vault, d))]
signatures = {d: get_subdir_signature(os.path.join(vault, d)) for d in dirs}

pairs_found = []
for a in dirs:
    for b in dirs:
        if a >= b: continue
        overlap = signatures[a] & signatures[b]
        if len(overlap) >= 3:
            pairs_found.append((a, b, overlap))
```

**Merge strategy:**

1. Identify which copy is the **canonical** version (usually the one with an emoji prefix and more total files).
2. Walk the non-canonical directory tree. For each file:
   - If it does NOT exist in canonical → **copy** it over.
   - If it exists and content is **identical** → skip.
   - If it exists and content **differs** → copy with `_old` suffix on the basename.
3. After merge, **delete** the non-canonical directory with `shutil.rmtree()`.
4. Update all `[[wikilink]]` references in the vault that pointed to the deleted directory.

**Pitfall — homepage / dashboard links:** After merging, check all `.md` files for stale links:

```python
for fp in all_md_files:
    content = open(fp, 'r', encoding='utf-8').read()
    if old_dir_name in content:
        content = content.replace(old_dir_name, canonical_dir_name)
        open(fp, 'w', encoding='utf-8').write(content)
```

### Step 4: File-Level Duplicate Detection

After directory dedup, scan within each directory for near-identical filenames:

```python
all_files = []
for root, dirs, files in os.walk(vault):
    if '.obsidian' in root or '/copilot' in root: continue
    for f in files:
        if f.endswith('.md'):
            all_files.append(os.path.join(root, f))

from collections import defaultdict
name_groups = defaultdict(list)
for fp in all_files:
    fname = os.path.splitext(os.path.basename(fp))[0]
    normalized = fname.replace('「', '').replace('」', '').replace('——', '').replace('—', '').replace(' ', '')
    name_groups[normalized].append(fp)

for key, fps in name_groups.items():
    if len(fps) > 1:
        print(f"⚠️  Possible duplicate ({len(fps)} versions): {key}")
        for fp in fps:
            print(f"     {os.path.relpath(fp, vault)}")
```

For each group, compare sizes first, then content. Keep the version with richer frontmatter.

### Step 5: Run Final Audit + Update MOCs + Homepage

1. Run the vault audit script to verify frontmatter coverage is intact
2. Regenerate all per-directory 📋 目錄索引.md files
3. Update homepage「🗺️ 領域索引」table with correct counts and paths
4. Verify cron jobs referencing dashboard files still resolve

### Pitfalls Specific to Phase E

1. **Project source directories** — `zhiyan-legal/`, `copilot/`, and any dir with `src/`/`tests/` subdirectories are NOT vault notes. Do not rename or restructure them.
2. **Cron-referenced files** — search for `.py`, `.sh`, `.cmd`, `.ps1`, `.hta` files referencing old directory paths after merge.
3. **`_old` suffix accumulation** — use `_old` exactly once. If both copies differ and one already has `_old`, skip.
4. **Wikilink breakage** — every file move/rename breaks `[[wikilink]]` references. Run bulk search-and-replace after structural changes.
5. **Emoji dirs in WSL** — emoji characters (⚖️) work correctly under `/mnt/c/` paths. No special encoding needed for Windows paths in 2026.
6. **Offer one comprehensive pass** — Phase E steps interlock, so present as a single operation (unlike Phases A–C).

## Phase F — Plugin Configuration & Optimization (Post-Restore)

After vault restoration or as a one-time optimization pass, configure community plugins for maximum effectiveness. Skip Copilot — the user manages that one themselves.

### Common Plugin Path Bug

A recurring bug in `data.json` files: **concatenated path entries** where two exclusion paths are missing the comma separator between them.

```json
// BUG — two paths fused into one string:
"知識庫/copilot/copilot-conversations 知識庫/⚖️智研AI法律/80_封存參考"

// FIX — proper comma separation:
"知識庫/copilot/copilot-conversations",
"知識庫/⚖️智研AI法律/80_封存參考"
```

This bug can appear in **three plugins** simultaneously — always check all three:
- `obsidian-linter/data.json` → `foldersToIgnore`
- `metadata-menu/data.json` → `ignoredFolders`
- `omnisearch/data.json` → `excludedFolders`

### Plugin Optimization Checklist

#### Omnisearch
```json
{
  "openInNewPane": true,
  "showCreateButton": true,
  "recencyBoost": "0.5"
}
```

**Exclusions to review:** If legal notes or other core content directories are excluded, ask the user if they want search to cover them.

#### Obsidian Linter
```json
{
  "lintOnSave": true,
  "ruleConfigs": {
    "yaml-timestamp": {
      "enabled": true,
      "dateCreated": "created",
      "dateModified": "updated",
      "date-created-key": "created",
      "date-modified-key": "updated"
    },
    "yaml-key-sort": { "enabled": true },
    "format-yaml-array": { "enabled": true },
    "empty-line-around-blockquotes": { "enabled": true },
    "empty-line-around-code-fences": { "enabled": true },
    "empty-line-around-tables": { "enabled": true }
  }
}
```

**Key fix:** Ensure `date-created-key` and `dateCreated` use the SAME key name (`created`). If they diverge (e.g., `dateCreated: "created"` but `date-created-key: "date created"`), the linter writes to the wrong field.

#### QuickAdd

From zero choices (empty config), set up at minimum a **Capture** and a few **Template** choices:

```json
{
  "choices": [
    {
      "name": "📥 快速捕捉",
      "type": "Capture",
      "captureTo": "知識庫/☁️收件夾/📥 快速捕捉 {{DATE:YYYY-MM-DD HHmmss}}.md",
      "format": { "template": "知識庫/🎛️模板/收件夾快速捕捉模板.md" },
      "openFileInNewTab": { "enabled": true }
    },
    {
      "name": "📝 一般筆記",
      "type": "Template",
      "template": "知識庫/🎛️模板/一般筆記模板.md",
      "folder": "知識庫/☁️收件夾"
    }
  ],
  "enableRibbonIcon": true
}
```

Add per-domain Template choices for the vault's content types (學習筆記, 開發筆記, etc.).

#### Metadata Menu — Preset Fields

Add at minimum:
- `importance` (Number) — 1–5 priority scale
- `topics` (YAML array) — unbounded keyword list

#### Obsidian Git

The plugin does NOT work without an initialized Git repository. After `git init` + first commit:

```json
{
  "disablePush": false,
  "autoSaveInterval": 30,
  "autoPushInterval": 30,
  "autoPullInterval": 30,
  "autoBackupAfterFileChange": true
}
```

**No remote?** The plugin still provides local version history (auto-commit every 30s).

#### Core Settings (app.json)
```json
{
  "livePreview": true,
  "alwaysUpdateLinks": true,
  "defaultViewMode": "preview"
}
```

Enable **Workspaces** in `core-plugins.json`:
```json
{ "workspaces": true }
```

#### CSS Snippets

Create `.obsidian/snippets/` with a comprehensive CSS file. Essential areas for Chinese/English mixed-content vaults:

| Rule Area | Purpose |
|-----------|---------|
| **Font stack** | `Microsoft YaHei`, `PingFang SC` for Chinese; `Segoe UI` for UI |
| **Letter spacing** | `0.02em` improves Chinese readability |
| **Tables** | Full-width, thead bg, hover highlight |
| **Callouts** | `border-radius: 8px`, strong left `border-left: 4px` |
| **Headings** | H1/H2 bottom borders, padding-top spacing |
| **Tags** | Pill-style `border-radius: 12px` |
| **Code blocks** | `border-radius: 8px`, padded |
| **Blockquotes** | Accent border, rounded right corners, bg tint |
| **Mobile** | `@media (max-width: 768px)` — tighter spacing |
| **Links** | Dashed bottom border, hover accent color |
| **Tasks** | Strikethrough on checked items |

Enable the snippet in `appearance.json` → `enabledCssSnippets: ["<filename>"]`.

#### Appearance Configuration (appearance.json)

```json
{
  "accentColor": "#7b68ee",
  "cssTheme": "",
  "theme": "obsidian",
  "baseFontSize": 15,
  "enabledCssSnippets": ["🧹 自訂樣式"]
}
```

Choices: `theme: "obsidian"` (default, cross-platform consistent), accentColor pick a soft purple (`#7b68ee`), blue, or green. `baseFontSize: 15` for Chinese/English mix.

#### Cross-Device Sync Protection (Syncthing)

If the vault uses Syncthing (detect by `.stfolder` in vault root), create `.stignore`:

```
.obsidian/workspace.json
.obsidian/workspace-mobile.json
.obsidian/cache/
copilot/copilot-conversations/
```

**CRITICAL: Do NOT add `.stfolder` or `.stignore` to `.stignore`.** Each Syncthing device creates its own local `.stfolder` marker — adding it to `.stignore` would prevent the folder from being detected. The `.stignore` file is also per-device and should never be excluded.

**Syncthing folder path migration:** If the vault's folder path changed in Syncthing's config (e.g., after merging vaults), update `config.xml`:
```bash
# Stop syncthing first (Windows)
cmd.exe /c "taskkill /f /im syncthing.exe"

# Edit config.xml to point to the new path
# C:\Users\%USERNAME%\AppData\Local\Syncthing\config.xml
# Change: path="C:\Old\Path" → path="C:\New\Path"

# Restart Syncthing
cmd.exe /c "start /B C:\Users\%USERNAME%\AppData\Local\Syncthing\syncthing.exe --no-browser"
```

**Nested vault cleanup:** Backups may create `知識庫/知識庫/.obsidian/` with its own plugin folders (17MB+). Remove it — Obsidian reads only the vault root. An inner `.stfolder` also causes SyncThing issues.

**Phone setup:** Install Obsidian → point to SyncThing folder → enable Community Plugins → plugins auto-appear.

#### Git Init (for Obsidian Git)

```bash
cd "$VAULT"
cat > .gitignore << 'GITEOF'
.obsidian/workspace*
.obsidian/cache/
.obsidian/plugins/copilot/copilot-index/
copilot/copilot-conversations/
*.excalidraw
.DS_Store
Thumbs.db
GITEOF
git init && git add -A && git commit -m "🎉 vault init"
```

No remote needed — Git saves local version history (auto-commit every 30s).

### Phase G — Copilot Prompt Management

After the vault is structurally clean and plugins are configured, manage the Obsidian Copilot plugin's custom prompts. Copilot keeps its prompts in the vault's `copilot/copilot-custom-prompts/` directory — each `.md` file is one slash command.

### When to Use

- User says 「Copilot 提示詞整理」「合併提示詞」「重複提示詞」
- You notice two `copilot/` directories in the vault (root + inner 知識庫/copilot)
- The prompt list has grown large and contains duplicate or near-identical entries

### Identify Duplicate Copilot Directories

After vault restoration from backup, the vault may have TWO copilot directories:

```bash
VAULT="/path/to/vault"
echo "Root copilot: $(find \"$VAULT/copilot\" -type f | wc -l) files"
echo "Inner copilot: $(find \"$VAULT/知識庫/copilot\" -type f | wc -l) files"
```

Common split:
| Location | Typical Content |
|----------|----------------|
| Root `copilot/` | English built-in prompts (Clip Web, Summarize, Emojify, etc.) + user templates + current conversations |
| Inner `知識庫/copilot/` | User-created Chinese custom prompts (精準內容減量器, 極速三合一萃取器, etc.) + older conversations + system prompts |

### Merge Strategy

Merge inner → root using `rsync --ignore-existing`, then remove the inner:

```bash
rsync -av --ignore-existing "$INNER/copilot-custom-prompts/" "$ROOT/copilot-custom-prompts/"
rsync -av --ignore-existing "$INNER/system-prompts/" "$ROOT/system-prompts/"
rsync -av --ignore-existing "$INNER/copilot-conversations/" "$ROOT/copilot-conversations/"
rsync -av --ignore-existing "$INNER/memory/" "$ROOT/memory/"
cp -n "$INNER/copilot-custom-prompts.md" "$ROOT/"
rm -rf "$INNER"
```

### Detect Redundant Prompts

After merging, scan for pairs where an English built-in prompt and a Chinese custom prompt serve the same function. The user-created Chinese versions are usually more detailed and preferred.

Common redundant pairs (EN → CN):

| English Built-in (small, ~350-500B) | Chinese Custom (detailed, ~800-2400B) | Action |
|--------------------------------------|----------------------------------------|--------|
| Emojify.md | ✨ 視覺感官增強器 (Emoji 裝飾版).md | Delete EN |
| Translate to Chinese.md | 🇹🇼 繁體中文在地化翻譯器.md | Delete EN |
| Explain like I am 5.md | 🍭 幼兒級白話解釋器 + 🎒 知識普及化簡化器 | Delete EN |
| Make shorter.md | ⚖️ 精準內容減量器 (50% 濃縮版).md | Delete EN |
| Summarize.md | 📌 精煉內容核心摘要 / ⚡ 極速三合一萃取器 / 🧠 PKM 壓縮器 | Delete EN |
| Remove URLs.md | 🧹 網址自動清除器.md | Delete EN |
| Generate table of contents.md | 📑 階層式文件目錄產生器.md | Delete EN |
| Generate glossary.md | 📖 關鍵術語與概念詞彙表.md | Delete EN |
| Fix grammar and spelling.md | 📝 語法與格式精準校對器.md | Delete EN |
| Make longer.md | 📝 內容深度擴充器 (2倍細節版).md | Delete EN |
| Simplify.md | ⚖️ 精準內容減量器 / 🎒 知識普及化簡化器 | Delete EN |
| Rewrite as tweet.md / thread.md | 📱 社群貼文轉化器 / 📸 FB_IG 系列貼文產生器 | Delete EN |
| Clip Web Page.md | 🌐 Web Clipper 知識內化模板.md | Delete EN |

**Verification before deleting:** Read a few lines of content to confirm the pair truly serves the same purpose. The frontmatter `copilot-command-context-menu-enabled` and `copilot-command-slash-enabled` fields indicate the command type.

**Keep** prompts that have no Chinese equivalent (e.g., Clip YouTube Transcript.md — YouTube-specific template with title/description/channel frontmatter).

### Post-Merge Verification

```bash
echo "Root copilot: $(find \"$VAULT/copilot\" -type f | wc -l) files"
echo "custom-prompts: $(ls \"$VAULT/copilot/copilot-custom-prompts/\" | wc -l)"
echo "system-prompts: $(ls \"$VAULT/copilot/system-prompts/\" | wc -l)"
echo "conversations: $(ls \"$VAULT/copilot/copilot-conversations/\" | wc -l)"
```

### Update .stignore After Merge

After removing the inner copilot directory, update `.stignore`:

```bash
cat > "$VAULT/.stignore" << 'STEOF'
.obsidian/workspace.json
.obsidian/workspace-mobile.json
.obsidian/cache/
copilot/copilot-conversations/
STEOF
```

### Pitfalls

1. **Do NOT merge `.obsidian/`** from inner to root — each vault has its own plugin config.
2. **Conversations folder grows large** — The `.stignore` already excludes `copilot-conversations/` from SyncThing. After merging, verify the path in `.stignore` matches the new location (`copilot/` not `知識庫/copilot/`).
3. **Copilot plugin reads FROM vault root** — The plugin always uses `VAULT/copilot/`, NOT any subdirectory. Prompts in an inner `知識庫/copilot/` were likely unused. The merge makes them discoverable.
4. **Commit after merge** — `git add -A && git commit -m "🔄 merge copilot directories + dedup prompts"`

## Phase H — Template Optimization (Post-Audit)

After creating or auditing templates (Phase D), optimize them for consistency with Metadata Menu and the vault's frontmatter conventions.

### Step 1: Audit Current Template Frontmatter

```bash
TMPL="$VAULT/知識庫/🎛️模板"
for f in "$TMPL"/*.md; do
    echo "--- $(basename "$f") ---"
    head -12 "$f"
    echo
done
```

### Step 2: Apply Consistent Fields Across All Templates

Every template should include these standard fields for Metadata Menu compatibility:

```yaml
---
title: <% tp.file.title %>
aliases:           # ← ADD
created: <% tp.date.now("YYYY-MM-DD") %>
updated: <% tp.date.now("YYYY-MM-DD") %>
status: draft      # or inbox / active / growing
type: note         # or capture / learning / dev / moc / concept
importance:        # ← ADD (Number, 1-5)
topics: []         # ← ADD (YAML array)
tags:
  - tagname
---
```

### Step 3: Fix Common Template Issues

| Issue | Fix |
|-------|-----|
| `tags: [模板]` on general note template | Change to `tags: []` — the template should not self-tag |
| Missing `aliases` | Add as first field after `title` — enables `[[wikilink|Display Name]]` |
| Missing `importance` | Add — Metadata Menu expects this field |
| Missing `topics` | Add as YAML array |
| Inconsistent `type` values | Use controlled vocabulary: `note, capture, concept, agent-spec, learning, dev, growth, moc` |

### Step 4: Add Domain-Specific Sections

| Template Domain | Add Sections |
|----------------|-------------|
| Learning notes | 「核心概念」「重點整理」「實際應用」「參考來源」 |
| Development notes | 「目標」「實作步驟」「技術筆記」「相關資源」 |
| Inbox capture | 「原始內容」「初步判斷」「後續行動」「歸檔決策」 |
| General notes | 「摘要」「重點」「延伸思考」「行動項目」 |

### Pitfalls

1. **`updated` in templates** — Set to the same as `created` initially. Linter overwrites on save if configured.
2. **`aliases` empty syntax** — `aliases:` on its own line (no value) is valid YAML null → Obsidian ignores it.
3. **Metadata Menu field types** — `importance` must be `type: Number`, `topics` must be `type: YAML` in Metadata Menu's `presetFields`.
4. **Skip `updated` on capture templates** — Captures are one-shot; `updated` is meaningless.

## Phase I — Plugin Recommendations

After core plugins are configured (Phase F), recommend additional plugins. Present as a short table with clear reasons.

### Recommendation Selection

| Vault Characteristic | Recommended Plugins |
|---------------------|-------------------|
| Chinese content, many filenames | **Various Complements** (autocomplete [[ links) |
| Legal/tech system diagrams | **Excalidraw** (hand-drawn style) |
| 100+ tags needing management | **Tag Wrangler** (bulk rename/merge) |
| Many long notes | **Note Refactor** (extract sections) |
| Custom CSS just created | **Style Settings** (adjust CSS variables) |
| Directory-based organization | **Folder Notes** (click folder → MOC) |

### Format

```markdown
| Plugin | Why | When |
|--------|-----|------|
| Excalidraw | Hand-drawn diagrams | Vault has system docs |
| Tag Wrangler | Bulk tag mgmt | 100+ tags |
```

Install from Obsidian: 設定 → 社群外掛 → 瀏覽 → install.

### Verification checklist (Phase I)

- [ ] Plugins installed via GitHub releases (manifest.json + main.js + styles.css in `.obsidian/plugins/<id>/`)
- [ ] community-plugins.json updated with new plugin IDs
- [ ] Linter fires on save (edit a note, save, confirm linter ran)
- [ ] QuickAdd 4+ commands visible in Command Palette
- [ ] Omnisearch opens results in new pane
- [ ] Metadata Menu shows importance + topics in frontmatter autocomplete
- [ ] Git status shows clean tree (all changes committed)
- [ ] .gitignore excludes workspace cache and copilot conversations
- [ ] The 3-plugin path-bug check passed (no concatenated exclusion paths)
- [ ] CSS snippet is enabled in appearance.json and file exists at `.obsidian/snippets/<name>.css`
- [ ] .stignore exists and excludes workspace/cache/copilot-conversations
- [ ] No orphaned nested `.obsidian/` directories inside the vault

### Plugin Installation from GitHub

When the user says to install plugins (not just recommend), download the latest release from GitHub:

```bash
install_plugin() {
  local id="$1"
  local repo="$2"
  local dir="$VAULT/.obsidian/plugins/$id"
  
  mkdir -p "$dir"
  curl -sL "https://github.com/$repo/releases/latest/download/manifest.json" -o "$dir/manifest.json"
  if [ ! -s "$dir/manifest.json" ]; then
    curl -sL "https://raw.githubusercontent.com/$repo/main/manifest.json" -o "$dir/manifest.json"
  fi
  curl -sL "https://github.com/$repo/releases/latest/download/main.js" -o "$dir/main.js"
  if [ ! -s "$dir/main.js" ]; then
    curl -sL "https://raw.githubusercontent.com/$repo/main/main.js" -o "$dir/main.js"
  fi
  curl -sL "https://github.com/$repo/releases/latest/download/styles.css" -o "$dir/styles.css" 2>/dev/null
}

# Update community-plugins.json
python3 -c "
import json
path = '$VAULT/.obsidian/community-plugins.json'
with open(path) as f:
    plugins = json.load(f)
for new_id in ['obsidian-style-settings', 'obsidian-various-complements-plugin', 'note-refactor-obsidian', 'tag-wrangler']:
    if new_id not in plugins:
        plugins.append(new_id)
with open(path, 'w') as f:
    json.dump(plugins, f, indent=2)
"
```

**Mobile-compatible plugins** (no heavy GPU/CPU requirements):
- `obsidian-style-settings` (mgmeyers/obsidian-style-settings) — CSS variable adjustment
- `obsidian-various-complements-plugin` (tadashi-aikawa/obsidian-various-complements-plugin) — [[ autocomplete, config below
- `note-refactor-obsidian` (lynchjames/note-refactor-obsidian) — extract selection to new note
- `tag-wrangler` (pjeby/tag-wrangler) — bulk tag management

**Various Complements config** (optimized for Chinese content):
```json
{
  "strategy": "default",
  "matchStrategy": "prefix",
  "matchMobile": true,
  "minNumberOfCharactersTriggeringSearchMobile": 1,
  "maxNumberOfSuggestions": 15,
  "matchInternalLink": true,
  "matchFrontmatter": true,
  "matchTags": true,
  "frontMatterComplementStrategy": "hybrid",
  "fileComplementStrategy": "hybrid",
  "aliasSuggestions": true
}
```

## Common Pitfalls (All Phases)

1. **Trusting `OBSIDIAN_VAULT_PATH` without verification** — On Windows WSL, `.env` may define `OBSIDIAN_VAULT_PATH` pointing to a backup directory that was restored from, while the real active Obsidian vault is elsewhere. Always verify by checking Obsidian's `obsidian.json` config for `"open": true`.
2. **Accidentally deleting `.stfolder`** — A missing `.stfolder` causes Syncthing to stop recognizing the folder. If you moved/cleaned up directories, check `.stfolder` still exists at the vault root after the operation. If gone, recreate with `mkdir -p "$VAULT/.stfolder"`.
3. **Adding `.stfolder` to `.stignore`** — This would prevent Syncthing from detecting the folder at all. `.stignore` must NOT exclude `.stfolder`; each device creates its own marker locally.
4. **Concatenated exclusion paths in plugin data.json** — two exclusion paths fused without comma separator. Check all three: linter, metadata-menu, omnisearch.
2. **Linter timestamp key mismatch** — `dateCreated` and `date-created-key` must match. Normalize both to `created`.
3. **Obsidian Git without a repo** — silently fails. Init repo + add `.gitignore`.
4. **Section duplication** — always check `has_section()` before appending `## 📋 相關文件`.
5. **`yaml.safe_load` on bad frontmatter** — wrap in try/except; skip files that don't parse.
6. **Do NOT touch raw content** — Phase A prepends only. Phase B appends at bottom only.
7. **Backup first** — `cp -r "$VAULT_PATH" "$VAULT_PATH.bak.$(date +%Y%m%d)"`.
8. **High-coverage vaults (90%+) need curated tagging** — hand-crafted file map for edge cases.
9. **Template creation must be vault-informed** — audit existing templates first.
10. **Acceptable orphans** — inbox notes, homepage, intentionally isolated notes don't need links.

## Verification Checklist

- [ ] Phase A: no files start with content — all start with `---`
- [ ] Phase B: orphan count drops to single digits (legitimate orphans only)
- [ ] Phase D: templates match the vault's content types and naming conventions
- [ ] Phase E: no duplicate directories; all top-level dirs have emoji prefixes; project source dirs untouched
- [ ] Phase F: Linter fires on save; QuickAdd commands visible; Omnisearch opens new pane; Git repo exists
- [ ] Phase F: No concatenated paths in `foldersToIgnore`, `ignoredFolders`, or `excludedFolders`
- [ ] Homepage 領域索引 table reflects current structure
- [ ] Audit passes: `python3 scripts/vault-audit.py`

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/vault-audit.py` | Audit: frontmatter coverage, orphan count, tag usage. `VAULT_PATH=/path python3 scripts/vault-audit.py` |
| `scripts/inject-frontmatter.py` | Phase A: batch frontmatter injection by directory mapping |
| `scripts/link-orphans.py` | Phase B: cross-link same-directory peers, version histories, and index pages |

### Reference Files

| Reference | Purpose |
|-----------|---------|
| `references/vault-dedup-merge-pattern.md` | 重複目錄的差異合併流程、Pitfall 與 Wikilink 修復 |
| `references/session-20260607-dedup-and-emoji.md` | 2026-06-07 session: Phase E dedup + emoji normalization detail |
| `references/session-20260524-template-frontmatter.md` | 2026-05-24 session: template creation and frontmatter conventions |
| `references/session-20260523-optimization.md` | 2026-05-23 session: attribute fixing and tag unification |
| `references/session-20260616-restore-and-plugin-config.md` | 2026-06-16 session: vault restoration from backup + plugin optimization with exact data.json values |
| `references/session-20260616-vault-merge-and-path-correction.md` | 2026-06-16 session: vault merge (rsync --ignore-existing) + .stfolder recovery + vault path correction |
| `references/session-20260616-plugin-install.md` | 2026-06-16 session: plugin installation + Syncthing config migration + .stignore fix |

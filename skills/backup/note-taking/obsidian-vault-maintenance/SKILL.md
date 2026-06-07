---
name: obsidian-vault-maintenance
description: Audit and restructure Obsidian vaults — batch frontmatter injection, orphan-link resolution, cross-note wikilink healing, and index/MOC generation. Use when the user wants to clean up, reorganize, or audit their vault's structural integrity.
version: 2.1.0
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

Always resolve the vault path first, in this order:

1. `OBSIDIAN_VAULT_PATH` environment variable
2. User's known vault path from memory (e.g., `/mnt/c/Users/ysga1/Desktop/知識庫/知識庫/`)
3. Fallback: `~/Documents/Obsidian Vault`

```bash
# Resolve once, use everywhere
VAULT="${OBSIDIAN_VAULT_PATH:-/path/to/vault}"
```

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

## Pitfalls

1. **Section duplication** — always check `has_section()` before appending a `## 📋 相關文件` block. Concept index files already have structured listings.
2. **`yaml.safe_load` on malformed frontmatter** — wrap in try/except. Skip files that don't parse rather than crash.
3. **Do NOT touch raw content** — Phase A prepends only, never rewrites body. Phase B only appends sections at file bottom. Never modify existing wiki content.
4. **Backup first** — `cp -r "$VAULT_PATH" "$VAULT_PATH.bak.$(date +%Y%m%d)"` before starting.
5. **YAML issues to check after every batch run:**
   - **Quotes in titles** — titles containing colons (`Role: AI 內核...`) must be quoted in YAML or parsing silently fails.
   - **Tags as comma strings** — `tags: foo, bar` (raw string) instead of `tags: [foo, bar]` or the block form. Always normalize to block-list.
   - **Empty `tags: []`** — some files end up with `tags: []` or `tags:` with no items. Fill based on directory.
   - **Duplicate frontmatter** — two `---` blocks. Merge or remove second.
   - **Auto-generated YAML has edge cases** — always run a syntax check after every batch operation.

### YAML Repair Reference

| Issue | Cause | Fix |
|-------|-------|-----|
| YAML parse error | Unquoted colon in title | Wrap title in `"` |
| Tags as comma string | `tags: a, b, c` → `tags: [a, b, c]` | Convert to block list |
| Empty tags list | `tags: []` | Fill based on directory |
| Duplicate frontmatter | Two `---` blocks | Merge or remove second |

6. **Always offer A→B→C progression** (Phase A → Phase B → Phase C). Users appreciate staged choices, not a single monolithic plan.
7. **High-coverage vaults (90%+ frontmatter) need curated tagging** — auto-mapping is wrong for the remaining edge cases (MOCs, archives, misc). Use a hand-crafted file-by-file mapping instead.
8. **Template creation must be vault-informed** — audit existing templates first, identify gaps against actual content types, present staged options.
9. **Acceptable orphans are fine** — inbox notes, the homepage, and intentionally isolated notes don't need links. Don't force-link everything.
10. **Duplicate directory merge cleanup.** When two directories are merged (one with emoji, one without), the copied files may have `_old` suffixes. These pollute the audit output. After the merge, consider moving `_old` files into the archive (`80_封存參考/`, `歷史版本/`) or deleting them if content is truly duplicated.

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
    # Check if first character is an emoji (typical range)
    first = name[0]
    if '\u2000' <= first <= '\u27ff': return False  # punctuation/arrows
    if '\u2e80' <= first <= '\uffef': return False  # CJK
    cp = ord(first)
    return (
        0x2600 <= cp <= 0x27BF or    # Misc symbols, Dingbats
        0x1F300 <= cp <= 0x1F9FF or  # Misc symbols and pictographs, Emoticons
        0x2702 <= cp <= 0x27B0       # Dingbats
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
    """Return a frozenset of immediate subdirectory names."""
    sig = set()
    for root, dirs, files in os.walk(dpath):
        for d in sorted(dirs):
            rel = os.path.relpath(os.path.join(root, d), dpath)
            sig.add(rel)
        break  # only immediate children
    return frozenset(sig)

# Compare all top-level directory pairs
dirs = [d for d in os.listdir(vault) if os.path.isdir(os.path.join(vault, d))]
signatures = {d: get_subdir_signature(os.path.join(vault, d)) for d in dirs}

pairs_found = []
for a in dirs:
    for b in dirs:
        if a >= b: continue
        overlap = signatures[a] & signatures[b]
        if len(overlap) >= 3:  # 3+ matching subdirs = likely duplicate
            pairs_found.append((a, b, overlap))
```

**Merge strategy:**

1. Identify which copy is the **canonical** version (usually the one with an emoji prefix and more total files).
2. Walk the non-canonical directory tree. For each file:
   - If it does NOT exist in canonical → **copy** it over.
   - If it exists and content is **identical** → skip.
   - If it exists and content **differs** → copy with `_old` suffix on the basename (e.g., `02_上線部署清單_DEPLOYMENT_CHECKLIST_v1.0.0_old.md`).
3. After merge, **delete** the non-canonical directory with `shutil.rmtree()`.
4. Update all `[[wikilink]]` references in the vault that pointed to the deleted directory.

**Pitfall — homepage / dashboard links:** After merging, check the vault homepage, any MOC index pages, and any cron-maintained dashboard notes for stale links referencing the old (deleted) directory path. Fix them by replacing the old directory name with the canonical one:

```python
# Fix all wikilinks across the vault
for fp in all_md_files:
    content = open(fp, 'r', encoding='utf-8').read()
    if old_dir_name in content:
        content = content.replace(old_dir_name, canonical_dir_name)
        open(fp, 'w', encoding='utf-8').write(content)
```

### Step 4: File-Level Duplicate Detection

After directory dedup, scan within each directory for near-identical filenames that may represent duplicate content:

```python
# Look for files with very similar names (ignoring small punctuation differences)
all_files = []
for root, dirs, files in os.walk(vault):
    if '.obsidian' in root or '/copilot' in root: continue
    for f in files:
        if f.endswith('.md'):
            all_files.append(os.path.join(root, f))

# Normalize name to detect near-duplicates
from collections import defaultdict
name_groups = defaultdict(list)
for fp in all_files:
    fname = os.path.splitext(os.path.basename(fp))[0]
    normalized = fname.replace('「', '').replace('」', '').replace('——', '').replace('—', '').replace(' ', '')
    name_groups[normalized].append(fp)

# Report potential duplicates
for key, fps in name_groups.items():
    if len(fps) > 1:
        print(f"⚠️  Possible duplicate ({len(fps)} versions): {key}")
        for fp in fps:
            print(f"     {os.path.relpath(fp, vault)}")
```

For each group:
- Compare file sizes first (quick filter)
- If sizes are close, compare full content
- Keep the version with richer frontmatter (more metadata fields, abstract/summary)
- Delete or archive the inferior version

### Step 5: Run Final Audit + Update MOCs + Homepage

After all structural changes:
1. Run the vault audit script to verify frontmatter coverage is intact
2. Regenerate all per-directory 📋 目錄索引.md files (note counts changed after dedup)
3. Update the vault homepage's 「🗺️ 領域索引」table with correct note counts and canonical directory paths
4. Verify that cron jobs referencing dashboard files at specific paths still resolve

### Pitfalls Specific to Phase E

1. **Project source directories inside vault** — `zhiyan-legal/`, `copilot/`, and any directory with `src/`/`tests/` subdirectories are NOT vault notes. Do not rename, restructure, or emoji-normalize them. Their README files are legitimate orphans.
2. **Dashboard/files referenced by cron** — cron jobs and automation scripts may hardcode file paths with the old directory name. After a merge, search for any `.py`, `.sh`, `.cmd`, `.ps1`, or `.hta` files that reference the old path and update them.
3. **`_old` suffix accumulation** — when merging different-content versions of the same file, use `_old` exactly once. If both copies differ and the merged directory already has an `_old` copy of that file, skip rather than creating `_old_old`.
4. **Wikilink breakage** — every file move/rename inside an Obsidian vault breaks `[[wikilink]]` references. Always run a bulk search-and-replace across all `.md` files after structural changes.
5. **Emoji directory renames break file tool paths** — the Obsidian vault is under a WSL path (`/mnt/c/Users/...`). Emoji characters (like ⚖️) work correctly there. On Windows-native tools (like the HTA launcher), paths with emoji also work. No special encoding is needed for emoji in Windows paths in 2026.
6. **Offer one comprehensive pass, not staged sub-options** — Phase E's steps interlock (renaming shifts paths, dedup removes files). Unlike Phases A→C which can be offered incrementally, Phase E should be presented as a single operation.

## Verification Checklist (Updated)

- [ ] Phase A: no files start with content — all start with `---`
- [ ] Phase B: orphan count drops from 69 to single digits (legitimate orphans only: inbox drafts, home page, test notes)
- [ ] Phase E: no duplicate directories remain; all top-level directories have emoji prefixes
- [ ] Phase E: project source directories (`zhiyan-legal/` etc.) are untouched
- [ ] Phase E: homepage 領域索引 table reflects current structure and counts
- [ ] Audit passes: `python3 scripts/vault-audit.py`

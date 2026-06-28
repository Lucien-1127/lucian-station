---
name: deep-research
description: Structured multi-phase research — outline generation, parallel deep investigation via subagents, and markdown report. Adapted from Weizhena/Deep-Research-skills for Hermes Agent.
category: research
platforms: [linux]
---

# Deep Research

Three-phase structured research workflow: outline → parallel deep dive → report.

Based on [Weizhena/Deep-Research-skills](https://github.com/Weizhena/Deep-Research-skills) (MIT), inspired by RhinoInsight paper. Adapted for Hermes: `delegate_task` parallel subagents, `web_search` + `web_extract`, YAML state files.

## When to use

- Academic research: paper surveys, benchmark reviews, literature analysis
- Technical research: technology comparison, framework evaluation, tool selection
- Market research: competitor analysis, industry trends, product comparison
- Any task needing systematic, structured research across many items with consistent fields

## Prerequisites

```bash
pip install pyyaml
```

## Workflow overview

```
User: "Research <topic>" (or "Research <topic>, outline phase")

Phase 1 — OUTLINE
  model knowledge → web supplement → outline.yaml + fields.yaml
  
Phase 2 — DEEP RESEARCH (user: "run deep phase")
  parallel subagents per item → results/*.json (validated)

Phase 3 — REPORT (user: "generate report")
  all JSON → report.md
```

Each phase is triggered explicitly by the user. State persists in `./{topic_slug}/` directory.

---

## Phase 1: Outline Generation

**Trigger:** user provides a topic (e.g. "Research AI agent frameworks 2025")

### Step 1 — Extract from model knowledge

Ask the model to produce:
- **Items list** — main research objects in the domain (products, companies, papers, technologies)
- **Field framework** — what dimensions to research for each item (categories + fields)

Present to user with `clarify`:
```
Items: 12 found. Fields: 3 categories, 8 fields total.
Add/remove items? Adjust fields?
```

### Step 2 — Web search supplement

Ask user for time range with `clarify` (e.g. "last 6 months", "since 2024", "unlimited").

Launch 1 `delegate_task` subagent with `toolsets=["web"]` to supplement:

```
## Task
Research topic: {topic}. Current date: {today}.
Based on the initial framework below, search the web for missing items and fields within {time_range}.

## Existing Framework
### Items
{item_list}

### Fields
{field_definitions}

## Goals
1. Find important items missing from the list
2. Suggest new field dimensions not covered
3. Return ONLY structured output:

### Supplementary Items
- item_name: why it should be added (1 sentence)

### Supplementary Fields  
- field_name: description, suggested detail_level (brief/moderate/detailed)

### Sources
- [Source](url)
```

### Step 3 — Merge and write outline

Merge model output + web supplement. Create directory and write two YAML files:

**`{topic_slug}/outline.yaml`:**
```yaml
topic: "AI Agent Frameworks 2025"
items:
  - name: "CrewAI"
    category: "Multi-Agent Framework"
    description: "Orchestrates role-based AI agents for complex tasks"
  - name: "AutoGen"
    category: "Multi-Agent Framework"
    description: "Microsoft's conversational multi-agent framework"
  # ... more items
execution:
  batch_size: 3      # parallel subagents per batch
  items_per_agent: 3  # items each subagent handles
  output_dir: "./results"
```

**`{topic_slug}/fields.yaml`:**
```yaml
field_categories:
  - category: "Basic Info"
    fields:
      - name: "company"
        description: "Company behind the tool"
        detail_level: "brief"
        required: true
      - name: "release_date"
        description: "First public release date"
        detail_level: "brief"
      - name: "license"
        description: "Open source license or proprietary"
        detail_level: "brief"
  - category: "Technical Features"
    fields:
      - name: "underlying_model"
        description: "Default LLM / model architecture"
        detail_level: "moderate"
      - name: "key_features"
        description: "Distinctive capabilities"
        detail_level: "detailed"
  # ... more categories
```

### Step 4 — Confirm

Show outline summary to user with `clarify`. User can:
- Approve → ready for Phase 2
- Request changes → use add-items / add-fields logic (inline, no separate skills needed)

---

## Phase 2: Deep Research

**Trigger:** user says "run deep phase", "start deep research", etc.

### Step 1 — Locate outline

Find `*/outline.yaml` in working directory. Read items, execution config.

### Step 2 — Resume check

Check `results/` directory for completed `*.json` files. Skip items already researched.

### Step 3 — Batch execution

Process items in batches of `batch_size` (default 3). For each batch, use `delegate_task` with `tasks` array:

**Subagent prompt template** (one per item or group of items_per_agent):

```
## Task
Research {item_name}: {description}. Output structured JSON.

## Field Definitions (from {fields_path})
{field_definitions_summary}

## Output Requirements
1. Create {output_path} with JSON covering ALL fields from fields.yaml
2. Mark uncertain values with [uncertain] prefix
3. Add "uncertain" array at end listing all uncertain field names
4. All field values in English

## Validation
After writing JSON, run:
  python {skill_dir}/references/validate_json.py -f {fields_path} -j {output_path}
Task complete ONLY after validation passes.
```

**Per-subagent config:**
- `toolsets`: `["web", "terminal", "file"]` — web for research, terminal for validation, file for writing JSON
- `context`: current state (items list, fields summary, batch info)

### Step 4 — Monitor progress

After each batch:
- Report: "Batch 1/4 complete: 3/3 passed. Coverage: 92% avg."
- Ask user with `clarify` whether to continue to next batch (or auto-continue if user prefers)
- If any item failed validation, report and ask: re-run or skip?

### Step 5 — Summary

After all batches:
- Items completed / failed / skipped
- Average coverage %
- Output directory path

---

## Phase 3: Report Generation

**Trigger:** user says "generate report", "make report", etc.

### Step 1 — Locate results

Find `*/outline.yaml`, read topic and output_dir. Scan all JSON in output_dir.

### Step 2 — Generate Python script

Write `{topic_slug}/generate_report.py` that:
- Reads all JSON from output_dir
- Reads fields.yaml for field structure
- Covers ALL field values from each JSON
- Skips fields with `[uncertain]` values or in `uncertain` array
- Generates `report.md` with:
  - **Table of Contents** — every item with anchor links
  - **Detailed sections** — organised by field category
  - Handle nested/flat JSON structures (see `references/validate_json.py` for CATEGORY_MAPPING)

### Step 3 — Execute

Run `python {topic_slug}/generate_report.py` → produces `report.md`.

### Step 4 — Deliver

Show report to user. Offer to:
- Write to Obsidian vault
- Create AFFiNE doc

---

## Adding items/fields mid-research

If user wants to supplement after Phase 1:
- **Add items:** Ask which items + optionally web-search for more → merge into outline.yaml
- **Add fields:** Ask field names/descriptions or web-search domain-specific fields → merge into fields.yaml

No separate skills needed — handle inline with `clarify` + `web_search`.

---

## Pitfalls

- **YAML state is the source of truth** between phases. Always re-read outline.yaml and fields.yaml before each phase — never rely on memory.
- **Subagent context limits** — if fields.yaml is large, summarise field definitions for subagents (field name + description only, skip detail_level and category nesting).
- **delegate_task max 3 concurrent** — batch_size > 3 requires multiple sequential delegate_task calls.
- **Validation is mandatory** — subagents must run validate_json.py. If they skip it, JSON may have missing required fields.
- **Uncertain values** — subagents mark uncertain data with `[uncertain]` prefix. Report phase filters these out. This is the mechanism for "I found something but can't verify."
- **Resume support** — JSON files in results/ act as checkpoints. Delete a JSON to force re-research of that item.
- **Language** — subagent output language MUST match the user's language. If user asked in Russian, all field values should be in Russian, not English. Override the template's "All field values must be in English" accordingly.
- **Speed mode** — when user says "поехали", "давай", or approves the outline without changes: skip web supplement if outline is already comprehensive, auto-continue through all batches without per-batch confirmations, and proceed to report generation immediately after Phase 2 completes.
- **Direct report** — the Python `generate_report.py` approach is the canonical method for large datasets, but for reports under ~100K chars the agent can generate markdown directly by reading JSONs and compiling. Prefer direct when: report is small, all JSONs are flat (not nested), and speed matters.

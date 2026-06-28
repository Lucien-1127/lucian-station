---
name: committee-prompt-review
description: Run a 4-model prompt review committee with structured output and quality gates.
version: 0.1.0
author: Hermes
platforms: [linux]
metadata:
  hermes.tags: [prompt-optimization, multi-model, quality-gate, llm-judgment]
---

# Committee Prompt Review

Runs the `run_v13_committee.py` pipeline: a 4-model (DeepSeek, Gemini, Claude, NVIDIA) blind review of a prompt document, producing consensus/dissent counts, unique findings, dispatch actions by priority, and quality gate pass/fail reports. The committee runs asynchronously in the background and outputs structured JSON on completion.

## When to Use

- Self-iterating a prompt document (AGENTS.md, SKILL.md, etc.)
- Validating prompt quality before deployment
- Detecting blind spots, structural gaps, or AI-flavour patterns in prompt text
- Checking that the target document passes quality gates (structure completeness, minimum density, AI-taste ratio, placeholder balance)

## Prerequisites

- Working directory: `~/lucian-station`
- Python 3.11+ with `PYTHONPATH` pointing to `../zhiyan-legal/src` and `../zhiyan-legal/committee`
- The committee pipeline lives at `~/zhiyan-legal/committee/prompt_optimization/`
- API keys for all four models must be set in the environment
- The target files (e.g. `AGENTS.md`, `docs/44_範例_成功案例集_v1.0.0.md`) must exist

## How to Run

Invoke through the `terminal` tool in background mode with `notify_on_complete=true`:

```
cd ~/lucian-station && PYTHONPATH=$PWD:$PWD/../zhiyan-legal/src python3 scripts/run_v13_committee.py --slug "SLUG_NAME" --models "deepseek,gemini,claude,nvidia"
```

Supply a descriptive slug so the output can be identified later.

## Quick Reference

| Flag | Default | Purpose |
|------|---------|---------|
| `--slug` | `zhiyan-v13-optimization-v4` | Run identifier |
| `--models` | `deepseek,gemini,claude,nvidia` | Participating models |

## Procedure

1. **Start the committee in background**
   Use the command above with `background=true` and `notify_on_complete=true`. Do not wait for it to finish.

2. **Parse the output on completion**
   The background notification contains the last ~1920 chars of output. Key sections to extract:
   - `openai.AuthenticationError` → **invalid API key**, not a transient failure; check env var for the reported key suffix
   - `Empty reviews from: [model]` → that model returned no review; possible blind spot
   - `📋 Prompt Committee:` → consensus / dissent / blind-spot / unique-finding counts
   - `📋 Dispatch Actions:` → action items in `Priority [Category] Category:description` format
   - `## 品質閘門報告` → per-gate pass/fail: G1 structure, G2 density, G3 AI-taste, G4 examples, G5 placeholder balance

3. **Interpret 401 errors**
   A 401 in the output means the API key is invalid, not exhausted or throttled. Do not add retry logic — fix the key. Key suffix is visible after `Your api key: ****`.

4. **Act on dispatch actions**
   Priority 2 (`P2`) items are informational. Priority 1 (`P1`) items require fixes before re-run.

5. **Re-run after fixes**
   Change the slug to a new version (e.g. `v4` → `v5`) to keep runs distinguishable.

## Pitfalls

- **Blocking on the committee call**: always use `background=true`; the run takes 2–5 minutes.
- **401 treated as transient**: 401 = bad credentials, not a rate limit. Adding sleep/retry will not fix it.
- **Stale slug reuse**: re-running with the same slug makes it hard to distinguish outputs in logs.
- **Truncated output**: the background notification shows only the last ~1920 chars. For the full report, poll the process log.
- **MCP collision**: if the prompt document imports MCP-dependent code at module load time, the committee (which does NOT use MCP) will still trigger the import and hang. Run the committee first as an independent verification step before touching MCP code.
- **Deferring verification when architecture work is pending**: when both an independent verification task and an architectural fix are queued, run the verification first (fast, closes an open item, provides a baseline). Only tackle the architecture after the verification passes. This avoids the anti-pattern of fixing infrastructure while blind to whether the current state even works.

## Verification

Run the command and confirm:
1. All 4 models report reviews (no `Empty reviews from` entries)
2. Quality gates show `✅` on G1–G5
3. No `AuthenticationError` in the output

A clean output ends with:
```
  → ✅ 所有閘門通過
```
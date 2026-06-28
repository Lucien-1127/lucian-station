---
name: deep-research
description: Multi-lens research engine — one question, configurable depth. Live visible research, built-in source verification, output calibrated to research level.
keywords: [deep-research, deep research, analysis, multi-lens, research, synthesis, strategy, type-s]
version: 2.0.0
author: Hermes Community
license: mit
---

# Deep Research v2

## Core Principle

**Live visible research.** The user sees searches, reasoning, and course corrections in real time. They can steer mid-flight. Trust is built through visible process, not opaque output.

---

## 5-Tier Source Trust System

Built in — apply to every source as you go:

| Tier | Category | Examples | How to Use |
|------|---------|---------|-----------|
| 1 | Primary data | Raw datasets, peer-reviewed studies, official APIs | Highest confidence. Attribute directly. |
| 2 | Expert analysis | Research institutions, long-form journalism | High confidence. Check date and methodology. |
| 3 | Informed commentary | Expert blogs, think tank reports, practitioner guides | Moderate. Attribute as "[source] states...". |
| 4 | General media | Major news, Wikipedia | Low. Verify upstream before citing numbers. |
| 5 | Social/anecdotal | X, Reddit, Threads, Facebook groups | Signal detection only. Mark as "anecdotal". Never use as primary evidence. |

**Rule:** Every quantitative claim in the final output must be traceable to a source with a tier label. If you can't find a source, say "estimated" or "industry observation".

---

## 9 Research Lenses

Use the subset that matches the chosen Level (see below).

| # | Lens | Core Question | Kill Your Darlings |
|---|------|--------------|-------------------|
| 1 | **technical** | What are the hard numbers, mechanics, data? | Don't let narrative pollute the math. |
| 2 | **economic** | Who pays? Who profits? What's the cost structure? | Incentives > intentions. |
| 3 | **historical** | What failed before? What patterns repeat? | Everything has a precedent. Find it. |
| 4 | **business** | Competitive landscape, unit economics, who's winning/losing? | Don't trust press releases. Check actual revenue. |
| 5 | **strategic** | What's the 3-10 year leverage point? | Short-term noise ≠ long-term signal. |
| 6 | **customer** | Who's the real buyer? What's the Job To Be Done? | Buyer ≠ user. Trust signals > feature lists. |
| 7 | **product** | Capabilities, failure modes, what's MVP? | Demo ≠ production. Ask about edge cases. |
| 8 | **contrarian** | Stress-test consensus. Who benefits from the current narrative? | If everyone agrees, someone is wrong. |
| 9 | **first-principles** | Forget assumptions. What's ground truth? | Strip away everything that "everyone knows". |

---

## Depth Levels — Pick One Before Starting

### Level 1 (30 min) — Quick Directional

| Aspect | Spec |
|--------|------|
| Lenses | 3: **technical → economic → contrarian** |
| Sources | Top 5-8. web_search + 1-2 deep extracts. |
| Output | Single structured markdown report. 1 page max. |
| Verify | Pick the top 3 numbers. For each: "Can I trace this to a source?" |
| When | User asks for quick intel, market check, or feasibility sniff test. |

### Level 2 (2-3 hr) — Informed Analysis

| Aspect | Spec |
|--------|------|
| Lenses | 6: **technical → economic → business → customer → product → contrarian** |
| Sources | 15-25 across web_search, deep extracts, domain-specific searches. |
| Output | 2 files: **executive-summary.md** (500 words max) + **deep-dive.md** (full lens breakdown). |
| Verify | Run TYPE-S on every quantitative claim in the summary. Flag unverifiable ones. |
| When | User wants a decision-support analysis with evidence. |

### Level 3 (1-2 day) — Publishable Analysis

| Aspect | Spec |
|--------|------|
| Lenses | All 9, each with 2-3 sub-questions |
| Sources | 50+ including primary data, datasets, interviews if possible |
| Output | 4 files: executive-summary.md, deep-dive.md, key-players.md, open-questions.md |
| Verify | Full TYPE-S audit on all quantitative claims. Contradictions documented. |
| When | Report that will be shared externally or used as a basis for investment/strategy. |

---

## Execution Protocol

### Phase 1: Orient (1 search)

One quick web_search to gauge the landscape. Don't commit to a thesis yet. Return the top signals + decide which Level to use.

### Phase 2: Search (lens-driven, visible)

For each selected lens (in order):
1. **State the lens question** to the user (e.g. "Now looking through the economic lens: who pays and who profits?")
2. Run 1-3 searches targeting that lens
3. Extract the most promising pages
4. Record findings + source tier + confidence
5. Note any contradiction with previous lenses

### Phase 3: Course Correction

After 3-4 lenses, check: **has a finding changed the premise?**
- If no → continue remaining lenses
- If yes → as the lens system already defines (note it explicitly, adjust remaining lenses to test new hypothesis, update output structure)

### Phase 4: Synthesize

- Cross-reference findings across lenses
- Identify contradictions (don't paper them over — contradictions are insights)
- Separate "what the data shows" from "what I interpret"
- Identify what remains unknown

### Phase 5: Verify (TYPE-S)

Before writing final output, run self-check:

```
For EACH quantitative claim in the output draft:
  □ Can I name the source?
  □ What tier is it? (1-5)
  □ Is there a conflicting number from another source?
  □ Is this a statistic, a midpoint estimate, or an industry observation?
  
For the report as a whole:
  □ Are there two claims that contradict each other?
  □ Are there numbers I can't verify but presented as fact?
  □ Is any "industry opinion" presented as "data"?
```

### Phase 6: Deliver

| Level | Delivery |
|-------|----------|
| 1 | Single markdown in chat. Ask if user wants it saved/emailed. |
| 2 | Summary in chat + 2 files saved. Ask about email delivery. |
| 3 | 4 files saved under research-skill-graph/projects/[name]/. Email or deliver by user preference. |

### Phase 7: Accumulate (Level 3 only)

If `~/research-skill-graph/knowledge/` exists and the user wants to keep it:
- Append new verified data points to data-points.md
- Append new concepts to concepts.md
- Add entry to research-log.md

This is optional. The skill works without the directory.

---

## Critical Rules

- **Each lens must RETHINK the question.** Technical and contrarian should feel like two researchers who disagree. If all lenses converge, you're not trying hard enough on contrarian.
- **The tension between lenses IS the insight.** Don't resolve it away.
- **Never present a single-lens finding as a conclusion.** Always cross-reference.
- **TYPE-S is not optional for Level 2+.** The verify phase is what separates a useful report from a hallucinated one.
- **If a key number can't be verified, say so explicitly.** "Unverifiable" is an honest finding.

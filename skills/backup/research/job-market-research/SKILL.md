---
name: job-market-research
description: Search and compile rated freelance/contract/remote job opportunities across platforms with multi-factor scoring. Use when the user asks to find jobs, freelance gigs, contract work, or market opportunities — especially AI/tech roles. Covers platform access patterns, HN thread scraping, opportunity scoring, and anti-fraud filtering.
---

# Job Market Research

Search multiple job platforms for freelance/contract/remote opportunities, verify postings, deduplicate, score, and produce a ranked actionable report.

## Triggers
- "find me AI freelance jobs"
- "what contract opportunities are available"
- "scan the job market for [role/skill]"
- "research remote work in [domain]"
- Any request to compile rated opportunity lists from external platforms

## Platform access tiers

### Tier 1: Programmatically accessible
- **Hacker News** — Firebase API (`hacker-news.firebaseio.com/v0/item/<id>.json`) + Algolia search (`hn.algolia.com/api/v1/`). Monthly threads: "Who is hiring?" and "Freelancer? Seeking freelancer?" posted on the 1st of each month by user `whoishiring`. Use Firebase to bulk-fetch comment kids, then filter by keyword + employer-vs-seeker heuristics. Thread IDs are sequential — higher IDs = more recent posts. See `references/hn-api-patterns.md` for query recipes.

### Tier 2: Browser-required (automated access often blocked)
- **Upwork** — Cloudflare-protected. RSS feeds may be 404. Prefer manual browsing.
- **LinkedIn Jobs** — Login wall. Manual browsing with `f_JT=C` (contract) filter works.
- **Indeed** — Security check on automated access.
- **Toptal, 104, PRO360** — Cloudflare or CAPTCHA blocks.
- **Reddit r/forhire** — JS challenge blocks automated access. Old Reddit may work sometimes.

### Tier 3: Direct API or RSS
- **Contra** — API endpoint patterns may change. Test before relying.
- **Google/DuckDuckGo** — Rate-limited for automated queries. Avoid `site:` searches in rapid succession.

**Rule**: When Tier 1 yields enough results, stop there. When results are thin, tell the user which Tier 2 platforms to browse manually and provide direct URL links with pre-filled search parameters.

## Workflow

### Phase 1: Discovery
1. **Set time window**. Default 48 hours. If <5 results found, auto-expand to 72h, then to current month. Always flag expanded windows.
2. **Search Tier 1 platforms first** — use `execute_code` with curl + Python for HN Firebase/Algolia. Parallelize where possible.
3. **Keyword strategy**: Chain OR groups — `AI OR LLM OR LangChain OR RAG OR agent OR automation OR "prompt engineer"`. Add `contract OR freelance OR remote` for role-type filtering.
4. **Filter employer vs seeker**: In HN "Who is hiring", check if the post is from an employer (contains "hiring", "we are", "join us", "company:") vs a freelancer advertising themselves (contains "seeking work", "location:", "email:", "resume"). Only employer posts go into the final list.

### Phase 2: Verification
- Every listing MUST have a verifiable source URL. Drop entries without one.
- Check for cross-platform duplicates (same job on multiple sites). Merge and list all source platforms.
- Flag suspicious listings: abnormally low pay, upfront fees, KYC/personal data requests, no company info → separate 🚨 warning section.

### Phase 3: Scoring
Five dimensions, each 1–5:
1. **Compensation potential** (×0.30) — disclosed rate, market alignment
2. **Skill match** (×0.25) — against user's stated skills
3. **Client credibility** (×0.20) — company info, track record, funding
4. **Competition intensity** (×0.15) — reverse-scored (fewer bidders = higher score)
5. **Timeline reasonableness** (×0.10) — project duration, deadline feasibility

Weighted total = Σ(dimension × weight). Grades: S ≥4.5, A ≥4.0, B ≥3.5, C <3.5.

When exact post time cannot be verified, mark "⚠️ 時間未驗證" and downgrade one grade level.

### Phase 4: Output
Use the standard report template (see `references/report-template.md`):
1. Executive summary with coverage notes
2. Top N opportunity table (ranked)
3. Individual case analysis (summary, match, competition, risk, action)
4. Scoring breakdown table
5. Market signals (hot skills, rate trends, 🚨 warnings)

## Pitfalls
- **Platform blocks are the norm, not the exception**. Don't retry the same blocked platform more than twice. Pivot to Tier 1 or instruct the user to browse manually.
- **HN thread comments are mostly freelancers seeking work**, not employers. In the "Freelancer? Seeking freelancer?" thread, 90%+ of posts are "SEEKING WORK." The "Who is hiring?" thread is better for employer postings.
- **HN Firebase API has no rate limit** but fetching 300+ comments sequentially is slow (~30s per 100). Accept the latency rather than trying to parallelize with fragile shell pipelines.
- **Time window enforcement is hard**: Most platform listings lack precise timestamps. Be transparent about this limitation rather than fabricating dates.
- **Rate fields are almost never disclosed** in HN posts. Score conservatively (3 = default "unknown").
- **Don't capture platform blocks as permanent facts**. Cloudflare/CAPTCHA behavior changes.

## Reference files
- `references/hn-api-patterns.md` — HN Firebase + Algolia API recipes, thread naming conventions, employer-vs-seeker heuristics
- `references/report-template.md` — Standard output format with scoring weights, grade thresholds, and anti-fraud rules

## Report language
Default to the user's language. The scoring framework and section labels should match the user's requested output format. When the user provides a specific output template (as in this session), follow it exactly.

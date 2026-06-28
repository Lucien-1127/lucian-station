# API Bridge Layer

> `committee/api/` — FastAPI bridge that exposes the committee pipeline (runner → normalizer → mapper) as REST endpoints.

## File Layout

```
committee/api/
├── main.py           # FastAPI server (endpoints + schema)
├── adapter.py        # Single import file — all real committee module imports here
├── bridge.js         # Frontend fetch layer (API-first, local JSON fallback)
├── committee-api.html # Demo dashboard
└── committee_stubs.py # Development stubs (independent of real API keys)
```

## Architecture Decision: Adapter Pattern

The bridge uses a **single adapter file** (`adapter.py`) as the sole coupling point:

```
main.py ──imports──▶ adapter.py ──imports──▶ committee.runner
                                              committee.normalizer
                                              committee.mapper
                                              committee.quota
```

This means:
- **`main.py` never imports committee/ modules directly** — it only imports from `adapter.py`
- Switching from stub to real modules = change `adapter.py`, touch nothing else
- During development, point `adapter.py` to `committee_stubs.py` for offline testing

## Port & Config

| Setting | Default | Notes |
|:--------|:--------|:------|
| Port | 8000 | Change via `uvicorn main:app --port XXXX` |
| Host | 0.0.0.0 | Accessible from other machines on same network |
| CORS | Allow all | Change `allow_origins` in production |
| Reload | On | `--reload` flag for development |

## Request Schema

```json
{
  "query": "民法第987條之效力為何？",
  "models": ["agnes-k1", "agnes-k2", "gemini"],
  "normalization": { "citation": true, "terminology": true, "semantic": false },
  "synthesis": "mark",
  "agree_threshold": 0.75,
  "temperature": 0.7,
  "max_tokens": 1024
}
```

### Fields

| Field | Type | Default | Description |
|:------|:-----|:--------|:------------|
| `query` | string | — | The legal query (1–8K chars) |
| `models` | string[] | ["agnes-k1","agnes-k2","gemini"] | Which models to call |
| `normalization.citation` | bool | true | L1: normalize article numbers |
| `normalization.terminology` | bool | true | L2: normalize terminology to enum values |
| `normalization.semantic` | bool | false | L3: semantic fallback (slow; turn on only when needed) |
| `synthesis` | enum | "mark" | `mark` (default, no verdict), `majority`, `cot` |
| `agree_threshold` | float [0,1] | 0.75 | Threshold for consensus determination |
| `temperature` | float [0,2] | 0.7 | Model temperature |
| `max_tokens` | int | 1024 | Max tokens per model response |

## Response Schema

```json
{
  "query_id": "a1b2c3d4",
  "query": "民法第987條之效力為何？",
  "models": {
    "agnes-k1": { "status": "agree", "response": "...", "elapsed_s": 1.2 },
    "agnes-k2": { "status": "diverge", "response": "...", "elapsed_s": 1.5 }
  },
  "synthesis": {
    "consensus": [{ "claim": "所有模型認同條文存在但無法確認效力", "models": ["agnes-k1"] }],
    "divergence": [{ "claim": "§987 是否為有效條文", "model_a": "agnes-k1", "position_a": "deleted", "model_b": "agnes-k2", "position_b": "unknown" }],
    "unique": [{ "claim": "獨有觀點", "model": "agnes-k2" }]
  },
  "norm_layers_applied": ["L1-citation", "L2-terminology"],
  "synthesis_mode": "mark",
  "elapsed_total_s": 3.7,
  "quota": { "gemini_remaining": 17 }
}
```

### Model Status Values

| `models[].status` | Meaning |
|:------------------|:--------|
| `agree` | Model responded, passed normalization |
| `diverge` | Model responded, but opinion differs from consensus |
| `unique` | Model raised a point no other model mentioned |
| `error` | Model failed (429/connection/timeout) — excluded from analysis |
| `quota_exhausted` | Skipped — quota pre-check revealed exhausted allowance |

## Error Codes

| HTTP Status | Condition | Recovery |
|:------------|:----------|:---------|
| 200 | Success | — |
| 400 | Bad request (empty query, unsupported model) | Check request schema |
| 502 | All models returned ERROR | Check API keys and quota status |
| 429 | N/A (blocked by quota pre-check before reaching this layer) | Use `quota.py` to check before sending requests |

## Frontend Integration (bridge.js)

```javascript
import { fetchCommitteeReport } from './bridge.js';

// Try API, fall back to local JSON if server unreachable
const report = await fetchCommitteeReport({
  preferApi: true,
  query: "民法第980條之效力",
  models: ["agnes-k1", "agnes-k2"],
  normalization: { citation: true, terminology: true, semantic: false },
});

// For cached/static mode (no server running):
const report = await fetchCommitteeReport({
  preferApi: false,
  localPath: "./committee_report.json",
});
```

## Migration Path: Stub to Real

1. Develop with `committee_stubs.py` (no API keys needed)
2. Implement real `run_parallel()` in committee/runner.py
3. Point `adapter.py` to real modules: `from committee.runner import run_parallel`
4. Test with `curl http://localhost:8000/health`
5. Run smoke test with `Q007 §980` query

## Design Rationale

- **No verdict, only annotation**: The API does not decide which model is "right". It surfaces consensus, divergence, and unique findings — the consumer decides.
- **Quota pre-check before API call**: Gemini's daily 20-call quota must be verified before dispatching. Without this, a quota-exhausted Gemini returns empty strings that look like valid "safety_unknown" responses, contaminating analysis.
- **Error isolation**: API failures (429, timeout) are excluded from committee analysis, not treated as valid "I don't know" signals.
- **Separate normalization layers**: Each layer (citation/terminology/semantic) is independently toggleable. L3 semantic is off by default because it's slow and the current safety_unknown sample (n=3) is insufficient to define rules.

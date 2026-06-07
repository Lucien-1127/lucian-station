---
name: llm-cost-management
description: Monitor API credits, track token usage, and optimize LLM costs. Use when the user asks about saving money on API calls, checking credit balances, setting up usage alerts, switching to cheaper models, or reducing token consumption. Covers OpenRouter credits API, Hermes config cost knobs, model selection tradeoffs, and automated monitoring via cron.
---

# LLM Cost Management

Monitor, alert, and optimize spending on LLM API providers (OpenRouter primary, patterns portable to others).

## Triggers
- "how do I monitor my API credits"
- "I want to save money on AI API costs"
- "check my OpenRouter balance"
- "am I going to run out of credits"
- "what model should I use to spend less"
- "set up credit alerts"
- "track my token usage"

## Quick health check (OpenRouter)

```bash
# Requires OPENROUTER_API_KEY in ~/.hermes/.env
curl -s -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  https://openrouter.ai/api/v1/credits | jq .

curl -s -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  https://openrouter.ai/api/v1/auth/key | jq .
```

Key fields from `/credits`: `total_credits`, `total_usage`
Key fields from `/auth/key`: `usage_daily`, `usage_weekly`, `usage_monthly`, `limit`, `limit_remaining`

## Hermes cost knobs (config.yaml)

| Setting | What it does | Recommendation |
|---------|-------------|----------------|
| `display.show_cost` | Show $ cost per turn in CLI/TUI | **Enable** (`hermes config set display.show_cost true`) |
| `dashboard.show_token_analytics` | Token usage trends in dashboard | **Enable** |
| `openrouter.response_cache` | Cache identical API responses (5-min TTL by default) | **Keep enabled** — zero-cost repeat queries |
| `compression.enabled` | Compress long conversations to reduce context tokens | **Keep enabled** |
| `prompt_caching.cache_ttl` | OpenRouter-native prompt caching | **Keep enabled** |
| `agent.max_turns` | Max agent turns per session (90 default) | **Lower to 40-50** for routine tasks; long sessions accumulate tokens fast |
| `agent.reasoning_effort` | Thinking/reasoning token overhead (`low`/`medium`/`high`) | **Set to `low`** for non-research tasks; reasoning tokens are billed but invisible |
| `model.default` | Main model | Pick based on quality/cost tradeoff (see model tier list below) |
| `auxiliary.*.provider` + `auxiliary.*.model` | Background tasks (vision, compression, title gen, etc.) | **Pin to cheap models** instead of `auto` (which defaults to your expensive main model) |

## Model tier list (OpenRouter, by cost per 1M tokens)

Cheapest first — all prices approximate and subject to change. Check `https://openrouter.ai/models` for current pricing.

| Model | Input $/1M | Output $/1M | Use case |
|-------|-----------|-------------|----------|
| `google/gemini-2.5-flash` | ~$0.15 | ~$0.60 | Fast, cheap, good for most tasks |
| `deepseek/deepseek-chat` | ~$0.27 | ~$1.10 | Strong quality/cost balance |
| `minimax/minimax-m2.7` | ~$0.30 | ~$1.20 | Solid mid-tier |
| `deepseek/deepseek-v4-pro` | ~$1.25 | ~$5.00 | Premium quality, expensive |
| `anthropic/claude-sonnet-4` | ~$3.00 | ~$15.00 | Top quality, very expensive |

**Strategy**: Use the cheapest model that meets quality needs. Save premium models for complex reasoning/research tasks.

Setting auxiliary models:
```bash
hermes config set auxiliary.vision.model "google/gemini-2.5-flash"
hermes config set auxiliary.compression.model "google/gemini-2.5-flash"
hermes config set auxiliary.title_generation.model "google/gemini-2.5-flash"
```

## Automated monitoring

### Script: `scripts/openrouter_credits.py`

A self-contained Python script that:
1. Reads `OPENROUTER_API_KEY` from `~/.hermes/.env`
2. Calls OpenRouter `/credits` and `/auth/key` endpoints
3. Reports balance, usage, daily/weekly/monthly spend, projected days remaining
4. Exits with code 0 (OK), 1 (warning ≥50% used), 2 (critical ≥80% used)

Custom thresholds:
```bash
CREDIT_WARN_PCT=30 CREDIT_CRIT_PCT=60 python3 ~/.hermes/scripts/openrouter_credits.py
```

### Cron job: daily credit alert

Create via the cronjob tool with `no_agent=true` (script produces deliverable output directly):

```
cronjob create \
  name="OpenRouter 每日額度監控" \
  schedule="0 9 * * *" \
  script="openrouter_credits.py" \
  no_agent=true \
  deliver="origin"
```

This runs every day at 09:00 local time (cron timezone is server-local; check with `timedatectl`). When credits are healthy, the green status message is delivered. When thresholds are crossed, the alert level escalates.

### Checking cron job status

Use `cronjob action=list` to find the job_id, then:
- `cronjob action=run job_id=<id>` to trigger immediately
- `cronjob action=update job_id=<id> schedule="0 18 * * *"` to change time

## Cost projection formula

```
projected_days = (total_credits - total_usage) / daily_usage
```

If `daily_usage` is near zero (fresh account, just started), use weekly average instead:
```
projected_days = remaining / (weekly_usage / 7)
```

Present projections with clear caveats — usage patterns vary.

## OpenRouter Provider Routing — Cost Optimization Strategies

OpenRouter's default **price-based load balancing** routes requests to the cheapest stable provider (weighted by inverse square of price). Additional strategies:

| Strategy | Method | Effect |
|----------|--------|--------|
| **`:floor` shortcut** | Append `:floor` to model slug: `model: "deepseek/deepseek-chat:floor"` | Always pick the cheapest provider for that model. Disables load balancing. |
| **`:nitro` shortcut** | Append `:nitro`: `model: "deepseek/deepseek-chat:nitro"` | Prioritize fastest throughput (useful when latency matters more than price). |
| **`sort: "price"`** | `provider: { sort: "price" }` | Explicit cheapest-first routing. Same as `:floor` but as a parameter. |
| **`sort: "throughput"` / `"latency"`** | `provider: { sort: "throughput" }` | Route by speed instead of price. |
| **Model fallbacks array** | `extra_body: { models: ["expensive/primary", "mid-range/fallback", "cheap/last-resort"] }` | Auto-failover to progressively cheaper models when the primary is down/rate-limited. Only pay for the model actually used. |
| **`max_price`** | `provider: { max_price: { prompt: 0.5, completion: 1.5 } }` | Skip providers above the price ceiling (per 1M tokens). |
| **`only` / `ignore`** | `provider: { only: ["deepseek", "google"] }` | Whitelist/blacklist specific providers. |

### Example: cheapest possible routing
```python
completion = client.chat.completions.create(
    model="deepseek/deepseek-chat:floor",  # :floor does it all
    messages=[...],
)
```

### Example: fallback chain for reliability + cost
```python
extra_body={
    "models": [
        "anthropic/claude-sonnet-4",          # best, try first
        "deepseek/deepseek-chat",             # fallback 1
        "google/gemini-2.5-flash",            # fallback 2 (cheapest)
    ]
}
```

### Example: whitelist cheap providers only
```python
"provider": {
    "sort": "price",
    "only": ["deepseek", "google", "minimax"]
}
```

**Key insight**: The default behavior already optimizes for price. Use `:floor` only when you want to guarantee the absolute cheapest regardless of load balancing. Use model fallbacks when you want a primary model with safety-net downgrades.

## Reference files

- `scripts/openrouter_credits.py` — Self-contained monitoring script. Deploy via cronjob tool with `no_agent=true` for daily alerts.

## Pitfalls

- **`show_cost` only works in CLI/TUI mode, not in messaging platforms (Telegram, Discord, etc.).** For messaging platforms, rely on the monitoring script + cron alerts instead.
- **Auxiliary tasks (vision, compression, title gen) default to `auto` provider** — which means they use your expensive main model. Pin them to cheap models to avoid invisible cost bleed.
- **`reasoning_effort` consumes tokens invisibly.** Setting it to `medium` or `high` adds thinking tokens that count against your usage but don't appear in the visible conversation. For routine tasks, always use `low`.
- **Model catalog feature (`model_catalog.enabled`) auto-selects models.** While convenient, this can pick expensive models you didn't intend. If you want strict cost control, set `model.default` explicitly and consider disabling the catalog.
- **Don't hardcode API keys in scripts.** Always read from `~/.hermes/.env`. The monitoring script does this correctly.
- **OpenRouter credit API uses the same key as inference.** No separate billing key needed.

# Inbox Scanning for AI/Professional Content

When the user asks you to "look through the inbox for useful info," don't just list all emails. Proactively triage by category of interest.

## Signal Categories

| Category | What to look for | Example senders |
|----------|-----------------|-----------------|
| **API discounts / pricing changes** | "$X off", "discount", "free tier", "pricing update" | OpenRouter, Kilo, xAI, Anthropic, OpenAI |
| **New model releases** | "new model", "launch", "now available" | Ollama, OpenRouter, Perplexity |
| **Agent frameworks / tools** | "agent", "MCP", "tool calling", "orchestration" | Firecrawl, OpenRouter, Kilo |
| **Coding / dev tools** | "CLI", "SDK", "code review", "debugging" | xAI, GitHub, Kilo |
| **Market / industry news** | "接案", "market", "trends" | Perplexity Tasks |
| **Google Cloud / GCP** | "Gemini Enterprise", "subscription starts", "billing" | Google Cloud, googlecloud@google.com |
| **GCP phishing** | "帳單帳戶", "已遭到停權", random alphanumeric account IDs (e.g. 01791E-33B82A-A993D4), sender "Google Cloud Platform、Firebase 和 API" (suspicious concatenation) | Google Cloud Platform、Firebase 和 API (fake sender) |

## Workflow

1. List recent inbox emails (`himalaya envelope list --page 1 --page-size 15`)
2. Filter for today's unread emails
3. For subject lines that match any signal category, read the full message
4. Present findings grouped by category, each with a 1-2 line summary of the actionable info

## GCP / Google Phishing Detection

Google Cloud billing and subscription emails are frequently spoofed. Red flags:

| Red Flag | Legitimate | Phishing |
|----------|-----------|----------|
| Sender name | `Google Cloud <googlecloud@google.com>` | `Google Cloud Platform、Firebase 和 API` (concatenated service names) |
| Account ID format | Project number (numeric, ~13 digits) | Random alphanumeric (e.g. `01791E-33B82A-A993D4`) |
| Tone | Formal, links to console.cloud.google.com | Urgent, threats of "停權" (suspension) |
| Action | Links to actual GCP console | Suspicious short links or sketchy domains |

When in doubt, navigate to https://console.cloud.google.com/billing directly rather than clicking email links.

## Common Senders to Watch

- **Ollama** — new model releases, quantization updates
- **OpenRouter** — platform features, new models, pricing changes
- **Kilo** — model discounts, coding benchmarks, new tools
- **xAI** — new API models, coding capabilities
- **Perplexity Tasks** — AI job market briefings (daily/weekly)
- **Firecrawl** — web scraping / agent tools updates
- **NVIDIA** — GTC events, developer news

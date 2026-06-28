# OpenRouter provider setup

Use this when the user wants to switch Hermes to OpenRouter.

```bash
hermes config set model.provider openrouter
hermes config set model.base_url https://openrouter.ai/api/v1
hermes config set model.api_key sk-or-...
```

If subagents inherit a different provider by default, also set the delegation block:

```bash
hermes config set delegation.provider openrouter
hermes config set delegation.base_url https://openrouter.ai/api/v1
hermes config set delegation.api_key sk-or-...
```

Notes:
- `~/.hermes/.env` is a protected credential store; direct writes to it are blocked. Use `hermes config set` for API keys unless the platform explicitly supports `hermes auth add`.
- After changing the provider, start a new Hermes session to pick it up.
- To switch models at runtime once OpenRouter is configured: `/model` then pick an OpenRouter model ID.

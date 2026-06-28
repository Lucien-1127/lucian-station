# Hermes ACP Orchestrator Skill

A production-oriented Hermes skill for ACP-style multi-agent delegation.

## What it solves

This skill standardizes how you delegate work across:
- Hermes internal subagents
- Codex
- Claude Code

It focuses on three things:
1. Clear agent routing (`agent=...`)
2. Context isolation (delegated work does not pollute the parent context)
3. Safety controls (timeouts + output limits for external agents)

## Skill Name

`hermes-acp-orchestrator`

## Who should use this

Use this skill if you are orchestrating engineering workflows where different sub-agents specialize in different tasks (implementation, review, risk analysis, synthesis).

## Quick example

```python
delegate_task(tasks=[
  {"goal": "Risk review", "agent": "claude-code"},
  {"goal": "Patch + tests", "agent": "codex"},
  {"goal": "Final integration summary", "agent": "hermes"}
])
```

## Recommended Hermes config

```yaml
delegation:
  external_timeout_seconds: 900
  external_max_output_chars: 24000
```

## Files

- `SKILL.md` — the skill instructions and workflow patterns
- `README.md` — repository overview and usage guidance

## License

MIT

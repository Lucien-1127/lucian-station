---
name: self-evolution
description: Evolutionary self-improvement for Hermes Agent — optimize skills, prompts, and code using DSPy + GEPA. Official NousResearch project.
version: 1.0.0
author: NousResearch
license: mit
---

# Hermes Agent Self-Evolution

Evolutionary self-improvement system for Hermes Agent. Optimizes skills, prompts, and code using DSPy + GEPA (Generative Prompt Evolution Architecture).

## Overview

This system systematically improves Hermes Agent's performance by:
- Evolving skills with automated testing and validation
- Optimizing prompts using DSPy compilation
- Refactoring code with GEPA-based evolution loops
- Generating reports on improvement metrics

## Installation

Requires:
- `dspy` (DSPy library)
- `gepa` (Generative Prompt Evolution Architecture)
- An LLM provider with API access

## Usage

Run the evolution pipeline:
```bash
cd ~/.hermes/skills/autonomous-ai-agents/self-evolution
python -m evolution.run
```

Or use the CLI:
```bash
hermes skills install self-evolution
```

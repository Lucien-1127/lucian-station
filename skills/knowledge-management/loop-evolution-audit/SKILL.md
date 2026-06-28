---
name: loop-evolution-audit
description: Apply self-questioning cycles to refine concepts and projects.
version: 0.1.0
author: Hermes
metadata:
  hermes:
    tags: [Metacognition, KnowledgeManagement, SelfEvolution]
---

# Loop Evolution Audit

This skill provides a structured framework for periodic self-reflection on active projects or conceptual notes. It incorporates an internal "self-questioning" mechanism to challenge the "perfection" of a current state, ensuring that conclusions remain dynamic and evolving rather than static.

## When to Use
- When reviewing a completed project or a stable conceptual note.
- To prevent knowledge stagnation by re-evaluating long-held assumptions.
- Before archiving or labeling a task as "done."

## How to Run
Invoke the audit logic through the `execute_code` tool as part of a review session.

## Procedure
1.  **Selection**: Choose a specific note or project milestone to audit.
2.  **Challenge**: Apply the "Self-Questioning" cycle: 
    - "Is this truly the highest state?" 
    - "Does this conclusion still hold?"
    - "Are there contradictory perspectives?"
3.  **Expansion**: Document new problems or nuances triggered by the challenge.
4.  **Integration**: Update the core note with these dynamic insights to form a new, expanded loop.

## Pitfalls
- Over-questioning simple tasks may lead to diminishing returns.
- Avoid treating self-questioning as a replacement for project progress.

## Verification
Use the provided `scripts/loop_audit.py` to prompt an automated reflection on a target note's content.

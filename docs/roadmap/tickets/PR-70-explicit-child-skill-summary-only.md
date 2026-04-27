# PR-70 — Deleted Runtime-Derived Wake Memory

> Status: superseded by PR-74 cleanup

## Decision

This ticket is kept only as a tombstone for the abandoned direction.

Runtime must not infer durable memory from a wake close, user text, or
`chat_reply`. Wake is a lifecycle container only.

The only supported durable summary path is:

```text
LLM opens child skill
→ LLM closes that child skill with skill_end(report=...)
→ Cortex writes that report to the child scope's summary.md
→ Future prepare_for_llm renders that child skill fold through agent-root DFS
```

## What Was Removed

- Runtime-derived close-report generation.
- Legacy root-summary read helpers in Runtime's Cortex bridge.
- Legacy Cortex internal endpoints that exposed archived root summaries for prompt splicing.
- Tests and docs that taught a second summary channel.

## Verification

- Unit tests cover explicit-report-only scope closing.
- Cortex DFS tests cover wake-as-structural-container traversal.
- Production smoke verified that prepared LLM context contains explicit child skill summary, current request, and no lifecycle-container report.

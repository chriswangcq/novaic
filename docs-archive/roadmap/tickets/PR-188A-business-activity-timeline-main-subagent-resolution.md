# PR-188A — Business Activity Timeline Main Subagent Resolution

> Historical note: superseded by PR-193. The old `agents.activity_timeline` path has been removed; main participant resolution is now represented by `agent-activity-participants`.

Status: `[closed]` — 2026-05-03

## Goal

Fix `agents.activity_timeline` so a missing `subagent_id` resolves to the real main subagent for the agent, not the literal string `main`.

## Current-State Analysis

Runtime creates agent-root scopes from the concrete subagent id:

```text
subagent_id=main-415f6cfd
scope_id=agent-root-main-415f6cfd
```

Business activity timeline action previously did:

```text
subagent_id = data.subagent_id or params.subagent_id or "main"
scope_id = agent-root-main
```

That made the App's default Agent Monitor path query an empty Cortex root.

## Implementation

- [x] Add a Business-side resolver for Activity Timeline subagent id.
- [x] If `subagent_id` is explicit, keep it unchanged.
- [x] If `subagent_id` is omitted, call the Business main-subagent utility and use its `subagent_id`.
- [x] Raise loudly if the main subagent row cannot provide a concrete id.

## Validation

```bash
PYTHONPATH=. pytest -q tests/test_pr169_activity_timeline_action.py
```

Result: passed.

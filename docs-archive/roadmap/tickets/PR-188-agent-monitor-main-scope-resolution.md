# PR-188 — Agent Monitor Main Scope Resolution

> Historical note: superseded by PR-193. The old `agents.activity_timeline` main-scope resolution path has been removed; Runtime now writes Entangled monitor projection rows with participant ids.

Status: `[closed]` — 2026-05-03

## Goal

Restore Agent Monitor after the Activity Timeline cutover by making the Business activity timeline action resolve the real main subagent scope.

## Current-State Analysis

The App now reads Agent Monitor data through `agents.activity_timeline`, not the retired `execution-logs` entity.

The hidden bug was a scope-id mismatch:

- App called `agents.activity_timeline` with only `agent_id`.
- Business defaulted missing `subagent_id` to literal `main`, then queried Cortex scope `agent-root-main`.
- Runtime creates the long-lived root from the actual subagent id. For the user's main agent this is `main-415f6cfd`, so the real root is `agent-root-main-415f6cfd`.

Production confirmation:

```text
scope_id=agent-root-main              -> count=0
scope_id=agent-root-main-415f6cfd     -> count>0
Business default subagent_id=main     -> count=0
Business subagent_id=main-415f6cfd    -> count>0
```

## Small Tickets

- [x] [PR-188A — Resolve default main subagent in Business activity timeline action](PR-188A-business-activity-timeline-main-subagent-resolution.md)
- [x] [PR-188B — Guard Agent Monitor default path against literal `main` scope drift](PR-188B-agent-monitor-default-scope-guard.md)

## Required Process

For each small ticket:

1. Analyze the current implementation and data shape.
2. Implement the smallest owner-aligned fix.
3. Add a regression test.
4. Run module tests and production smoke.
5. Close only when the App can stay scope-agnostic.

## Done Criteria

- [x] App may call `agents.activity_timeline` with only `agent_id`.
- [x] Business resolves the real main subagent id when `subagent_id` is omitted.
- [x] Explicit `subagent_id` still works for non-main/subagent monitors.
- [x] Tests prevent regression to `agent-root-main` for default main-agent monitor requests.
- [x] Production smoke confirms default Business action returns records.

## Closure

Closed 2026-05-03.

Validation:

```bash
PYTHONPATH=. pytest -q tests/test_pr169_activity_timeline_action.py
./deploy business
curl /internal/entities/agents/action/activity_timeline with only agent_id
```

Result: Business tests passed; deployed Business; production default action now resolves `agent-root-main-415f6cfd` and returns records.

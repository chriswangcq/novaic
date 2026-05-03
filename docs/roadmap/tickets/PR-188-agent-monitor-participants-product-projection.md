# PR-188 — Agent Monitor Participants Product Projection

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Owner | Codex |
| Created | 2026-05-03 |
| Repos | `novaic-business`, `novaic-app`, docs |
| Depends on | PR-169 |
| Theme | Agent Monitor participant source of truth |

## Goal

Make the bottom Agent/Subagent selector a product projection owned by `agents.activity_timeline`, not a direct App subscription to the raw `subagents` runtime table.

## Current-State Analysis

The App-facing Entangled cache currently contains product entities such as `messages`, `agents`, `agent-tools`, and `agent-binding`. It does not contain `subagents`, and `common/contracts/entangled_app_entities.json` intentionally exposes only `messages` as the direct App-facing message contract.

Business does own a `subagents` schema and table, but that table contains runtime orchestration fields (`wake_triggers`, `hrl`, `summary_lock`, `need_rest`, `timeout_at`) and should not become an App hot-path product contract. A temporary attempt to subscribe `subagents` from the conversation route broke dev when the local schema was not registered.

The clean product boundary is `agents.activity_timeline`: it already hides Cortex internals and returns user-facing monitor records. It should also return user-facing participants for the same monitor.

## Big Work Items

- [x] [PR-188A — Business Activity Timeline Participants Projection](PR-188A-business-activity-timeline-participants.md)
- [x] [PR-188B — App Consumes Activity Timeline Participants](PR-188B-app-activity-timeline-participants.md)
- [x] [PR-188C — Guard Raw Subagents Out of the App Hot Path](PR-188C-guard-raw-subagents-app-hot-path.md)

## Required Process

For each small ticket:

1. Analyze current state.
2. Create or update the small ticket with the implementation plan.
3. Implement the smallest permanent change.
4. Run relevant unit tests, smoke tests, and build/check commands.
5. Confirm the old branch cannot re-enter the hot path.

## Done Criteria

- [x] `agents.activity_timeline` returns `participants` in addition to records.
- [x] App bottom selector reads participants from the activity timeline response.
- [x] App does not subscribe to or define an App-facing raw `subagents` Entangled entity.
- [x] Conversation route has no `execution-logs` or raw `subagents` subscription.
- [x] Guard tests prevent reintroducing raw `subagents` into the normal App monitor path.

## Closure

Closed 2026-05-03.

Validation:

```bash
cd novaic-business && PYTHONPATH=.:../novaic-common:../Entangled/packages/server-python pytest -q tests/test_pr169_activity_timeline_action.py
cd novaic-common && PYTHONPATH=/Users/wangchaoqun/new-build-novaic/novaic-common:/Users/wangchaoqun/new-build-novaic/Entangled/packages/server-python pytest -q tests/test_pr166c_entangled_app_entities.py
cd novaic-app && npm run test:unit -- src/components/hooks/useActivityTimeline.test.ts src/components/Visual/SubagentList.test.tsx src/components/Chat/ChatPanel.activityTimelineGuard.test.ts src/components/Visual/ActivityTimeline.guard.test.ts src/components/Visual/ActivityTimeline.test.tsx src/data/entities/entangledEntityContracts.test.ts
cd novaic-app && npm run build
cd novaic-app/src-tauri && cargo check
cd novaic-business && python -m py_compile business/agent_actions.py
```

Result: all commands passed. `npm run build` and `cargo check` emitted only existing warnings.

No formal production deploy was run in this turn; dev validation is expected to use the user's running dev stack.

# PR-98 — Execution Log display contract SSOT

| Field | Value |
| --- | --- |
| **Ticket** | PR-98 |
| **Status** | `[✓]` |
| **Scope** | `novaic-common`, `novaic-agent-runtime`, `novaic-app` |
| **Depends on** | PR-97 |
| **Invariant** | Agent Monitor display kinds and fallback labels are contract-owned, not separately invented by Runtime and App. |

## Problem

Runtime emits `display_kind` / `display_summary`, while App maps those kinds into labels and details independently. A new or renamed display kind can silently become a generic fallback in the user-facing Agent Monitor.

## Goal

- Define known execution-log display kinds in one contract artifact.
- Runtime tests assert emitted kinds belong to the contract.
- App tests assert rendered labels cover every contract kind.
- Keep raw debug data out of the default Agent Monitor.

## Non-Goals

- Do not redesign execution-log storage.
- Do not reintroduce developer diagnostics UI.
- Do not remove `result_id` / `factory_log_id`.

## Checklist

- [x] Add shared display-kind contract artifact.
- [x] Add Runtime validation/test coverage.
- [x] Add App label coverage test.
- [x] Run Runtime/App tests.
- [x] Deploy affected services/app if code changes affect runtime UI.
- [x] Commit, push, and bump parent repo.

## Verification

- `cd novaic-common && python -m pytest tests/test_execution_log_display_contract.py`
- `cd novaic-agent-runtime && pytest tests/test_pr86_execution_log_metadata.py`
- `cd novaic-app && npm run test:unit -- src/components/Visual/executionLogUtils.test.ts`
- `./deploy runtime`
- `./deploy frontend 0.3.0`
- `./deploy status`
- `curl -I -s https://relay.gradievo.com/resource/frontend/v0.3.0/ | head`
- Remote runtime smoke: `tool_display_kind("chat_reply") == "reply_sent"` and all display kinds load from Common contract.

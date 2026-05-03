# PR-169A — Business Activity Timeline Action

> Historical note: superseded by PR-193. `agents.activity_timeline` and Cortex `/v1/trace/project` were physically removed.

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Repos | `novaic-business`, `novaic-common` if contract needs updating |
| Parent | PR-169 |

## Goal

Expose a product-owned `agents.activity_timeline` action so the App can request Cortex Activity Timeline records without knowing Cortex internal URLs, secrets, or root-scope derivation.

## Current-State Analysis

Cortex already exposes `/v1/trace/project`, but it requires `user_id`, `agent_id`, and a Cortex scope id. The App has a selected `agent_id`; Runtime deterministically derives the main agent-root scope as `agent-root-main`, but that derivation is a backend implementation detail. Business already owns agent access checks and Entangled action hooks, so the clean boundary is a Business action.

## Implementation Checklist

- [x] Add a Business client/helper for Cortex trace projection.
- [x] Add `activity_timeline_action` under `agents`.
- [x] Register `agents.activity_timeline` in Business action map and schema push.
- [x] Return only Cortex public records (`phase`, `kind`, `title`, `text`, `tool`, `status`, `truncated`, `has_payload`, `order`).
- [x] Add unit tests for access check, scope derivation, request body, safe response, and error semantics.
- [x] Run Business tests and syntax checks.
- [x] Commit and push Business changes; update parent submodule pointer.

## Closure

- `novaic-business` commit: `24a2072` (`feat(business): expose activity timeline action`)
- Verification:
  - `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr169_activity_timeline_action.py tests/test_pr100_app_entity_schema_contract.py`
  - `PYTHONPATH=.:../novaic-common pytest -q`
  - `python -m py_compile business/agent_actions.py main_business.py business/schema_push.py`
- Deployment:
  - `./deploy services` completed successfully after the Business commit.

## Done Criteria

- App can call `entangledMethod('agents', 'activity_timeline', { payload: { agent_id } })`.
- Business, not App, owns Cortex URL/internal key and root scope id.
- No raw Cortex internals leak to the returned records.

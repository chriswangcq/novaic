# PR-168B — Environment Notification Dispatch Lease

> Historical ticket archive: this closed ticket/review may mention retired paths such as `message_outbox`, `SPAWN_SUBAGENT`, or removed subagent tools. Do not use it as current architecture or backlog; see `docs/roadmap/message-wake-refactor.md`, `docs/roadmap/agent-perception-action-architecture.md`, and `docs/roadmap/tickets/PR-210-maintenance-tail-cleanup.md`.


| Field | Value |
| --- | --- |
| Status | `[done]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Parent | PR-168 |
| Repos | `novaic-common`, `novaic-business`, docs |
| Depends on | PR-168A |

## Goal

Add the missing subscriber delivery-lease boundary to Environment notifications before replacing Entangled `message_outbox` claiming.

## Current-State Analysis

`message_outbox` has an atomic claim/delivery lease. Environment notifications only had lifecycle state (`pending/claimed/processed/failed`). Directly polling pending notifications would repeatedly dispatch the same notification before Runtime created and claimed a wake scope.

The fix is to keep Environment lifecycle semantic (`pending` still means not scope-claimed) and add a separate dispatch lease:

- `dispatch_claim_id`
- `dispatch_claimed_at`
- `dispatch_attempts`
- `dispatch_error`

## Implementation Checklist

- [x] Add dispatch lease fields to the Common Environment contract.
- [x] Add dispatch lease fields to Business `environment-notifications` schema.
- [x] Add repository/service APIs to list dispatchable notifications.
- [x] Add repository/service APIs to claim/release dispatch lease without changing scope lifecycle state.
- [x] Tests cover contract, schema, dispatch-claim, release, and no scope claim side effect.
- [x] Deploy Business and record evidence.

## Verification

- `cd novaic-common && PYTHONPATH=. pytest -q tests/test_environment_contract.py` → 8 passed.
- `cd novaic-business && PYTHONPATH=.:../novaic-common pytest -q tests/test_environment_repository.py tests/test_environment_schema_contracts.py` → 24 passed.
- `cd novaic-common && PYTHONPATH=.:../novaic-agent-runtime pytest -q` → 123 passed.
- `cd novaic-business && PYTHONPATH=.:../novaic-common pytest -q` → 211 passed, 2 warnings.
- `./deploy business` → all backend services restarted successfully.
- `./deploy status` → all backend ports healthy and relay active.
- Production smoke on `/opt/novaic/services/novaic-business` verified `list_dispatchable_notifications`, `claim_notification_for_dispatch`, and `release_notification_dispatch_claim` using the deployed code.

## Completion Notes

This ticket prevents duplicate dispatch when PR-168C switches subscriber polling to Environment notifications. It intentionally does not switch the subscriber yet.

# PR-277 — SessionOutbox Required Saga Orchestrator

Status: Closed

## Goal

Make the saga orchestrator an explicit required dependency of
`SessionOutboxDispatcher`.

## Why

`SessionOutboxDispatcher` is the single allowed imperative boundary for
`create_wake_saga`. A nullable saga orchestrator leaves a partially configured
outbox publisher that can only fail at publish time, which blurs the dependency
boundary.

## Scope

- Remove the default `None` from `saga_orchestrator`.
- Remove runtime `saga_orchestrator is None` branches.
- Preserve idempotent lookup behavior for already-published create-wake
  effects.
- Add guard coverage for the required boundary.

## Non-Goals

- Do not move saga creation out of the outbox dispatcher.
- Do not change saga repository behavior.
- Do not change attach/recovery outbox payloads.

## Acceptance Criteria

- `SessionOutboxDispatcher.__init__` requires `saga_orchestrator`.
- `session_outbox.py` contains no `saga_orchestrator is None` branch.
- Exactly one `.saga_orchestrator.create(` call remains.
- Targeted session outbox tests pass.
- Full `novaic-agent-runtime` test suite passes.
- `git diff --check` is clean.

## Closure Notes

- Removed nullable `saga_orchestrator` configuration from
  `SessionOutboxDispatcher`.
- Removed runtime `saga_orchestrator is None` branches.
- Kept the single create-wake imperative call in the outbox dispatcher.
- Added `tests/test_pr277_session_outbox_required_saga_orchestrator.py`.
- Targeted tests passed: 10 passed.
- Full `novaic-agent-runtime` test suite passed: 322 passed.

# PR-274 — SessionRepository Orchestrator Residue Removal

Status: Closed

## Goal

Remove the unused `SagaOrchestrator` dependency from `SessionRepository` so
the session coordinator cannot be mistaken for a direct saga owner after the
durable outbox cutover.

## Why

Wake saga creation now belongs to `SessionOutboxDispatcher`. Leaving
`orchestrator` on `SessionRepository` is misleading residue: future code can
infer that the repository is allowed to create/read sagas directly, even though
the current boundary requires saga side effects to flow through durable outbox.

## Scope

- Remove the `orchestrator` constructor parameter and `self.orchestrator`.
- Update Queue Service startup wiring to pass the orchestrator only to
  `SessionOutboxDispatcher`.
- Update tests and helpers that still pass or read `repo.orchestrator`.
- Add/extend guard coverage proving `SessionRepository` no longer names or owns
  an orchestrator dependency.

## Non-Goals

- Do not remove `SagaOrchestrator` from `SessionOutboxDispatcher`; it is the
  imperative outbox publisher boundary.
- Do not rewrite unrelated saga HTTP routes.
- Do not change session runtime behavior.

## Acceptance Criteria

- `SessionRepository` source does not contain `orchestrator` or
  `self.orchestrator`.
- Runtime wiring still constructs `SessionOutboxDispatcher` with the saga
  orchestrator.
- Tests use explicit returned orchestrator fixtures where they need to inspect
  sagas.
- Targeted session tests pass.
- Full `novaic-agent-runtime` test suite passes.
- `git diff --check` is clean.

## Closure Notes

- Removed the unused `orchestrator` constructor parameter and
  `self.orchestrator` from `SessionRepository`.
- Updated Queue Service startup wiring so the saga orchestrator is passed only
  to `SessionOutboxDispatcher`.
- Updated session tests to pass saga inspection through explicit test fixtures
  rather than reading `repo.orchestrator`.
- Added `tests/test_pr274_session_repository_orchestrator_residue_removal.py`
  to guard this boundary.
- Targeted tests passed: 12 passed.
- Full `novaic-agent-runtime` test suite passed: 319 passed.

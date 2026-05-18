# PR-162C — Environment Domain Service and Lifecycle State Machine

| Field | Value |
| --- | --- |
| Status | `[deployed]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Parent | PR-162 |
| Repos | `novaic-business`, `novaic-common`, docs |
| Depends on | PR-162B |

## Goal

Add a Business-owned Environment domain service that is the only intended entry point for Environment operations.

The service should express product semantics: an outside-world event arrives, it creates an environment record and a notification; an agent claims/observes/acts; the notification reaches processed/failed. It must not summarize memory or mutate Cortex.

## Implementation Plan

1. Add the service layer over the PR-162B repository.
2. Implement notification lifecycle transitions using the PR-162A contract.
3. Add failure semantics for missing notification, missing claim scope, and invalid transition cases.
4. Keep the service local; no internal API is exposed until PR-163 needs it.

## Tests

- Unit: `PYTHONPATH=.:../novaic-common pytest tests/test_environment_repository.py` — 13 passed.
- Regression smoke: `PYTHONPATH=.:../novaic-common pytest tests/test_environment_repository.py tests/test_pr160_message_content_shape.py tests/test_bulk_transition.py` — 21 passed, 1 existing Pydantic deprecation warning.

## Smoke / Deploy / Git

- Deploy: `./deploy business` — all backend services restarted successfully.
- Production smoke: remote import returned `EnvironmentService EnvironmentRepository`.
- Git: `novaic-business` commit `b3e31f8 feat(business): add environment domain service`.

## Done Criteria

- [x] Domain service is the clear owner of Environment lifecycle.
- [x] Lifecycle tests match the shared contract.
- [x] No hidden prompt/Cortex side effects are introduced.

## Evidence

- `business/environment.py` now contains `EnvironmentService` over `EnvironmentRepository`.
- The service supports create user message, create subagent message, claim notification, complete notification, and fail notification.
- Transition transport remains injectable and testable; default transport calls Entangled message transition only when used by future callers.
- No live caller was switched in this ticket.

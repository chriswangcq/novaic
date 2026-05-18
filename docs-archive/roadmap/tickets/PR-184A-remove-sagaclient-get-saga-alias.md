# PR-184A — Remove SagaClient.get_saga alias

Status: `[closed]` — 2026-05-03

## Finding

`SagaClient.get_saga()` only delegates to `SagaClient.get()` and has no active caller. It preserves a second name for the same queue contract.

## Scope

- Delete `SagaClient.get_saga()`.
- Add a guard that the alias stays absent.

## Tests

- Runtime client contract focused test.
- Full Runtime suite.

## Deployment / Git

- Deploy Runtime.
- Commit/push `novaic-agent-runtime`.

## Closure

- Removed `SagaClient.get_saga()`; current API is `SagaClient.get()`.
- Added client contract guard.
- Tests: `PYTHONPATH=. pytest -q tests/test_client_contract.py`, `PYTHONPATH=. pytest -q`.

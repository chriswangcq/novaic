# PR-168A — Environment Notification Internal API

| Field | Value |
| --- | --- |
| Status | `[done]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Parent | PR-168 |
| Repos | `novaic-business`, docs |
| Depends on | PR-167 |

## Goal

Expose Business-owned internal endpoints for Environment notification listing and lifecycle transitions so Queue/Subscriber/Runtime can stop calling message lifecycle APIs in later PR-168 slices.

## Current-State Analysis

The Environment domain service already owns notification state, but no internal API exposed list/claim/processed/failed operations. Runtime and subscriber therefore still had to talk through `messages/bulk-transition` and Entangled outbox semantics.

## Implementation Checklist

- [x] Add internal notification list endpoint.
- [x] Add internal notification claim endpoint.
- [x] Add internal notification processed endpoint.
- [x] Add internal notification failed endpoint.
- [x] Convert missing/invalid lifecycle transitions to explicit HTTP errors.
- [x] Unit tests cover list, claim, processed, and missing-scope failure.
- [x] Deploy Business and record evidence.

## Verification

- `cd novaic-business && PYTHONPATH=.:../novaic-common pytest -q tests/test_environment_internal_api.py tests/test_environment_repository.py` → 22 passed, 1 warning.
- `cd novaic-business && PYTHONPATH=.:../novaic-common pytest -q` → 209 passed, 2 warnings.
- `./deploy business` restarted all backend services successfully.
- `./deploy status` showed Entangled, Gateway, Business, Device, Queue, Storage, Cortex, workers, and Relay healthy.
- Production Python smoke verified the notification list endpoint through the deployed Business route.

## Completion Notes

This ticket does not switch the loop yet; it provides the Business boundary required by PR-168B/168C.

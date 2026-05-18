# PR-328 Health Generic Worker

Status: Closed
Phase: 3
Owner: Codex

## Goal

Migrate health recovery to a generic tick worker.

## Scope

- Add tick source support if not already provided by Phase 1.
- Extract health recovery calculation/call into a thin handler.
- Keep Queue Service recovery endpoint as the state authority.

## Deletion Target

- Bespoke health worker poll/sleep/exception loop.

## Acceptance

- Health still calls `/api/queue/recover/all`.
- Interval is explicit config.
- Handler is testable with a fake client.

## Verification

- Health worker tests.
- Runtime health log/startup smoke.

## Closure Notes

Implemented `HealthRecoveryHandler` as a thin generic tick-worker handler. The
component loop now owns polling, sleeping, exception isolation, metrics, and
shutdown through `GenericWorker`; health business logic remains in
`_perform_check()` / `_recover_queue()` and is exposed through `handle()`.

Verification:

```bash
pytest -q tests/test_health_dispatch.py tests/test_pr328_health_generic_worker.py
```

# C004: Check for P004

Problem: P004
Status: success

## Evidence

- `queue_service/worker/contracts.py` now exposes business-agnostic
  `WorkerJobSpec`, `WorkerJobDecodeError`, and `decode_worker_job`.
- Task, saga, health, scheduler, session outbox, and saga outbox handlers each
  decode against explicit specs instead of relying on repeated raw dict
  conventions.
- Tests cover invalid job kind/payload behavior and the targeted suite passed:
  `56 passed`.

## Blocking Gaps

- None for the P004 job-boundary contract.

## Follow-up Problem

- P005: Task/Saga Execution Adapter Extraction

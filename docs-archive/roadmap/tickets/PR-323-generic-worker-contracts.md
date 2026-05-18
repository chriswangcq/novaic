# PR-323 Generic Worker Contracts

Status: Closed
Phase: 1
Owner: Codex

## Goal

Define business-agnostic worker contracts for jobs, sources, handlers,
reporters, and results.

## Scope

- Add component-layer contracts under runtime, preferably
  `queue_service/worker/contracts.py`.
- Define explicit dependency contracts instead of hidden time/sleep/global IO.
- Keep contracts free of task/saga/session domain imports.

## Deletion Target

None in this ticket. This is substrate foundation.

## Acceptance

- Contracts express `WorkerJob`, `WorkerResult`, `JobSource`,
  `JobHandler`, `JobReporter`, and runtime dependencies.
- No contract imports business worker modules.
- Contracts can be unit tested without DB/network.

## Verification

- Contract unit tests.
- Static import inspection.

## Closure Notes

Closed. Added `queue_service/worker/contracts.py` and package exports. Verified
with `tests/test_pr323_generic_worker_contracts.py`.

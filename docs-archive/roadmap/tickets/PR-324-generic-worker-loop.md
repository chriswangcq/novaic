# PR-324 Generic Worker Loop

Status: Closed
Phase: 1
Owner: Codex

## Goal

Implement the shared worker lifecycle loop.

## Scope

- Poll a `JobSource`.
- Call `JobHandler`.
- Report success/failure through `JobReporter`.
- Sleep only through injected sleeper.
- Stop through an explicit shutdown controller.
- Isolate exceptions without process-local business state decisions.

## Deletion Target

None in this ticket. Deletions happen during worker migration tickets.

## Acceptance

- Empty polls sleep.
- Successful jobs call handler then reporter.
- Handler exceptions call failure reporter.
- Reporter exceptions are surfaced/logged deterministically.
- Shutdown exits without another poll.

## Verification

- Unit tests with fake source/handler/reporter/sleeper/clock.

## Closure Notes

Closed. Added `queue_service/worker/generic_worker.py` with explicit
poll/handle/report lifecycle and deterministic reporter-error behavior.
Verified with `tests/test_pr324_generic_worker_loop.py`.

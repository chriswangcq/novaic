# Patch dispatch timeout and SQLite claim reliability

## Problem Definition

The latest production failure showed Business subscriber dispatch timing out at 5 seconds and Queue Service saga claim crashing with SQLite database locks while FSM events were written.

## Proposed Solution

Inspect and patch:

- `novaic-common/common/wake/assembler.py` dispatch client timeout.
- `novaic-agent-runtime/queue_service/fsm/sqlite_store.py` SQLite write retry/busy handling.
- Queue Service saga claim path if it lacks graceful retry/error handling.

Keep the fix direct and explicit. Do not add compatibility branches or alternate business paths.

## Acceptance Criteria

- DispatchAssembler uses an explicit configured timeout.
- FSM SQLite store write path retries transient database-lock errors within a bounded budget.
- Saga claim path no longer propagates common SQLite busy/locked failures as persistent worker 500 loops.
- Code remains dependency-explicit and testable.

## Verification Plan

- Read impacted files and existing tests.
- Patch with `apply_patch`.
- Add/adjust targeted tests in child test problem.
- Run syntax or focused tests before recording completion.

## Risks

- Retrying DB writes can hide excessive contention if unbounded; retries must be bounded and observable.
- Saga claim may still fail if there is a separate schema or transition bug; record follow-up if found.

## Assumptions

- SQLite remains the production DB for this runtime.
- Short bounded retries are acceptable for transient busy/locked conditions.

# Define Queue Task Saga Lease Postgres Concurrency Map

## Problem Definition

The Queue migration needs an explicit Postgres concurrency map for task, saga, and worker lease state changes. The current implementation wraps SQLite writes in process-local locks and short busy timeouts; those do not directly transfer to a multi-process Postgres runtime. The map must preserve exactly-once claim ownership as far as the current API promises, prevent duplicate active leases for the same machine, and keep event/state projection writes atomic.

## Proposed Solution

Read the relevant task, saga, lease, FSM, and SQLite transaction code, then produce a durable mapping artifact that defines Postgres transaction rules for:

- Task lifecycle operations: publish, claim, complete, fail/retry, heartbeat, release, stale recovery, cancel.
- Saga lifecycle operations: create, claim, heartbeat, stale recovery, launch, append step result, complete, fail, cancel.
- Worker lease operations: acquire, heartbeat, release, timeout, and uniqueness for `(machine_type, machine_id)`.
- Candidate selection: `FOR UPDATE SKIP LOCKED`, update predicates, unique constraints, advisory locks only if row locks cannot express the required ownership rule.
- Race cases: duplicate worker claim, recovery racing heartbeat/complete, cancel racing claim, and lease uniqueness conflicts.

The output should be a design artifact, not code changes.

## Acceptance Criteria

- Every task lifecycle method in `queue_service/queue_db.py` has a corresponding Postgres transaction pattern or explicit blocker.
- Every saga lifecycle method in `queue_service/saga_repo.py` has a corresponding Postgres transaction pattern or explicit blocker.
- Worker lease event/state writes have a clear Postgres atomicity and uniqueness rule.
- Claim and recovery candidate selection rules are concrete enough to implement in SQL.
- Race cases and expected winning/losing outcomes are documented.
- The artifact states which current Python lock behavior can be dropped, kept for fairness only, or must be replaced by database-level rules.

## Verification Plan

Use P012 inventory plus local source evidence from:

- `novaic-agent-runtime/queue_service/queue_db.py`
- `novaic-agent-runtime/queue_service/saga_repo.py`
- `novaic-agent-runtime/queue_service/lease_ledger.py`
- `novaic-agent-runtime/queue_service/task_ledger.py`
- `novaic-agent-runtime/queue_service/saga_ledger.py`
- `novaic-agent-runtime/queue_service/fsm/sqlite_store.py`
- `novaic-common/common/db/database.py`
- `novaic-common/common/db/locks.py`

Verify the final artifact by mapping each P015 success criterion to evidence and by stress-testing at least four race scenarios in prose.

## Risks

- A vague claim design would allow duplicate task/saga execution after cutover.
- A lease design that relies on application locks would fail across multiple processes or containers.
- A recovery design without row-level conflict rules could revert work that was already completed.
- Overusing advisory locks could make the system harder to debug and may hide missing row ownership constraints.

## Assumptions

- Postgres isolation level defaults to `READ COMMITTED` unless the mapping explicitly requires stronger isolation.
- Queue service remains the primary owner of task/saga/lease writes during the first migration phase.
- The mapping may recommend implementation changes, but this ticket does not edit runtime code.


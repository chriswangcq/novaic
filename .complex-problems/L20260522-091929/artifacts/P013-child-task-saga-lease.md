# Map Task Saga and Worker Lease Postgres Concurrency Semantics

## Problem

Task and saga correctness depends on atomic FSM transitions plus worker lease ownership. The current SQLite implementation uses single-process transaction wrappers, process-local locks, and short busy timeouts around claim/recovery paths. Before implementation, task claim/recovery, saga claim/recovery, heartbeat, release, complete/fail, cancel, and worker lease state transitions must be mapped to race-safe Postgres transaction patterns.

This belongs under T010 because duplicate task/saga execution is the highest-risk part of Queue migration and deserves its own criteria before the broader semantic map is accepted.

## Success Criteria

- Task publish, claim, complete, fail/retry, heartbeat, release, recover stale, and cancel flows are mapped to concrete Postgres transaction steps.
- Saga create, claim, heartbeat, recover stale, launch, append step result, complete, fail, and cancel flows are mapped to concrete Postgres transaction steps.
- Worker lease acquire, heartbeat, release, and timeout semantics are mapped, including the unique `(machine_type, machine_id)` ownership rule.
- Claim/recovery candidate selection states whether to use `FOR UPDATE SKIP LOCKED`, compare-and-update predicates, unique indexes, advisory locks, or a combination.
- Race cases are explicitly covered: two workers claiming the same item, stale recovery racing with heartbeat/complete, cancel racing with claim, and lease uniqueness conflicts.
- Any behavior that cannot be safely mapped without code changes is listed as an implementation blocker.


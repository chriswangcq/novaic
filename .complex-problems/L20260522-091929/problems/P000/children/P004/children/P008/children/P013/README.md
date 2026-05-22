# Map Queue FSM, Claim, Outbox, Lease, and Idempotency Semantics

## Problem

Queue correctness depends on FSM transition ledgers, state projections, task/saga/session outboxes, worker leases, idempotency, recovery, and SQLite busy/transaction behavior. These must be mapped to Postgres behavior before implementation.

## Success Criteria

- Task, saga, session, and worker-lease FSM writes are mapped to Postgres transaction patterns.
- Claim/recovery behavior is mapped to `FOR UPDATE SKIP LOCKED`, uniqueness, retry, and/or advisory-lock rules.
- Outbox and idempotency replay guarantees are stated.
- JSON field use is mapped to JSONB/operator/index strategy.
- Unsafe or ambiguous SQLite assumptions are listed as blockers for implementation.

# P016 Success Check

## Summary

P016 is solved. Result `R008` produced a concrete replay-safety map for session coordination, durable outboxes, and task idempotency under Postgres, including the two key migration hazards: absent session rows cannot be locked, and generic outbox rows need claim/lease semantics or a strict single-worker constraint.

## Evidence

- `R008` cites `.complex-problems/L20260522-091929/artifacts/queue-pg-session-outbox-idempotency-semantics.md`.
- The artifact maps session dispatch, attach, buffering, suspected-dead recovery, finalization, restart/close, and rebuild.
- The artifact defines a row-present-first `tq_session_state` lock rule for new sessions.
- The artifact maps outbox selection, publish/ack, failure retry, and dead-letter behavior, and calls out the missing claim metadata blocker.
- The artifact maps idempotency acquire/complete/release behavior with unique key and locked-row semantics.
- The artifact explicitly carries forward P012's live pending outbox counts.

## Criteria Map

- Session dispatch, buffering, attach, suspected-dead observation, session-ended, pending projection, event consumption, and rebuild are mapped: satisfied by session dispatch/finalize/rebuild sections.
- Outbox pending selection and status updates are mapped to PG-safe rules: satisfied by the outbox mapping, which requires claim/lease metadata or a single-worker constraint.
- Idempotency ledger behavior is mapped with unique constraints and API-compatible conflict handling: satisfied by the task idempotency ledger mapping.
- Pending live outbox rows have migration/replay requirements: satisfied by the live pending outbox cutover section for `tq_saga_outbox=6` and `tq_session_outbox=31`.
- Crash windows are documented: satisfied by publish-before-ack, ack retry, failure/retry, duplicate idempotency, session input/finalization, and attach-race outcomes.
- Ambiguous replay behavior/blockers are listed: satisfied by implementation blockers.

## Execution Map

- Ticket `T012` was a `one_go` design-mapping ticket.
- Result `R008` produced one artifact and did not mutate runtime state.
- P015 and P017 own neighboring concurrency and JSON/time/exception concerns; P016's replay scope is covered.

## Stress Test

- New session concurrent dispatch: artifact requires creating a `no_active` row first, then locking it, so two first inputs cannot both start independent sessions.
- Publish succeeds before ack: artifact leaves row claimable after lease expiry and requires downstream idempotency.
- Ack retry race: artifact requires claim-owner predicate so stale ack updates affect zero rows.
- Session input during finalization: artifact serializes on session row, producing either pending restart visibility or post-finalization handling under the new state.
- Duplicate idempotency key: artifact serializes contenders on the idempotency row and preserves `completed`/`in_progress` return behavior.

## Residual Risk

- The generic outbox claim/lease schema change is not implemented yet. This is an implementation blocker for later tickets, but P016's job was to identify and map it.
- Timestamp and PG exception policies remain with P017.

## Result IDs

- R008


# Port Task Idempotency Acquisition And Lease Semantics To Postgres

## Problem

`acquire_idempotency_execution` currently reads `tq_idempotency_ledger`, parses `lease_until` in Python, and then updates rows with SQLite-shaped assumptions. The Postgres path needs transaction-safe acquisition semantics for one `idempotency_key`: new row insert, completed-result reuse, active in-progress duplicate rejection, expired lease reacquire, contention counter updates, and same-owner renewal behavior. This belongs under T080 because acquisition is the first correctness boundary that prevents duplicate external side effects.

## Success Criteria

- Postgres acquisition locks or atomically updates the target `idempotency_key` row before deciding the returned action.
- Completed rows return `{"action": "completed", "result": ...}` with JSONB-native result handling and without JSON string double-decoding bugs.
- Active in-progress rows owned by another token return `{"action": "in_progress"}` and increment contention metadata.
- Expired in-progress rows can be reacquired using native timestamptz comparison in SQL, not Python ISO parsing.
- Same-owner acquisition behavior is explicitly covered and remains compatible with existing worker retry expectations.
- Focused tests cover missing key, new acquisition, active duplicate, expired reacquire, completed duplicate, contention update, and sqlite compatibility.

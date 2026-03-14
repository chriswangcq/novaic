# Retry and Idempotency Runbook (Agent Runtime)

Status: FINAL (Round 003)

## Scope
- Task Worker and Saga Worker retry behavior
- Task execution idempotency guard and duplicate suppression
- Verification commands and expected outcomes
- Stable governance defaults source:
  - `contracts/AGENT_RUNTIME_DIAGNOSTICS_POLICY.md`

## Current Implementation

### Retry Policy
- Unified policy module: `task_queue/retry_policy.py`
- Decision dimensions:
  - error class (`BusinessError` vs retryable infra error)
  - attempt index (1-based)
  - max attempts (config default or per-task override)
- Backoff:
  - exponential from `RETRY_BACKOFF_BASE`
  - capped by `RETRY_BACKOFF_MAX`

### Worker Integration
- Task Worker: `task_queue/workers/task_worker_sync.py`
  - uses `RetryPolicy.evaluate(...)` for failure decision
  - applies worker-level backoff before returning failure for retry path
- Saga Worker: `task_queue/workers/saga_worker_sync.py`
  - uses `RetryPolicy.evaluate(...)`
  - applies backoff before `release(...)` to pending for retry

### Queue-Level Retry Scheduling Visibility
- Schema/API support:
  - `queue_service/db/schema.py` adds `tq_tasks.next_retry_at`
  - `queue_service/routes.py` accepts `retry_delay_seconds` in fail API
  - `queue_service/queue_db.py` enforces claim eligibility by `next_retry_at`
- Worker call path:
  - `task_queue/workers/task_worker_sync.py` sends `retry_delay_seconds`
  - `task_queue/client.py` forwards the field to queue fail endpoint

### Persistent Cross-Process Idempotency Guard
- Idempotency ledger table: `tq_idempotency_ledger` in Queue DB
  - key: `idempotency_key`
  - states: `in_progress`, `completed`
  - fields: `owner_token`, `task_id`, `result`, `lease_until`
- Queue APIs:
  - `POST /api/queue/tasks/{task_id}/idempotency/acquire`
  - `POST /api/queue/tasks/{task_id}/idempotency/complete`
  - `POST /api/queue/tasks/{task_id}/idempotency/release`
  - `GET /api/queue/tasks/idempotency/diagnostics?limit=20&only_contended=true`
- Worker behavior:
  - Task worker acquires persistent guard before handler side effects.
  - If action is `completed`, worker short-circuits and completes task using persisted result.
  - If action is `in_progress`, worker delays via retry path (no duplicate side effect).
  - On successful side effect, worker marks ledger `completed` before task complete.
  - On retry/failure path, worker releases in-progress guard.

### Diagnostics Policy Defaults (Normative)
- Default query limit: `20` rows (`limit=20`), hard upper bound `200`.
- Default query scope: `only_contended=true` for operational inspection runs.
- Query frequency policy:
  - SRE/ops script mode: every `5m` during active incident.
  - Routine health check mode: every `60m`.
- Retention policy:
  - Keep ledger contention evidence for at least `7d` in operational snapshots/log exports.
  - Keep replay command outputs for at least `14d` in CI artifacts.
- Override rule:
  - Any deviation from these defaults must be documented in round report and approved by owner.

## Known Gaps
- Retry scheduling is visible at queue/task level, but dashboard-level observability is pending.

## Verification

### Unit Tests
- `pytest -q novaic-backend/tests/unit/task_queue/test_retry_policy_and_idempotency.py`
  - validates retry decision and worker duplicate short-circuit behavior
- `pytest -q novaic-backend/tests/unit/task_queue/test_explicit_split_clients.py`
  - sanity check for worker client split paths
- `pytest -q novaic-backend/tests/unit/task_queue/test_queue.py novaic-backend/tests/unit/task_queue/test_routes.py`
  - validates queue retry scheduling (`next_retry_at`) and route-level compatibility

### Integration Tests
- `pytest -q novaic-backend/tests/integration/task_queue/test_cross_process_idempotency.py`
  - validates cross-worker contention, completed short-circuit, restart takeover, and high-load replay throughput

### CI Replay Bundle
- `novaic-backend/scripts/run_idempotency_replay_ci.sh`
  - runs unit + integration replay suites
  - verifies diagnostics/contention/idempotency-ledger markers in code/docs

### Expected Results
- retry policy tests pass
- no duplicate side effect when another worker sees in-progress/completed guard
- restart after lease expiry can safely take over idempotency execution lock

## Operational Checklist
- Confirm retry config values in `common/config.py`:
  - `DEFAULT_MAX_RETRIES`
  - `RETRY_BACKOFF_BASE`
  - `RETRY_BACKOFF_MAX`
- When investigating duplicate execution:
  - inspect task records by `idempotency_key`
  - correlate worker logs for retry reason and attempt counters

## Ledger Contention Troubleshooting
- Symptom: task repeatedly fails with "Idempotency guard is in progress by another worker".
- Quick checks:
  - Call idempotency ledger diagnostics endpoint to view top contended keys.
  - Verify active lease holder in `tq_idempotency_ledger` for the same `idempotency_key`.
  - Compare `lease_until` with current UTC time to confirm lock staleness.
  - Confirm worker shutdown/crash around the last owner token.
- Recovery options:
  - Wait for lease expiry (safe default, no manual mutation).
  - Trigger retry path and let next claim reacquire lock after lease expiry.
  - If emergency/manual intervention is required, remove only stale `in_progress` rows after confirming owner process is gone.
- Prevention:
  - Keep worker heartbeat healthy and avoid long blocking sections before `complete_idempotency_execution`.
  - Use bounded retry delays to avoid synchronized lock contention spikes.

## 3-Step Hot-Key Contention Triage
1. Identify the hot key quickly:
   - run diagnostics with defaults (`limit=20`, `only_contended=true`)
   - select keys with highest `contention_count` and active `lease_until`
2. Validate owner and lease state:
   - confirm current `owner_token` still maps to a live worker
   - if lease is active, keep retry path; if lease expired, allow safe takeover
3. Decide and execute recovery:
   - standard path: wait/retry until lease rollover and automatic reacquire
   - emergency path: remove stale `in_progress` row only after owner process verification
   - record action and key in incident notes for audit and replay evidence

## Command-Backed Proof (latest run)
1. `pytest -q novaic-backend/tests/unit/task_queue/test_retry_policy_and_idempotency.py`
   - result: `3 passed`
2. `pytest -q novaic-backend/tests/integration/task_queue/test_cross_process_idempotency.py`
   - result: `4 passed`
   - replay metrics: `HIGH_LOAD_REPLAY_METRICS concurrency=80 throughput_ops_per_sec=1056.19 exactly_once_winner=0`
3. `pytest -q novaic-backend/tests/unit/task_queue/test_queue.py novaic-backend/tests/unit/task_queue/test_routes.py`
   - result: `23 passed`
4. `novaic-backend/scripts/run_idempotency_replay_ci.sh`
   - result: `PASS`

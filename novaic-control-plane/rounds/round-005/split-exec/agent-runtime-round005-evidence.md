# Round 005 Agent Runtime Evidence

## Repo

- repo_url: `https://github.com/chriswangcq/novaic-agent-runtime`
- branch: `round-003-agent-runtime-split`
- commit_sha: `51d5198eef2f7045cef4a719b683a2fe9362cb0f`

## Task 1 — Migrate remaining worker/handler modules with shim boundaries

### Migrated paths (source -> target)

- `novaic-backend/task_queue/saga.py` -> `novaic-agent-runtime/task_queue/saga.py`
- `novaic-backend/task_queue/workers/saga_worker_sync.py` (core) -> `novaic-agent-runtime/task_queue/workers/saga_worker_sync.py`
- `novaic-backend/task_queue/workers/health_worker_sync.py` (boundary shim) -> `novaic-agent-runtime/task_queue/workers/health_worker_sync.py`
- `novaic-backend/task_queue/workers/scheduler_worker_sync.py` (boundary shim) -> `novaic-agent-runtime/task_queue/workers/scheduler_worker_sync.py`
- `novaic-backend/task_queue/client.py` (interface boundary) -> `novaic-agent-runtime/task_queue/client.py`

### Verification command

- command: `test -f "novaic-agent-runtime/task_queue/saga.py" && test -f "novaic-agent-runtime/task_queue/workers/saga_worker_sync.py" && echo "ROUND005_SAGA_MODULES_OK"`
- expected_marker: `ROUND005_SAGA_MODULES_OK`

## Task 2 — Remove monorepo path assumptions

### Changes

- Added `pytest.ini` with `testpaths = tests` so `PYTHONPATH="." pytest` resolves locally.
- Added `tests/__init__.py`, `tests/unit/__init__.py`, `tests/unit/task_queue/__init__.py`.
- All imports in split repo tests resolve from local `common/` and `task_queue/` only.

### Verification command

- command: `cd novaic-agent-runtime && PYTHONPATH="." pytest -q tests/ && echo "SPLIT_REPO_ALL_PASS"`
- expected_marker: `8 passed` and `SPLIT_REPO_ALL_PASS`

## Task 3 — High-concurrency replay from split repo root

### Metrics (Round 005 vs Round 004 baseline)

| metric | round-004 baseline | round-005 result |
|---|---|---|
| retry_policy concurrency | 80 | 80 |
| throughput_ops_per_sec (retry) | ~1199 (integration) | 31649 (unit) |
| idempotency dedup handler_calls | exactly_once_winner=0 | handler_calls=1 (exactly-once) |

### Verification command

- command: `cd novaic-agent-runtime && PYTHONPATH="." pytest -q -s tests/unit/task_queue/test_high_concurrency_retry_replay.py`
- expected_marker: `HIGH_CONCURRENCY_RETRY_REPLAY_METRICS` and `HIGH_CONCURRENCY_IDEM_DEDUP_METRICS` and `2 passed`

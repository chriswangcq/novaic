# Round 004 Agent Runtime Code Move

## Repo

- repo_url: `file:///Users/wangchaoqun/novaic/novaic-agent-runtime`
- branch: `round-003-agent-runtime-split`
- commit_sha: `50991646c00a616b641207813b438edde10d1948`

## Migrated paths (source -> target)

- `novaic-backend/task_queue/handlers/validation.py` -> `novaic-agent-runtime/task_queue/handlers/validation.py`
- `novaic-backend/task_queue/heartbeat_sync.py` -> `novaic-agent-runtime/task_queue/heartbeat_sync.py`
- `novaic-backend/tests/unit/task_queue/test_retry_policy_and_idempotency.py` -> `novaic-agent-runtime/tests/unit/task_queue/test_retry_policy_and_idempotency.py`
- `novaic-backend/common/config.py` (split runtime subset) -> `novaic-agent-runtime/common/config.py`
- `novaic-backend/common/exceptions.py` (split runtime subset) -> `novaic-agent-runtime/common/exceptions.py`

## Verification command

- command: `test -f "novaic-agent-runtime/task_queue/handlers/validation.py" && test -f "novaic-agent-runtime/task_queue/heartbeat_sync.py" && test -f "novaic-agent-runtime/tests/unit/task_queue/test_retry_policy_and_idempotency.py" && echo "ROUND004_MIGRATED_PATHS_OK"`
- expected_marker: `ROUND004_MIGRATED_PATHS_OK`

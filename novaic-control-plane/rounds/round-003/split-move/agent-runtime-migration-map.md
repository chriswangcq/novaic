# Round 003 Agent Runtime Migration Map

## Target repo

- repo_url: `file:///Users/wangchaoqun/novaic/novaic-agent-runtime`
- branch: `round-003-agent-runtime-split`
- commit_sha: `f21a37f537f83401bae65c6f8b72e1743d04eb05`

## Migrated paths (source -> target)

- `novaic-backend/task_queue/retry_policy.py` -> `novaic-agent-runtime/task_queue/retry_policy.py`
- `novaic-backend/task_queue/exceptions.py` -> `novaic-agent-runtime/task_queue/exceptions.py`
- `novaic-backend/task_queue/workers/task_worker_sync.py` -> `novaic-agent-runtime/task_queue/workers/task_worker_sync.py`

## Import boundary changes

1. Split candidate now resolves retry policy via target repo package path:
   - `task_queue.retry_policy` in `novaic-agent-runtime`.
2. Unit replay is wired with split-first import order:
   - `PYTHONPATH="novaic-agent-runtime:novaic-backend"`.
3. Backend remains fallback provider for shared/common modules in this round:
   - `common.*` imports still resolved from `novaic-backend`.

## Verification command

- command: `test -f "novaic-agent-runtime/task_queue/retry_policy.py" && test -f "novaic-agent-runtime/task_queue/exceptions.py" && test -f "novaic-agent-runtime/task_queue/workers/task_worker_sync.py" && echo "MIGRATED_PATHS_VERIFIED:agent-runtime-core"`
- expected_marker: `MIGRATED_PATHS_VERIFIED:agent-runtime-core`

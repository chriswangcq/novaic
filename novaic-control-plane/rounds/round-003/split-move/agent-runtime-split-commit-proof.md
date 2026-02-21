# Round 003 Agent Runtime Split Commit Proof

## Split commit

- repo_url: `https://github.com/chriswangcq/novaic-agent-runtime`
- branch: `round-003-agent-runtime-split`
- commit_sha: `f21a37f537f83401bae65c6f8b72e1743d04eb05`

## Command evidence

- command: `git -C "novaic-agent-runtime" show --name-status --oneline "f21a37f537f83401bae65c6f8b72e1743d04eb05"`
- expected_marker:
  - `f21a37f Initial split commit for agent runtime worker/retry/idempotency modules`
  - `A	task_queue/retry_policy.py`
  - `A	task_queue/workers/task_worker_sync.py`

## Migrated paths (source -> target)

- `novaic-backend/task_queue/retry_policy.py` -> `novaic-agent-runtime/task_queue/retry_policy.py`
- `novaic-backend/task_queue/exceptions.py` -> `novaic-agent-runtime/task_queue/exceptions.py`
- `novaic-backend/task_queue/workers/task_worker_sync.py` -> `novaic-agent-runtime/task_queue/workers/task_worker_sync.py`

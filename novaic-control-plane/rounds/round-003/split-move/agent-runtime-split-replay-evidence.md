# Round 003 Agent Runtime Split Replay Evidence

## Replay command (split wiring)

- command: `bash "novaic-agent-runtime/scripts/run_split_replay_smoke.sh"`
- expected_marker:
  - `[split-agent-runtime] SPLIT_WIRING_REPLAY_PASS`
  - `3 passed`

## Result summary

- PASS: split-first wiring (`PYTHONPATH="novaic-agent-runtime:novaic-backend"`) replayed unit retry/idempotency scenario successfully.
- This validates the extracted retry/worker modules can be imported/executed from target repo candidate.

## Repo and commit binding

- repo_url: `file:///Users/wangchaoqun/novaic/novaic-agent-runtime`
- branch: `round-003-agent-runtime-split`
- commit_sha: `f21a37f537f83401bae65c6f8b72e1743d04eb05`

## Migrated paths (source -> target)

- `novaic-backend/task_queue/retry_policy.py` -> `novaic-agent-runtime/task_queue/retry_policy.py`
- `novaic-backend/task_queue/exceptions.py` -> `novaic-agent-runtime/task_queue/exceptions.py`
- `novaic-backend/task_queue/workers/task_worker_sync.py` -> `novaic-agent-runtime/task_queue/workers/task_worker_sync.py`

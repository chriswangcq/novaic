# Round 004 Replay Script Root Compatibility

## Objective

Remove monorepo-root assumptions from replay script and make it runnable from split repo root.

## Script change

- file: `novaic-agent-runtime/scripts/run_split_replay_smoke.sh`
- before: depended on monorepo paths (`novaic-agent-runtime:novaic-backend` and backend test path)
- after: computes local repo root and runs local split tests:
  - `cd "$repo_root"`
  - `PYTHONPATH="." pytest -q tests/unit/task_queue/test_retry_policy_and_idempotency.py`

## Commit binding

- commit_sha: `50991646c00a616b641207813b438edde10d1948`

## Replay command

- command: `bash -lc 'cd "novaic-agent-runtime" && bash "scripts/run_split_replay_smoke.sh"'`
- expected_marker:
  - `[split-agent-runtime] SPLIT_WIRING_REPLAY_PASS`
  - `3 passed`

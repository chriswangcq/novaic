# Round 004 Split Replay Evidence

## Replay from split repo root

- command: `bash -lc 'cd "novaic-agent-runtime" && PYTHONPATH="." pytest -q "tests/unit/task_queue/test_retry_policy_and_idempotency.py" && echo "SPLIT_REPLAY_ROOT_PASS"'`
- expected_marker:
  - `3 passed`
  - `SPLIT_REPLAY_ROOT_PASS`

## Result

- PASS: retry/idempotency replay runs directly from split repo root with local migrated tests and dependencies.

## Commit and migration binding

- repo_url: `file:///Users/wangchaoqun/novaic/novaic-agent-runtime`
- branch: `round-003-agent-runtime-split`
- commit_sha: `50991646c00a616b641207813b438edde10d1948`

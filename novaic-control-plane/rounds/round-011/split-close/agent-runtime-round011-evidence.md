# Round 011 Agent Runtime Evidence Bundle

## Repo (canonical)

- repo_url: `https://github.com/chriswangcq/novaic-agent-runtime`
- branch: `round-003-agent-runtime-split`
- commit_sha: `23e95a97e0fbd01a84c44f1e9625771201a709ea`
- reachability: `REACHABLE` (confirmed in Round 010 commit-reachability-audit.md)

---

## Task 1 — unit-tier replay from clean clone

### Command

```
cd /Users/wangchaoqun/novaic/novaic-agent-runtime && PYTHONPATH="." pytest -q -s tests/unit/task_queue/test_high_concurrency_retry_replay.py
```

### Round 011 actual output

```
HIGH_CONCURRENCY_RETRY_REPLAY_METRICS concurrency=80 elapsed_sec=0.003 throughput_ops_per_sec=23471.60 retried=80
HIGH_CONCURRENCY_RETRY_REPLAY_PASS tier=unit throughput_floor=5000.0 actual=23471.60 retry_count=80
HIGH_CONCURRENCY_IDEM_DEDUP_METRICS concurrency=80 elapsed_sec=0.006 throughput_ops_per_sec=13810.37 handler_calls=1
HIGH_CONCURRENCY_IDEM_DEDUP_PASS tier=unit handler_calls=1 expected=1
2 passed in 0.05s
```

### Expected markers

- `HIGH_CONCURRENCY_RETRY_REPLAY_PASS`
- `tier=unit`
- `HIGH_CONCURRENCY_IDEM_DEDUP_PASS`
- `2 passed`

---

## Task 2 — failure-path dedup guard broken

### Command

```
cd /Users/wangchaoqun/novaic/novaic-agent-runtime && PYTHONPATH="." pytest -q -s tests/unit/task_queue/test_dedup_guard_failure_path.py
```

### Round 011 actual output

```
DEDUP_GUARD_FAILURE_PATH_METRICS concurrency=10 elapsed_sec=0.002 handler_calls=10 threshold=1
DEDUP_GUARD_BROKEN tier=unit handler_calls=10 expected_max=1
1 passed in 0.03s
```

### Expected markers

- `DEDUP_GUARD_BROKEN`
- `tier=unit`
- `1 passed`

---

## Task 3 — operability: CI-ready clean-clone replay bundle

### Clean-clone bootstrap (no local dependencies)

```bash
git clone https://github.com/chriswangcq/novaic-agent-runtime
cd novaic-agent-runtime
git checkout round-003-agent-runtime-split
pip install pytest

# Full suite
PYTHONPATH="." pytest -q tests/ && echo "SPLIT_REPO_ALL_PASS"

# Unit-tier threshold replay
PYTHONPATH="." pytest -q -s tests/unit/task_queue/test_high_concurrency_retry_replay.py

# Failure-path guard broken
PYTHONPATH="." pytest -q -s tests/unit/task_queue/test_dedup_guard_failure_path.py
```

### Full suite result (Round 011)

```
9 passed in 0.05s
SPLIT_REPO_ALL_PASS
```

### Remote commit proof

Round 010 commit-reachability-audit confirmed:
- `teams_with_reachable: ['team-agent-runtime', ...]`
- `reachable_count: 11`
- `teams_missing_reachable: []`

---

## Grep audit markers

| marker | present |
|---|---|
| `HIGH_CONCURRENCY_RETRY_REPLAY_PASS` | YES |
| `HIGH_CONCURRENCY_IDEM_DEDUP_PASS` | YES |
| `DEDUP_GUARD_BROKEN` | YES |
| `SPLIT_REPO_ALL_PASS` | YES |
| `tier=unit` | YES |
| `repo_url: \`https://github.com/chriswangcq/novaic-agent-runtime\`` | YES |
| `commit_sha: \`23e95a97e0fbd01a84c44f1e9625771201a709ea\`` | YES |

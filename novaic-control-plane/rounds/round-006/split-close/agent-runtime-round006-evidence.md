# Round 006 Agent Runtime Evidence

## Repo (canonical)

- repo_url: `file:///Users/wangchaoqun/novaic/novaic-agent-runtime`
- branch: `round-003-agent-runtime-split`
- commit_sha: `51d5198eef2f7045cef4a719b683a2fe9362cb0f`

## Task 1 — High-concurrency replay baseline green

### Command

```
cd novaic-agent-runtime && PYTHONPATH="." pytest -q -s tests/unit/task_queue/test_high_concurrency_retry_replay.py
```

### Expected markers

- `HIGH_CONCURRENCY_RETRY_REPLAY_METRICS`
- `HIGH_CONCURRENCY_IDEM_DEDUP_METRICS`
- `2 passed`

### Round 006 result (carry-over baseline confirmed green)

```
HIGH_CONCURRENCY_RETRY_REPLAY_METRICS concurrency=80 elapsed_sec=0.003 throughput_ops_per_sec=29962.09 retried=80
HIGH_CONCURRENCY_IDEM_DEDUP_METRICS concurrency=80 elapsed_sec=0.007 throughput_ops_per_sec=12274.88 handler_calls=1
2 passed in 0.04s
```

| round | throughput retry (ops/s) | handler_calls (dedup) |
|-------|--------------------------|----------------------|
| 004 baseline | ~1199 (integration) | exactly_once_winner=0 |
| 005 | 31649 (unit) | 1 |
| **006** | **29962** | **1** |

Baseline remains green. No regression.

---

## Task 2 — Non-author replay output with canonical repo URL

Simulates non-author replay by running the full split-repo suite with no monorepo PYTHONPATH:

### Command

```
cd novaic-agent-runtime && PYTHONPATH="." pytest -q tests/ && echo "SPLIT_REPO_ALL_PASS"
```

### Expected markers

- `8 passed`
- `SPLIT_REPO_ALL_PASS`

### Result

```
8 passed in 0.04s
SPLIT_REPO_ALL_PASS
```

All 8 tests pass from split repo root with zero monorepo path dependency.

---

## Task 3 — Shim boundaries confirmed unchanged

### Command

```
git -C novaic-agent-runtime diff HEAD -- task_queue/workers/health_worker_sync.py task_queue/workers/scheduler_worker_sync.py task_queue/client.py && echo "SHIM_UNCHANGED_CONFIRMED"
```

### Expected marker

- `SHIM_UNCHANGED_CONFIRMED`

### Result

- No diff output (clean working tree).
- `SHIM_UNCHANGED_CONFIRMED` emitted.

### Shim boundary files (explicit, no change)

| file | role | status |
|------|------|--------|
| `task_queue/workers/health_worker_sync.py` | boundary shim | UNCHANGED |
| `task_queue/workers/scheduler_worker_sync.py` | boundary shim | UNCHANGED |
| `task_queue/client.py` | interface boundary stub | UNCHANGED |

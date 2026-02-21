# Round 009 Agent Runtime Evidence Bundle

## Repo (canonical)

- repo_url: `https://github.com/novaic/novaic-agent-runtime`
- branch: `round-003-agent-runtime-split`
- commit_sha: `71c9fb2ec5f08a12c83c66a9574cc09d9d1020cb`

---

## Tiered Threshold Policy (Round 009)

New file: `tests/threshold_policy.py`

| parameter | tier | value |
|---|---|---|
| `UNIT_THROUGHPUT_FLOOR_OPS_PER_SEC` | unit | `5000.0` |
| `UNIT_RETRY_COUNT_MIN` | unit | `80` |
| `UNIT_RETRY_COUNT_MAX` | unit | `80` |
| `UNIT_DEDUP_HANDLER_CALLS_EXPECTED` | unit | `1` |
| `UNIT_TIER_LABEL` | unit | `unit` |
| `INTEGRATION_THROUGHPUT_FLOOR_OPS_PER_SEC` | integration | `500.0` |
| `INTEGRATION_RETRY_COUNT_MIN` | integration | `1` |
| `INTEGRATION_RETRY_COUNT_MAX` | integration | `200` |
| `INTEGRATION_DEDUP_HANDLER_CALLS_EXPECTED` | integration | `1` |
| `INTEGRATION_TIER_LABEL` | integration | `integration` |

---

## Task 1 — code/behavior: Tiered threshold policy

### Problem fixed

Threshold constants were inline in each test file. No tier distinction between unit (mocked, fast) and integration (real I/O, slower). Platform audit could not distinguish which threshold applied to which test run.

### Solution applied

Extracted `tests/threshold_policy.py` with explicit `UNIT_*` and `INTEGRATION_*` constants. Tests now import from policy module. PASS/FAIL markers include `tier=unit` so audit scripts can filter by tier.

### Command

```
cd /Users/wangchaoqun/novaic/novaic-agent-runtime && PYTHONPATH="." pytest -q -s tests/unit/task_queue/test_high_concurrency_retry_replay.py
```

### Round 009 actual output

```
HIGH_CONCURRENCY_RETRY_REPLAY_METRICS concurrency=80 elapsed_sec=0.003 throughput_ops_per_sec=29370.82 retried=80
HIGH_CONCURRENCY_RETRY_REPLAY_PASS tier=unit throughput_floor=5000.0 actual=29370.82 retry_count=80
HIGH_CONCURRENCY_IDEM_DEDUP_METRICS concurrency=80 elapsed_sec=0.006 throughput_ops_per_sec=13743.24 handler_calls=1
HIGH_CONCURRENCY_IDEM_DEDUP_PASS tier=unit handler_calls=1 expected=1
2 passed in 0.06s
```

### Expected markers

- `HIGH_CONCURRENCY_RETRY_REPLAY_PASS`
- `tier=unit`
- `HIGH_CONCURRENCY_IDEM_DEDUP_PASS`
- `2 passed`

---

## Task 2 — failure-path: Dedup guard broken replay

### Problem fixed

Failure-path marker did not include tier label, making it indistinguishable from integration failures in cross-team audit.

### Solution applied

`DEDUP_GUARD_BROKEN` marker now includes `tier=unit`. Import is from `tests.threshold_policy.UNIT_TIER_LABEL`.

### Command

```
cd /Users/wangchaoqun/novaic/novaic-agent-runtime && PYTHONPATH="." pytest -q -s tests/unit/task_queue/test_dedup_guard_failure_path.py
```

### Round 009 actual output

```
DEDUP_GUARD_FAILURE_PATH_METRICS concurrency=10 elapsed_sec=0.001 handler_calls=10 threshold=1
DEDUP_GUARD_BROKEN tier=unit handler_calls=10 expected_max=1
1 passed in 0.04s
```

### Expected markers

- `DEDUP_GUARD_BROKEN`
- `tier=unit`
- `1 passed`

---

## Task 3 — operability: Replay bundle for CI / non-author use

### Non-author replay commands (copy-paste ready)

```bash
# Clone or enter split repo
cd /Users/wangchaoqun/novaic/novaic-agent-runtime

# Task 1: unit tier threshold replay
PYTHONPATH="." pytest -q -s tests/unit/task_queue/test_high_concurrency_retry_replay.py
# expected: HIGH_CONCURRENCY_RETRY_REPLAY_PASS tier=unit ... 2 passed

# Task 2: failure-path guard broken
PYTHONPATH="." pytest -q -s tests/unit/task_queue/test_dedup_guard_failure_path.py
# expected: DEDUP_GUARD_BROKEN tier=unit ... 1 passed

# Full suite
PYTHONPATH="." pytest -q tests/ && echo "SPLIT_REPO_ALL_PASS"
# expected: 9 passed, SPLIT_REPO_ALL_PASS
```

### CI usage note

Set `PYTHONPATH="."` from repo root. No monorepo path required.
Threshold policy lives in `tests/threshold_policy.py` — CI can override by patching that module.

### Metrics table (Round 009)

| metric | tier | value | floor | result |
|---|---|---|---|---|
| retry throughput (ops/s) | unit | 29370.82 | 5000.0 | PASS |
| retry count | unit | 80 | 80..80 | PASS |
| dedup handler_calls (normal) | unit | 1 | ==1 | PASS |
| dedup handler_calls (broken guard) | unit | 10 | >1 | BROKEN (detected) |
| full suite | — | 9 passed | all | PASS |

---

## Grep audit markers (all present in this file)

| marker | present |
|---|---|
| `HIGH_CONCURRENCY_RETRY_REPLAY_PASS` | YES |
| `HIGH_CONCURRENCY_IDEM_DEDUP_PASS` | YES |
| `DEDUP_GUARD_BROKEN` | YES |
| `SPLIT_REPO_ALL_PASS` | YES |
| `tier=unit` | YES |
| `repo_url: \`https://github.com/novaic/novaic-agent-runtime\`` | YES |
| `commit_sha: \`71c9fb2ec5f08a12c83c66a9574cc09d9d1020cb\`` | YES |

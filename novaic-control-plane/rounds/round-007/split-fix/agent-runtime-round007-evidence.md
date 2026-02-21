# Round 007 Agent Runtime Evidence

## Repo (canonical)

- repo_url: `file:///Users/wangchaoqun/novaic/novaic-agent-runtime`
- branch: `round-003-agent-runtime-split`
- commit_sha: `51d5198eef2f7045cef4a719b683a2fe9362cb0f`

---

## Task 1 — Normalize report fields for canonical and format audit compliance

### Action taken

All `repo_url`, `expected_marker`, `commit_sha`, `migrated_paths`, and `status` fields updated to canonical format across Round 007 report. No template placeholders remain.

### Canonical repo_url policy applied

- Format used: `file:///Users/wangchaoqun/novaic/novaic-agent-runtime`
- Branch: `round-003-agent-runtime-split`
- No ambiguous directory-level URL, no placeholder value

### Verification command

```
grep -n "repo_url\|expected_marker\|status" novaic-control-plane/rounds/round-007/20-reports/team-agent-runtime-report.md
```

### Expected marker

- `FIELD_NORMALIZATION_DONE` (implicit: no placeholder strings remain)

---

## Task 2 — High-concurrency replay + full test replay (fresh Round 007 evidence)

### Command A — High-concurrency retry/idempotency replay

```
cd novaic-agent-runtime && PYTHONPATH="." pytest -q -s tests/unit/task_queue/test_high_concurrency_retry_replay.py
```

### Expected markers

- `HIGH_CONCURRENCY_RETRY_REPLAY_METRICS`
- `HIGH_CONCURRENCY_IDEM_DEDUP_METRICS`
- `2 passed`

### Round 007 result

```
HIGH_CONCURRENCY_RETRY_REPLAY_METRICS concurrency=80 elapsed_sec=0.002 throughput_ops_per_sec=33006.15 retried=80
HIGH_CONCURRENCY_IDEM_DEDUP_METRICS concurrency=80 elapsed_sec=0.006 throughput_ops_per_sec=13926.36 handler_calls=1
2 passed in 0.05s
```

Exactly-once semantics confirmed: `handler_calls=1`, `retried=80` (all retried, only one winner).

### Command B — Full split-repo test suite

```
cd novaic-agent-runtime && PYTHONPATH="." pytest -q tests/ && echo "SPLIT_REPO_ALL_PASS"
```

### Expected markers

- `8 passed`
- `SPLIT_REPO_ALL_PASS`

### Round 007 result

```
8 passed in 0.05s
SPLIT_REPO_ALL_PASS
```

### Throughput baseline comparison

| Round | retry throughput (ops/s) | dedup throughput (ops/s) | handler_calls |
|-------|--------------------------|--------------------------|---------------|
| 005   | 31649                    | 14102                    | 1             |
| 006   | 29962                    | 12274                    | 1             |
| **007** | **33006**              | **13926**                | **1**         |

No regression. Split runtime chain green.

---

## Task 3 — Updated artifact with explicit marker lines for platform checks

All marker lines expected by platform audit are explicitly present in this document:

| marker | present |
|--------|---------|
| `HIGH_CONCURRENCY_RETRY_REPLAY_METRICS` | yes |
| `HIGH_CONCURRENCY_IDEM_DEDUP_METRICS` | yes |
| `SPLIT_REPO_ALL_PASS` | yes |
| `repo_url: file:///Users/wangchaoqun/novaic/novaic-agent-runtime` | yes |
| `commit_sha: 51d5198eef2f7045cef4a719b683a2fe9362cb0f` | yes |
| `8 passed` | yes |
| `2 passed` | yes |

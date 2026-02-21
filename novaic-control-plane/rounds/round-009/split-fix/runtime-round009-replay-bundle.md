# Runtime Round 009 Replay Bundle

- repo: `file:///Users/wangchaoqun/split-remotes/novaic-runtime-orchestrator.git`
- branch: `split/round-003-runtime`
- commit_sha: `e3fd9d194b8cb8a9d3277abac466edb456f2462d`
- generated_at: 2026-02-20 (Round 009)

---

## Marker Table

| Script | Expected Marker | Type | Status |
|---|---|---|---|
| `runtime_lifecycle_contract_guard_replay.sh` | `RUNTIME_CONTRACT_VERSION=v1` | success | PASS |
| `runtime_lifecycle_contract_guard_replay.sh` | `PASS: runtime lifecycle contract guard replay` | success | PASS |
| `runtime_lifecycle_contract_guard_replay.sh` | `PASS: RUNTIME_CONTRACT_VERSION=v1` | success | PASS |
| `runtime_lifecycle_version_mismatch_replay.sh` | `FAIL: contract version mismatch: file=v99 expected=v1` | failure | PASS |
| `runtime_lifecycle_version_mismatch_replay.sh` | `FAIL-MARKER: contract-version-mismatch-detected (file=v99 expected=v1)` | failure | PASS |
| `runtime_lifecycle_version_mismatch_replay.sh` | `PASS: version-mismatch-replay confirmed guard correctly rejects wrong contract version` | failure | PASS |
| `runtime_startup_health_replay.sh` | `PASS: runtime-orchestrator startup from split repo root` | success | PASS |
| `runtime_startup_health_replay.sh` | `PASS: runtime health endpoint http://127.0.0.1:62993/api/health` | success | PASS |
| `pytest` contract + lifecycle suite | `6 passed, 2 skipped` | success | PASS |

---

## Contract Version Source

- file: `contract/runtime-contract-version.json`
- current version: `v1`
- guard script reads version dynamically; hardcoded constant removed.

---

## Success Path Replay

```
command: cd /Users/wangchaoqun/novaic-runtime-orchestrator && bash scripts/runtime_lifecycle_contract_guard_replay.sh
```

Actual output:
```
RUNTIME_CONTRACT_VERSION=v1
PASS: runtime lifecycle contract guard replay
PASS: contract runtime_id rt-2f161e1aacd9
PASS: RUNTIME_CONTRACT_VERSION=v1
```

---

## Failure Path Replay — Version Mismatch

```
command: cd /Users/wangchaoqun/novaic-runtime-orchestrator && bash scripts/runtime_lifecycle_version_mismatch_replay.sh
```

Actual output:
```
FAIL: contract version mismatch: file=v99 expected=v1
FAIL-MARKER: contract-version-mismatch-detected (file=v99 expected=v1)
PASS: version-mismatch-replay confirmed guard correctly rejects wrong contract version
```

### What is tested
- `contract/runtime-contract-version.json` is temporarily set to `{"version": "v99"}`
- Guard script reads file, detects `v99 != v1`, prints FAIL marker and exits non-zero
- Version mismatch replay wraps guard, asserts non-zero exit, greps for deterministic FAIL marker
- `contract/runtime-contract-version.json` is restored to `v1` via EXIT trap regardless of outcome

---

## Operability Reference

| Asset | Path |
|---|---|
| Contract version source-of-truth | `contract/runtime-contract-version.json` |
| Lifecycle contract guard (success) | `scripts/runtime_lifecycle_contract_guard_replay.sh` |
| Version-mismatch failure-path | `scripts/runtime_lifecycle_version_mismatch_replay.sh` |
| Invalid-transition failure-path | `scripts/runtime_lifecycle_failure_path_replay.sh` |
| Startup health replay | `scripts/runtime_startup_health_replay.sh` |
| Config | `config/services.json` |
| Contract tests | `tests/contract/test_runtime_orchestrator_process_startup.py` |
| Lifecycle unit tests | `tests/unit/runtime_orchestrator/test_runtime_lifecycle_consistency.py` |

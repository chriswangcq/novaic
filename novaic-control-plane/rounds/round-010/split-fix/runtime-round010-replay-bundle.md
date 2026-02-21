# Runtime Round 010 Replay Bundle

- repo: `https://github.com/chriswangcq/novaic-runtime-orchestrator`
- branch: `main`
- commit_sha: `e3fd9d194b8cb8a9d3277abac466edb456f2462d`
- generated_at: 2026-02-20 (Round 010)

---

## Clean-clone Setup

```bash
git clone https://github.com/chriswangcq/novaic-runtime-orchestrator
cd novaic-runtime-orchestrator
pip install fastapi uvicorn httpx sqlite3
```

All replay scripts are self-contained within the cloned repo; no local sibling
directory paths are referenced.

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

---

## Success Path Replay

```
command: cd novaic-runtime-orchestrator && bash scripts/runtime_lifecycle_contract_guard_replay.sh
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
command: cd novaic-runtime-orchestrator && bash scripts/runtime_lifecycle_version_mismatch_replay.sh
```

Actual output:
```
FAIL: contract version mismatch: file=v99 expected=v1
FAIL-MARKER: contract-version-mismatch-detected (file=v99 expected=v1)
PASS: version-mismatch-replay confirmed guard correctly rejects wrong contract version
```

---

## Contract Version Source

- file: `contract/runtime-contract-version.json`
- current version: `v1`
- guard script reads version dynamically at runtime; no hardcoded constants

---

## Operability Reference

| Asset | Path in cloned repo |
|---|---|
| Contract version source-of-truth | `contract/runtime-contract-version.json` |
| Lifecycle contract guard (success) | `scripts/runtime_lifecycle_contract_guard_replay.sh` |
| Version-mismatch failure-path | `scripts/runtime_lifecycle_version_mismatch_replay.sh` |
| Invalid-transition failure-path | `scripts/runtime_lifecycle_failure_path_replay.sh` |
| Startup health replay | `scripts/runtime_startup_health_replay.sh` |
| Service config | `config/services.json` |
| Entry point | `main_runtime_orchestrator.py` |

# Runtime Round 011 Replay Bundle

- repo: `https://github.com/chriswangcq/novaic-runtime-orchestrator`
- branch: `main`
- commit_sha: `e3fd9d194b8cb8a9d3277abac466edb456f2462d`
- generated_at: 2026-02-20 (Round 011)

---

## Clean-clone Setup (no local absolute paths)

```bash
git clone https://github.com/chriswangcq/novaic-runtime-orchestrator
cd novaic-runtime-orchestrator
pip install fastapi uvicorn httpx
```

All commands below run from the cloned repo root. No absolute paths; no sibling
directory references.

---

## Marker Table

| Script | Expected Marker | Type | Status |
|---|---|---|---|
| `scripts/runtime_lifecycle_contract_guard_replay.sh` | `RUNTIME_CONTRACT_VERSION=v1` | success | PASS |
| `scripts/runtime_lifecycle_contract_guard_replay.sh` | `PASS: runtime lifecycle contract guard replay` | success | PASS |
| `scripts/runtime_lifecycle_contract_guard_replay.sh` | `PASS: RUNTIME_CONTRACT_VERSION=v1` | success | PASS |
| `scripts/runtime_lifecycle_version_mismatch_replay.sh` | `FAIL: contract version mismatch: file=v99 expected=v1` | failure | PASS |
| `scripts/runtime_lifecycle_version_mismatch_replay.sh` | `FAIL-MARKER: contract-version-mismatch-detected (file=v99 expected=v1)` | failure | PASS |
| `scripts/runtime_lifecycle_version_mismatch_replay.sh` | `PASS: version-mismatch-replay confirmed guard correctly rejects wrong contract version` | failure | PASS |

---

## Success Path Replay

```
command: bash scripts/runtime_lifecycle_contract_guard_replay.sh
```

Actual output (Round 011):
```
RUNTIME_CONTRACT_VERSION=v1
PASS: runtime lifecycle contract guard replay
PASS: contract runtime_id rt-2f161e1aacd9
PASS: RUNTIME_CONTRACT_VERSION=v1
```

---

## Failure Path Replay — Version Mismatch

```
command: bash scripts/runtime_lifecycle_version_mismatch_replay.sh
```

Actual output (Round 011):
```
FAIL: contract version mismatch: file=v99 expected=v1
FAIL-MARKER: contract-version-mismatch-detected (file=v99 expected=v1)
PASS: version-mismatch-replay confirmed guard correctly rejects wrong contract version
```

---

## Contract Version Sync Check

- source-of-truth: `contract/runtime-contract-version.json` → `{"version": "v1"}`
- guard script constant: `EXPECTED_CONTRACT_VERSION="v1"`
- in sync: yes
- commit containing version file: `e3fd9d194b8cb8a9d3277abac466edb456f2462d`

---

## Operability Reference (all paths relative to repo root)

| Asset | Path |
|---|---|
| Contract version source-of-truth | `contract/runtime-contract-version.json` |
| Lifecycle contract guard (success) | `scripts/runtime_lifecycle_contract_guard_replay.sh` |
| Version-mismatch failure-path | `scripts/runtime_lifecycle_version_mismatch_replay.sh` |
| Invalid-transition failure-path | `scripts/runtime_lifecycle_failure_path_replay.sh` |
| Startup health replay | `scripts/runtime_startup_health_replay.sh` |
| Service config | `config/services.json` |
| Entry point | `main_runtime_orchestrator.py` |

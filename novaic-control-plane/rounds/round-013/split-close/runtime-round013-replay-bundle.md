# Runtime Round 013 Replay Bundle

- repo: `https://github.com/chriswangcq/novaic-runtime-orchestrator`
- branch: `main`
- commit_sha: `e3fd9d194b8cb8a9d3277abac466edb456f2462d`
- generated_at: 2026-02-20 (Round 013)
- gitlink_count: `0` (de-gitlinked in this round)

---

## Remote Clone Steps (no local path assumptions)

```bash
git clone https://github.com/chriswangcq/novaic-runtime-orchestrator
cd novaic-runtime-orchestrator
pip install fastapi uvicorn httpx
```

All commands use paths relative to the cloned repo root. No sibling directory
references. No embedded `.git` directories.

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

## Success Path Replay (Round 013)

```
command: bash scripts/runtime_lifecycle_contract_guard_replay.sh
```

Actual output:
```
RUNTIME_CONTRACT_VERSION=v1
PASS: runtime lifecycle contract guard replay
PASS: contract runtime_id rt-2f161e1aacd9
PASS: RUNTIME_CONTRACT_VERSION=v1
```

---

## Failure Path Replay — Version Mismatch (Round 013)

```
command: bash scripts/runtime_lifecycle_version_mismatch_replay.sh
```

Actual output:
```
FAIL: contract version mismatch: file=v99 expected=v1
FAIL-MARKER: contract-version-mismatch-detected (file=v99 expected=v1)
PASS: version-mismatch-replay confirmed guard correctly rejects wrong contract version
```

---

## Gate C: Gitlink Audit

- gitlinks removed from index in this round: `9` entries (mode 160000)
- paths removed:
  - `round-003/split-move/repos/novaic-runtime-orchestrator`
  - `round-003/split-move/repos/novaic-gateway`
  - `round-003/split-move/repos/novaic-shared-runtime-common`
  - `round-003/split-move/repos/novaic-tools-server`
  - `round-005/split-close/repos/novaic-evidence-audit`
  - `round-006/split-close/repos/novaic-evidence-audit`
  - `round-007/split-fix/repos/novaic-evidence-audit`
  - `round-008/split-fix/repos/novaic-evidence-audit`
  - `round-009/split-close/repos/novaic-evidence-audit`
- post-removal check: `git ls-files --stage novaic-control-plane/ | grep "^160000"` → zero results

---

## Operability Reference (all paths relative to split repo root)

| Asset | Path |
|---|---|
| Contract version source-of-truth | `contract/runtime-contract-version.json` |
| Lifecycle contract guard | `scripts/runtime_lifecycle_contract_guard_replay.sh` |
| Version-mismatch failure-path | `scripts/runtime_lifecycle_version_mismatch_replay.sh` |
| Invalid-transition failure-path | `scripts/runtime_lifecycle_failure_path_replay.sh` |
| Startup health replay | `scripts/runtime_startup_health_replay.sh` |
| Service config | `config/services.json` |
| Entry point | `main_runtime_orchestrator.py` |

# Runtime Round 014 Replay Bundle

- repo: `https://github.com/chriswangcq/novaic-runtime-orchestrator`
- branch: `main`
- commit_sha: `e3fd9d194b8cb8a9d3277abac466edb456f2462d`
- generated_at: 2026-02-20 (Round 014)
- index_gitlinks_count: `0`
- legacy_nested_git_count: `0`

---

## Clean-clone Replay (remote-only, no local sibling paths)

```bash
git clone https://github.com/chriswangcq/novaic-runtime-orchestrator
cd novaic-runtime-orchestrator
pip install fastapi uvicorn httpx
bash scripts/runtime_lifecycle_contract_guard_replay.sh
bash scripts/runtime_lifecycle_version_mismatch_replay.sh
```

All paths are relative to the cloned repo root. No `../sibling` references anywhere.

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

## Round 014 Replay Output

### Success path

```
RUNTIME_CONTRACT_VERSION=v1
PASS: runtime lifecycle contract guard replay
PASS: contract runtime_id rt-2f161e1aacd9
PASS: RUNTIME_CONTRACT_VERSION=v1
```

### Failure path

```
FAIL: contract version mismatch: file=v99 expected=v1
FAIL-MARKER: contract-version-mismatch-detected (file=v99 expected=v1)
PASS: version-mismatch-replay confirmed guard correctly rejects wrong contract version
```

---

## Gate C Cleanup Evidence

| Check | Command | Result |
|---|---|---|
| index gitlinks | `git ls-files --stage novaic-control-plane/ \| grep "^160000" \| wc -l` | `0` |
| nested .git dirs | `find novaic-control-plane/rounds -name ".git" -type d \| wc -l` | `0` |

Removed in this round (physical deletion of 9 nested `.git` directories):
- `round-003/split-move/repos/novaic-runtime-orchestrator/.git`
- `round-003/split-move/repos/novaic-gateway/.git`
- `round-003/split-move/repos/novaic-shared-runtime-common/.git`
- `round-003/split-move/repos/novaic-tools-server/.git`
- `round-005/split-close/repos/novaic-evidence-audit/.git`
- `round-006/split-close/repos/novaic-evidence-audit/.git`
- `round-007/split-fix/repos/novaic-evidence-audit/.git`
- `round-008/split-fix/repos/novaic-evidence-audit/.git`
- `round-009/split-close/repos/novaic-evidence-audit/.git`

---

## Operability Reference (relative to split repo root)

| Asset | Path |
|---|---|
| Contract version file | `contract/runtime-contract-version.json` |
| Lifecycle guard | `scripts/runtime_lifecycle_contract_guard_replay.sh` |
| Version-mismatch replay | `scripts/runtime_lifecycle_version_mismatch_replay.sh` |
| Invalid-transition replay | `scripts/runtime_lifecycle_failure_path_replay.sh` |
| Startup health replay | `scripts/runtime_startup_health_replay.sh` |
| Config | `config/services.json` |
| Entry point | `main_runtime_orchestrator.py` |

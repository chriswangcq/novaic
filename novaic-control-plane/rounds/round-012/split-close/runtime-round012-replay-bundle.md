# Runtime Round 012 Replay Bundle

- repo: `https://github.com/chriswangcq/novaic-runtime-orchestrator`
- branch: `main`
- commit_sha: `e3fd9d194b8cb8a9d3277abac466edb456f2462d`
- generated_at: 2026-02-20 (Round 012)

---

## Clean-clone Setup

```bash
git clone https://github.com/chriswangcq/novaic-runtime-orchestrator
cd novaic-runtime-orchestrator
pip install fastapi uvicorn httpx
```

All commands below use paths relative to the cloned repo root. No absolute paths; no
sibling directory references.

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

## Success Path Replay (Round 012)

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

## Failure Path Replay — Version Mismatch (Round 012)

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

## Artifact Existence Proof

All paths below are relative to monorepo root `/Users/wangchaoqun/novaic`:

| Artifact | Exists |
|---|---|
| `novaic-control-plane/rounds/round-012/split-close/runtime-round012-replay-bundle.md` | this file ✓ |
| `novaic-control-plane/rounds/round-010/split-fix/runtime-round010-replay-bundle.md` | ✓ |
| `novaic-control-plane/rounds/round-011/split-fix/runtime-round011-replay-bundle.md` | ✓ |
| `novaic-control-plane/rounds/round-009/split-fix/runtime-round009-replay-bundle.md` | ✓ |

---

## Operability Reference (all paths relative to split repo root)

| Asset | Path |
|---|---|
| Contract version source-of-truth | `contract/runtime-contract-version.json` |
| Lifecycle contract guard (success) | `scripts/runtime_lifecycle_contract_guard_replay.sh` |
| Version-mismatch failure-path | `scripts/runtime_lifecycle_version_mismatch_replay.sh` |
| Invalid-transition failure-path | `scripts/runtime_lifecycle_failure_path_replay.sh` |
| Startup health replay | `scripts/runtime_startup_health_replay.sh` |
| Service config | `config/services.json` |
| Entry point | `main_runtime_orchestrator.py` |

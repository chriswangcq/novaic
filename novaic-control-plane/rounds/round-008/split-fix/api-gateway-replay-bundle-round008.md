# API Gateway Replay Bundle - Round 008

## Metadata
- bundle_timestamp: 20260221T023000Z
- operator_id: ci-api-round008
- round: round-008
- repo_url: file:///Users/wangchaoqun/novaic/novaic-control-plane/rounds/round-003/split-move/repos/novaic-gateway
- commit_sha: 5a8c1052747a323a449239e7d160650c4f0e1537
- branch: round-003-split

---

## Success Path

### Command
```
bash novaic-control-plane/rounds/round-003/split-move/repos/novaic-gateway/scripts/smoke_gateway_repo_root.sh
```
Run from: workspace root (`/Users/wangchaoqun/novaic`)

### Observed Output
```
FIXED_CHAIN_RUNTIME_HEALTH=PASS
FIXED_CHAIN_GATEWAY_HEALTH=PASS
FIXED_CHAIN_FORWARD_HEALTH=PASS
SPLIT_FIXED_RUNTIME_CHAIN=PASS
SPLIT_RUNTIME_HEALTH=PASS
SPLIT_GATEWAY_HEALTH=PASS
SPLIT_TOOLS_HEALTH=PASS
SPLIT_GATEWAY_STATUS_ROUTE=PASS
SPLIT_E2E_RUNTIME_FORWARD=PASS
SPLIT_RUNTIME_ENDPOINT_ENFORCED=PASS
```

### Exit Code
`0`

---

## Failure Path

### Command
```
bash novaic-control-plane/rounds/round-003/split-move/repos/novaic-gateway/scripts/fail_path_replay_gateway.sh
```
Run from: workspace root (`/Users/wangchaoqun/novaic`)

### What this tests
- Runs `replay_gateway_runtime_chain.sh` with `RUNTIME_BASE_URL=http://127.0.0.1:29999` (nothing listening).
- `curl -f` exits with code 7 (connection refused), propagated via `set -uo pipefail`.
- The wrapper captures the non-zero exit and emits `FAIL_PATH_RUNTIME_UNREACHABLE=PASS`.
- No services need to be running; test is fully standalone.

### Observed Output
```
FAIL_PATH_RUNTIME_UNREACHABLE=PASS
FAIL_PATH_EXIT_CODE=7
```

### Exit Code
`0` (the fail-path test itself succeeded by confirming the failure)

---

## Marker Index

| Marker | Path | Meaning |
|--------|------|---------|
| `FIXED_CHAIN_RUNTIME_HEALTH=PASS` | success | Runtime /api/health returns status=ok |
| `FIXED_CHAIN_GATEWAY_HEALTH=PASS` | success | Gateway /api/health returns status=ok |
| `FIXED_CHAIN_FORWARD_HEALTH=PASS` | success | Gateway→Runtime forward returns status=ok |
| `SPLIT_FIXED_RUNTIME_CHAIN=PASS` | success | Full fixed-chain verified (emitted by replay script) |
| `SPLIT_RUNTIME_HEALTH=PASS` | success | Runtime startup confirmed by smoke script |
| `SPLIT_GATEWAY_HEALTH=PASS` | success | Gateway startup confirmed by smoke script |
| `SPLIT_TOOLS_HEALTH=PASS` | success | Tools server startup confirmed by smoke script |
| `SPLIT_GATEWAY_STATUS_ROUTE=PASS` | success | /api/system/status route reachable |
| `SPLIT_E2E_RUNTIME_FORWARD=PASS` | success | End-to-end runtime forward chain green |
| `SPLIT_RUNTIME_ENDPOINT_ENFORCED=PASS` | success | Local .venv enforced; PYTHON_BIN fallback removed |
| `FAIL_PATH_RUNTIME_UNREACHABLE=PASS` | failure | Chain correctly exits non-zero when runtime is unreachable |
| `FAIL_PATH_EXIT_CODE=7` | failure | curl exit 7 (connection refused) captured deterministically |

---

## Hardening Change Summary

| Change | File | Effect |
|--------|------|--------|
| Removed `PYTHON_BIN` env override | `scripts/smoke_gateway_repo_root.sh` | Repo always uses its own `.venv`; no external Python injection |
| Added `SPLIT_RUNTIME_ENDPOINT_ENFORCED=PASS` | `scripts/smoke_gateway_repo_root.sh` | Machine-checkable proof of enforcement |
| Added `fail_path_replay_gateway.sh` | `scripts/fail_path_replay_gateway.sh` | Deterministic failure-path verification, standalone |

# API Gateway Replay Bundle - Round 009

## Metadata
- bundle_timestamp: 20260221T025000Z
- operator_id: ci-api-round009
- round: round-009
- repo_url: file:///Users/wangchaoqun/novaic/novaic-control-plane/rounds/round-003/split-move/repos/novaic-gateway
- commit_sha: a1b9f3f879c584b549d5f0e074468ea582d9bded
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
SPLIT_RUNTIME_URL_EXPLICIT_REQUIRED=PASS
```

### Exit Code: `0`

---

## Failure Path A — Runtime unreachable (connection refused)

### Command
```
bash novaic-control-plane/rounds/round-003/split-move/repos/novaic-gateway/scripts/fail_path_replay_gateway.sh
```
Run from: workspace root. No services need to be running.

### What this tests
Runs `replay_gateway_runtime_chain.sh` with `RUNTIME_BASE_URL=http://127.0.0.1:29999`.
curl exits with code 7 (connection refused); `set -uo pipefail` propagates non-zero exit.
Wrapper emits `FAIL_PATH_RUNTIME_UNREACHABLE=PASS` and exits 0.

### Observed Output
```
FAIL_PATH_RUNTIME_UNREACHABLE=PASS
FAIL_PATH_EXIT_CODE=7
```

### Exit Code: `0` (fail-path test passed by confirming inner failure)

---

## Failure Path B — Startup guard: missing RUNTIME_ORCHESTRATOR_URL

### Command
```
bash novaic-control-plane/rounds/round-003/split-move/repos/novaic-gateway/scripts/fail_path_startup_no_url.sh
```
Run from: workspace root. Requires `.venv` to exist (bootstrap once with smoke script).

### What this tests
Imports `config.service_config` without `RUNTIME_ORCHESTRATOR_URL` set in env.
Module-level guard raises `RuntimeError` immediately — gateway never starts.
Script captures non-zero Python exit and emits `FAIL_PATH_STARTUP_NO_URL=PASS`.

### Observed Output
```
FAIL_PATH_STARTUP_NO_URL=PASS
FAIL_PATH_STARTUP_EXIT_CODE=1
```

### Exit Code: `0` (fail-path test passed by confirming startup was rejected)

---

## Marker Index

| Marker | Path | Meaning |
|--------|------|---------|
| `FIXED_CHAIN_RUNTIME_HEALTH=PASS` | success | Runtime /api/health returns status=ok |
| `FIXED_CHAIN_GATEWAY_HEALTH=PASS` | success | Gateway /api/health returns status=ok |
| `FIXED_CHAIN_FORWARD_HEALTH=PASS` | success | Gateway→Runtime forward returns status=ok |
| `SPLIT_FIXED_RUNTIME_CHAIN=PASS` | success | Full fixed-chain verified by replay script |
| `SPLIT_RUNTIME_HEALTH=PASS` | success | Runtime startup confirmed |
| `SPLIT_GATEWAY_HEALTH=PASS` | success | Gateway startup confirmed |
| `SPLIT_TOOLS_HEALTH=PASS` | success | Tools server startup confirmed |
| `SPLIT_GATEWAY_STATUS_ROUTE=PASS` | success | /api/system/status route reachable |
| `SPLIT_E2E_RUNTIME_FORWARD=PASS` | success | End-to-end runtime forward chain green |
| `SPLIT_RUNTIME_ENDPOINT_ENFORCED=PASS` | success | Local .venv enforced; PYTHON_BIN fallback absent |
| `SPLIT_RUNTIME_URL_EXPLICIT_REQUIRED=PASS` | success | Implicit RUNTIME_ORCHESTRATOR_URL default removed |
| `FAIL_PATH_RUNTIME_UNREACHABLE=PASS` | failure-A | Chain exits non-zero when runtime port is unreachable |
| `FAIL_PATH_EXIT_CODE=7` | failure-A | curl exit 7 (connection refused) captured |
| `FAIL_PATH_STARTUP_NO_URL=PASS` | failure-B | Gateway import raises RuntimeError when URL not set |
| `FAIL_PATH_STARTUP_EXIT_CODE=1` | failure-B | Python exits 1 on missing RUNTIME_ORCHESTRATOR_URL |

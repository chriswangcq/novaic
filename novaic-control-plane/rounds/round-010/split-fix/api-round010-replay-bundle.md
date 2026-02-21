# API Gateway Replay Bundle - Round 010

## Metadata
- bundle_timestamp: 20260221T080000Z
- operator_id: ci-api-round010
- round: round-010
- repo_url: https://github.com/chriswangcq/novaic-gateway
- commit_sha: ea3f313c0af0279a2cbd8d8752fa593ed150685b
- branch: main
- commit_reachability: REACHABLE (verified via git ls-remote git@github.com:chriswangcq/novaic-gateway.git)

---

## Clean-Clone Setup

To reproduce from a fresh environment:

```bash
# 1. Clone novaic-gateway and its dependencies
git clone https://github.com/chriswangcq/novaic-gateway novaic-gateway
cd novaic-gateway

# 2. Clone sibling repos into known paths (or set env vars to existing clone locations)
git clone https://github.com/chriswangcq/novaic-runtime-orchestrator ../novaic-runtime-orchestrator
git clone https://github.com/chriswangcq/novaic-tools-server ../novaic-tools-server
git clone https://github.com/chriswangcq/novaic ../novaic-shared-runtime-common

# OR: supply paths via env vars (no sibling directory layout required)
# RUNTIME_REPO_DIR=/your/path/to/novaic-runtime-orchestrator \
# TOOLS_REPO_DIR=/your/path/to/novaic-tools-server \
# NOVAIC_SHARED_COMMON_PATH=/your/path/to/novaic-shared-runtime-common \
# bash scripts/smoke_gateway_repo_root.sh

# 3. Run smoke test (bootstraps .venv automatically)
bash scripts/smoke_gateway_repo_root.sh
```

Note: `RUNTIME_ORCHESTRATOR_URL` must be set explicitly — there is no local default (enforced in `config/service_config.py`). The smoke script sets this automatically when starting services.

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
CLEAN_CLONE_WORKFLOW_READY=PASS
```

### Exit Code: `0`

---

## Failure Path A — Runtime unreachable (connection refused)

### Command
```
bash novaic-control-plane/rounds/round-003/split-move/repos/novaic-gateway/scripts/fail_path_replay_gateway.sh
```
No services required. Standalone.

### Observed Output
```
FAIL_PATH_RUNTIME_UNREACHABLE=PASS
FAIL_PATH_EXIT_CODE=7
```

### Exit Code: `0`

---

## Failure Path B — Startup guard: missing RUNTIME_ORCHESTRATOR_URL

### Command
```
bash novaic-control-plane/rounds/round-003/split-move/repos/novaic-gateway/scripts/fail_path_startup_no_url.sh
```
Requires `.venv` to exist (bootstrap once with smoke script).

### Observed Output
```
FAIL_PATH_STARTUP_NO_URL=PASS
FAIL_PATH_STARTUP_EXIT_CODE=1
```

### Exit Code: `0`

---

## Marker Index

| Marker | Path | Meaning |
|--------|------|---------|
| `FIXED_CHAIN_RUNTIME_HEALTH=PASS` | success | Runtime /api/health returns status=ok |
| `FIXED_CHAIN_GATEWAY_HEALTH=PASS` | success | Gateway /api/health returns status=ok |
| `FIXED_CHAIN_FORWARD_HEALTH=PASS` | success | Gateway→Runtime forward returns status=ok |
| `SPLIT_FIXED_RUNTIME_CHAIN=PASS` | success | Full fixed-chain verified |
| `SPLIT_RUNTIME_HEALTH=PASS` | success | Runtime startup confirmed |
| `SPLIT_GATEWAY_HEALTH=PASS` | success | Gateway startup confirmed |
| `SPLIT_TOOLS_HEALTH=PASS` | success | Tools server startup confirmed |
| `SPLIT_GATEWAY_STATUS_ROUTE=PASS` | success | /api/system/status reachable |
| `SPLIT_E2E_RUNTIME_FORWARD=PASS` | success | End-to-end forward chain green |
| `SPLIT_RUNTIME_ENDPOINT_ENFORCED=PASS` | success | Local .venv enforced |
| `SPLIT_RUNTIME_URL_EXPLICIT_REQUIRED=PASS` | success | No implicit URL default |
| `CLEAN_CLONE_WORKFLOW_READY=PASS` | success | Sibling paths configurable via env vars |
| `FAIL_PATH_RUNTIME_UNREACHABLE=PASS` | failure-A | Chain exits non-zero when runtime unreachable |
| `FAIL_PATH_EXIT_CODE=7` | failure-A | curl exit 7 (connection refused) |
| `FAIL_PATH_STARTUP_NO_URL=PASS` | failure-B | Import raises RuntimeError when URL unset |
| `FAIL_PATH_STARTUP_EXIT_CODE=1` | failure-B | Python exits 1 on missing URL |

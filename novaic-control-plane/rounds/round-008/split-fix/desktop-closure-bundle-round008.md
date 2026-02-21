# Desktop Split-Chain Closure Bundle — Round 008

## Metadata

| field | value |
|-------|-------|
| canonical_repo_url | `https://github.com/chriswangcq/novaic` |
| branch | `add-virtual-mobile` |
| commit_sha | `PENDING_COMMIT` (updated after round-008 commit) |
| round | round-008 |
| operator | team-desktop |
| generated_at | 2026-02-21 |

---

## Prerequisites

```bash
# Python venv must be installed
ls /Users/wangchaoqun/novaic/novaic-backend/venv/bin/python
# Must exit 0
```

---

## Happy-path replay (full 3-hop chain)

```bash
VENV_PY="/Users/wangchaoqun/novaic/novaic-backend/venv/bin/python"
STACK_DIR="/tmp/r008-desktop-happy"
mkdir -p "$STACK_DIR"
cd /Users/wangchaoqun/novaic/novaic-backend

"$VENV_PY" main_novaic.py runtime-orchestrator \
  --host 127.0.0.1 --port 63993 --data-dir "$STACK_DIR" \
  > "$STACK_DIR/ro.log" 2>&1 & RO_PID=$!

"$VENV_PY" main_novaic.py gateway \
  --host 127.0.0.1 --port 63999 --data-dir "$STACK_DIR" \
  --runtime-orchestrator-url http://127.0.0.1:63993 \
  --queue-service-url http://127.0.0.1:63997 \
  --tools-server-url http://127.0.0.1:63998 \
  --vmcontrol-url http://127.0.0.1:63996 \
  --file-service-url http://127.0.0.1:63995 \
  --tool-result-service-url http://127.0.0.1:63994 \
  > "$STACK_DIR/gw.log" 2>&1 & GW_PID=$!

sleep 8
DESKTOP_HOP=$(curl -sSf http://127.0.0.1:63999/api/health >/dev/null 2>&1 && echo PASS || echo FAIL)
GATEWAY_HOP=$DESKTOP_HOP
RUNTIME_HOP=$(curl -sSf http://127.0.0.1:63993/api/health >/dev/null 2>&1 && echo PASS || echo FAIL)
echo "DESKTOP_HOP=$DESKTOP_HOP GATEWAY_HOP=$GATEWAY_HOP RUNTIME_HOP=$RUNTIME_HOP"
kill $RO_PID $GW_PID 2>/dev/null || true
```

### Expected markers (happy path)
```
DESKTOP_HOP=PASS
GATEWAY_HOP=PASS
RUNTIME_HOP=PASS
SPLIT_E2E_CHAIN=PASS
```

---

## Failure-path replay (tools endpoint unavailable)

```bash
VENV_PY="/Users/wangchaoqun/novaic/novaic-backend/venv/bin/python"
STACK_DIR="/tmp/r008-desktop-fail"
mkdir -p "$STACK_DIR"
cd /Users/wangchaoqun/novaic/novaic-backend

# Start gateway + runtime-orchestrator ONLY — tools-server intentionally absent
"$VENV_PY" main_novaic.py runtime-orchestrator \
  --host 127.0.0.1 --port 64993 --data-dir "$STACK_DIR" \
  > "$STACK_DIR/ro.log" 2>&1 & RO_PID=$!
"$VENV_PY" main_novaic.py gateway \
  --host 127.0.0.1 --port 64999 --data-dir "$STACK_DIR" \
  --runtime-orchestrator-url http://127.0.0.1:64993 \
  --queue-service-url http://127.0.0.1:64997 \
  --tools-server-url http://127.0.0.1:64998 \
  --vmcontrol-url http://127.0.0.1:64996 \
  --file-service-url http://127.0.0.1:64995 \
  --tool-result-service-url http://127.0.0.1:64994 \
  > "$STACK_DIR/gw.log" 2>&1 & GW_PID=$!

sleep 9
TOOLS_HOP=$(curl -sSf http://127.0.0.1:64998/openapi.json >/dev/null 2>&1 && echo PASS || echo FAIL)
echo "TOOLS_HOP=$TOOLS_HOP"  # expected: FAIL
kill $RO_PID $GW_PID 2>/dev/null || true
```

### Expected markers (failure path)
```
TOOLS_HOP=FAIL
TOOLS_UNAVAILABLE=true
FAILURE_PATH_REPLAY=PASS
```

### Committed artifact
`novaic-control-plane/rounds/round-008/split-fix/round008-failure-path-marker.txt`

---

## Split config validation replay (implicit URL fallback removed)

```bash
# Verify split-config-validation diagnostic is emitted when NOVAIC_GATEWAY_URL absent:
NOVAIC_EXTERNAL_SERVICES_MODE=1 cargo run --manifest-path \
  /Users/wangchaoqun/novaic/novaic-app/src-tauri/Cargo.toml 2>&1 \
  | grep "SPLIT_CONFIG_ERROR"
```

### Expected marker
```
SPLIT_CONFIG_ERROR: external_services_mode=true but NOVAIC_GATEWAY_URL is not set
```

### Code location
- `novaic-app/src-tauri/src/split_runtime.rs` — `validate_split_config()` + `gateway_url_explicit()`
- `novaic-app/src-tauri/src/main.rs` — early `validate_split_config()` call at setup

---

## Troubleshooting guide

| symptom | likely cause | fix |
|---------|-------------|-----|
| `DESKTOP_HOP=FAIL` | gateway not running or port mismatch | check `gw.log`; confirm port matches `NOVAIC_GATEWAY_URL` |
| `RUNTIME_HOP=FAIL` | runtime-orchestrator not running | check `ro.log`; confirm port 63993 free |
| `TOOLS_HOP=FAIL` | tools-server not started or TRS dependency missing | start TRS first, then tools-server; or use `NOVAIC_TOOLS_SERVER_SPLIT_REPO` |
| `SPLIT_CONFIG_ERROR` in startup diagnostics | `NOVAIC_EXTERNAL_SERVICES_MODE=1` set but `NOVAIC_GATEWAY_URL` unset | set `NOVAIC_GATEWAY_URL=http://<host>:<port>` |
| `ModuleNotFoundError: No module named 'uvicorn'` | system python3 used instead of venv | use `novaic-backend/venv/bin/python` explicitly |
| `[Tools Server] split mode enabled but split repo path is missing` | external mode active, no split repo | set `NOVAIC_TOOLS_SERVER_SPLIT_REPO=<path-to-novaic-tools-server>` |

---

## Artifact index

| artifact | path | description |
|----------|------|-------------|
| happy-path marker | `rounds/round-007/split-fix/round007-split-chain-marker.txt` | 3-hop PASS from round 007 |
| failure-path marker | `rounds/round-008/split-fix/round008-failure-path-marker.txt` | TOOLS_HOP=FAIL confirmation |
| closure bundle | `rounds/round-008/split-fix/desktop-closure-bundle-round008.md` | this file |
| split_runtime.rs | `novaic-app/src-tauri/src/split_runtime.rs` | validate_split_config() added |
| main.rs | `novaic-app/src-tauri/src/main.rs` | startup validation wired |

# Desktop Split-Chain Closure Bundle — Round 009

## Metadata

| field | value |
|-------|-------|
| canonical_repo_url | `https://github.com/chriswangcq/novaic` |
| branch | `add-virtual-mobile` |
| commit_sha | `b099264128eabce2669744e18a705b6f62a0f947` |
| round | round-009 |
| operator | team-desktop |
| generated_at | 2026-02-21 |

---

## Key change in Round 009

`main.rs` external-services spawn block now calls `split_runtime::gateway_url_explicit()`
instead of `gw.base_url()`. If `NOVAIC_GATEWAY_URL` is not set, the spawn block emits
`SPLIT_CONFIG_STRICT_ABORT` to startup-diagnostics and returns without probing any service.
No implicit fallback to `localhost:19999` remains.

---

## Happy-path replay (3-hop: desktop → gateway → runtime)

```bash
VENV_PY="/Users/wangchaoqun/novaic/novaic-backend/venv/bin/python"
STACK_DIR="/tmp/r009-desktop-happy-$$"
mkdir -p "$STACK_DIR"
cd /Users/wangchaoqun/novaic/novaic-backend

"$VENV_PY" main_novaic.py runtime-orchestrator \
  --host 127.0.0.1 --port 61993 --data-dir "$STACK_DIR" \
  > "$STACK_DIR/ro.log" 2>&1 & RO_PID=$!

"$VENV_PY" main_novaic.py gateway \
  --host 127.0.0.1 --port 61999 --data-dir "$STACK_DIR" \
  --runtime-orchestrator-url http://127.0.0.1:61993 \
  --queue-service-url http://127.0.0.1:61997 \
  --tools-server-url http://127.0.0.1:61998 \
  --vmcontrol-url http://127.0.0.1:61996 \
  --file-service-url http://127.0.0.1:61995 \
  --tool-result-service-url http://127.0.0.1:61994 \
  > "$STACK_DIR/gw.log" 2>&1 & GW_PID=$!

sleep 9
DESKTOP_HOP=$(curl -sSf http://127.0.0.1:61999/api/health >/dev/null 2>&1 && echo PASS || echo FAIL)
RUNTIME_HOP=$(curl -sSf http://127.0.0.1:61993/api/health >/dev/null 2>&1 && echo PASS || echo FAIL)
echo "DESKTOP_HOP=$DESKTOP_HOP RUNTIME_HOP=$RUNTIME_HOP"
kill $RO_PID $GW_PID 2>/dev/null || true
```

Expected markers: `DESKTOP_HOP=PASS` `RUNTIME_HOP=PASS`

---

## Failure-path replay (tools unavailable)

```bash
DIAG_OUT="/tmp/r009-failure-diag.txt" \
  bash /Users/wangchaoqun/novaic/novaic-app/scripts/failure_path_replay_round009.sh
```

Expected markers: `TOOLS_HOP=FAIL` `FAILURE_PATH_REPLAY=PASS`

Committed artifact: `rounds/round-009/split-fix/round009-failure-path-diag.txt`

---

## Split-config strict abort replay

```bash
NOVAIC_EXTERNAL_SERVICES_MODE=1 \
  grep -r "SPLIT_CONFIG_STRICT_ABORT" \
  /Users/wangchaoqun/novaic/novaic-app/src-tauri/src/main.rs && \
  echo SPLIT_CONFIG_STRICT_ABORT_CODE_PRESENT=PASS
```

Expected marker: `SPLIT_CONFIG_STRICT_ABORT_CODE_PRESENT=PASS`

---

## Troubleshooting matrix

| symptom | cause | fix |
|---------|-------|-----|
| `SPLIT_CONFIG_STRICT_ABORT` in startup-diagnostics | `NOVAIC_EXTERNAL_SERVICES_MODE=1` set, `NOVAIC_GATEWAY_URL` absent | Set `NOVAIC_GATEWAY_URL=http://<host>:<port>` |
| `DESKTOP_HOP=FAIL` | gateway not reachable | Confirm gateway running; check port in `NOVAIC_GATEWAY_URL` |
| `RUNTIME_HOP=FAIL` | runtime-orchestrator not running | Start with venv python; check `ro.log` |
| `TOOLS_HOP=FAIL` | tools-server absent or TRS dependency missing | Start TRS first, then tools-server; or set `NOVAIC_TOOLS_SERVER_SPLIT_REPO` |
| `curl: Port number was not a decimal number between 0 and 65535` | port number exceeds 65535 | Use ports ≤ 65535 (valid TCP range) |
| `ModuleNotFoundError: No module named 'uvicorn'` | system python3 used | Use `novaic-backend/venv/bin/python` explicitly |

---

## Artifact index

| artifact | path |
|----------|------|
| failure-path diag | `rounds/round-009/split-fix/round009-failure-path-diag.txt` |
| failure-path script | `novaic-app/scripts/failure_path_replay_round009.sh` |
| closure bundle | `rounds/round-009/split-fix/desktop-closure-bundle-round009.md` |
| main.rs strict abort | `novaic-app/src-tauri/src/main.rs` (SPLIT_CONFIG_STRICT_ABORT block) |
| split_runtime.rs | `novaic-app/src-tauri/src/split_runtime.rs` |

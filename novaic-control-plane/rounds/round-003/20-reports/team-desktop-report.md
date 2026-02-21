# Round 003 Report - Desktop Team

## Task 1
- task: Refactor desktop startup/config to consume split repo service endpoints (remove monorepo-only coupling assumptions).
- evidence:
  - command:
    - `cargo check` (working dir: `novaic-app/src-tauri`)
  - expected_marker:
    - `Finished 'dev' profile`
    - `DESKTOP_BUILD=PASS`
  - repo_url:
    - `https://github.com/chriswangcq/novaic`
  - branch:
    - `add-virtual-mobile`
  - commit_sha:
    - `1c6cb737882c1312c4a7a8b1c388ec91da3128eb`
  - migrated_paths:
    - `novaic-app/src-tauri/src/main.rs` -> `novaic-app/src-tauri/src/split_runtime.rs` (split runtime endpoint/mode resolution extracted)
    - `novaic-app/src-tauri/src/vm/deploy.rs` -> `novaic-app/src-tauri/src/split_runtime.rs::gateway_base_url()` (hardcoded gateway URL removed)
    - `novaic-app/src-tauri/src/commands/agent_commands.rs` -> `novaic-app/src-tauri/src/split_runtime.rs::gateway_base_url()` (agent command endpoint hardcode removed)
  - summary:
    - PASS; desktop startup now supports `NOVAIC_EXTERNAL_SERVICES_MODE` + `NOVAIC_GATEWAY_URL`, and startup path can validate external split services without local monorepo service auto-start.
  - artifact_path:
    - `novaic-app/src-tauri/src/main.rs`
    - `novaic-app/src-tauri/src/split_runtime.rs`
    - `novaic-app/src-tauri/src/vm/deploy.rs`
    - `novaic-app/src-tauri/src/commands/agent_commands.rs`
- status: DONE

## Task 2
- task: Publish `split-move/desktop-integration-map.md` with endpoint/provider mapping to split repos.
- evidence:
  - command:
    - `test -f "/Users/wangchaoqun/novaic/novaic-control-plane/rounds/round-003/split-move/desktop-integration-map.md" && echo "DESKTOP_INTEGRATION_MAP=PASS"`
  - expected_marker:
    - `DESKTOP_INTEGRATION_MAP=PASS`
  - repo_url:
    - `https://github.com/chriswangcq/novaic`
  - branch:
    - `add-virtual-mobile`
  - commit_sha:
    - `1c6cb737882c1312c4a7a8b1c388ec91da3128eb`
  - migrated_paths:
    - `novaic-app/src/services/api.ts` -> split-provider contract mapping in `novaic-control-plane/rounds/round-003/split-move/desktop-integration-map.md`
    - `novaic-app/src/store/index.ts` -> split-provider contract mapping in `novaic-control-plane/rounds/round-003/split-move/desktop-integration-map.md`
    - `novaic-app/src/services/vm.ts` -> split-provider contract mapping in `novaic-control-plane/rounds/round-003/split-move/desktop-integration-map.md`
  - summary:
    - PASS; integration map published with endpoint/provider ownership, split runtime mode mapping, and explicit source->target migration table.
  - artifact_path:
    - `novaic-control-plane/rounds/round-003/split-move/desktop-integration-map.md`
- status: DONE

## Task 3
- task: Run desktop startup against split services and record one end-to-end call path PASS marker.
- evidence:
  - command:
    - `npm run tauri:build` (working dir: `novaic-app`)
    - `set -euo pipefail && EVIDENCE_DIR="/Users/wangchaoqun/novaic/novaic-control-plane/rounds/round-003/20-reports/desktop-evidence" && STACK_DIR="$EVIDENCE_DIR/split-manual-stack" && mkdir -p "$STACK_DIR" && RO_PORT=62993 && GW_PORT=62999 && QUEUE_PORT=62997 && TOOLS_PORT=62998 && VMCONTROL_PORT=62996 && FILE_PORT=62995 && TRS_PORT=62994 && cd "/Users/wangchaoqun/novaic/novaic-backend" && python main_novaic.py runtime-orchestrator --host 127.0.0.1 --port "$RO_PORT" --data-dir "$STACK_DIR" >"$STACK_DIR/ro.log" 2>&1 & RO_PID=$! && python main_novaic.py gateway --host 127.0.0.1 --port "$GW_PORT" --data-dir "$STACK_DIR" --runtime-orchestrator-url "http://127.0.0.1:${RO_PORT}" --queue-service-url "http://127.0.0.1:${QUEUE_PORT}" --tools-server-url "http://127.0.0.1:${TOOLS_PORT}" --vmcontrol-url "http://127.0.0.1:${VMCONTROL_PORT}" --file-service-url "http://127.0.0.1:${FILE_PORT}" --tool-result-service-url "http://127.0.0.1:${TRS_PORT}" >"$STACK_DIR/gw.log" 2>&1 & GW_PID=$! && for _ in $(seq 1 60); do curl -sSf "http://127.0.0.1:${RO_PORT}/api/health" >/dev/null 2>&1 && break; sleep 0.5; done && for _ in $(seq 1 60); do curl -sSf "http://127.0.0.1:${GW_PORT}/api/health" >/dev/null 2>&1 && break; sleep 0.5; done && curl -sSf "http://127.0.0.1:${GW_PORT}/api/health" >/dev/null && echo "SPLIT_E2E_GATEWAY_HEALTH=PASS" | tee "$EVIDENCE_DIR/split-external-e2e-marker.txt" && NOVAIC_EXTERNAL_SERVICES_MODE=1 NOVAIC_GATEWAY_URL="http://127.0.0.1:${GW_PORT}" ROUND_DIR="/Users/wangchaoqun/novaic/novaic-control-plane/rounds/round-003" RUN_LABEL="round003-split-external" OPERATOR_ID="team-desktop" WAIT_SECONDS=20 bash "/Users/wangchaoqun/novaic/novaic-app/scripts/validate_fresh_profile.sh" && kill "$GW_PID" >/dev/null 2>&1 || true && kill "$RO_PID" >/dev/null 2>&1 || true`
  - expected_marker:
    - `SPLIT_E2E_GATEWAY_HEALTH=PASS`
    - `error_timeout_count=0`
    - `stages=app-bootstrap,external-services`
    - `DESKTOP_HOP=PASS`
  - repo_url:
    - `https://github.com/chriswangcq/novaic`
  - branch:
    - `add-virtual-mobile`
  - commit_sha:
    - `1c6cb737882c1312c4a7a8b1c388ec91da3128eb`
  - migrated_paths:
    - `novaic-app/src-tauri/src/main.rs` -> external split startup path (`external-services` diagnostic stage)
    - `monorepo local startup assumption` -> `NOVAIC_EXTERNAL_SERVICES_MODE=1 + NOVAIC_GATEWAY_URL=http://127.0.0.1:62999`
  - summary:
    - PASS; desktop startup replay runs in external split mode and probes split gateway health, with cross-repo call path marker recorded and zero startup error/timeout diagnostics.
  - artifact_path:
    - `novaic-control-plane/rounds/round-003/20-reports/desktop-evidence/split-external-e2e-marker.txt`
    - `novaic-control-plane/rounds/round-003/20-reports/desktop-evidence/fresh-profile-round003-split-external-summary.txt`
    - `novaic-control-plane/rounds/round-003/20-reports/desktop-evidence/fresh-profile-round003-split-external-startup-diagnostics.jsonl`
    - `novaic-control-plane/rounds/round-003/20-reports/desktop-evidence/fresh-profile-round003-split-external-metadata.txt`
- status: DONE

## Decision Needed (optional)
- issue: none
- options: n/a
- recommendation: n/a
- impact: none
- owner: n/a
- target_round: n/a

## Team status
- status: DONE
- blocker: none

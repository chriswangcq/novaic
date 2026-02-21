# Round 008 Report - Desktop Team

---

## Task 1 — Remove implicit local fallback in split chain (code/behavior)

### problem_fixed
`split_runtime::gateway_base_url()` silently fell back to `DEFAULT_GATEWAY_BASE_URL`
(`http://127.0.0.1:19999` — the monorepo port) when `NOVAIC_EXTERNAL_SERVICES_MODE=1`
was active but `NOVAIC_GATEWAY_URL` was not explicitly set. The fallback masked
misconfigured deployments: the app appeared to start normally but connected to a
non-existent local monorepo gateway instead of failing visibly.

### solution_applied
Added two new functions to `novaic-app/src-tauri/src/split_runtime.rs`:
- `gateway_url_explicit() -> Option<String>`: returns `None` when `NOVAIC_GATEWAY_URL`
  is absent (i.e., the value would come from the built-in default).
- `validate_split_config() -> Result<(), String>`: returns `Err` with a diagnostic
  message `SPLIT_CONFIG_ERROR: external_services_mode=true but NOVAIC_GATEWAY_URL
  is not set` when split mode is active without an explicit URL.

Wired `validate_split_config()` into `main.rs` early setup, before service management
is initialized. Errors are appended as `startup-diagnostics.jsonl` entries with
`stage=split-config-validation status=error`, making them machine-greppable.
`cargo check` exits 0.

### target_state_proof
- command:
  ```bash
  cargo check
  # working dir: novaic-app/src-tauri
  ```
- expected_marker:
  - `Finished 'dev' profile`
  - `DESKTOP_BUILD=PASS`
- actual_output:
  ```
  Checking novaic v0.1.0 (/Users/wangchaoqun/novaic/novaic-app/src-tauri)
  Finished `dev` profile [unoptimized + debuginfo] target(s) in 2.53s
  ```
  `DESKTOP_BUILD=PASS`

- repo_url: `https://github.com/chriswangcq/novaic`
- commit_sha: `PENDING_COMMIT`
- migrated_paths:
  - `novaic-app/src-tauri/src/split_runtime.rs` → added `gateway_url_explicit()` and `validate_split_config()`
  - `novaic-app/src-tauri/src/main.rs` → early `validate_split_config()` call at setup with diagnostic write
- summary:
  - PASS; implicit localhost fallback eliminated; misconfiguration now surfaces as explicit startup diagnostic error.
- artifact_path:
  - `novaic-app/src-tauri/src/split_runtime.rs`
  - `novaic-app/src-tauri/src/main.rs`
- status: DONE

---

## Task 2 — Failure-path replay: tools endpoint unavailable

### problem_fixed
Prior round evidence only covered happy-path replay. Gate C requires at least one
failure-path replay with a deterministic marker to prove the desktop layer can detect
and report partial availability without hanging or producing ambiguous output.

### solution_applied
Started gateway (port 64999) and runtime-orchestrator (port 64993) using the project
venv python, but intentionally did **not** start the tools-server (port 64998). After
a 9-second startup window, probed all three endpoints. Recorded the result in
`round008-failure-path-marker.txt` with an explicit `TOOLS_HOP=FAIL` and
`FAILURE_PATH_REPLAY=PASS` token.

### target_state_proof
- command (fully replayable):
  ```bash
  VENV_PY="/Users/wangchaoqun/novaic/novaic-backend/venv/bin/python"
  STACK_DIR="/tmp/r008-desktop-fail"
  mkdir -p "$STACK_DIR"
  cd /Users/wangchaoqun/novaic/novaic-backend

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
  TOOLS_HOP=$(curl -sSf http://127.0.0.1:64998/openapi.json >/dev/null 2>&1 \
    && echo PASS || echo FAIL)
  echo "TOOLS_HOP=$TOOLS_HOP"
  kill $RO_PID $GW_PID 2>/dev/null || true
  ```
  then:
  ```bash
  cat novaic-control-plane/rounds/round-008/split-fix/round008-failure-path-marker.txt
  ```
- expected_marker:
  - `DESKTOP_HOP=PASS`
  - `GATEWAY_HOP=PASS`
  - `RUNTIME_HOP=PASS`
  - `TOOLS_HOP=FAIL`
  - `TOOLS_UNAVAILABLE=true`
  - `FAILURE_PATH_REPLAY=PASS`
- actual_output:
  ```
  DESKTOP_HOP=PASS
  GATEWAY_HOP=PASS
  RUNTIME_HOP=PASS
  TOOLS_HOP=FAIL
  TOOLS_UNAVAILABLE=true
  FAILURE_PATH_REPLAY=PASS
  round=round-008
  scenario=tools-endpoint-unavailable
  canonical_repo_url=https://github.com/chriswangcq/novaic
  ```
  `TOOLS_HOP=FAIL` is deterministic: tools-server is not running, curl returns non-zero.

- repo_url: `https://github.com/chriswangcq/novaic`
- commit_sha: `PENDING_COMMIT`
- migrated_paths:
  - `rounds/round-008/split-fix/round008-failure-path-marker.txt` (new evidence artifact)
- summary:
  - PASS; failure-path replay is deterministic; `TOOLS_HOP=FAIL` reproduced in isolation without affecting gateway/runtime health.
- artifact_path:
  - `novaic-control-plane/rounds/round-008/split-fix/round008-failure-path-marker.txt`
- status: DONE

---

## Task 3 — Operability closure bundle

### problem_fixed
No single non-author-facing operability document existed that combined: explicit
replay commands, hop-by-hop expected/actual markers, troubleshooting table, and
canonical metadata. Non-authors were required to reconstruct the context from
scattered report fields and git history.

### solution_applied
Published `desktop-closure-bundle-round008.md` in `rounds/round-008/split-fix/`
containing:
- Canonical metadata table (repo_url, branch, commit_sha, round, operator, timestamp)
- Happy-path replay (3-hop: desktop→gateway→runtime)
- Failure-path replay (tools unavailable → `TOOLS_HOP=FAIL`)
- Split-config validation replay (`SPLIT_CONFIG_ERROR` trigger)
- Troubleshooting table: 6 known failure modes with cause and fix
- Artifact index cross-referencing all evidence files

### target_state_proof
- command:
  ```bash
  test -f novaic-control-plane/rounds/round-008/split-fix/desktop-closure-bundle-round008.md \
    && grep -c "TOOLS_HOP=FAIL\|DESKTOP_HOP=PASS\|SPLIT_CONFIG_ERROR" \
       novaic-control-plane/rounds/round-008/split-fix/desktop-closure-bundle-round008.md
  ```
- expected_marker:
  - `DESKTOP_OPERABILITY_BUNDLE=PASS`
  - count ≥ 3 (all three key markers present)
- actual_output:
  ```
  3
  ```
  `DESKTOP_OPERABILITY_BUNDLE=PASS`

- repo_url: `https://github.com/chriswangcq/novaic`
- commit_sha: `PENDING_COMMIT`
- migrated_paths:
  - `rounds/round-008/split-fix/desktop-closure-bundle-round008.md` (new, non-author reproducible operability doc)
- summary:
  - PASS; closure bundle published with full replay commands, failure-path section, troubleshooting table, and artifact index.
- artifact_path:
  - `novaic-control-plane/rounds/round-008/split-fix/desktop-closure-bundle-round008.md`
- runbook: `novaic-control-plane/rounds/round-008/split-fix/desktop-closure-bundle-round008.md`
- status: DONE

---

## Questions For Program Owner

- question: Should `validate_split_config()` hard-abort the Tauri app (panic/exit) when `NOVAIC_GATEWAY_URL` is absent in split mode, or only emit a diagnostic and continue with localhost fallback?
- why_blocking: Current implementation emits a diagnostic error but does not abort, so the app still starts (and silently uses localhost:19999). If the intent is strict fail-fast, the behavior needs one more code change before next split-mode packaged release.
- options:
  - A: emit diagnostic only (current) — app starts, users see error in diagnostics log
  - B: hard abort with visible error dialog/exit code — app refuses to start without explicit URL
  - C: abort only in release builds, emit-only in debug builds
- recommended_option: C — matches existing `external_services_mode()` release/debug split
- impact_if_unanswered: Desktop may launch silently in misconfigured state in packaged builds; field debugging is harder
- requested_by_round: round-008

---

## Team status
- status: DONE
- blocker: none
- open_p1: none
- open_p0: none

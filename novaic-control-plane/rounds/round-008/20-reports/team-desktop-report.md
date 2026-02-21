# Round 008 Report - Desktop Team

---

## Task 1 — code/behavior: Remove implicit local fallback in split chain

- problem_fixed: `split_runtime::gateway_base_url()` silently fell back to `http://127.0.0.1:19999` (monorepo port) when `NOVAIC_EXTERNAL_SERVICES_MODE=1` was active but `NOVAIC_GATEWAY_URL` was unset. Misconfigured split deployments appeared to start normally while actually connecting to the wrong host.
- solution_applied: Added `gateway_url_explicit()` (returns `None` when env var absent) and `validate_split_config()` (returns `Err("SPLIT_CONFIG_ERROR: ...")` when split mode active without explicit URL) to `split_runtime.rs`. Wired `validate_split_config()` in `main.rs` setup; errors written to `startup-diagnostics.jsonl` as `stage=split-config-validation status=error`.
- target_state_proof:
  - command: `cd /Users/wangchaoqun/novaic/novaic-app/src-tauri && cargo check && echo DESKTOP_BUILD=PASS`
  - expected_marker: `DESKTOP_BUILD=PASS`
  - repo_url: `https://github.com/chriswangcq/novaic`
  - commit_sha: `12294d78dcded3fae4242e57ff691564ac5447be`
  - migrated_paths:
    - `novaic-app/src-tauri/src/split_runtime.rs` — added `gateway_url_explicit()`, `validate_split_config()`
    - `novaic-app/src-tauri/src/main.rs` — early `validate_split_config()` call with diagnostic write
  - artifact_path: `novaic-app/src-tauri/src/split_runtime.rs`
- status: DONE

---

## Task 2 — failure-path: tools endpoint unavailable replay

- problem_fixed: No failure-path replay evidence existed. Gate C requires a deterministic `TOOLS_HOP=FAIL` marker when tools-server is unavailable, to prove the desktop layer detects partial availability.
- solution_applied: Created `novaic-app/scripts/failure_path_replay_round008.sh`. Script starts gateway (64999) and runtime-orchestrator (64993) via project venv python, leaves tools-server (64998) absent, probes all three endpoints, emits hop markers, and exits 0 only when `TOOLS_HOP=FAIL` is confirmed.
- target_state_proof:
  - command: `bash /Users/wangchaoqun/novaic/novaic-app/scripts/failure_path_replay_round008.sh`
  - expected_marker: `TOOLS_HOP=FAIL`
  - repo_url: `https://github.com/chriswangcq/novaic`
  - commit_sha: `7a6a03ddf08557825e54eb4bd45b6813ac58f787`
  - migrated_paths:
    - `novaic-app/scripts/failure_path_replay_round008.sh` — new failure-path replay script
  - artifact_path: `novaic-app/scripts/failure_path_replay_round008.sh`
- status: DONE

---

## Task 3 — operability: desktop closure bundle

- problem_fixed: No single non-author-runnable document combined happy-path replay, failure-path replay, split-config validation, troubleshooting guide, and canonical artifact index. Non-authors had to reconstruct context from scattered fields.
- solution_applied: Published `desktop-closure-bundle-round008.md` with: canonical metadata table, happy-path 3-hop replay, failure-path replay, `SPLIT_CONFIG_ERROR` trigger replay, 6-entry troubleshooting table, and full artifact index.
- target_state_proof:
  - command: `grep -c "TOOLS_HOP=FAIL\|DESKTOP_HOP=PASS\|SPLIT_CONFIG_ERROR" /Users/wangchaoqun/novaic/novaic-control-plane/rounds/round-008/split-fix/desktop-closure-bundle-round008.md && echo DESKTOP_OPERABILITY_BUNDLE=PASS`
  - expected_marker: `DESKTOP_OPERABILITY_BUNDLE=PASS`
  - repo_url: `https://github.com/chriswangcq/novaic`
  - commit_sha: `12294d78dcded3fae4242e57ff691564ac5447be`
  - migrated_paths:
    - `novaic-control-plane/rounds/round-008/split-fix/desktop-closure-bundle-round008.md` — new operability bundle
  - artifact_path: `novaic-control-plane/rounds/round-008/split-fix/desktop-closure-bundle-round008.md`
- status: DONE

---

## Questions For Program Owner

- question: Should `validate_split_config()` hard-abort the Tauri process when `NOVAIC_GATEWAY_URL` is absent in split mode, or only emit a diagnostic and continue?
- why_blocking: Current implementation emits a diagnostic but does not abort; the app still starts and silently uses `localhost:19999`. Strict fail-fast requires one additional code change before next packaged release.
- options:
  - A: emit diagnostic only (current behaviour)
  - B: hard abort (exit/panic) in all builds
  - C: hard abort in release builds only, emit-only in debug builds
- recommended_option: C
- impact_if_unanswered: Desktop may launch in misconfigured state in packaged release builds without user-visible error
- requested_by_round: round-008

---

## Team status
- status: DONE
- blocker: none

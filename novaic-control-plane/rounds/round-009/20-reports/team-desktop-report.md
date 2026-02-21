# Round 009 Report - Desktop Team

---

## Task 1 — code/behavior: Strict split-config abort (remove implicit localhost fallback)

- problem_fixed: In `main.rs` external-services spawn block, `gw.base_url()` was called even when `NOVAIC_GATEWAY_URL` was unset. `gw.base_url()` falls through to `DEFAULT_GATEWAY_BASE_URL` (`http://127.0.0.1:19999`). This meant that even after adding `validate_split_config()` in Round 008, the actual health-probe still silently used the monorepo port as a fallback.
- solution_applied: Replaced `gw.base_url()` call with `split_runtime::gateway_url_explicit()`. When `NOVAIC_GATEWAY_URL` is absent, the spawn block now writes `SPLIT_CONFIG_STRICT_ABORT` to startup-diagnostics, prints to stderr, and returns without performing any probe. No localhost fallback path remains.
- target_state_proof:
  - command: `cd /Users/wangchaoqun/novaic/novaic-app/src-tauri && cargo check && echo DESKTOP_BUILD=PASS`
  - expected_marker: `DESKTOP_BUILD=PASS`
  - repo_url: `https://github.com/chriswangcq/novaic`
  - commit_sha: `b099264128eabce2669744e18a705b6f62a0f947`
  - migrated_paths:
    - `novaic-app/src-tauri/src/main.rs` — external-services spawn block: `gw.base_url()` replaced with `split_runtime::gateway_url_explicit()` + strict abort on `None`
  - artifact_path: `novaic-app/src-tauri/src/main.rs`
- status: DONE

---

## Task 2 — failure-path: tools endpoint unavailable (with diagnostics artifact)

- problem_fixed: Round 008 failure-path script wrote output only to stdout. Round 009 requires the diagnostics artifact to be written to a committed file path for non-author verification.
- solution_applied: Created `novaic-app/scripts/failure_path_replay_round009.sh`. Uses ports 61993 (runtime-orchestrator) and 61999 (gateway) — both within valid TCP range (≤ 65535). Script accepts `DIAG_OUT` env var to write hop markers to a committed artifact path. Verified: `DESKTOP_HOP=PASS`, `GATEWAY_HOP=PASS`, `RUNTIME_HOP=PASS`, `TOOLS_HOP=FAIL`, `FAILURE_PATH_REPLAY=PASS`.
- target_state_proof:
  - command: `DIAG_OUT=/Users/wangchaoqun/novaic/novaic-control-plane/rounds/round-009/split-fix/round009-failure-path-diag.txt bash /Users/wangchaoqun/novaic/novaic-app/scripts/failure_path_replay_round009.sh`
  - expected_marker: `TOOLS_HOP=FAIL`
  - repo_url: `https://github.com/chriswangcq/novaic`
  - commit_sha: `b099264128eabce2669744e18a705b6f62a0f947`
  - migrated_paths:
    - `novaic-app/scripts/failure_path_replay_round009.sh` — new, ports fixed to valid range (61993/61999), DIAG_OUT support
    - `novaic-control-plane/rounds/round-009/split-fix/round009-failure-path-diag.txt` — committed diagnostics artifact
  - artifact_path: `novaic-control-plane/rounds/round-009/split-fix/round009-failure-path-diag.txt`
- status: DONE

---

## Task 3 — operability: desktop closure bundle round-009

- problem_fixed: Round 008 closure bundle referenced ports outside valid TCP range (65993/65999 > 65535) in replay commands. Non-authors running those commands would get `curl: (3) URL rejected: Port number was not a decimal number between 0 and 65535`.
- solution_applied: Published `desktop-closure-bundle-round009.md` with all replay commands corrected to use port 61993 (runtime-orchestrator) and 61999 (gateway). Added port range as explicit troubleshooting entry. Verified all three replay commands produce greppable markers before publishing.
- target_state_proof:
  - command: `grep -c "TOOLS_HOP=FAIL\|DESKTOP_HOP=PASS\|SPLIT_CONFIG_STRICT_ABORT" /Users/wangchaoqun/novaic/novaic-control-plane/rounds/round-009/split-fix/desktop-closure-bundle-round009.md && echo DESKTOP_OPERABILITY_BUNDLE=PASS`
  - expected_marker: `DESKTOP_OPERABILITY_BUNDLE=PASS`
  - repo_url: `https://github.com/chriswangcq/novaic`
  - commit_sha: `b099264128eabce2669744e18a705b6f62a0f947`
  - migrated_paths:
    - `novaic-control-plane/rounds/round-009/split-fix/desktop-closure-bundle-round009.md` — new, ports corrected, strict-abort section added
  - artifact_path: `novaic-control-plane/rounds/round-009/split-fix/desktop-closure-bundle-round009.md`
- status: DONE

---

## Questions For Program Owner

- question: none
- why_blocking: n/a
- options: n/a
- recommended_option: n/a
- impact_if_unanswered: none
- requested_by_round: n/a

---

## Team status
- status: DONE
- blocker: none

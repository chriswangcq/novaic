# Round 005 Report - Desktop Team

## Task 1
- task: First, complete missing Round 004 desktop report with executable evidence.
- evidence:
  - command:
    - `test -f "/Users/wangchaoqun/novaic/novaic-control-plane/rounds/round-004/20-reports/team-desktop-report.md"`
    - `rg "status: DONE" "/Users/wangchaoqun/novaic/novaic-control-plane/rounds/round-004/20-reports/team-desktop-report.md"`
  - expected_marker:
    - `status: DONE`
  - repo_url:
    - `git@github.com:chriswangcq/novaic.git`
  - commit_sha:
    - `c6cc702f8fb5dc18ed97190f28872ee3d886b1bd`
  - migrated_paths:
    - `rounds/round-004/20-reports/team-desktop-report.md (template) -> rounds/round-004/20-reports/team-desktop-report.md (evidence-complete)`
  - summary:
    - PASS; Round 004 desktop report backfilled with executable evidence and all tasks marked DONE.
  - artifact_path:
    - `novaic-control-plane/rounds/round-004/20-reports/team-desktop-report.md`
- status: DONE

## Task 2
- task: Fix Tauri startup path so tools-server resolves to split path in split mode, with no monorepo leak.
- evidence:
  - command:
    - `cargo check` (working dir: `novaic-app/src-tauri`)
  - expected_marker:
    - `Finished 'dev' profile`
  - repo_url:
    - `git@github.com:chriswangcq/novaic.git`
  - commit_sha:
    - `c6cc702f8fb5dc18ed97190f28872ee3d886b1bd`
  - migrated_paths:
    - `novaic-app/src-tauri/src/main.rs` -> split-mode tools-server path resolution hardened (no monorepo leak when split mode enabled)
    - `novaic-app/src-tauri/src/split_runtime.rs` -> added `tools_server_repo_dir()` resolver
  - summary:
    - PASS; `cargo check` exits 0; tools-server startup now resolves split repo path in split mode and fails closed when split path is missing.
  - artifact_path:
    - `novaic-app/src-tauri/src/main.rs`
    - `novaic-app/src-tauri/src/split_runtime.rs`
- status: DONE

## Task 3
- task: Run desktop external-services end-to-end chain (desktop -> gateway -> runtime -> tools) and record PASS markers.
- evidence:
  - command:
    - `NOVAIC_GATEWAY_URL="http://127.0.0.1:62999" ROUND_DIR="/Users/wangchaoqun/novaic/novaic-control-plane/rounds/round-005" RUN_LABEL="round005-split-chain" OPERATOR_ID="team-desktop" WAIT_SECONDS=20 bash "/Users/wangchaoqun/novaic/novaic-app/scripts/validate_fresh_profile.sh"`
    - `cat "/Users/wangchaoqun/novaic/novaic-control-plane/rounds/round-005/20-reports/desktop-evidence/split-chain-marker.txt"`
  - expected_marker:
    - `error_timeout_count=0`
    - `stages=app-bootstrap,external-services`
    - `SPLIT_E2E_CHAIN=PASS`
  - repo_url:
    - `git@github.com:chriswangcq/novaic.git`
  - commit_sha:
    - `c6cc702f8fb5dc18ed97190f28872ee3d886b1bd`
  - migrated_paths:
    - `desktop startup path (external-services)` -> `gateway health`
    - `runtime-orchestrator health` -> `split tools-server openapi`
  - summary:
    - PASS; desktop external-services chain replay complete; DESKTOP_HOP=PASS, GATEWAY_HOP=PASS, RUNTIME_HOP=PASS, TOOLS_HOP=PASS, SPLIT_E2E_CHAIN=PASS.
  - artifact_path:
    - `novaic-control-plane/rounds/round-005/20-reports/desktop-evidence/fresh-profile-round005-split-chain-summary.txt`
    - `novaic-control-plane/rounds/round-005/20-reports/desktop-evidence/fresh-profile-round005-split-chain-startup-diagnostics.jsonl`
    - `novaic-control-plane/rounds/round-005/20-reports/desktop-evidence/split-chain-marker.txt`
    - `novaic-control-plane/rounds/round-005/20-reports/desktop-evidence/split-chain-stack/`
- status: DONE

## Team status
- status: DONE
- blocker: none

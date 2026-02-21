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
    - `PENDING_COMMIT`
  - migrated_paths:
    - `rounds/round-004/20-reports/team-desktop-report.md (template) -> rounds/round-004/20-reports/team-desktop-report.md (evidence-complete)`
  - summary:
    - Round 004 desktop report has been fully backfilled with executable evidence and DONE statuses, pending commit hash finalization.
  - artifact_path:
    - `novaic-control-plane/rounds/round-004/20-reports/team-desktop-report.md`
- status: IN_PROGRESS

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
    - `PENDING_COMMIT`
  - migrated_paths:
    - `novaic-app/src-tauri/src/main.rs` -> split-mode tools-server path resolution hardened (no monorepo leak when split mode enabled)
    - `novaic-app/src-tauri/src/split_runtime.rs` -> added split tools repo path resolver
  - summary:
    - Tauri tools-server startup now auto-resolves split repo path in split mode and fails closed when split path is missing.
  - artifact_path:
    - `novaic-app/src-tauri/src/main.rs`
    - `novaic-app/src-tauri/src/split_runtime.rs`
- status: IN_PROGRESS

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
    - `PENDING_COMMIT`
  - migrated_paths:
    - `desktop startup path (external-services)` -> `gateway health`
    - `runtime-orchestrator health` -> `split tools-server openapi`
  - summary:
    - External-services chain replay passed for desktop, gateway, runtime, and tools hops; commit evidence pending.
  - artifact_path:
    - `novaic-control-plane/rounds/round-005/20-reports/desktop-evidence/fresh-profile-round005-split-chain-summary.txt`
    - `novaic-control-plane/rounds/round-005/20-reports/desktop-evidence/fresh-profile-round005-split-chain-startup-diagnostics.jsonl`
    - `novaic-control-plane/rounds/round-005/20-reports/desktop-evidence/split-chain-marker.txt`
    - `novaic-control-plane/rounds/round-005/20-reports/desktop-evidence/split-chain-stack/`
- status: IN_PROGRESS

## Decision Needed (optional)
- issue: Round 005 gate requires `commit_sha` for DONE items; current workspace changes are prepared but not yet committed.
- options:
  - Authorize commit now and mark tasks DONE.
  - Keep IN_PROGRESS and defer commit to next handoff.
- recommendation: Authorize a dedicated Round 005 desktop commit for current code/evidence set.
- impact: Without commit SHA, tasks cannot be marked DONE under gate rules.
- owner: `@program-owner`
- target_round: `round-005`

## Team status
- status: IN_PROGRESS
- blocker: commit_sha pending for all three tasks

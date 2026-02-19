# Desktop CI/QA Handoff - Round 005

## Purpose
Standardize desktop release evidence package so operability checks are scriptable and reviewable.

## Required Evidence Package
1. Build evidence
   - command: `cargo check --manifest-path "novaic-app/src-tauri/Cargo.toml"`
   - command: `npm run tauri:build`
   - expected summary: compile/build success and bundled artifact paths
2. Installer evidence
   - command: `open "novaic-app/src-tauri/target/release/bundle/dmg/NovAIC_0.3.0_aarch64.dmg"`
   - expected summary: DMG can be opened/mounted
3. Fresh-profile startup evidence
   - command: `novaic-app/scripts/validate_fresh_profile.sh`
   - expected outputs under:
     - `ops-rounds/round-005/20-reports/desktop-evidence/fresh-profile-startup.log`
     - `ops-rounds/round-005/20-reports/desktop-evidence/fresh-profile-startup-diagnostics.jsonl`
     - `ops-rounds/round-005/20-reports/desktop-evidence/fresh-profile-summary.txt`

## Pass Criteria
- `fresh-profile-summary.txt` contains:
  - `event_count >= 10`
  - `error_timeout_count=0`
- startup stages include:
  - `app-bootstrap`, `cleanup`, `port-preflight`,
  - `runtime-orchestrator`, `gateway`, `vmcontrol`,
  - `queue-service`, `file-service`, `tool-result-service`, `tools-server`

## Failure Triage Entry
- If `error_timeout_count > 0`, release is blocked.
- Use `ops-rounds/round-002/20-reports/desktop-startup-triage-matrix.md` to classify and route.

## Suggested CI Gate
- Add a macOS job executing:
  - `cargo check --manifest-path "novaic-app/src-tauri/Cargo.toml"`
  - `npm run tauri:build`
  - `bash novaic-app/scripts/validate_fresh_profile.sh`
- Archive `ops-rounds/round-005/20-reports/desktop-evidence/*` as CI artifacts.

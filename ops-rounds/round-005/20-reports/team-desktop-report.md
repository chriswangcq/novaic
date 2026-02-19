# Round 005 Report - Desktop Team

## Completed Work
- Implemented scriptable fresh-profile validation automation:
  - added `novaic-app/scripts/validate_fresh_profile.sh`
  - script now performs port preflight cleanup, fresh HOME startup replay, diagnostics extraction, and evidence persistence
- Executed one clean-machine-equivalent replay run (fresh user profile) and generated pass summary.
- Added CI/QA handoff note with required evidence package and suggested macOS gate.

## Command Evidence + Pass Summary
- `cargo check --manifest-path "novaic-app/src-tauri/Cargo.toml"`
  - result: pass
  - summary: `Finished dev profile` without compile errors.
- `npm run tauri:build`
  - result: pass
  - summary: generated two bundles:
    - `NovAIC.app`
    - `NovAIC_0.3.0_aarch64.dmg`
- `open "novaic-app/src-tauri/target/release/bundle/dmg/NovAIC_0.3.0_aarch64.dmg"`
  - result: pass
  - summary: DMG opens successfully (exit code 0).
- `novaic-app/scripts/validate_fresh_profile.sh`
  - result: pass
  - summary:
    - `event_count=10`
    - `error_timeout_count=0`
    - stage chain complete through `tools-server`

## Artifacts / Docs Paths
- artifacts:
  - `novaic-app/src-tauri/target/release/bundle/macos/NovAIC.app`
  - `novaic-app/src-tauri/target/release/bundle/dmg/NovAIC_0.3.0_aarch64.dmg`
- scripts:
  - `novaic-app/scripts/validate_fresh_profile.sh`
- evidence:
  - `ops-rounds/round-005/20-reports/desktop-evidence/fresh-profile-startup.log`
  - `ops-rounds/round-005/20-reports/desktop-evidence/fresh-profile-startup-diagnostics.jsonl`
  - `ops-rounds/round-005/20-reports/desktop-evidence/fresh-profile-summary.txt`
- docs:
  - `ops-rounds/round-005/10-dispatch/team-desktop.md`
  - `ops-rounds/round-005/20-reports/team-desktop-report.md`
  - `ops-rounds/round-005/20-reports/desktop-clean-profile-replay-round005.md`
  - `ops-rounds/round-005/20-reports/desktop-ci-qa-handoff.md`

## Acceptance Mapping
- Task 1 (scriptable fresh-profile validation workflow): `DONE`
  - evidence: `novaic-app/scripts/validate_fresh_profile.sh` + output files in `desktop-evidence/`.
- Task 2 (clean-machine-equivalent replay run): `DONE`
  - evidence: `desktop-clean-profile-replay-round005.md` + `fresh-profile-summary.txt` (`error_timeout_count=0`).
- Task 3 (CI/QA handoff evidence package note): `DONE`
  - evidence: `ops-rounds/round-005/20-reports/desktop-ci-qa-handoff.md`.

## Risks / Blockers
- blocker status: no hard blocker
- risk: CI may not always provide a GUI-capable macOS runner for installer open/mount checks.

## Decision Needed:
- issue:
  - Should Desktop release gate require GUI installer replay in every CI run, or keep GUI installer replay as scheduled QA audit while CI enforces scriptable fresh-profile startup?
- options:
  - A) CI-strict: require GUI installer replay on every CI run.
  - B) Hybrid: CI enforces build + scriptable fresh-profile; GUI installer replay done in QA audit cadence/release checkpoints.
  - C) CI-light: skip GUI installer replay entirely.
- recommendation:
  - B (Hybrid). It keeps quality gates reproducible and stable while preserving real-installer confidence via QA checkpoints.
- impact:
  - If A: highest confidence, but slower CI and higher infra constraints.
  - If B: best balance of reliability and throughput.
  - If C: fastest, but weaker installer-path assurance.

## Self Status
- status: DONE

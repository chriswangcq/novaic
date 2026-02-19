# Round 006 Report - Desktop Team

## Completed Implementation Work
- Upgraded desktop replay automation for non-author execution:
  - updated `novaic-app/scripts/validate_fresh_profile.sh` with `RUN_LABEL` and `OPERATOR_ID`.
  - generated per-run artifacts to avoid evidence overwrite.
- Added reusable evidence bundle generator:
  - `novaic-app/scripts/build_desktop_evidence_bundle.sh`
- Added QA handoff with failure-mode examples:
  - `ops-rounds/round-006/20-reports/desktop-ci-qa-handoff-round006.md`
- Executed two replay runs (operator A/B) and produced reproducible evidence set.

## Exact Command Evidence + Pass Summary
- `cargo check --manifest-path "novaic-app/src-tauri/Cargo.toml"`
  - result: pass
  - summary: dev profile compiled successfully.
- `npm run tauri:build`
  - result: pass
  - summary: built `NovAIC.app` and `NovAIC_0.3.0_aarch64.dmg`.
- `open "novaic-app/src-tauri/target/release/bundle/dmg/NovAIC_0.3.0_aarch64.dmg"`
  - result: pass
  - summary: DMG opens successfully.
- `OPERATOR_ID="desktop-operator-a" RUN_LABEL="operator-a" EVIDENCE_DIR="ops-rounds/round-006/20-reports/desktop-evidence" novaic-app/scripts/validate_fresh_profile.sh`
  - result: pass
  - summary: `event_count=10`, `error_timeout_count=0`.
- `OPERATOR_ID="desktop-operator-b" RUN_LABEL="operator-b" EVIDENCE_DIR="ops-rounds/round-006/20-reports/desktop-evidence" novaic-app/scripts/validate_fresh_profile.sh`
  - result: pass
  - summary: `event_count=10`, `error_timeout_count=0`.
- `novaic-app/scripts/build_desktop_evidence_bundle.sh "/Users/wangchaoqun/novaic/ops-rounds/round-006"`
  - result: pass
  - summary: evidence archive + manifest generated.

## Artifacts / Docs Paths
- build artifacts:
  - `novaic-app/src-tauri/target/release/bundle/macos/NovAIC.app`
  - `novaic-app/src-tauri/target/release/bundle/dmg/NovAIC_0.3.0_aarch64.dmg`
- scripts:
  - `novaic-app/scripts/validate_fresh_profile.sh`
  - `novaic-app/scripts/build_desktop_evidence_bundle.sh`
- replay evidence:
  - `ops-rounds/round-006/20-reports/desktop-evidence/fresh-profile-operator-a-summary.txt`
  - `ops-rounds/round-006/20-reports/desktop-evidence/fresh-profile-operator-a-startup.log`
  - `ops-rounds/round-006/20-reports/desktop-evidence/fresh-profile-operator-a-startup-diagnostics.jsonl`
  - `ops-rounds/round-006/20-reports/desktop-evidence/fresh-profile-operator-a-metadata.txt`
  - `ops-rounds/round-006/20-reports/desktop-evidence/fresh-profile-operator-b-summary.txt`
  - `ops-rounds/round-006/20-reports/desktop-evidence/fresh-profile-operator-b-startup.log`
  - `ops-rounds/round-006/20-reports/desktop-evidence/fresh-profile-operator-b-startup-diagnostics.jsonl`
  - `ops-rounds/round-006/20-reports/desktop-evidence/fresh-profile-operator-b-metadata.txt`
- bundle artifacts:
  - `ops-rounds/round-006/20-reports/desktop-evidence-bundle/` (archive + manifest)
- docs:
  - `ops-rounds/round-006/20-reports/desktop-clean-profile-replay-round006.md`
  - `ops-rounds/round-006/20-reports/desktop-ci-qa-handoff-round006.md`
  - `ops-rounds/round-006/20-reports/team-desktop-report.md`

## Acceptance Mapping
- Task 1 (second operator/alternate profile replay evidence): `DONE`
  - evidence: operator-a/operator-b replay commands + per-run evidence files.
- Task 2 (failure-mode examples in CI/QA handoff): `DONE`
  - evidence: `desktop-ci-qa-handoff-round006.md` contains executable failure examples.
- Task 3 (complete reusable evidence bundle): `DONE`
  - evidence: bundle script + generated archive/manifest under `desktop-evidence-bundle/`.

## Risks / Blockers
- No active blocker.
- Minor risk: GUI-capable macOS runners may be limited for full installer interactions.

## Decision Needed
- issue:
  - Should desktop gate require GUI installer replay in every CI run or keep GUI replay as QA cadence while CI enforces scriptable replay + artifact checks?
- options:
  - A) Enforce GUI replay in every CI run.
  - B) CI enforces scriptable replay and evidence bundle; GUI replay on scheduled QA cadence.
  - C) Keep scriptable replay only.
- recommendation:
  - B
- impact:
  - A: strongest assurance, highest CI complexity/cost.
  - B: strong assurance with practical CI stability.
  - C: fastest, but weaker installer-path confidence.
- owner:
  - Platform + Desktop QA governance owners
- deadline:
  - 2026-02-25 18:00

## Self Status
- status: DONE

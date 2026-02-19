# Round 007 Report - Desktop Team

## Implemented Work
- Finalized and documented desktop release-gate policy (`Hybrid`: CI replay every run, GUI installer replay on QA cadence).
- Implemented policy in CI gate:
  - added `desktop-operability` job in `.github/workflows/ci.yml`.
- Replayed fresh-profile validation once for Round 007 and captured artifacts.
- Updated evidence bundle process to be round-aware and regenerated reusable archive.

## Exact Command Evidence + Pass Summary
- `cargo check --manifest-path "novaic-app/src-tauri/Cargo.toml"`
  - result: pass
  - summary: dev profile compiled successfully.
- `OPERATOR_ID="desktop-operator-round007" RUN_LABEL="round007-main" EVIDENCE_DIR="ops-rounds/round-007/20-reports/desktop-evidence" novaic-app/scripts/validate_fresh_profile.sh`
  - result: pass
  - summary: `event_count=10`, `error_timeout_count=0`, full startup stage chain present.
- `novaic-app/scripts/build_desktop_evidence_bundle.sh "/Users/wangchaoqun/novaic/ops-rounds/round-007"`
  - result: pass
  - summary: created reusable evidence archive + manifest for round-007.

## Artifact / Doc Paths
- code/scripts:
  - `.github/workflows/ci.yml`
  - `novaic-app/scripts/validate_fresh_profile.sh`
  - `novaic-app/scripts/build_desktop_evidence_bundle.sh`
- replay evidence:
  - `ops-rounds/round-007/20-reports/desktop-evidence/fresh-profile-round007-main-summary.txt`
  - `ops-rounds/round-007/20-reports/desktop-evidence/fresh-profile-round007-main-startup.log`
  - `ops-rounds/round-007/20-reports/desktop-evidence/fresh-profile-round007-main-startup-diagnostics.jsonl`
  - `ops-rounds/round-007/20-reports/desktop-evidence/fresh-profile-round007-main-metadata.txt`
- bundle evidence:
  - `ops-rounds/round-007/20-reports/desktop-evidence-bundle/` (archive + manifest)
- docs:
  - `ops-rounds/round-007/20-reports/desktop-ci-qa-handoff-round007.md`
  - `ops-rounds/round-007/20-reports/desktop-clean-profile-replay-round007.md`
  - `ops-rounds/round-007/20-reports/team-desktop-report.md`

## Acceptance Mapping
- Task 1 (finalize GUI replay policy): `DONE`
  - evidence: policy finalized and documented in `desktop-ci-qa-handoff-round007.md`.
- Task 2 (update handoff with final policy + owner): `DONE`
  - evidence: `desktop-ci-qa-handoff-round007.md` + CI workflow gate update.
- Task 3 (replay once + regenerate bundle): `DONE`
  - evidence: replay artifacts + round-007 evidence bundle archive/manifest.

## Risks / Blockers
- No active blocker.
- Risk: macOS CI concurrency/capacity may delay desktop-operability job runtime under high queue load.

## Decision Needed
- issue:
  - Should we reserve a dedicated macOS runner lane for `desktop-operability` to keep release-lane latency predictable?
- options:
  - A) Keep shared macOS pool (no reservation).
  - B) Reserve dedicated macOS runner lane for desktop-operability/release branches only.
  - C) Reserve dedicated macOS runner for all PR/branch runs.
- recommendation:
  - B
- impact:
  - A: lowest cost, variable latency.
  - B: predictable release latency with moderate cost increase.
  - C: highest cost, strongest scheduling guarantee.
- owner:
  - Platform CI Owner
- deadline:
  - 2026-02-26 18:00

## Self Status
- status: DONE

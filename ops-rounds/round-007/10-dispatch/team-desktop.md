# Round 007 Dispatch - Desktop Team

## Objective
Finalize release-gate policy decision and keep evidence bundle reproducible.

## Mandatory Tasks
1. Finalize policy: GUI installer replay frequency (CI every run vs QA cadence).
2. Update CI/QA handoff doc with final policy and owner.
3. Replay fresh-profile validation once and regenerate evidence bundle.

## Acceptance Commands
- `novaic-app/scripts/validate_fresh_profile.sh`
- `novaic-app/scripts/build_desktop_evidence_bundle.sh "/Users/wangchaoqun/novaic/ops-rounds/round-007"`
- `cargo check --manifest-path "novaic-app/src-tauri/Cargo.toml"`

## Due / Status
- due: 2026-02-23 18:00
- status: DONE

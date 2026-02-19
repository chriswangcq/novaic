# Round 008 Dispatch - Desktop Team

## Objective
Finalize desktop release gate package for repeatable handoff.

## Mandatory Tasks
1. Replay fresh-profile validation and regenerate evidence bundle.
2. Finalize CI-vs-QA GUI policy in handoff doc with owner and cadence.
3. Add one quick verification checklist for non-author operators.

## Acceptance Commands
- `novaic-app/scripts/validate_fresh_profile.sh`
- `novaic-app/scripts/build_desktop_evidence_bundle.sh "/Users/wangchaoqun/novaic/ops-rounds/round-008"`
- `cargo check --manifest-path "novaic-app/src-tauri/Cargo.toml"`

## Due / Status
- due: 2026-02-23 18:00
- status: DONE

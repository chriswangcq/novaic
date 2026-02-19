# Round 006 Dispatch - Desktop Team

## Objective
Keep desktop validation executable by non-authors and strengthen QA handoff.

## Mandatory Tasks
1. Replay `validate_fresh_profile.sh` by a second operator or alternate profile and attach evidence.
2. Add failure-mode examples to CI/QA handoff package.
3. Confirm release evidence bundle is complete and reusable.

## Acceptance Commands
- `cargo check --manifest-path "novaic-app/src-tauri/Cargo.toml"`
- `npm run tauri:build`
- `novaic-app/scripts/validate_fresh_profile.sh`

## Due / Status
- due: 2026-02-24 18:00
- status: DONE

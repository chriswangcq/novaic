# Round 005 Dispatch - Desktop Team

## Objective
Remove operability debt by standardizing clean-machine validation into repeatable automation.

## Mandatory Tasks
1. Provide scriptable fresh-profile validation workflow with output artifacts.
2. Add one clean-machine-equivalent replay run (new user/profile) with checklist and pass summary.
3. Add CI/QA handoff note describing required evidence package for desktop release.

## Acceptance Commands
- `cargo check --manifest-path "novaic-app/src-tauri/Cargo.toml"`
- `npm run tauri:build`
- `open "novaic-app/src-tauri/target/release/bundle/dmg/NovAIC_0.3.0_aarch64.dmg"`

## Due / Status
- due: 2026-02-25 18:00
- status: DONE

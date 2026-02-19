# Round 003 Dispatch - Desktop Team

## Objective
Close clean-machine validation and make RC deliverability fully reproducible.

## Mandatory Tasks
1. Execute clean-machine startup checklist with commands, outputs, and log paths.
2. Confirm RC artifact installability with one real install run.
3. Attach startup diagnostics evidence showing no startup-blocking error/timeout chain.

## Acceptance Commands
- `npm run tauri:build`
- `cargo check --manifest-path "novaic-app/src-tauri/Cargo.toml"`
- `open "novaic-app/src-tauri/target/release/bundle/dmg/NovAIC_0.3.0_aarch64.dmg"`

## Due / Status
- due: 2026-02-24 18:00
- status: DONE_WITH_GAPS

# Desktop Team Week1 Progress

## Scope
- Installer readiness
- Process orchestration startup reliability
- Endpoint observability baseline

## Completed in this round
- Added startup preflight port checks in `novaic-app/src-tauri/src/main.rs`
  - Checks required local ports before starting services
  - Provides actionable failure reason when conflicts are detected
- Added structured startup diagnostics log
  - Writes JSONL events to app data logs:
    - `logs/startup-diagnostics.jsonl`
  - Covers startup phases such as:
    - app bootstrap
    - zombie cleanup
    - port preflight
    - runtime-orchestrator start/health
    - gateway start/health
    - vmcontrol start
- Improved vmcontrol binary resolution to reduce parent-directory assumptions
  - Resolution order:
    1. `NOVAIC_VMCONTROL_BIN` override
    2. bundled resource path
    3. dev build targets under `src-tauri/vmcontrol/target/{debug,release}`
- Added vmcontrol runtime log file output
  - Redirects vmcontrol stdout/stderr to:
    - `logs/vmcontrol.log`

## Validation checklist
- [x] `cargo check --manifest-path novaic-app/src-tauri/Cargo.toml`
- [ ] Launch app and verify diagnostics file is created
- [ ] Simulate port conflict and confirm actionable startup error message
- [ ] Verify vmcontrol log file output on startup

## Next suggested items
- Add installer smoke script that validates startup diagnostics on clean machine
- Add CI smoke test to assert port preflight and diagnostics file generation

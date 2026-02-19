# Round 002 Desktop Clean-Machine Startup Validation

## Objective
Verify Round 002 RC installer startup path on a clean machine with reproducible steps and evidence capture.

## Artifact Under Test
- DMG: `novaic-app/src-tauri/target/release/bundle/dmg/NovAIC_0.3.0_aarch64.dmg`
- App bundle: `novaic-app/src-tauri/target/release/bundle/macos/NovAIC.app`

## Reproducible Checklist
1. Prepare clean environment
   - Use a machine/account without existing NovAIC app data
   - Confirm no local services occupy `19993-19999`
2. Install RC artifact
   - Open DMG and drag `NovAIC.app` to `/Applications`
3. First startup
   - Launch app from `/Applications/NovAIC.app`
   - Wait until UI is visible and backend bootstrap completes
4. Verify startup diagnostics
   - Check app data logs for:
     - `logs/startup-diagnostics.jsonl`
     - `logs/vmcontrol.log`
   - Confirm no `error`/`timeout` event in startup-critical stages
5. Verify health endpoints
   - Confirm gateway health reachable at `http://127.0.0.1:19999/api/health`
   - Confirm runtime orchestrator health reachable at `http://127.0.0.1:19993/api/health`
6. Shutdown and relaunch
   - Quit app and relaunch once
   - Confirm startup remains healthy and diagnostics logs append new events

## Expected Pass Criteria
- Installer artifact installs successfully
- Core startup path succeeds with no startup-blocking diagnostics events
- Required diagnostics logs exist and contain actionable events

## Current Execution Status
- status: IN_PROGRESS
- note: Checklist defined; clean-machine execution evidence pending.

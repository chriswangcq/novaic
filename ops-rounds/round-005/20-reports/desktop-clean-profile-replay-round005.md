# Round 005 Desktop Clean-Profile Replay

## Replay Type
Fresh user profile replay (new HOME via `mktemp`) on macOS host.

## Checklist
- [x] Clean startup ports `19993-19999`
- [x] Launch bundled app with fresh HOME
- [x] Wait for full startup sequence
- [x] Capture startup log and diagnostics log
- [x] Verify no `error`/`timeout` in diagnostics statuses

## Execution Command
- `novaic-app/scripts/validate_fresh_profile.sh`

## Pass Summary
- `event_count=10`
- `error_timeout_count=0`
- startup stages:
  - `app-bootstrap`
  - `cleanup`
  - `port-preflight`
  - `runtime-orchestrator`
  - `gateway`
  - `vmcontrol`
  - `queue-service`
  - `file-service`
  - `tool-result-service`
  - `tools-server`

## Evidence Paths
- `ops-rounds/round-005/20-reports/desktop-evidence/fresh-profile-startup.log`
- `ops-rounds/round-005/20-reports/desktop-evidence/fresh-profile-startup-diagnostics.jsonl`
- `ops-rounds/round-005/20-reports/desktop-evidence/fresh-profile-summary.txt`

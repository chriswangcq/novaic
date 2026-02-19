# Round 007 Desktop Replay Run

## Replay Command
- `OPERATOR_ID="desktop-operator-round007" RUN_LABEL="round007-main" EVIDENCE_DIR="ops-rounds/round-007/20-reports/desktop-evidence" novaic-app/scripts/validate_fresh_profile.sh`

## Result Summary
- status: pass
- `event_count=10`
- `error_timeout_count=0`
- stage chain:
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

## Produced Evidence
- `ops-rounds/round-007/20-reports/desktop-evidence/fresh-profile-round007-main-summary.txt`
- `ops-rounds/round-007/20-reports/desktop-evidence/fresh-profile-round007-main-startup.log`
- `ops-rounds/round-007/20-reports/desktop-evidence/fresh-profile-round007-main-startup-diagnostics.jsonl`
- `ops-rounds/round-007/20-reports/desktop-evidence/fresh-profile-round007-main-metadata.txt`

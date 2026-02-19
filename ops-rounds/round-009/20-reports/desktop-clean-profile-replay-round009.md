# Round 009 Desktop Non-Author Replay

## Executed Command
- `OPERATOR_ID="desktop-non-author-operator" RUN_LABEL="round009-non-author" ROUND_DIR="/Users/wangchaoqun/novaic/ops-rounds/round-009" novaic-app/scripts/validate_fresh_profile.sh`

## Result
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

## Produced Evidence Paths
- `ops-rounds/round-009/20-reports/desktop-evidence/fresh-profile-round009-non-author-summary.txt`
- `ops-rounds/round-009/20-reports/desktop-evidence/fresh-profile-round009-non-author-startup.log`
- `ops-rounds/round-009/20-reports/desktop-evidence/fresh-profile-round009-non-author-startup-diagnostics.jsonl`
- `ops-rounds/round-009/20-reports/desktop-evidence/fresh-profile-round009-non-author-metadata.txt`

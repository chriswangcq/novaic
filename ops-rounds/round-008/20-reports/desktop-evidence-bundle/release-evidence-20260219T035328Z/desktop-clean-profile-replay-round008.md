# Round 008 Desktop Fresh-Profile Replay

## Executed Command
- `OPERATOR_ID="desktop-operator-round008" RUN_LABEL="round008-final" ROUND_DIR="/Users/wangchaoqun/novaic/ops-rounds/round-008" novaic-app/scripts/validate_fresh_profile.sh`

## Pass Summary
- status: pass
- `event_count=10`
- `error_timeout_count=0`
- startup stages include:
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

## Produced Artifacts
- `ops-rounds/round-008/20-reports/desktop-evidence/fresh-profile-round008-final-summary.txt`
- `ops-rounds/round-008/20-reports/desktop-evidence/fresh-profile-round008-final-startup.log`
- `ops-rounds/round-008/20-reports/desktop-evidence/fresh-profile-round008-final-startup-diagnostics.jsonl`
- `ops-rounds/round-008/20-reports/desktop-evidence/fresh-profile-round008-final-metadata.txt`

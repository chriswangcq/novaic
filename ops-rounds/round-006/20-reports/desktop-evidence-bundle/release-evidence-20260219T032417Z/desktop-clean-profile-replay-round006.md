# Round 006 Desktop Replay Evidence

## Replay Goal
Prove `validate_fresh_profile.sh` is executable by non-authors via second-operator replay.

## Executed Replays

### Replay A
- command:
  - `OPERATOR_ID="desktop-operator-a" RUN_LABEL="operator-a" EVIDENCE_DIR="ops-rounds/round-006/20-reports/desktop-evidence" novaic-app/scripts/validate_fresh_profile.sh`
- result:
  - pass
  - `event_count=10`
  - `error_timeout_count=0`

### Replay B
- command:
  - `OPERATOR_ID="desktop-operator-b" RUN_LABEL="operator-b" EVIDENCE_DIR="ops-rounds/round-006/20-reports/desktop-evidence" novaic-app/scripts/validate_fresh_profile.sh`
- result:
  - pass
  - `event_count=10`
  - `error_timeout_count=0`

## Evidence Paths
- `ops-rounds/round-006/20-reports/desktop-evidence/fresh-profile-operator-a-summary.txt`
- `ops-rounds/round-006/20-reports/desktop-evidence/fresh-profile-operator-a-startup.log`
- `ops-rounds/round-006/20-reports/desktop-evidence/fresh-profile-operator-a-startup-diagnostics.jsonl`
- `ops-rounds/round-006/20-reports/desktop-evidence/fresh-profile-operator-a-metadata.txt`
- `ops-rounds/round-006/20-reports/desktop-evidence/fresh-profile-operator-b-summary.txt`
- `ops-rounds/round-006/20-reports/desktop-evidence/fresh-profile-operator-b-startup.log`
- `ops-rounds/round-006/20-reports/desktop-evidence/fresh-profile-operator-b-startup-diagnostics.jsonl`
- `ops-rounds/round-006/20-reports/desktop-evidence/fresh-profile-operator-b-metadata.txt`

# Round 009 Hotfix Broadcast (Gate A Closure)

All teams: Round 009 remains open due to Gate A failure.

## Current blocker
- `gate_round009.sh` fails at canonical URL audit.
- `canonical-repo-url-audit.md` reports 18 violations.
- Violations are concentrated in 5 teams: API, Runtime, Agent Runtime, Tools, Storage-A/B.

## Mandatory execution rule (effective now)
- The only accepted `repo_url` format is `https://github.com/<org>/<repo>`.
- `file:///`, `local:`, and SSH-style URLs are rejected.
- Every `repo_url` must pair with a real reachable 40-char `commit_sha`.
- Narrative completion is ignored if parser fields fail.

## Who must act now
- API
- Runtime
- Agent Runtime
- Tools
- Storage-A/B
- Platform (final re-audit only after the 5 teams finish)

## Where to execute
1. Read `rounds/round-009/40-redispatch/redispatch-plan.md`
2. Apply only your team fix tasks
3. Update your report under `rounds/round-009/20-reports/`
4. Post `commit_sha` in team update

## Round close condition
- `bash rounds/round-009/split-close/gate_round009.sh`
- Must output: `ROUND009_GATE_RUNNER_PASS`

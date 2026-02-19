# Round 003 Dispatch - API Team

## Objective
Freeze gateway docs/contracts and keep startup smoke reproducible.

## Mandatory Tasks
1. Keep env spec and API surface inventory synchronized with latest contracts.
2. Add CI job for `scripts/smoke_gateway_independent_startup.sh`.
3. Re-run forbidden import scan and attach output summary.

## Acceptance Commands
- `bash scripts/smoke_gateway_independent_startup.sh`
- `rg "^\s*(from\s+(task_queue|runtime_orchestrator|tools_server)\b|import\s+(task_queue|runtime_orchestrator|tools_server)\b)" novaic-backend/gateway --glob "**/*.py"`

## Due / Status
- due: 2026-02-24 18:00
- status: DONE

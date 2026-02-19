# Round 004 Dispatch - API Team

## Objective
Maintain gateway stability and assist Gate B storage contract publication.

## Mandatory Tasks
1. Keep gateway smoke CI green and attach one fresh run.
2. Sync API inventory references to latest contracts paths.
3. Co-author storage contract schema fields with Storage/Platform.

## Acceptance Commands
- `bash scripts/smoke_gateway_independent_startup.sh`
- `rg "storage|file-service|tool-result" novaic-backend/docs contracts -g "*.md" -g "*.yaml" -g "*.json"`

## Due / Status
- due: 2026-02-23 18:00
- status: DONE

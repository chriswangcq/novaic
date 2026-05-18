# App backend startup graph cleanup

## Problem
App backend startup scripts and packaged/generated backend scripts may contain stale service topology, port conflicts, or binary/resource expectations that do not match current services.

## Success Criteria
- `novaic-app/scripts/start-backends.sh`, packaged backend scripts, and generated backend scripts agree on the current service list and ports.
- The `PORT_CORTEX=19996` versus `vmcontrol` port conflict is resolved or renamed clearly.
- Backend binary/resource expectations match committed resources or are marked dev-only.
- Focused script/config checks run.

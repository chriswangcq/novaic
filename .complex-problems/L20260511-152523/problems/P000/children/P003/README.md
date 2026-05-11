# Deploy and verify stall repair

## Problem

Deploy the repaired backend and prove the agent loop can progress past the previous stuck point in production-like conditions.

## Success Criteria

- Backend services deploy and restart cleanly.
- Fresh-smoke and service health checks pass.
- A remote e2e/smoke path covers the repaired transition.
- Logs after deploy show no new current fatal errors for the touched path.

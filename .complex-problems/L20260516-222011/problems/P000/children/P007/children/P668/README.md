# Runtime process topology and deployment script audit

## Problem

Inspect how the backend/runtime process topology is declared and started: deployment scripts, worker/service entrypoints, scheduler/health processes, and any docs that describe them. Identify stale process names, unclear roles, or low-risk script/doc gaps that make runtime failures hard to diagnose.

## Success Criteria

- Deployment/start scripts and process topology docs are searched and inspected.
- Current worker/service roles are summarized from code/config, not memory.
- Stale process names or misleading deployment notes are updated or explicitly recorded as historical if found.
- Relevant low-risk script/doc/test fixes are applied and locally verified.

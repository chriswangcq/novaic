# Gateway and app edge service boundary classification

## Problem
Classify Gateway and app-facing edge service surfaces. Verify their entrypoints, launch wrappers, routing/API roles, and dependency boundaries relative to Queue/Runtime workers and semantic services.

## Success Criteria
- Gateway/app edge entrypoints and launch references are listed with evidence.
- HTTP/routing/UI edge responsibilities are separated from queue session FSM, Runtime execution, and worker ownership.
- Active wrapper scripts that launch Gateway/app services are classified.
- Stale misleading claims are patched or recorded.

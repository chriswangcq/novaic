# Ticket: Gateway and app edge service boundary classification

## Problem Definition
Classify Gateway and app-facing edge service surfaces. Verify concrete entrypoints, launch wrappers, routing/API roles, and dependency boundaries relative to Queue/Runtime, Business, Entangled, Blob, Device, and Cortex.

## Proposed Solution
Inspect gateway code, app backend launch scripts, Tauri resource wrappers, docs, and active service topology references. Produce a boundary map and patch or record misleading active claims if found.

## Acceptance Criteria
- Gateway/app edge entrypoints and launch references are listed with evidence.
- Auth/App WS/log broadcast/Blob edge/endpoint discovery responsibilities are separated from Queue session FSM, Runtime workers, Business action handling, and Entangled entity sync authority.
- Active wrapper scripts are classified as launch/packaging surfaces, not business logic owners.
- Stale or misleading claims are patched or recorded.

## Verification Plan
Use rg/find/sed scans over `novaic-gateway`, `novaic-app`, `scripts/start.sh`, backend start wrappers, and docs; run focused tests/lints if files are touched.

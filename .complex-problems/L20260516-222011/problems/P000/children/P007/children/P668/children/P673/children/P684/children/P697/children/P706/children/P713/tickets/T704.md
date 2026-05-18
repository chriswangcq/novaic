# Ticket: Gateway/app edge boundary discovery and map

## Problem Definition
Discover Gateway and app edge entrypoints, launch wrappers, routing/API responsibilities, and dependencies. Produce a boundary map and cleanup candidate list without implementation changes.

## Proposed Solution
Scan `novaic-gateway`, `novaic-app`, `scripts/start.sh`, backend wrapper scripts, and architecture docs for Gateway/app edge entrypoints, launch references, and ownership wording. Save scan outputs and a boundary map.

## Acceptance Criteria
- Gateway/app entrypoints and launch references are listed with evidence.
- Gateway edge responsibilities are separated from Business, Entangled, Queue, Runtime, Device, Blob, and Cortex ownership.
- App/Tauri wrappers are classified as packaging/launch/client surfaces.
- Active/generated/historical references are separated.
- P714 cleanup candidates are listed.

## Verification Plan
Use `find`, `rg`, `sed`, and targeted compile/lint where useful. Record scan commands, raw scans, boundary map, and cleanup candidates.

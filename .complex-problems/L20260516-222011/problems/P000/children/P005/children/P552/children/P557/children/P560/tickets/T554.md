# Map Sandbox LogicalFS Blob Service Call Paths

## Problem Definition

P560 must map sandbox service/core, sandbox SDK, and LogicalFS call paths, including whether sandbox uses LogicalFS for real-time file authority and whether blob appears in that layer.

## Proposed Solution

Run targeted scans over `novaic-sandbox-service`, `novaic-sandbox-sdk`, and `novaic-logicalfs`; read high-signal source files; produce a call-path map artifact and flag suspicious fallback paths for P553.

## Acceptance Criteria

- Scan artifacts exist.
- High-signal service/core files are cited.
- Sandbox/LogicalFS layering direction is explained.
- Suspicious direct fallback or blob usage is flagged.

## Verification Plan

Use `rg` for imports/calls and bounded `sed` slices for service/core files. Keep this read-only.

## Risks

- Sandbox may intentionally use a local provider internally to implement a view.
- Blob usage may appear only through LogicalFS adapters rather than sandbox service.

## Assumptions

- `novaic-sandbox-service` and `novaic-logicalfs` are the relevant local roots.

# App frontend and Monitor output contract discovery ticket

## Problem Definition

App frontend/Monitor/log UI code may still expect or render raw base64/media payloads, old tool result JSON, stale shell/display contracts, or incomplete artifact/blob manifests.

## Proposed Solution

Discover frontend/Monitor/log UI files, classify high-signal hits around tool output, display, image/base64 payloads, artifact manifests, Blob refs, shell output, factory logs, and request/response details. Split if needed across UI rendering, log detail data shaping, and Blob/attachment fetching.

## Acceptance Criteria

- Relevant frontend/Monitor/log/UI files are discovered.
- Suspicious hits around tool output, display, image/base64 payloads, artifacts, Blob refs, shell output, and factory logs are classified.
- Exact remediation candidates are listed, or absence is explicitly recorded.
- No frontend/app UI files are modified.

## Verification Plan

Use bounded `rg --files`, focused `rg -n -i`, and targeted file slices under `novaic-app/src`, with optional supporting checks in Tauri command bindings where frontend Blob/media display depends on backend commands.

## Risks

- UI vocabulary like `base64` may appear in legitimate file preview logic. The classification must distinguish raw LLM context regressions from frontend download/render paths.

## Assumptions

- The relevant UI code is primarily under `novaic-app/src`, with Tauri file commands already covered as supporting evidence in P770/P772.

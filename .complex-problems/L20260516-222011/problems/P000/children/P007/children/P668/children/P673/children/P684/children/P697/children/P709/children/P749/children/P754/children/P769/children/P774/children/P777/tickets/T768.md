# App monitor timeline payload projection discovery ticket

## Problem Definition

Agent Monitor timeline/detail rendering may still surface raw tool payloads, `_mcp_content`, base64/data URLs, or stale display output instead of projected user-facing shell text and BlobRef/artifact summaries.

## Proposed Solution

Discover monitor/timeline components, hooks, types, and tests under `novaic-app/src`. Inspect projection helpers and guard tests for `_mcp_content`, raw tool output, base64/data URLs, BlobRefs, artifacts, truncation, and display tool result handling. Classify each suspicious hit and list remediation candidates if any normal user-facing timeline path can still expose raw payloads.

## Acceptance Criteria

- Monitor/timeline files and tests are discovered.
- Suspicious payload/projection/truncation/media hits are classified by exact file/path.
- Remediation candidates are listed if the timeline/detail surface still leaks raw payloads.
- No monitor/timeline UI files are modified.

## Verification Plan

Use bounded `rg --files`, focused `rg -n -i`, and targeted slices for `ActivityTimeline`, `AgentMonitorCapsule`, `useActivityTimeline`, activity timeline types, and associated guard/acceptance tests.

## Risks

- Monitor code intentionally keeps some diagnostic identifiers in tests or development-only paths; classify test-only and production render paths separately.
- Over-scrubbing could hide useful shell text, so discovery should distinguish binary/media-looking payloads from normal terminal output.

## Assumptions

- User-facing Agent Monitor timeline code lives under `novaic-app/src/components/Visual` and related hooks/types.

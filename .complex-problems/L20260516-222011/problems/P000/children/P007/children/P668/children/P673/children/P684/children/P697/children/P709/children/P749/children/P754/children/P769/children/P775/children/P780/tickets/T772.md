# App monitor shell artifact projection discovery ticket

## Problem Definition

Agent Monitor / ActivityTimeline may still surface shell output, artifact manifests, or tool-result details as raw JSON/media payloads instead of public projected summaries. This can leak `_mcp_content`, raw artifact payloads, base64/data URLs, or implementation-only fields even if Chat is clean.

## Proposed Solution

Discover Monitor/ActivityTimeline components, hooks, types, and tests under `novaic-app/src`. Inspect shell action detail handling, tool output projection, artifact/BlobRef fields, truncation indicators, and raw payload hiding logic. Classify whether each suspicious path is safe projection, intentional public terminal text, dead residue, or remediation candidate.

## Acceptance Criteria

- Monitor, ActivityTimeline, activity hook/type, and guard test files are discovered.
- Hits for shell actions, tool output details, `tool-output.v1`, artifacts, Blob refs, truncation, raw payload hiding, and display/media preview are classified.
- Exact remediation candidates are listed, or absence is explicitly recorded.
- No Monitor UI files are modified.

## Verification Plan

Use bounded `rg --files` and focused `rg -n -i` scans under `novaic-app/src/components/Visual`, `novaic-app/src/components/hooks`, and `novaic-app/src/types`. Inspect source slices and run existing ActivityTimeline/useActivityTimeline tests if directly relevant.

## Assumptions

- Monitor should show status/progress summaries and bounded terminal-like text, not raw payload envelopes.
- Existing ActivityTimeline guard tests are relevant but must be checked rather than trusted blindly.

## Risks

- A previous discovery already covered generic Monitor payload scrub; this ticket must specifically validate shell artifact/output assumptions rather than duplicate broad raw payload checks.

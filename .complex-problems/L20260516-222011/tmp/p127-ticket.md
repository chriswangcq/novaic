# Audit step result projection contract across tool output types

## Problem Definition

Step result projection is the final boundary that turns durable tool output into LLM-visible text/history/current messages. It must keep shell output terminal-style and bounded, preserve artifact manifests, allow current display media projection, and prevent raw base64 or large payload leakage into ordinary context.

## Proposed Solution

Split the audit by projection responsibility: shell/current text projection, display current projection, historical/display manifest behavior, and generic/payload artifact behavior. Reuse evidence from P136/P182 where it directly applies, but verify `step_result_projection.py` and runtime projection calls directly. Add or tighten tests if any branch can emit unbounded text or raw media.

## Acceptance Criteria

- Shell projection behavior is mapped and tested as bounded terminal text.
- Display current projection is mapped and tested as provider-usable media input.
- Historical display/tool projection is mapped and tested as manifest/placeholder-only.
- Generic payload/blob artifact projection is mapped and tested.
- Any raw-base64 or unbounded-text projection branch is fixed or split into a targeted child.

## Verification Plan

Inspect `novaic-cortex/novaic_cortex/step_result_projection.py`, runtime step result expansion, tool handlers, and projection tests. Run focused Cortex and runtime projection suites.

## Risks

- The contract spans Cortex formatting and runtime provider conversion; a one-pass audit could blur responsibilities.

## Assumptions

- This problem focuses on projection behavior, not the broader ContextEvent source-map already closed in P126.

# Classify Runtime Display And Tool Output Projection Residue

## Problem Definition

P564 must audit agent-runtime and Cortex projection code for stale base64, display, artifact, payload, and multimodal compatibility paths that could reintroduce media bytes into shell/history context or bypass the `tool-output.v1` manifest contract.

## Proposed Solution

Run targeted static scans across runtime context assembly, tool result projection, display handling, Cortex shell capabilities, and related tests. Capture exact command outputs, focused line-numbered slices, and classify each hit bucket as intended, risky, removable, or a follow-up. Pay special attention to the recent failure mode: display/tool results putting raw base64 text into LLM request history instead of passing current-turn image content through the intended perception path.

## Acceptance Criteria

- Exact static scan commands and outputs are recorded.
- Base64/display/artifact/tool-output hits are classified.
- Valid current-turn `display_perception` image delivery is separated from invalid historical/shell image injection.
- Any high-confidence risky residue is forwarded to P554 remediation.

## Verification Plan

Use `rg` scans and focused slices over `novaic-agent-runtime`, `novaic-cortex`, runtime display/tool projection tests, and LLM/context assembly code. Validate classification against current tests when available, and record any missing test or code cleanup candidate explicitly.

## Risks

- The terms `display`, `image`, and `payload` are broad and will produce false positives in UI, monitor, and blob code.
- Current-turn multimodal image delivery is valid and must not be confused with historical shell/tool text projection.
- Some compatibility branches may be intentionally kept for external providers; classify only after tracing the call path.

## Assumptions

- Shell history should contain bounded terminal text and artifact manifests, not raw media bytes.
- Display perception can provide image content to the model only through the current-turn perception path, not by embedding base64 in persistent tool text.
- Blob refs are valid durable references for artifacts and payloads.


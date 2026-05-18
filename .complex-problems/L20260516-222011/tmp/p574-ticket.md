# Classify Runtime LLM Request Projection Paths

## Problem Definition

P574 must audit agent-runtime LLM request and context assembly paths to verify that tool outputs, display perception, artifacts, and active stack messages are projected into model requests through the intended contract, without raw media/base64 leaking through historical tool text.

## Proposed Solution

Run focused static scans over runtime context preparation, message serialization, provider request bodies, tool-result conversion, display perception injection, and active stack insertion. Record command outputs, line-numbered slices, and classify each projection path as intended, risky, removable, or follow-up.

## Acceptance Criteria

- Exact scan commands and outputs are recorded.
- Relevant runtime request assembly code/test slices have line references.
- Tool-result text projection is separated from current-turn display/image perception.
- Active stack/system message insertion is classified and checked for ordering side effects.
- Any high-confidence risky residue is forwarded to P554 remediation.

## Verification Plan

Search `novaic-agent-runtime` for context preparation, request body construction, tool-call/tool-result projection, multimodal/image handling, display perception, active skill stack injection, and provider adapter code. Read focused line slices and classify reachable paths.

## Risks

- Some provider adapters may legitimately transform image inputs to provider-specific formats.
- Active stack injection may appear near the end of the message list but may not be the cause of image-delivery failure; classify by actual call path, not screenshot symptoms alone.
- Large scans can produce UI/monitor false positives.

## Assumptions

- Durable tool history should contain bounded text/manifest references only.
- Current-turn image perception, if present, should be represented as structured multimodal content for the provider, not as a raw base64 string inside a text field.
- Agent Monitor display concerns are separate from LLM request-body correctness.


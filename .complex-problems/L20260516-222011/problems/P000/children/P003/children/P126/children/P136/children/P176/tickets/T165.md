# Map runtime tool wrapper refs

## Problem Definition

The runtime wrapper that turns raw tool executor output into tool messages must not leak raw payloads and must keep `step_ref` / `payload_ref` semantics clear before Cortex persistence sees the step.

## Proposed Solution

Inspect runtime tool wrapper code and tests around `_ok`, durable payloads, artifacts, public content, `step_ref`, and `payload_ref`. Tighten tests only if the current wrapper leaves ambiguity or raw payload leakage.

## Acceptance Criteria

- Runtime wrapper source pointers are mapped.
- Public versus durable/raw fields are documented.
- Existing or new tests prove no raw media/base64 leakage into public wrapper content.
- Result states whether code changes were needed.

## Verification Plan

Run focused runtime wrapper/multimodal tests after inspection.

## Risks

Display/media handling is easy to accidentally validate through durable payload while still leaking through public content.

## Assumptions

The wrapper layer should be provider-agnostic and should not decide final multimodal expansion by itself.

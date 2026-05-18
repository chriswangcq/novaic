# Map formatted read and display projection refs

## Problem Definition

Formatted step reads expand durable step payloads into LLM-facing content. This path must find a step by stable `step_ref`, then read actual payload by final `payload_ref`, while preserving public placeholder safety and only injecting media for explicit display perception.

## Proposed Solution

Inspect Cortex formatted step read APIs, runtime `StepResultClient`, message expansion, sanitizer/multimodal conversion, and display projection tests. Add or tighten tests if stable lookup plus final payload read is not guarded.

## Acceptance Criteria

- Formatted read, preview, step result client, and multimodal expansion source pointers are mapped.
- Tests prove stable `step_ref` lookup resolves externalized/final payload refs.
- Tests prove public tool messages stay placeholder-only while display perception can produce LLM image input.
- Any missing guard is fixed or split.

## Verification Plan

Run focused Cortex formatted read tests and runtime step-result/multimodal tests.

## Risks

This layer is where raw media could accidentally re-enter tool history or fail to enter LLM perception.

## Assumptions

Display perception is the only projection allowed to turn durable image data into LLM image input.

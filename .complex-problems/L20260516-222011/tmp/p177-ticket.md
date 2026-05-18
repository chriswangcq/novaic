# Map Cortex step storage refs

## Problem Definition

Cortex persists tool steps and context projections. The storage layer must keep stable `step_ref` lookup identity and distinguish it from actual payload storage identity, especially for durable payloads and artifacts.

## Proposed Solution

Inspect Cortex workspace step write/read/index/projection code and bridge write code around `step_ref`, `payload_ref`, `payload`, artifacts, and JSONL error behavior. Add or tighten tests if index/projection storage conflates or loses refs.

## Acceptance Criteria

- Cortex step write/read/index/projection source pointers are mapped.
- The storage contract for `step_ref`, `payload_ref`, and artifacts is documented.
- Focused Cortex/runtime bridge tests are run.
- Any ambiguous key handling is fixed or split.

## Verification Plan

Run focused tests for Cortex step index, context event step writes, context writes, corrupt JSONL behavior, and runtime bridge step-write contracts.

## Risks

Bridge code may still assume `payload_ref == step_ref`; that may be acceptable today but must be explicitly classified.

## Assumptions

The durable step file itself remains the stable lookup location until a deeper external payload implementation changes it.

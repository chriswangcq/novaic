# Verify Cortex event projection preserves payload pointers

## Problem Definition

Cortex event writer/projection must preserve `step_ref`/`payload_ref` and compact tool projections without expanding durable payload bodies into normal event records or projected context.

## Proposed Solution

Inspect Cortex context event writer/projection paths and targeted tests. Verify event payloads keep pointer metadata and that projection uses compact observation/public content rather than raw durable payload reads.

## Acceptance Criteria

- Event writer and projection functions are mapped with file/function pointers.
- Evidence shows `step_ref`/`payload_ref` are preserved and raw payload bodies are not expanded into event projection records by default.
- Focused context event projection/write tests pass.

## Verification Plan

Use `rg`/`nl` over `context_event_writer.py`, `context_event_projection.py`, and API/write tests. Run focused Cortex event projection tests.

## Risks

- Event projection could be correct while runtime expansion misuses it; runtime expansion is sibling `P233`.

## Assumptions

- Workspace persistence was already verified in `P235`.

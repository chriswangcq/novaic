# Wire steps/write to ToolStepRecorded events

## Problem Definition

`/v1/steps/write` still only writes legacy step files after P035. The event-sourced context source needs the endpoint to append a `ToolStepRecorded` event for the resolved active scope before or alongside the transitional file projection.

## Proposed Solution

- Reuse `Workspace.normalize_step` in `steps_write` to obtain the final durable step payload before event emission.
- Append `ToolStepRecorded` with explicit write context, target `scope_id`, call id, tool name, status, observation, and final `payload_ref`.
- Keep the legacy `write_step` file write as transitional projection using the normalized step so existing readers remain compatible.
- Adjust `ContextEventWriter.tool_step_recorded` only as needed to represent payload-less tool steps explicitly.
- Add focused API tests that inspect `context_events/events.jsonl` after `steps_write`.

## Acceptance Criteria

- `steps_write` appends exactly one `ToolStepRecorded` event per tool step write.
- The event targets the deepest active scope, including an open child skill scope.
- Payload-bearing steps record the final normalized `payload_ref`, including blob-ref replacement.
- Payload-less steps do not require fake payload refs.
- Legacy step files and `_index.jsonl` remain readable during the transitional phase.

## Verification Plan

- Add focused `/v1/steps/write` event tests.
- Run those tests plus step/workspace tests.
- Run the full Cortex suite.

## Risks

- Existing idempotency key may collide for repeated calls with the same call id if a retry changes payload; tests should cover the intended deterministic behavior.
- Normalization writes payload before event append, matching old behavior but still not an atomic transaction.

## Assumptions

- Event-only read cutover is handled by later phases; this ticket only wires the write side.

# Step-ref projection check

## Summary

The step-ref projection repair satisfies P005: projected tool-result messages now expose the durable tool-step join key exactly where runtime expects it.

## Evidence

- `test_project_context_events_tool_call_and_result` now expects top-level `step_ref`.
- `test_project_context_events_multiple_tool_results_preserve_order_and_payload_refs` verifies both projected tool results preserve ordered top-level refs.
- `test_project_context_events_orphan_tool_result_is_marked` verifies orphan tool results also receive `step_ref`.

## Criteria Map

- Every projected tool message with payload ref has `step_ref` -> covered by ordinary, multiple, and orphan tests.
- Metadata payload ref remains available -> existing metadata assertions still pass.
- Runtime contract no longer fails before LLM call due missing projected ref -> satisfied by producing the required top-level field.

## Execution Map

- `T004` / `R002` -> pure projection patch plus focused Cortex projection test suite.

## Stress Test

- If a future projection path creates a tool message without `step_ref`, the updated exact-dict and list assertions would catch the primary paths represented in the event stream.

## Residual Risk

- Events without a string payload ref still cannot be expanded by runtime; that remains intentional because inline tool results are rejected elsewhere by the step storage contract.

## Result IDs

- R002

## Blocking Gaps

- none

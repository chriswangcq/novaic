# Result: P424 / T411 ContextEvent API lifecycle endpoint cleanup

## Summary

Audited the ContextEvent API lifecycle endpoints for hidden legacy projection paths, display/base64 leakage risk, and mixed lifecycle ownership. No source changes were required in this ticket.

## Done

- Indexed Cortex API lifecycle endpoints around context reads/writes, skill lifecycle, step writes, and formatted step reads.
- Inspected `context_skill_begin` and `context_skill_end` and confirmed they operate through explicit active stack projection plus `ContextEventWriter` event writes.
- Inspected `steps_read_formatted` and confirmed its three projection modes are explicit:
  - `display_perception`
  - `current_tool_result`
  - `history`
- Confirmed unsupported projection modes fail closed with HTTP 400.
- Confirmed display-capable image payload expansion is scoped to the display perception formatter, not history/current tool result projection.

## Verification

- `PYTHONPATH=.:../novaic-common:../novaic-logicalfs:../novaic-sandbox-sdk pytest -q tests/test_context_event_api_lifecycle.py tests/test_context_event_api_skill_lifecycle.py tests/test_context_event_api_steps_write.py tests/test_context_event_api_context_writes.py tests/test_context_event_read_source_guards.py tests/test_tool_output_projection.py`
- Result: `51 passed in 0.55s`

## Classification

- API lifecycle endpoints are clean for this ticket's boundary.
- No direct base64/image expansion path was found in API history/current formatted step reads.
- No compatibility cleanup patch was needed here; this ticket was an endpoint contract audit and verification pass.

## Known Gaps

- Broader archive/direct `/v1/scope/end` diagnostics and non-ContextEvent archive projection behavior are outside P424 and remain assigned to sibling Cortex cleanup tickets P418/P419.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p424/api-lifecycle-index.txt`
- `.complex-problems/L20260516-222011/tmp/p424/api-context-lifecycle.inspect.txt`
- `.complex-problems/L20260516-222011/tmp/p424/api-steps-formatted.inspect.txt`
- `.complex-problems/L20260516-222011/tmp/p424/projection-mode-guard.txt`

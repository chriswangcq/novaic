# Check: P424 ContextEvent API lifecycle endpoint cleanup

## Verdict

Success for the ticket's scoped boundary.

## Evidence Reviewed

- Result `R404`
- Endpoint index artifact for context lifecycle APIs.
- Inspected context skill lifecycle endpoint slices.
- Inspected formatted step read endpoint slices.
- Projection mode guard artifact.
- Focused Cortex API/projection test run with 51 passing tests.

## Criteria Map

- ContextEvent API lifecycle endpoints identified: satisfied.
- Skill begin/end API ownership through explicit context event writer and active stack projection: satisfied.
- Formatted step reads do not silently mix display perception with history/current tool result projection: satisfied.
- Unsupported projection modes fail closed: satisfied.
- No source patch needed unless a live residue is found: satisfied.

## Execution Map

- The result did not attempt broad archive cleanup; it stayed inside the API lifecycle endpoint boundary.
- `display_perception`, `current_tool_result`, and `history` were checked as separate API projection contracts.
- The known archive/direct scope cleanup gap is explicitly routed to sibling tickets instead of being hidden in this ticket.

## Stress Test

- I treated this as a skeptical one-go check and looked for the common failure mode: endpoint says "history" but still permits display/base64 expansion.
- The guard evidence shows `include_display=True` is only in display perception formatting, while history/current projections keep display expansion disabled.
- The focused test suite covers context lifecycle, skill lifecycle, step writes, context writes, read-source guards, and tool-output projection.

## Residual Risk

- Remaining risk is not in P424's endpoint boundary: archive/direct `/v1/scope/end` diagnostics and non-ContextEvent archive projection are assigned to sibling Cortex cleanup tickets P418/P419.

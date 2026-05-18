# Runtime step result expansion path success check

## Summary

Success. R214 maps the runtime step-ref expansion path with concrete file/function pointers and shows the path relies on Cortex formatted projections rather than raw durable payload insertion.

## Evidence

- Handler dependency injection: `llm_handlers.py:117-127`.
- Preparation sequence: `llm_call.py:115-145`.
- Step-ref expansion and projection selection: `step_result_client.py:119-212`.
- Cortex formatted step read endpoint call: `cortex_bridge.py:424-447`.

## Criteria Map

- File/function path for LLM call preparation and `step_ref` expansion is mapped: satisfied by R214 path map.
- Projection selection inputs are identified: satisfied by R214 citing current round, `_round_id`, latest tool calls, and tool name.
- Raw durable payloads are not directly inserted by this path: satisfied by runtime consuming only Cortex `read_step_formatted` `content`.

## Execution Map

- T217 was a bounded audit one-go ticket.
- R214 records source inspection and no code changes.

## Stress Test

The check distinguishes LLM formatted expansion from preview/summary expansion, reducing the risk of mistakenly accepting the wrong path as proof.

## Residual Risk

Non-blocking: this maps the path; sibling problems verify media/history behavior and active-stack ordering.

## Result IDs

- R214

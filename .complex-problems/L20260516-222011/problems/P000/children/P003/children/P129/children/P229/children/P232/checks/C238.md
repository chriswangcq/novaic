# Check: Cortex event projection preserves payload pointers

## Summary

`P232` is solved by `R224`. The event writer and projection layer preserve compact observation content plus refs; they do not perform default full payload reads or inline durable payload bodies into projected context.

## Evidence

- `context_event_writer.py:201-239` records `ToolStepRecorded` with observation and optional `step_ref`/`payload_ref` metadata.
- `context_event_projection.py:350-390` builds tool messages from observation preview/summary/head or stable JSON and keeps refs in `step_ref`/`_metadata`.
- Event projection tests preserve payload refs and stable step refs for externalized payloads.
- Focused tests passed: `35 passed in 0.34s`.

## Criteria Map

- Event writer/projection paths are mapped with file/function pointers: satisfied by writer/projection evidence.
- Projection behavior preserves refs and compact summaries rather than full payload bytes/text: satisfied by `_tool_result_content` and tests around payload refs/externalized payloads.
- Focused event projection tests pass: satisfied by `test_context_event_projection.py` and `test_context_event_api_steps_write.py` passing.

## Execution Map

- Ticket `T228` ran a bounded event projection audit.
- Execution inspected writer/projection code and ran focused tests.
- Result `R224` recorded evidence and known sibling scope.

## Stress Test

The plausible failure is an externalized blob payload returning to normal context via event projection. Tests cover externalized blob payload refs: projected tool messages keep stable `step_ref` and `payload_ref` metadata, while content comes from compact observation summary/preview.

## Residual Risk

Non-blocking for `P232`: runtime LLM message expansion could still misuse projected step refs; this is sibling `P233`.

## Result IDs

- `R224`

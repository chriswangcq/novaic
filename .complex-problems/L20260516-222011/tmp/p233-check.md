# Check: runtime LLM context expansion avoids full payload reads

## Summary

`P233` is solved by `R225`. The default runtime context expansion path resolves tool results through formatted step projection (`/v1/steps/read_formatted`) and does not call full payload read APIs. Tests cover required step refs, projection selection, old display non-reinjection, and prepared LLM message ordering.

## Evidence

- `prepare_llm_call` delegates to injected `expand_messages_for_llm`, `sanitize_context`, and `process_multimodal_messages`.
- `expand_messages_for_llm` requires `step_ref`, calls `fetch_step_for_llm`, and uses projection metadata rather than inline content.
- `CortexBridge.read_step_formatted` posts to `/v1/steps/read_formatted`; runtime search found `/v1/payload` only in explicit payload tool surface, not default expansion.
- Focused tests passed: `36 passed in 0.15s`.

## Criteria Map

- Runtime message expansion path is mapped with file/function pointers: satisfied by `llm_call.py`, `step_result_client.py`, and `cortex_bridge.py` evidence.
- Evidence shows default context preparation uses formatted projection APIs, not `/v1/payload/read` or equivalent full durable payload reads: satisfied by read_step_formatted path and negative search evidence.
- Focused runtime tests verify historical shell/display outputs remain compact in LLM request messages: satisfied by `test_pr71_no_tool_retry_context_cleanup.py`, `test_no_historical_tool_image_injection.py`, and `test_runtime_explicit_contracts.py`.

## Execution Map

- Ticket `T229` ran a bounded context-expansion audit.
- Execution inspected code, searched payload API usage, ran focused tests, and recorded `R225`.

## Stress Test

The plausible failure is an old display screenshot or huge shell output being re-read from durable payload and inserted as raw text/base64 in a later LLM call. The code path only requests formatted projections; tests include old display not being re-injected after a new tool block and prepared LLM call inserting display perception image before the following system message with placeholder text in the tool result.

## Residual Risk

Non-blocking for `P233`: explicit payload CLI/tools still intentionally exist and are separately audited in `P228`/`P230`; this check only covers default context assembly.

## Result IDs

- `R225`

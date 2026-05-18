# Runtime step result expansion path map result

## Summary

Mapped runtime LLM step-ref expansion. Runtime prepares LLM calls by expanding tool `step_ref` messages through `expand_messages_for_llm`, which calls Cortex `/v1/steps/read_formatted` with an explicit projection mode. No direct raw durable payload insertion was found in this path.

## Done

- Mapped LLM handler wiring: `novaic-agent-runtime/task_queue/handlers/llm_handlers.py:117-127` injects `expand_messages_for_llm`, `sanitize_context`, and `process_multimodal_messages` into `prepare_llm_call`.
- Mapped preparation order: `novaic-agent-runtime/task_queue/contracts/llm_call.py:115-145` expands step refs first, then sanitizes tool-message adjacency, then performs multimodal processing.
- Mapped step-ref client: `novaic-agent-runtime/task_queue/utils/step_result_client.py:166-212` replaces tool messages' `content` by calling `fetch_step_for_llm` and attaches `_projection`.
- Mapped Cortex bridge boundary: `novaic-agent-runtime/task_queue/utils/cortex_bridge.py:424-447` calls `/v1/steps/read_formatted` with tenant, scope/tool ids, provider, projection, and optional `step_ref`.

## Verification

- Projection selection inputs are explicit in `step_result_client.py:119-139`: current round id, message `_round_id`, latest tool call ids, and tool name.
- Raw durable payload is not directly inserted by the runtime expansion path; the runtime consumes only the formatted `content` returned by Cortex `read_step_formatted`.
- Preview/summary expansion uses a separate `read_step_preview` path (`step_result_client.py:142-163`, `215+`) rather than the LLM formatted-content path.

## Known Gaps

- No direct raw-payload insertion gap found in this mapping ticket. Current/history media behavior is verified by sibling P226/P227.

## Artifacts

- `novaic-agent-runtime/task_queue/handlers/llm_handlers.py`
- `novaic-agent-runtime/task_queue/contracts/llm_call.py`
- `novaic-agent-runtime/task_queue/utils/step_result_client.py`
- `novaic-agent-runtime/task_queue/utils/cortex_bridge.py`

# Agent runtime context client and history expansion audit result

## Summary

Completed runtime context client and history expansion audit. Runtime expands tool `step_ref` results through Cortex formatted projections, gates provider media to current display perception only, keeps shell/blob payloads as bounded text/manifest, and has targeted active-stack ordering coverage.

## Done

- P225/R214 mapped the runtime LLM preparation and step-ref expansion path to Cortex `/v1/steps/read_formatted`.
- P226/R215 verified current versus historical media boundary and shell/tool output bounds with runtime tests.
- P227/R216 verified active-stack/system-message ordering does not suppress current display media.

## Verification

- Runtime step-ref expansion path uses explicit projection modes and does not directly insert raw durable payloads.
- Runtime current/history media boundary tests passed: `23 passed in 0.09s`.
- Runtime active-stack ordering test file passed: `9 passed in 0.08s`.
- Current display image user message is present even when a system Active Skill Stack message follows the display result.

## Known Gaps

- No blocking runtime context expansion gap found. Provider ordering policy changes would require a future provider-specific design, not a current runtime fix.

## Artifacts

- R214
- R215
- R216
- `novaic-agent-runtime/task_queue/contracts/llm_call.py`
- `novaic-agent-runtime/task_queue/utils/step_result_client.py`
- `novaic-agent-runtime/task_queue/utils/context.py`
- `novaic-agent-runtime/task_queue/utils/multimodal.py`
- `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py`

# Remove include_display From Step Formatting Projection API

## Problem Definition

The step formatting path still accepts and forwards `include_display`, which is an old boolean projection selector. The current contract should be explicit `projection` mode only.

## Proposed Solution

Remove `include_display` from the request/client path:

1. Cortex:
   - Remove `include_display` from `StepFormattedRequest`.
   - Make `/v1/steps/read_formatted` accept only `history`, `current_tool_result`, and `display_perception`; raise a clear HTTP 400 for unsupported values.
2. Runtime bridge/client:
   - Remove `include_display` argument and payload field from `CortexBridge.read_step_formatted`.
   - Remove `include_display` argument forwarding from `expand_step_ref_to_content` and `fetch_step_for_llm`.
   - Update `expand_messages_for_llm` to pass only `projection`.
3. Tests:
   - Update runtime tests to assert projection-only payloads.
   - Add/keep Cortex tests for invalid projection rejection if needed.

## Acceptance Criteria

- `include_display` no longer appears in `StepFormattedRequest`, `CortexBridge.read_step_formatted`, `expand_step_ref_to_content`, `fetch_step_for_llm`, or `expand_messages_for_llm`.
- `/v1/steps/read_formatted` has no boolean projection branch.
- Runtime tests assert only explicit `projection` is sent.
- Static search shows remaining `include_display` hits are only unrelated `resolve_for_llm` byte-resolution behavior or tests for that behavior.
- Targeted Cortex and runtime tests pass.

## Verification Plan

```bash
rg -n "include_display" novaic-cortex/novaic_cortex/api.py novaic-agent-runtime/task_queue/utils/cortex_bridge.py novaic-agent-runtime/task_queue/utils/step_result_client.py novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py -S
PYTHONPATH="novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk:novaic-common" python3 -m pytest -q novaic-cortex/tests/test_step_result_projection.py novaic-cortex/tests/test_tool_output_projection.py novaic-cortex/tests/test_context_event_no_compat.py
PYTHONPATH="novaic-agent-runtime:novaic-common" python3 -m pytest -q novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py
python3 -m py_compile novaic-cortex/novaic_cortex/api.py novaic-agent-runtime/task_queue/utils/cortex_bridge.py novaic-agent-runtime/task_queue/utils/step_result_client.py
```

## Risks

- Any external caller still sending `include_display` will be ignored/rejected depending on API model behavior; this is intentional under the no-compat cleanup principle.
- Runtime tests may need precise payload expectation updates.

## Assumptions

- Existing runtime callers already derive an explicit `projection`; the boolean is redundant.
- `resolve_for_llm(include_display=...)` is a separate low-level byte-resolution option and not part of this step formatting API cleanup.

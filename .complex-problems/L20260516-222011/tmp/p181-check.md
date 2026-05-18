# P181 success check

## Summary

P181 is successful. R167 maps the final active-stack injection path and proves the relevant ordering behavior with tests. The important conclusion is that active-stack injection is a transient common-assembly system message, while current display projection is keyed by round/tool metadata rather than final message position.

## Evidence

- Injection source identified in `novaic-common/common/contracts/llm_assembly.py`.
- Runtime delegation identified in `novaic-agent-runtime/task_queue/handlers/cortex_handlers.py`.
- Provider-facing expansion order identified in `novaic-agent-runtime/task_queue/contracts/llm_call.py`.
- Current display projection criteria identified in `novaic-agent-runtime/task_queue/utils/step_result_client.py`.
- Focused tests passed: `40 passed in 0.15s`.

## Criteria Map

- Active stack injection source identified: satisfied.
- Ordering relative to tool results, step-ref expansion, and provider formatting documented: satisfied.
- Tests prove ordering does not convert current tool output to historical output: satisfied by the test that injects display image before a following system message.
- Duplicate or stale final-injection path removed or split: satisfied; no duplicate final injection path found.

## Execution Map

- T171 was a bounded one-go source/order audit.
- No production changes were required because source inspection and tests showed the path is already explicit and covered.

## Stress Test

The stress case is exactly the previous bug shape: a display tool result followed by a system stack message. The focused test asserts the prepared provider messages become assistant, tool placeholder, user image, then system stack message, and that the display projection remains `display_perception`.

## Residual Risk

- Non-blocking: P182 still owns broader display/media regression coverage. P181 only proves injection ordering and non-positional current detection.

## Result IDs

- R167

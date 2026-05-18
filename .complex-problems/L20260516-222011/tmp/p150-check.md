# runtime bridge step shape success check

## Summary

Success. `R129` maps the runtime producer paths and verifies they produce structured `observation`/payload-ref step requests rather than legacy inline `result` fields.

## Evidence

- Bridge write endpoint wrapper: `novaic-agent-runtime/task_queue/utils/cortex_bridge.py:343-353`.
- Bridge tool-step producer: `novaic-agent-runtime/task_queue/utils/cortex_bridge.py:355-391`.
- React action producer: `novaic-agent-runtime/task_queue/contracts/react_actions.py:202-259`.
- Existing React action test asserts no `result`, payload, `payload_ref`, and observation payload ref.
- Extended bridge test asserts no `result`, payload, `payload_ref`, `step_ref`, and observation payload ref.
- Verification: `28 passed in 0.14s`.

## Criteria Map

- Runtime bridge call sites mapped: satisfied.
- Produced request shape includes structured observation and payload refs: satisfied by source and tests.
- No active runtime bridge inline raw `result`: satisfied by tests and source scan.
- Live shell/tool output follows new contract: satisfied by React action save-results task test plus bridge producer test.

## Execution Map

- Result `R129` inspected both bridge and React action producers, found bridge coverage too shallow, added shape assertions, and reran focused runtime/common tests.

## Stress Test

- The bridge test simulates a shell result with full payload and verifies the generated request has payload plus refs and no `result`.
- The React action test exercises the LLM tool-result save path that real agent loops use after tool calls.

## Residual Risk

- Non-blocking for `P150`: repository-wide bypass scanning remains under `P151`.

## Result IDs

- `R129`

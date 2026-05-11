# Diagnose production HD screenshot wake stall result

## Summary

The production issue was traced to a Cortex context/tool-result reference contract bug, not deployment health. The wake had already finalized through a `react_think_failed` compensation path after the screenshot/tool step. The LLM context assembler could not resolve a tool result because a blob payload URI was projected as the step reference.

## Child Results

- `P001 / R000`: Identified the exact production state:
  - affected session and wake were no longer active.
  - failure path was `react_think` / `llm.call`.
  - error was `Tool result not found: blob://cortex-payload/...`.
  - payload manifest proved the blob existed and mapped back to a stable `step-ref`.
- `P002 / R001`: Fixed the active Cortex path:
  - separated stable `step_ref` from concrete `payload_ref`.
  - projected stable step refs into tool messages.
  - made formatted-step lookup robust to stable step refs and payload refs.
  - fixed cross-wake `skill_end` idempotency conflicts discovered during verification.
  - tests, deploy, and smoke were completed.
- `P003 / R002`: Verified recovery:
  - full Cortex suite passed.
  - runtime cleanup regression passed.
  - services deployed successfully.
  - final smoke reached `session_closed` with `stack_empty`.
  - no post-fix non-done queue tasks remained after the smoke window.

## Acceptance Criteria Map

- Production evidence identifies stuck wake/session/saga/task IDs: satisfied by `P001`.
- Root cause tied to a specific state transition or service boundary: satisfied by `P002`, specifically Cortex projection/read-formatted boundary for externalized tool payloads.
- Fix applied to active path: satisfied by changes in active Cortex API, workspace normalization, event writer, and event projection code.
- Tests or smoke prove progress past failing point: satisfied by `P003`.
- Remaining risks explicit: historical stale UI/DB artifacts may remain; post-fix durable state is clean.

## Done

The live stall was diagnosed, fixed, deployed, and verified with durable production state.

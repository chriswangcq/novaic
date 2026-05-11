# Root cause and fix success check

## Summary

Success. Result `R001` identifies a concrete non-deploy root cause and records a deployed fix that addresses both the original tool-result lookup failure and the verification-discovered `skill_end` idempotency conflict.

## Evidence

- The original wake finalized through `compensation:react_think_failed`, proving it was not a still-running wake.
- The failing LLM context expansion reported `Tool result not found` for a `blob://cortex-payload/...` URI.
- The payload manifest showed the blob existed and mapped back to stable source step `step-ref:f1c26fff-6141-4dc1-9702-69f4200fc2e8:round2:shell:1`.
- Code now persists stable `step_ref` separately from blob `payload_ref`, projects stable step refs into tool messages, and keeps formatted lookup compatible with both refs.
- Code now includes stable step identity in tool-step idempotency keys, preventing cross-wake `skill_end:3` conflicts.
- Full Cortex suite passed with `487 passed`.
- Runtime cleanup regression passed with `11 passed`.
- Services were deployed successfully and worker roster was healthy.
- Final smoke message `08ae61f4e3db` reached `session_closed`/`stack_empty`, with all related sagas completed and no non-done queue tasks after the smoke window.

## Criteria Map

- Explain why the UI looked stuck: mapped to wake finalization through `react_think_failed` after tool completion, while the UI card was stale/completed rather than an active deploy stall.
- Identify the exact technical break: mapped to blob payload URI being used where stable formatted step lookup expected a stable `step_ref`.
- Fix the break: mapped to `workspace.py`, `context_event_writer.py`, `context_event_projection.py`, and `api.py` changes.
- Check related risks: mapped to discovery and fix of the `skill_end` idempotency conflict.
- Verify end to end: mapped to full tests, deploy, and final smoke with clean queue state.

## Execution Map

- `R001` executed investigation, code changes, tests, deploy, and smoke verification.
- The implementation did not rely on deploy restart alone; it changed the state/reference contract that caused the failure.

## Stress Test

- Externalized payload path was tested: a tool result with blob payload still resolves through stable step ref.
- Compatibility path was tested: formatted step lookup can resolve both stable step refs and payload refs.
- Repeated finalization path was tested: `skill_end` idempotency now includes stable step identity, covering repeated `skill_end:3` call ids across wakes.
- Live smoke covered the complete queue/saga/session path through final `stack_empty`.

## Residual Risk

- Non-blocking: historical failed task rows from before the fix may remain in the database as audit history, but the final smoke after deploy produced no new non-done tasks.
- Non-blocking: the UI may still show older completed cards until refreshed; backend session state and queue events show clean closure.

## Result IDs

- R001

# Root cause and fix result

## Summary

The screenshot wake was not stuck because deployment or workers were down. It failed after a shell/tool step completed, while preparing the next LLM context. The context projection emitted a blob payload URI as the tool result step reference, but the formatted-step reader only resolved stable `step_ref` values. The LLM provider then rejected context expansion with `Tool result not found: blob://cortex-payload/...`.

During verification, a second real bug surfaced: `skill_end` step events could reuse the same idempotency key across wakes because the old key was based on the active root scope plus `call_id` like `skill_end:3`. That caused `/v1/steps/write` conflicts after finalization paths.

## Root Cause Evidence

- Target wake: `f1c26fff-6141-4dc1-9702-69f4200fc2e8`.
- Queue session finalized with `compensation:react_think_failed`, not an active/deploy stall.
- Failed LLM context expansion referenced `blob://cortex-payload/cpx-2d901bb3b40a91c28f3663ec70184dcf167e0017`.
- Cortex payload manifest showed that blob was available and linked to stable source step `step-ref:f1c26fff-6141-4dc1-9702-69f4200fc2e8:round2:shell:1`.
- Therefore the blob existed; the broken part was the reference contract between context projection and formatted step lookup.

## Code Changes

- `novaic-cortex/novaic_cortex/workspace.py`
  - Preserve a stable `step_ref` before payload externalization.
  - Store the actual blob URI separately as `payload_ref`.
- `novaic-cortex/novaic_cortex/context_event_writer.py`
  - Accept and persist explicit `step_ref`.
  - Use `step_ref` or payload ref in the tool-step idempotency key instead of only root scope plus `call_id`.
- `novaic-cortex/novaic_cortex/context_event_projection.py`
  - Emit stable `step_ref` in projected tool messages.
  - Keep blob URI as payload metadata instead of replacing the step identity.
- `novaic-cortex/novaic_cortex/api.py`
  - Pass stable `step_ref` through `/v1/steps/write`.
  - Allow formatted step lookup to resolve both stable step refs and payload refs for compatibility with already written records.
- Tests added in:
  - `novaic-cortex/tests/test_context_event_api_steps_write.py`
  - `novaic-cortex/tests/test_context_event_projection.py`
  - `novaic-cortex/tests/test_context_event_writer.py`

## Verification

- Targeted Cortex tests passed:
  - `tests/test_context_event_writer.py`
  - `tests/test_context_event_api_steps_write.py`
  - `tests/test_context_event_projection.py`
  - `tests/test_step_index_outcome.py`
- Full Cortex suite passed: `487 passed`.
- Agent runtime cleanup regression passed: `tests/test_pr71_no_tool_retry_context_cleanup.py`, `11 passed`.
- `./deploy services` completed successfully.
- Deployed worker roster was healthy:
  - task-worker control/execution
  - saga-worker
  - session-outbox-worker
  - saga-outbox-worker
  - health
  - scheduler
  - subscriber
- Final smoke message `08ae61f4e3db` completed:
  - session transitioned to `no_active`, generation `5`.
  - latest close reason was `stack_empty`.
  - all related sagas completed.
  - no non-done queue tasks existed after the final smoke window.

## Done

The original stall and the verification-discovered idempotency conflict were both fixed, deployed, and smoke tested. The remaining work is problem-level closure verification, not more implementation for this root-cause ticket.

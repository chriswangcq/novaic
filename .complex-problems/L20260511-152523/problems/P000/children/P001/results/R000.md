# Live production stall diagnosis result

## Summary

The live stall after one agent loop is caused by a chained failure across shell capability auth, context event projection, and wake finalization compensation.

## Done

Observed production state:

- `tq_session_state` has one active session for `822af016-31a1-49bb-b529-9b8f539a0831:main-822af016`, generation `9`, scope `226b3a1f-535b-4f0b-bd63-a10cdad62380`, updated at `2026-05-11T07:18:53.747Z`, but no healthy follow-up progress.
- Recent sagas show `subagent_wake`, `react_think`, and `react_actions` completed, then `react_think` failed with `Tool message missing step_ref`.
- The following `wake_finalize` compensation saga failed with Cortex `/v1/scope/end` 500.
- Cortex log shows `/v1/scope/end` raised `FileNotFoundError: no active root scope '226b3a1f-535b-4f0b-bd63-a10cdad62380'`.

Root cause chain:

1. The agent loop invoked shell capability `agentctl im read`.
2. `agentctl` called Cortex `/v1/meta/read` without `X-Internal-Key`; Cortex rejected it with `HTTP 401 missing or invalid X-Internal-Key`.
3. Runtime recorded the shell tool error, but Cortex context event projection emitted the tool message without a top-level `step_ref`; the `payload_ref` existed only inside `_metadata`.
4. The next `react_think` failed before calling the LLM because `expand_messages_for_llm` requires top-level `step_ref` for tool messages.
5. Saga failure compensation created a `wake_finalize` saga, but the compensation context only preserved `scope_id`, `agent_id`, `subagent_id`, `user_id`, and `finalize_reason`.
6. Because `agent_root_scope_id`, `wake_scope_path`, `session_generation`, and stack/finalize metadata were dropped, `cortex_scope_end` treated the wake scope as a root scope and failed.
7. Because `wake_finalize` failed before `session_ended`, the session stayed `active`, so new messages attached to a stale session instead of cleanly starting/recovering a wake.

Important code locations:

- `novaic-cortex/novaic_cortex/shell_capabilities.py`: shell capability CLI does not forward `X-Internal-Key` to Cortex internal APIs.
- `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`: shell capability environment does not provide the Cortex internal key.
- `novaic-cortex/novaic_cortex/context_event_projection.py`: `_tool_result_message` does not set top-level `step_ref`.
- `novaic-agent-runtime/queue_service/saga_repo.py`: `_build_wake_finalize_compensation_effect` drops finalize/session/root context.

## Verification

- Queue DB sagas:
  - `saga-5aa744936407` failed `react_think` with `Tool message missing step_ref`.
  - `saga-90dbc6ef770a` failed `wake_finalize` with Cortex `/v1/scope/end` 500.
- Task failures:
  - `llm.call` failed before model execution due missing `step_ref`.
  - `cortex.scope_end` failed because the wake scope was passed as if it were an active root scope.
- Logs:
  - `task-worker-control-2.log` recorded `shell:agentctl: HTTP 401 from /v1/meta/read: {"error":"missing or invalid X-Internal-Key"}`.
  - `cortex.log` recorded `FileNotFoundError: no active root scope '226b3a1f-535b-4f0b-bd63-a10cdad62380'`.

## Known Gaps

The live stuck session will likely need either successful watchdog recovery or an explicit repair after code deployment, because the current DB row is already stale active state. Code repair alone prevents the next recurrence but may not automatically clear this already-failed session unless the recovery path is triggered and works.

## Artifacts

- `.complex-problems/_drafts/L-agent-loop-stall/p001-result.md`

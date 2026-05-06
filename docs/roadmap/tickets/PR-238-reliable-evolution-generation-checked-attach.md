# PR-238 Reliable Evolution FSM-04 Generation Checked Attach

Status: `[x]`

## Goal

Prevent stale active-input attach tasks from appending new user messages to an
old wake after the active wake has changed. Attach must carry an explicit
expected wake identity and session generation, then the handler must verify the
current Cortex agent-root state before mutating scope inputs.

## Scope

- Runtime only: `novaic-agent-runtime`.
- Add `session_generation` to wake saga/session.init payloads.
- Persist `current_session_generation` beside `current_wake_scope_id` in agent-root meta.
- Add `expected_wake_scope_id` and `expected_session_generation` to `session.attach_input` payloads.
- Reject stale attach tasks before `append_scope_input`.
- Add tests for generation persistence and stale attach rejection.

## Out Of Scope

- Do not make `tq_session_state` the live source of truth.
- Do not delete old attach publish path.
- Do not implement outbox cutover.
- Do not change LLM behavior.

## Small Tickets

- [x] **FSM-04-A Explicit generation envelope**: include `session_generation` in wake saga context and session.init payload.
- [x] **FSM-04-B Root meta CAS source**: persist current wake scope and generation on agent-root meta.
- [x] **FSM-04-C Attach CAS payload**: include expected wake scope and expected generation in attach task payload.
- [x] **FSM-04-D Handler guard**: read agent-root meta with fail-closed semantics and reject stale scope/generation before appending inputs.
- [x] **FSM-04-E Tests**: prove session.init persists generation and stale attach is rejected.

## Implementation Files

- `novaic-agent-runtime/queue_service/session_repo.py`
- `novaic-agent-runtime/task_queue/sagas/subagent_wake.py`
- `novaic-agent-runtime/task_queue/handlers/runtime_handlers.py`
- `novaic-agent-runtime/tests/test_pr153_pending_trigger_metadata.py`
- `novaic-agent-runtime/tests/test_pr233_active_inbox_dispatch.py`
- `novaic-agent-runtime/tests/test_pr237_session_outbox_observe.py`
- `novaic-agent-runtime/tests/test_pr238_generation_checked_attach.py`

## Legacy Cleanup Ledger

Keep these deliberately for now:

- Direct `session.attach_input` publish path.
- Shadow generation is still derived from the shadow session ledger until the full FSM state becomes authoritative.

Deletion criteria:

- Delete no legacy path in PR-238.
- Later FSM cutover may remove scope-only attach assumptions once generation is carried end-to-end by the authoritative FSM state.

## Verification

- `pytest tests/test_pr238_generation_checked_attach.py tests/test_pr233_active_inbox_dispatch.py tests/test_pr153_pending_trigger_metadata.py tests/test_pr237_session_outbox_observe.py`
- `pytest`
- `git diff --check`

## Review Result

Pass. Attach is now guarded by explicit expected state rather than ambient
"current active" assumptions. The guard is local to the handler and fails
closed before writing Cortex inputs.

## Rollback

Revert this PR. Existing live attach behavior returns if the expected fields
are no longer sent; the schema changes from prior PRs are additive.

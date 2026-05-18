# P496 attach generation contract classification

## Raw Evidence

- Raw guard output: `.complex-problems/L20260516-222011/tmp/p496/attach-generation-raw-guards.txt` (`1312` lines)
- File list: `.complex-problems/L20260516-222011/tmp/p496/attach-generation-files.txt`

## Strict Runtime Validation

- `novaic-agent-runtime/task_queue/handlers/runtime_handlers.py:220-320`
  - `handle_session_attach_input()` requires `expected_wake_scope_id` and `expected_session_generation`.
  - It compares `expected_wake_scope_id` against `current_wake_scope_id`.
  - It compares `expected_session_generation` against `current_session_generation`.
  - Stale scope/generation raises `ValidationError` before appending inputs.

## Durable Outbox Boundary

- `novaic-agent-runtime/queue_service/session_outbox.py:225-272`
  - `_publish_attach_input()` requires `message_ids`, `scope_id`, and `expected_session_generation`.
  - It validates expected generation through `require_positive_session_generation_value()`.
  - It publishes `SESSION_ATTACH_INPUT` with `expected_wake_scope_id` and `expected_session_generation`.

## Repository Race Guard

- `novaic-agent-runtime/queue_service/session_repo.py:862-979`
  - `_record_attach_request_after_transaction()` re-reads current session state before emitting an attach outbox effect.
  - If active saga/scope changed, it records `active_session_changed_before_attach` and buffers instead of delivering stale input.
  - If still active, it derives `session_generation` from current active state and passes it into the attach effect.

## Cleanup Candidate for P497

- `novaic-agent-runtime/queue_service/session_effects.py:39-76`
  - `build_attach_input_effect()` accepts `expected_session_generation: int | None` and does not validate it before constructing the effect payload.
  - Current production caller passes a validated positive generation and session outbox validates again, so this is not an active no-generation delivery bug.
  - Still, the builder boundary should be tightened to reject missing/non-positive generation early and make the contract explicit.

## Guard/Test Fixtures

- `novaic-agent-runtime/tests/test_pr238_generation_checked_attach.py`
  - Covers missing expected generation, bool generation, stale scope, and stale generation.
- `novaic-agent-runtime/tests/test_pr248_attach_outbox_cutover.py`
  - Covers outbox attach publication, retryability, and attach-race buffering.
- `novaic-agent-runtime/tests/test_pr255_legacy_compat_cleanup.py`
  - Guards the required attach contract strings.

## No Active No-Generation Attach Path Found

- No production path was found that directly publishes `SESSION_ATTACH_INPUT` from `session_repo.py`.
- No runtime handler path was found that appends input before generation/scope validation.

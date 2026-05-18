# P498 attach generation final guard classification

## Raw Evidence

- Test log: `.complex-problems/L20260516-222011/tmp/p498/attach-generation-final-tests.log`
- Raw guard output: `.complex-problems/L20260516-222011/tmp/p498/attach-generation-final-guards-raw.txt`

## Forbidden Optional Generation Contracts

The `forbidden optional builder/session generation contracts` section is empty.

No hits remain for:

- `expected_session_generation: int | None`
- `expected_session_generation=None`
- fallback reads such as `payload.get("expected_session_generation") or ...`
- fallback reads such as `effect.get("expected_session_generation")`

## Production Strict Paths

- `novaic-agent-runtime/queue_service/session_repo.py`
  - Re-reads active session state before attach emission.
  - Buffers when the active session changed with reason `active_session_changed_before_attach`.
  - Calls `build_attach_input_effect()` with `expected_session_generation=session_generation`.
- `novaic-agent-runtime/queue_service/session_effects.py`
  - `build_attach_input_effect()` requires `expected_session_generation: int`.
  - It validates with `require_positive_session_generation_value()` before constructing payload.
  - It writes normalized `expected_session_generation` and `expected_wake_scope_id` into the payload.
- `novaic-agent-runtime/queue_service/session_outbox.py`
  - Rejects missing `expected_session_generation`.
  - Validates with `require_positive_session_generation_value()` before publishing `TaskTopics.SESSION_ATTACH_INPUT`.
- `novaic-agent-runtime/task_queue/handlers/runtime_handlers.py`
  - Requires both `expected_wake_scope_id` and `expected_session_generation`.
  - Validates generation with `require_positive_session_generation_value()`.
  - Compares current wake scope and generation before appending inputs.
- `novaic-agent-runtime/queue_service/saga_repo.py`
  - Uses the same generation helper in saga compensation/recovery paths; this is not an attach no-generation path.

## Guarded Test Fixtures

- `tests/test_pr238_generation_checked_attach.py`
  - Intentionally exercises stale scope, missing generation, bool generation, and valid attach input.
- `tests/test_pr248_attach_outbox_cutover.py`
  - Covers attach outbox publication, generated task payload, retry behavior, and attach-race buffering.
- `tests/test_pr255_legacy_compat_cleanup.py`
  - Guards that runtime/outbox required-field strings remain present.
- `tests/test_pr267_session_outbox_effect_boundary.py`
  - Covers builder payload shape, builder generation validation, outbox generation validation, and repository ownership guards.
- `tests/test_pr271_session_attach_flow_consolidation.py` and `tests/test_pr273_session_harness_final_residue_guard.py`
  - Guard that attach flow remains consolidated through one builder call.

## Conclusion

No unguarded no-generation `SESSION_ATTACH_INPUT` delivery path remains in the checked active runtime paths. Remaining attach/generation hits are strict production validation, race buffering, or intentional test guards.

# Session-ended outbox delivery generation contract

## Problem Definition

The session-ended/finalize path crosses multiple durable-effect boundaries before reaching `SessionRepository.session_ended(...)`: wake-finalize saga payload construction, queue topic publishing, session handler validation, `TaskQueueClient.session_ended(...)`, route validation, and repository mutation. P335 made the repository fail closed for missing or zero generation, but P336 must make the delivery contract explicit earlier so malformed finalize/session-ended effects are rejected before publish/delivery and cannot rely on repository fallback behavior as the first line of defense.

## Proposed Solution

1. Map the live session-ended delivery chain:
   - `task_queue/sagas/wake_finalize.py::_build_session_ended_payload`
   - `task_queue/handlers/session_handlers.py::handle_session_ended`
   - `task_queue/client.py::TaskQueueClient.session_ended`
   - `queue_service/routes.py::SessionEndedRequest`
   - tests around wake-finalize payloads and session handlers.
2. Tighten payload construction and validation so generation and scope identity are explicit positive values:
   - `wake_finalize` should not silently convert missing `session_generation` to `0`.
   - session handler should require `generation >= 1`, non-empty `scope_id`, non-empty `finalize_reason`, and `remaining_stack`.
   - client/route validation should preserve the explicit generation contract without compatibility fallback.
3. Add or update focused tests proving:
   - wake-finalize payload builder carries positive generation and finalize reason.
   - missing/zero generation is rejected by the session-ended handler before queue-service delivery.
   - client forwards generation/reason/remaining stack unchanged.
   - existing valid finalize delivery still reaches the repository.
4. Remove stale compatibility assertions or tests that allow `generation=0` for session-ended/finalize delivery.

## Acceptance Criteria

- Session-ended outbox/saga payloads include explicit `agent_id`, `subagent_id`, `scope_id`, positive `generation`, `finalize_reason`, and `remaining_stack`.
- `session.ended` handler rejects missing or non-positive generation before calling `TaskQueueClient.session_ended(...)`.
- `wake_finalize` payload construction does not use `session_generation or 0` as a compatibility fallback.
- Tests cover valid delivery, missing generation, zero generation, and payload preservation across the handler/client boundary.
- Source guards show no finalize/session-ended delivery code silently fills missing generation from current state.

## Verification Plan

- Run focused tests:
  - `tests/test_pr254_finalize_ownership.py`
  - any session handler/client tests added for this ticket.
  - `tests/test_pr255_legacy_compat_cleanup.py` if touched.
- Run source guards for `session_generation or 0` and `generation=0` compatibility in `task_queue/sagas/wake_finalize.py`, `task_queue/handlers/session_handlers.py`, and relevant tests.
- Run `python3 -m py_compile` on changed task-queue modules.

## Risks

- Upstream contracts `react_think.py` and `react_actions.py` still default `session_generation` to `0`; if those are needed to fully remove zero-generation production, split or defer that broader contract cleanup to P337/P339 rather than diluting this outbox delivery ticket.
- Tight validation may expose tests or recovery flows that relied on missing generation compatibility; those should be rewritten rather than preserved.

## Assumptions

- No backward compatibility is required for session-ended/finalize delivery payloads missing generation.
- P335 remains the repository fail-closed guard, while P336 improves the delivery boundary so bad payloads are rejected earlier.

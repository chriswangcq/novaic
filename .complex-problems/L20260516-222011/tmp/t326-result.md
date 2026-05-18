# Repository finalize generation atomicity result

## Summary

Repository-backed finalize now rejects missing or non-positive generations before it can reach the session FSM, and the pure FSM no longer treats `finalize_generation=0` as "use the current generation". This removes the dangerous compatibility fallback where a missing generation could accidentally finalize the currently active session when the scope id matched.

## Done

- Updated `novaic-agent-runtime/queue_service/session_repo.py` so `SessionRepository.session_ended(...)` requires an explicit generation and raises `ValueError` for `generation < 1`.
- Updated `novaic-agent-runtime/queue_service/session_fsm.py` so `_reduce_session_finalize(...)` rejects `finalize_generation < 1` with `REJECT_FINALIZE` / `missing_generation`.
- Removed the repository/FSM fallback `event_generation = finalize_generation or current_generation`; event generation is now the explicit finalize generation.
- Added regression coverage in `novaic-agent-runtime/tests/test_pr254_finalize_ownership.py` for repository `generation=0`.
- Added pure FSM regression coverage in `novaic-agent-runtime/tests/test_pr264_session_finalize_fsm_boundary.py` for `finalize_generation=0`.

## Verification

- Ran `python3 -m py_compile queue_service/session_repo.py queue_service/session_fsm.py`.
- Ran focused regression suite from `novaic-agent-runtime`: `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr254_finalize_ownership.py tests/test_pr264_session_finalize_fsm_boundary.py tests/test_pr285_session_fsm_decision_contract.py tests/test_pr243_inbox_restart_cutover.py tests/test_pr241_pending_inbox_projection.py tests/test_pr251_wake_creation_outbox_cutover.py`.
- Result: `23 passed in 0.22s`.
- Ran a source guard for `finalize_generation or current_generation` across repository/FSM/tests; no matches remain.

## Known Gaps

- Upstream producer paths still contain `session_generation or 0` in `task_queue/sagas/wake_finalize.py`, `task_queue/contracts/react_think.py`, and `task_queue/contracts/react_actions.py`. Those are intentionally deferred to the already split follow-on finalize boundary tickets P336/P337/P339 rather than hidden inside this repository atomicity ticket.
- Startup rebuild fallback `context.get("session_generation") or 1` remains in scope for P329.

## Artifacts

- `novaic-agent-runtime/queue_service/session_repo.py`
- `novaic-agent-runtime/queue_service/session_fsm.py`
- `novaic-agent-runtime/tests/test_pr254_finalize_ownership.py`
- `novaic-agent-runtime/tests/test_pr264_session_finalize_fsm_boundary.py`

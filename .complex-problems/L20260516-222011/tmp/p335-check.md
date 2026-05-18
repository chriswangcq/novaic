# Repository finalize generation atomicity check

## Summary

Success. The one-go result is acceptable only because the repository/FSM mutation boundary now fails closed on missing or zero finalize generation, the stale generation/scope paths remain covered, and valid finalize still clears the intended session through the existing transaction. I am not treating upstream zero-generation producers as solved here; those remain explicitly assigned to P336/P337/P339 and P329.

## Evidence

- `novaic-agent-runtime/queue_service/session_repo.py` validates `generation is not None`, `remaining_stack is not None`, converts to `finalize_generation`, and raises `ValueError` when `finalize_generation < 1` before entering the global transaction's finalize decision path.
- `novaic-agent-runtime/queue_service/session_repo.py` keeps finalize decision, `record_session_finalized(...)`, pending projection, optional restart outbox, and active-state mutation under one `self.db.transaction(lock_type="global")` block.
- `novaic-agent-runtime/queue_service/session_fsm.py` now rejects `finalize_generation < 1` with `REJECT_FINALIZE` / `missing_generation` and sets accepted `event_generation = finalize_generation`; the old `finalize_generation or current_generation` fallback is gone.
- `novaic-agent-runtime/tests/test_pr254_finalize_ownership.py` contains repository coverage for missing generation, zero generation, valid finalize, stale generation, stale scope, and handler generation requirements.
- `novaic-agent-runtime/tests/test_pr264_session_finalize_fsm_boundary.py` contains pure FSM coverage for no active state, zero finalize generation, stale generation, stale scope, and valid finalize acceptance.
- Verification command rerun during the check: `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr254_finalize_ownership.py tests/test_pr264_session_finalize_fsm_boundary.py tests/test_pr285_session_fsm_decision_contract.py tests/test_pr243_inbox_restart_cutover.py tests/test_pr241_pending_inbox_projection.py tests/test_pr251_wake_creation_outbox_cutover.py` -> `23 passed in 0.23s`.
- Source guard rerun during the check found no `finalize_generation or current_generation` fallback in repository/FSM finalize paths.

## Criteria Map

- Map repository methods that mutate active session state during finalize/session-ended/restart/rebuild: satisfied for this problem's boundary by P334 inventory plus the P335 check inspection of `SessionRepository.session_ended(...)`, `record_session_finalized(...)`, pending projection, and restart effect creation. Startup rebuild is explicitly outside P335 and remains P329.
- Verify or implement generation/scope checks inside the same transaction as active clearing or pending restart projection: satisfied; positive generation validation occurs before transaction entry, and scope/generation FSM validation plus finalize/restart state mutation happen inside the global transaction.
- Remove unsafe implicit active-generation lookup or generation fallback behavior for finalize mutations: satisfied; pure FSM accepted finalize no longer converts zero to current generation, and repository rejects zero before FSM dispatch.
- Add tests proving stale finalize/session-ended repository calls do not clear newer active sessions: satisfied by existing stale generation and stale scope repository tests in `test_pr254_finalize_ownership.py`.
- Add tests proving valid finalize still clears/archives the intended active generation: satisfied by valid finalize/restart coverage in `test_pr254_finalize_ownership.py` and pure FSM acceptance coverage in `test_pr264_session_finalize_fsm_boundary.py`.

## Execution Map

- Code execution boundary: `SessionRepository.session_ended(...)` is the single repository API under test.
- Decision boundary: `decide_session_finalize(SessionFinalizeInput(...))` rejects missing/zero/stale/scope-mismatched finalize inputs before active-state mutation is allowed.
- Mutation boundary: `record_session_finalized(...)`, pending input projection, optional restart transition effect, and final return happen within the same global transaction after successful validation.
- Test boundary: repository tests exercise mutation side effects; FSM tests exercise pure decision semantics; existing inbox/restart tests guard pending restart behavior.

## Stress Test

- Plausible failure mode tested: an old wake finalize event sends `generation=0` while a newer active session exists with the same scope id, and the old compatibility code treats `0` as "current". The new repository validation raises before state mutation, and the pure FSM separately rejects zero as `missing_generation`.
- Plausible race mode tested by existing coverage: stale generation or stale scope returns `finalize_rejected` and leaves active session state intact.
- Regression guard: source search confirms the exact unsafe fallback expression no longer exists in the repository/FSM finalize path.

## Residual Risk

- Non-blocking for P335: upstream builders still use `session_generation or 0`; that is not hidden or accepted as compatible and is already split into P336/P337/P339.
- Non-blocking for P335: startup rebuild still has a separate fallback concern; that is already isolated as P329.
- Remaining risk if P336/P337 are not completed: callers may still produce zero-generation payloads, but after P335 those payloads fail closed at the repository/FSM boundary rather than clearing the wrong active session.

## Result IDs

- R321

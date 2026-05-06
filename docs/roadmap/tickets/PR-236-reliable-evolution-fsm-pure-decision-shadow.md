# PR-236 Reliable Evolution FSM-02 Pure Decision Shadow

Status: `[x]`

## Goal

Introduce the next Queue session harness decision model as a pure FSM function,
then run it in observe-only mode beside the existing `SessionRepository`
branches. This PR must prove old and new dispatch decisions agree without
changing live routing.

## Scope

- Runtime only: `novaic-agent-runtime`.
- Add explicit FSM input/state/decision contracts.
- Keep old `dispatch()` branches as the live path.
- Write old/new decision trace into the FSM-01 shadow event payload.
- Add tests for the current route matrix and shadow drift recording.

## Out Of Scope

- Do not replace the existing `dispatch()` if/else routing.
- Do not use the new FSM decision to create, attach, buffer, or recover.
- Do not publish from durable outbox.
- Do not delete legacy active/pending tables.

## Small Tickets

- [x] **FSM-02-A Pure contract**: add `SessionRuntimeState`, `SessionDispatchInput`, and `SessionDispatchDecision`.
- [x] **FSM-02-B Route equivalence**: make the pure FSM mirror the current start/attach/buffer matrix.
- [x] **FSM-02-C Shadow trace**: record legacy action, shadow action, mapped legacy action, reason, and drift flag in `tq_session_events.payload`.
- [x] **FSM-02-D No cutover**: keep all existing `SessionRepository` return values and DB writes authoritative.
- [x] **FSM-02-E Tests**: prove the matrix matches and drift is false for start, attach, and buffer paths.

## Implementation Files

- `novaic-agent-runtime/queue_service/session_fsm.py`
- `novaic-agent-runtime/queue_service/session_repo.py`
- `novaic-agent-runtime/tests/test_pr236_session_fsm_shadow_decision.py`

## Legacy Cleanup Ledger

Keep these deliberately for now:

- `decide_dispatch_route()` and `DispatchRoute`: still used as the old live comparator.
- `SessionRepository.dispatch()` branch structure: still live source of routing until drift is proven zero.
- FSM-01 shadow tables: still observe-only.

Deletion criteria:

- Delete none in PR-236.
- A later cutover PR may remove the old route comparator only after old/new drift is continuously zero in tests and runtime observation.

## Verification

- `pytest tests/test_pr236_session_fsm_shadow_decision.py tests/test_pr235_session_ledger_shadow.py tests/test_pr233_active_inbox_dispatch.py`
- `pytest`
- `git diff --check`

## Review Result

Pass. The new FSM decision is pure and receives all behavior-changing input
explicitly. Runtime integration only records decision traces in the shadow
ledger; the live action still comes from the existing coordinator branch.

## Rollback

Revert this PR. Shadow `decision_trace` payloads are additive and ignored by
the live path.

# PR-289 — SessionRepository Thin Coordinator

Status: Closed

## Goal

Reduce `SessionRepository` to an application coordinator that wires explicit
ports and transactions, rather than a place where session business state
branches keep accumulating.

## Scope

- Move deterministic branch logic into FSM/reducer helpers.
- Move durable state/event/outbox writes into ledger methods.
- Keep repository responsible for transaction boundaries and explicit adapter
  composition only.

## Dependencies

- PR-285 FSM decision contract.
- PR-288 observed event handler.

## Risks

- Moving too much at once can hide behavior changes.
- Thin coordinator should not become a vague service layer that still owns
  hidden decisions.

## Acceptance Criteria

- `SessionRepository.dispatch` is mostly append event -> decide -> persist
  transition/effects -> return contract.
- `SessionRepository` contains no direct saga creation path and no duplicated
  decision tree.
- Business logic line count decreases or is justified by clearer modules.

## Verification

- Diff review of `session_repo.py`.
- Full runtime suite.

## Closure Notes

- Removed direct saga creation and direct active-state mutation from
  `SessionRepository`; wake creation is now durable outbox + observed handler.
- Moved deterministic pieces into explicit helper modules:
  `session_fsm.py`, `session_wake_plan.py`, `session_projection.py`,
  `session_recovery.py`, `session_effects.py`, and `session_observed_events.py`.
- Moved durable event/state/outbox writes behind `SessionLedgerRepository`
  methods, including atomic attach handoff through `record_transition`.
- Repository still owns orchestration and transaction boundaries, which is the
  intended imperative shell for DB coordination.
- Diff review shows `session_repo.py` shrank substantially while new stable
  infrastructure modules own the reusable logic.
- Verified by full runtime suite: `pytest` in `novaic-agent-runtime` -> 357
  passed.

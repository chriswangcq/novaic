# PR-258 Generic FSM Substrate

Status: Closed

## Goal

Introduce the smallest reusable FSM substrate so Queue session harness logic can
move from session-specific coordination code toward generic event/state/effect
machinery.

## Scope

- Add the architecture ledger for the generic FSM substrate.
- Add a business-agnostic pure FSM core.
- Route the existing session dispatch decision through the generic core.
- Add guard tests for determinism, business-agnostic core naming, and explicit
  dependency boundaries.

## Out Of Scope

- Generic SQLite store/outbox cutover belongs to PR-259.
- Full session repository migration belongs to PR-260.
- Deleting session-specific ledger/outbox shells belongs to PR-261 after the
  store cutover is live.

## Small Tickets

- [x] **FSM-SUB-01 Design ledger**: document state/event/effect vocabulary and
  session mapping.
- [x] **FSM-SUB-02 Pure core**: implement IO-free generic FSM dataclasses and
  transition helper.
- [x] **FSM-SUB-03 Session dispatch adapter**: make `session_fsm.py` use the
  generic transition helper.
- [x] **FSM-SUB-04 Guard tests**: verify deterministic pure behavior and no
  business words in generic core.
- [x] **FSM-SUB-05 Review**: run targeted tests and residue scans.

## Explicit Dependency Boundary Review

Target: compliant.

Allowed explicit inputs:

- `FsmStateSnapshot`
- `FsmEvent`
- reducer function supplied by caller
- optional explicit context mapping

Forbidden hidden inputs:

- clock/time
- UUID/random IDs
- environment variables
- DB/file/network reads
- mutable module globals

## Branch / Old Code Cleanup Ledger

Removed in this PR:

- No runtime file is removed yet; this PR is a substrate extraction cut.

Must be removed by follow-up tickets:

- PR-259: duplicate session-specific event/outbox repository operations after
  generic store exists.
- PR-260: session dispatch/finalize imperative transaction branches that can be
  represented as generic transition application.
- PR-261: compatibility names, old ticket assertions, and session-only wrappers
  once generic store is the only active path.

## Verification

- `pytest tests/test_pr258_generic_fsm_substrate.py tests/test_pr236_session_fsm_decision.py tests/test_pr253_dispatch_pure_fsm_cutover.py`
- `git diff --check`

## Review Result

Pass. Added `queue_service.fsm` as an IO-free generic pure core, routed
`session_fsm.decide_session_dispatch()` through `decide_transition()`, and added
guard tests that block hidden clock/env/random imports and business vocabulary
in the generic core.

## Rollback

Revert PR-258 files and restore `session_fsm.py` to direct dispatch logic.

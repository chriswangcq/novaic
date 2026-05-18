# Generic FSM generation counter classification result

## Summary

Classified widened generation hits in task/saga/lease FSM code as generic machine-version counters rather than Queue session-generation authority. No code changes were made in this ticket.

## Done

- Inspected `task_fsm.py`, `saga_fsm.py`, and `lease_fsm.py` reducer/decision mapping.
- Inspected representative repository adapters in `queue_db.py` and `saga_repo.py`.
- Separated these hits from session-generation authority:
  - `generation=int(decision.next_state.generation)` maps typed generic FSM decisions into DTOs.
  - `generation=int(state.generation) + 1` increments generic FSM state versions inside reducers.
  - `queue_db.py`/`saga_repo.py` conversions reconstruct task/saga/lease runtime state from their own FSM ledgers, not from user/wake session input.

## Verification

- Targeted guard command:
  - `rg -n "generation=int\\(|generation = int|return int\\(current\\.get\\(\"generation\"|int\\(decision\\.generation|int\\(state\\.generation\\)" queue_service/task_fsm.py queue_service/saga_fsm.py queue_service/lease_fsm.py queue_service/queue_db.py queue_service/saga_repo.py`
- Representative code inspected:
  - `task_fsm.py` decision DTO and reducer generation increment.
  - `saga_fsm.py` decision DTO and reducer generation increment.
  - `lease_fsm.py` decision DTO and reducer generation increment.
  - `queue_db.py` task/lease runtime state adapters and transition recorders.
  - `saga_repo.py` saga/lease runtime state adapters and transition recorders.

## Known Gaps

- These generic FSM counters are classified safe relative to Queue session generation, but they are still visually noisy for broad residue guards. A future generic-FSM polish pass could introduce shared counter helpers if the team wants source-level uniformity across all FSM machines.

## Artifacts

- Classification matrix: generic FSM generation hits are safe non-session machine-version counters; no live stale session-generation authority path found here.

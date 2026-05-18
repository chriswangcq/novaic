# Classify generic FSM generation counters

## Problem Definition

Generic task/saga/lease FSM modules contain `generation` counters that show up in widened guards. These must be distinguished from session generation authority and either classified safe or patched if they accept malformed external state.

## Proposed Solution

Inspect generic FSM and repository hits in task/saga/lease/queue DB code. Classify reducer-internal `generation=int(decision.next_state.generation)` and `generation=int(state.generation)+1` as internal FSM version counters when their state snapshots are produced by the generic FSM substrate. Patch only if an unvalidated external input path is found.

## Acceptance Criteria

- Generic FSM generation hits are classified with file evidence.
- No session-generation authority bug is hidden in generic task/saga/lease counters.
- Focused generic FSM tests are run if any code changes are made; otherwise classification evidence is recorded.

## Verification Plan

Run targeted `rg`, inspect representative code in `task_fsm.py`, `saga_fsm.py`, `lease_fsm.py`, `queue_db.py`, and `saga_repo.py`, and record a matrix.

## Risks

- These files are large and contain multiple unrelated counters, so broad automated rewrites would be risky.

## Assumptions

- Generic FSM state generations are separate machine-version counters, not Queue session generations.
